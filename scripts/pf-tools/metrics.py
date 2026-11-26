#!/usr/bin/env python3
"""portfolio/portfolio.md + Yahoo 시세 → 비율 전용 파생지표 마크다운.

사용: python3 -I scripts/pf-tools/metrics.py portfolio/portfolio.md content/reports/_parts/{날짜}/portfolio-metrics.md {날짜}

- 출력에는 절대금액이 없다(비중·수익률·%p만). 그래도 출력 파일은 _parts/(커밋 안 함)에 둔다.
- 시트가 갱신되지 않았으면 "시트 평가액 × (현재가 ÷ 시트 기준일 종가)"로 추정한다.
- 연금 3계좌(연금저축·IRP·퇴직연금) = 자산배분·리밸런싱 → 목표비중 대비 괴리와 밴드 판정을 계산.
- ISA = 추세추종 → 비중·수익률만 계산(추세 신호는 trend.md에서 etf 섹션이 붙인다).
"""
import datetime as dt
import json
import re
import subprocess
import sys
import time

# 종목명 키워드 → (티커, 자산군). 위에서부터 먼저 맞는 것을 쓴다(구체적인 것 먼저).
TICKERS = [
    ('S&P500 헬스케어', '453640', '미국주식'),
    ('은행고배당', '466940', '한국주식'),
    ('미국채 10년', '305080', '미국채권'),
    ('미국채10년', '305080', '미국채권'),
    ('30년국채', '476760', '미국채권'),
    ('미국배당미국채혼합', '490490', '혼합'),
    ('200 미국채혼합', '284430', '혼합'),
    ('200미국채혼합', '284430', '혼합'),
    ('미국배당다우존스', None, '미국주식(배당)'),  # 운용사별로 아래에서 분기
    ('미국 S&P500', '360750', '미국주식'),
    ('미국S&P500', '360750', '미국주식'),
    ('나스닥100', '133690', '미국주식'),
    ('금현물', '411060', '금'),
    ('200TR', '294400', '한국주식'),
    ('달러단기채권', '329750', '달러/현금'),
    ('달러SOFR', '456610', '달러/현금'),
    ('AI데이터센터', '0142D0', '테마'),
    ('반도체TOP4', '446770', '테마'),
    ('조선TOP3', '466920', '테마'),
    ('AI전력', '487230', '테마'),
]
PENSION = ['연금저축펀드', '개인IRP', '퇴직연금']
TREND_ACCT = 'ISA'


def lookup(name):
    if name == '현금':
        return None, '달러/현금'
    for key, tic, cls in TICKERS:
        if key.replace(' ', '').lower() in name.replace(' ', '').lower():
            if key == '미국배당다우존스':
                tic = '446720' if name.upper().startswith('SOL') else '458730'
            return tic, cls
    return 'UNKNOWN', '기타'


def fetch(tic):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{tic}.KS?range=6mo&interval=1d'
    for host in ('query1', 'query2'):
        try:
            raw = subprocess.run(['curl', '-s', '--max-time', '20', '-A', 'Mozilla/5.0',
                                  url.replace('query1', host)], capture_output=True, text=True).stdout
            r = json.loads(raw)['chart']['result'][0]
            kst = dt.timezone(dt.timedelta(hours=9))
            return sorted((dt.datetime.fromtimestamp(t, kst).date(), c)
                          for t, c in zip(r['timestamp'], r['indicators']['quote'][0]['close']) if c)
        except Exception:
            time.sleep(2)
    return None


def close_on(series, day):
    vals = [(d, c) for d, c in series if d <= day]
    return vals[-1] if vals else None


def band(target):
    """5/25 규칙: 목표 20% 이상은 ±5%p, 20% 미만은 목표의 ±25%(최소 1%p)."""
    return 5.0 if target >= 20 else max(1.0, target * 0.25)


