#!/usr/bin/env python3
"""구글시트 CSV → portfolio/portfolio.md (로컬 전용, 커밋 금지 파일을 만든다).

사용: python3 -I scripts/pf-tools/parse_sheet.py portfolio/_sheet_gid0.csv portfolio/portfolio.md

시트 구조(계좌 블록):
  헤더 행  : col1=계좌명, col2=="입금금액"
  종목 행  : col1=종목명, col2=입금금액, col4=평가금액, col7=목표비중(%) (리밸런싱 열, 없으면 빈칸)
  합계 행  : col1 빈칸 → 블록 종료
출력 표에는 목표비중 열을 함께 남긴다(빈칸 = 시트에 목표 미설정).
"""
import csv
import sys

ACCOUNTS = ['연금저축펀드', '개인IRP', '퇴직연금', 'ISA']


def to_int(s):
    s = (s or '').replace(',', '').strip()
    return int(s) if s.lstrip('-').isdigit() else None


def to_pct(s):
    s = (s or '').replace('%', '').strip()
    try:
        return float(s)
    except ValueError:
        return None


def main(src, dst):
    rows = [r + [''] * 10 for r in csv.reader(open(src, encoding='utf-8'))]
    sheet_date = next((r[1] for r in rows if r[0].strip() == '날짜'), '')
    out = [f'<!-- sheet date: {sheet_date} -->']
    cur = None
    for r in rows:
        name = r[1].strip()
        if name in ACCOUNTS and r[2].strip() == '입금금액':
            cur = name
            out += ['', f'## {cur}', '| 종목명 | 입금금액 | 평가금액 | 목표비중(%) |', '|---|---|---|---|']
            continue
        if not cur:
            continue
        if not name:
            # 합계 행(입금 합계가 있고 비중 100%)이면 블록 종료
            if to_int(r[2]) is not None and r[3].strip().startswith('100'):
                cur = None
            continue
        dep, val = to_int(r[2]), to_int(r[4])
        if dep is None or val is None:
            cur = None  # 계좌 블록 아래의 메모·자산군 표 등
            continue
        tgt = to_pct(r[7])
        out.append(f"| {name} | {dep} | {val} | {'' if tgt is None else f'{tgt:g}'} |")
    with open(dst, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    print(f'✓ {dst} 저장 (시트 날짜: {sheet_date})')


if __name__ == '__main__':
    main(*sys.argv[1:3])