def main(pf_path, out_path, report_date):
    today = dt.date.fromisoformat(report_date)
    text = open(pf_path, encoding='utf-8').read()
    m = re.search(r'sheet date:\s*(\d+)월\s*(\d+)일', text)
    sheet_day = dt.date(today.year, int(m.group(1)), int(m.group(2))) if m else today
    if sheet_day > today:
        sheet_day = sheet_day.replace(year=today.year - 1)

    accts, cur = {}, None
    for line in text.splitlines():
        if line.startswith('## '):
            cur = line[3:].strip(); accts[cur] = []
        elif cur and line.startswith('| ') and not line.startswith('| 종목명'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            name, dep, val = cells[0], int(cells[1]), int(cells[2])
            tgt = float(cells[3]) if len(cells) > 3 and cells[3] else None
            if dep == 0 and val == 0 and not tgt:
                continue
            tic, cls = lookup(name)
            accts[cur].append(dict(name=name, dep=dep, val=val, tgt=tgt, tic=tic, cls=cls))

    tics = sorted({h['tic'] for a in accts.values() for h in a if h['tic'] not in (None, 'UNKNOWN')})
    px, failed = {}, []
    for i, t in enumerate(tics):
        s = fetch(t)
        (px.__setitem__(t, s) if s else failed.append(t))
        time.sleep(1 if (i + 1) % 9 else 4)

    prev_day = today - dt.timedelta(days=7)
    dates = {}

    def value(h, day):
        if h['tic'] is None or h['tic'] not in px:
            return h['val']
        base, now = close_on(px[h['tic']], sheet_day), close_on(px[h['tic']], day)
        if not base or not now:
            return h['val']
        dates.setdefault(day, now[0])
        return h['val'] * now[1] / base[1]

    for a in accts.values():
        for h in a:
            h['v0'], h['v1'], h['v2'] = h['val'], value(h, prev_day), value(h, today)

    tot = {k: sum(h[k] for a in accts.values() for h in a) for k in ('v0', 'v1', 'v2')}
    dep_all = sum(h['dep'] for a in accts.values() for h in a)
    stale = (today - sheet_day).days
    d1, d2 = dates.get(prev_day, prev_day), dates.get(today, today)
    o = ['# 포트폴리오 파생지표 (비율만 — 절대금액 없음)', '',
         f'- 시트 기준일: {sheet_day} ({stale}일 전{" — 갱신 안 됨, 아래는 가격 변화로 추정" if stale > 3 else ""})',
         f'- 가격 기준: 지난주 {d1} / 이번 주 {d2} 종가 (Yahoo)',
         f'- 시세 실패: {", ".join(failed) or "없음"} / 매핑 안 된 종목: '
         f'{", ".join(h["name"] for a in accts.values() for h in a if h["tic"] == "UNKNOWN") or "없음"}', '',
         f'**전체 누적 수익률** 지난주 {tot["v1"] / dep_all - 1:+.2%} → 이번 주 {tot["v2"] / dep_all - 1:+.2%} '
         f'/ **이번 주 변화** {tot["v2"] / tot["v1"] - 1:+.2%}', '',
         '## 계좌별', '| 계좌 | 운용 방식 | 전체 비중 | 누적 수익률 | 이번 주 | 전체 기여(%p) |', '|---|---|---|---|---|---|']
    for k, a in accts.items():
        v1, v2, dp = sum(h['v1'] for h in a), sum(h['v2'] for h in a), sum(h['dep'] for h in a)
        mode = '추세추종' if k == TREND_ACCT else '자산배분·리밸런싱'
        o.append(f'| {k} | {mode} | {v2 / tot["v2"]:.1%} | {v2 / dp - 1:+.2%} | {v2 / v1 - 1:+.2%} | '
                 f'{(v2 - v1) / tot["v1"] * 100:+.2f} |')

    o += ['', '## A. 연금 3계좌 — 목표 비중 대비 괴리 (리밸런싱 판정)',
          '판정 밴드 = 5/25 규칙: 목표 20% 이상은 ±5%p, 20% 미만은 목표의 ±25%(최소 ±1%p). '
          '목표가 시트에 없으면 **입금 비중을 목표 대용**으로 쓴다.']
    for k in PENSION:
        a = accts.get(k, [])
        if not a:
            continue
        v2, dp = sum(h['v2'] for h in a), sum(h['dep'] for h in a)
        has_tgt = any(h['tgt'] for h in a)
        tsum = sum(h['tgt'] or 0 for h in a)
        o += ['', f'### {k}' + ('' if has_tgt else ' (시트 목표 미설정 → 입금 비중 대용)')]
        if has_tgt and abs(tsum - 100) > 0.5:
            o.append(f'> 시트 목표 합계 {tsum:g}% — {100 - tsum:+g}%p 미배정. 비교는 시트 값 그대로 한다.')
        o += ['| 종목 | 자산군 | 목표 | 현재 | 괴리 | 밴드 | 판정 | 누적 수익률 | 이번 주 |', '|---|---|---|---|---|---|---|---|---|']
        flags = []
        for h in sorted(a, key=lambda x: -x['v2']):
            t = h['tgt'] if has_tgt else h['dep'] / dp * 100
            t = t or 0.0
            w = h['v2'] / v2 * 100
            gap, b = w - t, band(t) if t else 1.0
            mark = '✅ 밴드 안' if abs(gap) <= b else ('⬆️ 초과' if gap > 0 else '⬇️ 부족')
            if abs(gap) > b:
                flags.append((h['name'], gap))
            ret = h['v2'] / h['dep'] - 1 if h['dep'] else 0
            wk = h['v2'] / h['v1'] - 1 if h['v1'] else 0
            o.append(f'| {h["name"]} | {h["cls"]} | {t:.1f}% | {w:.1f}% | {gap:+.1f}%p | ±{b:.1f}%p | {mark} | {ret:+.2%} | {wk:+.2%} |')
        under = sorted([(h['name'], (h['tgt'] if has_tgt else h['dep'] / dp * 100) - h['v2'] / v2 * 100) for h in a
                        if h['name'] != '현금'], key=lambda x: -x[1])
        o.append('')
        o.append(f'- 밴드 이탈: {", ".join(f"{n} {g:+.1f}%p" for n, g in flags) or "없음 → 이번 주 리밸런싱 불필요"}')
        o.append(f'- 신규 납입 우선순위(가장 모자란 순): {", ".join(f"{n}({g:+.1f}%p)" for n, g in under[:3] if g > 0) or "모두 목표 이상"}')

    a = accts.get(TREND_ACCT, [])
    if a:
        v2, v1 = sum(h['v2'] for h in a), sum(h['v1'] for h in a)
        o += ['', f'## B. {TREND_ACCT} — 추세추종 계좌 (추세 신호는 trend.md에서 붙인다)',
              f'계좌 이번 주 {v2 / v1 - 1:+.2%}, 누적 {v2 / sum(h["dep"] for h in a) - 1:+.2%}', '',
              '| 종목 | 티커 | 자산군 | 계좌내 비중 | 누적 수익률 | 이번 주 |', '|---|---|---|---|---|---|']
        for h in sorted(a, key=lambda x: -x['v2']):
            o.append(f'| {h["name"]} | {h["tic"] or "-"} | {h["cls"]} | {h["v2"] / v2:.1%} | '
                     f'{h["v2"] / h["dep"] - 1 if h["dep"] else 0:+.2%} | {h["v2"] / h["v1"] - 1 if h["v1"] else 0:+.2%} |')

    cls = {}
    for acc in accts.values():
        for h in acc:
            c = cls.setdefault(h['cls'], [0, 0, 0]); c[0] += h['v1']; c[1] += h['v2']; c[2] += h['dep']
    o += ['', '## 자산군별 (전체)', '| 자산군 | 비중 | 이번 주 | 기여(%p) | 누적 수익률 |', '|---|---|---|---|---|']
    for c, (v1, v2, dp) in sorted(cls.items(), key=lambda x: -x[1][1]):
        o.append(f'| {c} | {v2 / tot["v2"]:.1%} | {v2 / v1 - 1:+.2%} | {(v2 - v1) / tot["v1"] * 100:+.2f} | {v2 / dp - 1:+.2%} |')

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(o) + '\n')
    print('\n'.join(o))


if __name__ == '__main__':
    main(*sys.argv[1:4])
