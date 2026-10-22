# -*- coding: utf-8 -*-
"""월간 거시 리포트용 데이터 수집 + 차트 생성.

한국은행 ECOS OpenAPI와 Yahoo Finance에서 6개 축(GDP·수출입·심리·물가·금리·환율)의
원데이터를 받아 수치 요약(markdown)과 차트 PNG를 _parts/{발행일}/ 아래에 쓴다.
해석·집필은 하지 않는다 — 그건 agents/macro-monthly.md 가 맡는다.

사용법:
    python scripts/macro/fetch_and_chart.py [YYYY-MM-DD]

인증키는 환경변수 ECOS_API_KEY, 없으면 ~/.config/ecos/key 에서 읽는다(저장소에 두지 않는다).
"""
import os, sys, json, warnings
from pathlib import Path
from datetime import date

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import koreanize_matplotlib  # noqa: F401  (한글 폰트)
from PublicDataReader import Ecos

ROOT = Path(__file__).resolve().parents[2]
PUB_DATE = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
OUTDIR = ROOT / "content" / "reports" / "_parts" / PUB_DATE
CHARTS = OUTDIR / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)


def service_key():
    k = os.environ.get("ECOS_API_KEY")
    if k:
        return k.strip()
    p = Path.home() / ".config" / "ecos" / "key"
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    sys.exit("ECOS 인증키를 찾을 수 없습니다. 환경변수 ECOS_API_KEY 또는 ~/.config/ecos/key 를 설정하세요.")


api = Ecos(service_key())

# Yahoo Finance: 사내 프록시가 SSL을 가로채는 환경에서는 기본 검증이 실패한다.
# 먼저 정상 세션으로 시도하고, 실패하면 검증을 끈 세션으로 재시도한다.
def yahoo_session():
    from curl_cffi import requests as cr
    import yfinance as yf
    for verify in (True, False):
        s = cr.Session(impersonate="chrome", verify=verify)
        try:
            probe = yf.download("^GSPC", period="5d", progress=False, auto_adjust=True, session=s)
            if not probe.empty:
                if not verify:
                    print("  ! Yahoo Finance: SSL 검증을 끄고 접속(사내 프록시 추정)")
                return s
        except Exception:
            continue
    sys.exit("Yahoo Finance에 접속할 수 없습니다.")


# ---------------------------------------------------------------- 공통 유틸
def ecos(code, cycle, start, end):
    d = api.get_statistic_search(통계표코드=code, 주기=cycle, 검색시작일자=start, 검색종료일자=end)
    d["값"] = pd.to_numeric(d["값"], errors="coerce")
    return d


def pv(d, col="통계항목명1"):
    return d.pivot_table(index="시점", columns=col, values="값")


def q_range(years=12):
    y = date.today().year
    return f"{y - years}Q1", f"{y + 1}Q4"


def m_range(years=4):
    y = date.today().year
    return f"{y - years}01", f"{y + 1}12"


# ---------------------------------------------------------------- 차트 스타일
BG, SURF, BORDER = "#f7f8fa", "#ffffff", "#e3e7ee"
TEXT, SOFT = "#1a2230", "#5a6474"
ACC, POS, NEG, WARN = "#1f4e79", "#137a4b", "#c0392b", "#b8860b"
SERIES = [ACC, NEG, POS, WARN, "#6b7fa3", "#8e44ad"]

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF,
    "axes.edgecolor": BORDER, "axes.labelcolor": TEXT,
    "text.color": TEXT, "xtick.color": SOFT, "ytick.color": SOFT,
    "grid.color": BORDER, "axes.grid": True, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
    "legend.frameon": False, "figure.dpi": 130, "savefig.dpi": 130,
    "savefig.bbox": "tight", "savefig.facecolor": SURF,
})


def finish(fig, name, note=None):
    if note:
        fig.text(0.01, -0.02, note, fontsize=8.5, color=SOFT, ha="left")
    fig.savefig(CHARTS / name)
    plt.close(fig)
    print(f"  차트 {name}")


# ---------------------------------------------------------------- 수집 + 차트
md = []          # 수치 요약 markdown
fresh = {}       # 계열별 최신 시점


def to_md(df):
    """DataFrame → 파이프 테이블(markdown). tabulate 의존을 피한다."""
    d = df.copy()
    d.index = [str(i) for i in d.index]
    cols = [str(c) for c in d.columns]
    head = "| " + " | ".join([d.index.name or ""] + cols) + " |"
    sep = "|" + "---|" * (len(cols) + 1)
    rows = []
    for idx, row in d.iterrows():
        vals = ["" if pd.isna(v) else (f"{v:,.2f}".rstrip("0").rstrip(".") if isinstance(v, (int, float, np.floating)) else str(v))
                for v in row]
        rows.append("| " + " | ".join([idx] + vals) + " |")
    return "\n".join([head, sep] + rows)


def section(title):
    md.append(f"\n## {title}\n")


def table(df, caption):
    md.append(f"\n**{caption}**\n")
    md.append(to_md(df))
    md.append("")


def main():
    qs, qe = q_range()
    ms, me = m_range()

    # ===================================================== 1. GDP
    print("[1/6] GDP")
    n, r = ecos("200Y107", "Q", qs, qe), ecos("200Y108", "Q", qs, qe)
    pn, pr = pv(n), pv(r)
    g = "국내총생산에 대한 지출"
    fresh["GDP"] = pr.index.max()

    section("1. GDP")
    cols = ["최종소비지출", "가계", "정부", "총자본형성", "건설투자", "설비투자",
            "지식재산생산물투자", "재화와 서비스의 수출", "(공제)재화와 서비스의 수입", g]
    cols = [c for c in cols if c in pr.columns]
    table((pr[cols].pct_change(4) * 100).tail(8).round(2), "실질 전년동기비(%)")
    table((pn[cols].pct_change(4) * 100).tail(8).round(2), "명목 전년동기비(%)")

    defl = pn[g] / pr[g] * 100
    table(pd.DataFrame({"디플레이터": defl.round(2),
                        "전년동기비%": (defl.pct_change(4) * 100).round(2)}).tail(8),
          "GDP 디플레이터")

    base = pr[g].shift(1)
    contrib = pd.DataFrame({
        "최종소비": pr["최종소비지출"].diff() / base * 100,
        "총자본형성": pr["총자본형성"].diff() / base * 100,
        "순수출": (pr["재화와 서비스의 수출"].diff()
                 - pr["(공제)재화와 서비스의 수입"].diff()) / base * 100,
    })
    contrib["GDP(전기비)"] = pr[g].pct_change() * 100
    table(contrib.tail(8).round(2), "실질 전기비 성장 기여도(%p)")

    ri = ecos("200Y104", "Q", qs, qe)
    pri = pv(ri)
    ind_yoy = (pri.pct_change(4) * 100).tail(4).round(2)
    table(ind_yoy.T.sort_values(ind_yoy.index[-1], ascending=False),
          "경제활동별 실질 전년동기비(%) — 전체 업종")

    # 차트 01
    real_y, nom_y = pr[g].pct_change(4) * 100, pn[g].pct_change(4) * 100
    defl_y = defl.pct_change(4) * 100
    w = real_y.index[-18:]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(w, defl_y[w], color=WARN, alpha=.35, label="GDP 디플레이터 (전년동기비)", width=.6)
    ax.plot(w, real_y[w], color=ACC, marker="o", ms=4, lw=2.2, label="실질 GDP (전년동기비)")
    ax.plot(w, nom_y[w], color=NEG, marker="o", ms=4, lw=2.2, label="명목 GDP (전년동기비)")
    ax.axhline(0, color=SOFT, lw=1)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_title("명목·실질 GDP 성장률과 디플레이터")
    plt.xticks(rotation=45, ha="right"); ax.legend(loc="upper left")
    finish(fig, "01-gdp-nominal-real.png", "자료: 한국은행 ECOS 200Y107/200Y108")

    # 차트 02
    c = contrib.tail(10)
    fig, ax = plt.subplots(figsize=(11, 5))
    bp = np.zeros(len(c)); bn = np.zeros(len(c))
    for col, color in zip(["최종소비", "총자본형성", "순수출"], [ACC, WARN, POS]):
        v = c[col].values
        p_, n_ = np.where(v > 0, v, 0), np.where(v < 0, v, 0)
        ax.bar(c.index, p_, bottom=bp, color=color, label=col, width=.65)
        ax.bar(c.index, n_, bottom=bn, color=color, width=.65)
        bp += p_; bn += n_
    ax.plot(c.index, c["GDP(전기비)"].values, color=TEXT, marker="D", ms=4, lw=1.8, label="실질 GDP 전기비")
    ax.axhline(0, color=SOFT, lw=1); ax.set_ylabel("%p")
    ax.set_title("실질 GDP 전기비 성장 기여도")
    plt.xticks(rotation=45, ha="right"); ax.legend(ncol=4, loc="upper left")
    finish(fig, "02-gdp-contribution.png", "자료: 한국은행 ECOS 200Y108 (기여도 = 항목 증감 ÷ 직전분기 GDP)")

    # 차트 03
    last_q = ind_yoy.index[-1]
    s = ind_yoy.loc[last_q].dropna().sort_values()
    s = pd.concat([s.head(5), s.tail(6)])
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.barh(range(len(s)), s.values,
            color=[NEG if v < 0 else (ACC if v < 10 else POS) for v in s.values], height=.65)
    ax.set_yticks(range(len(s)))
    ax.set_yticklabels([t.replace(" 제조업", "\n제조업") for t in s.index], fontsize=9.5)
    for i, v in enumerate(s.values):
        ax.text(v + (0.4 if v >= 0 else -0.4), i, f"{v:+.1f}%", va="center",
                ha="left" if v >= 0 else "right", fontsize=9.5, color=TEXT, fontweight="bold")
    ax.axvline(0, color=SOFT, lw=1)
    pad = max(abs(s.min()), abs(s.max())) * 0.35
    ax.set_xlim(s.min() - pad, s.max() + pad)
    ax.grid(axis="y", visible=False)
    ax.set_title(f"{last_q} 경제활동별 실질 성장률 (전년동기비) — 상·하위")
    finish(fig, "03-industry-growth.png", "자료: 한국은행 ECOS 200Y104")

    # ===================================================== 2. 수출입
    print("[2/6] 수출입")
    section("2. 수출입")
    t = ecos("901Y121", "M", ms, me)
    ex = t[t["통계항목명1"] == "수출금액"].groupby("시점")["값"].sum().sort_index()
    im = t[t["통계항목명1"] == "수입금액"].groupby("시점")["값"].sum().sort_index()
    fresh["수출입(상대국)"] = ex.index.max()
    trade = pd.DataFrame({"수출": ex, "수입": im, "무역수지": ex - im,
                          "수출yoy%": ex.pct_change(12) * 100,
                          "수입yoy%": im.pct_change(12) * 100})
    table(trade.tail(14).round(1), "수출입 총액(백만달러)과 무역수지")

    for kind, label in [("수출금액", "수출"), ("수입금액", "수입")]:
        d = t[t["통계항목명1"] == kind].copy()
        tot = d.groupby("시점")["값"].sum().rename("tot")
        d = d.join(tot, on="시점"); d["ratio"] = d["값"] / d["tot"] * 100
        p = d.pivot_table(index="시점", columns="통계항목명2", values="ratio")
        top = p.iloc[-1].sort_values(ascending=False).head(10).index
        table(p[top].tail(6).round(1), f"{label} 상대국 비중(%) 상위10")
        pvv = d.pivot_table(index="시점", columns="통계항목명2", values="값")
        table((pvv[top].pct_change(12) * 100).tail(4).round(1), f"{label} 상위 상대국 전년동월비(%)")

    amt = ecos("403Y001", "M", ms, me)   # 수출금액지수
    vol = ecos("403Y002", "M", ms, me)   # 수출물량지수
    ta = amt[amt["통계항목명1"] == "총지수"].set_index("시점")["값"].sort_index()
    tv = vol[vol["통계항목명1"] == "총지수"].set_index("시점")["값"].sort_index()
    unit = ta / tv * 100
    fresh["수출입지수"] = ta.index.max()
    decomp = pd.DataFrame({"금액지수yoy%": ta.pct_change(12) * 100,
                           "물량지수yoy%": tv.pct_change(12) * 100,
                           "단가yoy%": unit.pct_change(12) * 100})
    table(decomp.tail(12).round(1), "수출 증가의 분해 (단가 = 금액지수 ÷ 물량지수)")

    tt = pv(ecos("403Y005", "M", ms, me))
    table(tt.tail(12).round(1), "교역조건지수")

    # 차트 04
    w = ex.index[-22:]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(w, (ex - im)[w] / 1000, color=POS, alpha=.35, label="무역수지(좌)", width=.65)
    ax2 = ax.twinx(); ax2.grid(False)
    ax2.plot(w, ex[w] / 1000, color=ACC, marker="o", ms=3.5, lw=2.2, label="수출")
    ax2.plot(w, im[w] / 1000, color=NEG, marker="o", ms=3.5, lw=2.2, label="수입")
    ax.set_ylabel("무역수지 (억달러)", color=POS); ax2.set_ylabel("수출입 (억달러)")
    ax.set_title("수출입 금액과 무역수지")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h2 + h1, l2 + l1, loc="upper left", ncol=3)
    ax.set_xticks(w[::2]); ax.set_xticklabels(w[::2], rotation=45, ha="right")
    finish(fig, "04-trade-balance.png", "자료: 한국은행 ECOS 901Y121 (상대국 합산)")

    # 차트 05
    w = decomp.index[-22:]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(w, decomp.loc[w, "물량지수yoy%"], color=ACC, alpha=.75, label="물량 기여", width=.65)
    ax.bar(w, decomp.loc[w, "단가yoy%"], bottom=decomp.loc[w, "물량지수yoy%"],
           color=WARN, alpha=.8, label="단가(가격) 기여", width=.65)
    ax.plot(w, decomp.loc[w, "금액지수yoy%"], color=NEG, marker="o", ms=4, lw=2.4,
            label="수출금액 (전년동월비)")
    ax.axhline(0, color=SOFT, lw=1)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_title(f"수출 증가의 분해 — {w[-1]} 물량 {decomp['물량지수yoy%'].iloc[-1]:+.0f}% · "
                 f"단가 {decomp['단가yoy%'].iloc[-1]:+.0f}%")
    plt.xticks(rotation=45, ha="right"); ax.legend(loc="upper left", ncol=3)
    finish(fig, "05-export-price-volume.png",
           "자료: 한국은행 ECOS 403Y001(금액지수), 403Y002(물량지수). 막대 합과 선의 차이는 물량×단가 교차항")

    # 차트 05b
    w = tt.index[-22:]
    fig, ax = plt.subplots(figsize=(11, 5))
    for col, color in zip(["순상품교역조건지수", "소득교역조건지수"], [ACC, NEG]):
        if col in tt.columns:
            ax.plot(w, tt.loc[w, col], color=color, marker="o", ms=4, lw=2.4, label=col)
    ax.axhline(100, color=TEXT, lw=1.2, ls="--")
    ax.set_title("교역조건지수")
    plt.xticks(rotation=45, ha="right"); ax.legend(loc="upper left")
    finish(fig, "05b-terms-of-trade.png", "자료: 한국은행 ECOS 403Y005")

    # ===================================================== 3. 심리
    print("[3/6] 심리지표")
    section("3. 심리지표")
    keep = ["전 산 업", "제 조 업", "대 기 업", "중소기업", "수출기업", "내수기업", "비제조업", "서비스업"]
    for code, m in [("512Y013", "기업심리지수실적"), ("512Y014", "기업심리지수전망")]:
        d = ecos(code, "M", ms, me)
        d = d[(d["통계항목명2"] == m) & (d["통계항목명1"].isin(keep))]
        p = pv(d)
        fresh[m] = p.index.max()
        table(p.tail(12).round(1), f"BSI {m}")
        if m == "기업심리지수실적":
            bsi = p

    bm = ecos("512Y013", "M", ms, me)
    bm = bm[bm["통계항목명1"] == "제 조 업"]
    pm = pv(bm, col="통계항목명2")
    table(pm.tail(8).round(0), "제조업 세부 BSI 실적")

    cs = ecos("511Y002", "M", ms, me)
    cs = cs[cs["통계항목명2"] == "전체"]
    pcs = pv(cs)
    fresh["CSI"] = pcs.index.max()
    table(pcs.tail(12).round(1), "소비자동향조사(CSI)")

    # 차트 06
    cols = [c for c in ["제 조 업", "수출기업", "내수기업", "중소기업", "서비스업"] if c in bsi.columns]
    w = bsi.index[-22:]
    fig, ax = plt.subplots(figsize=(11, 5))
    for col, color in zip(cols, SERIES):
        ax.plot(w, bsi.loc[w, col], marker="o", ms=3.5, lw=2, color=color, label=col.replace(" ", ""))
    ax.axhline(100, color=TEXT, lw=1.2, ls="--")
    ax.set_title("기업심리지수(BSI) 실적")
    plt.xticks(rotation=45, ha="right"); ax.legend(ncol=5, loc="lower left")
    finish(fig, "06-bsi.png", "자료: 한국은행 ECOS 512Y013")

    # 차트 07
    w = pm.index[-22:]
    pairs = [("원자재구입가격실적BSI 4)", NEG, "원자재구입가격 BSI", "-"),
             ("제품판매가격실적BSI 4)", ACC, "제품판매가격 BSI", "-"),
             ("채산성실적BSI 6)", WARN, "채산성 BSI", "--")]
    fig, ax = plt.subplots(figsize=(11, 5))
    for col, color, label, ls in pairs:
        if col in pm.columns:
            ax.plot(w, pm.loc[w, col], color=color, marker="o", ms=4, lw=2.2, ls=ls, label=label)
    ax.axhline(100, color=TEXT, lw=1.2, ls="--")
    ax.set_title("제조업 가격 BSI — 원가 전가력과 마진")
    plt.xticks(rotation=45, ha="right"); ax.legend(loc="upper right")
    finish(fig, "07-bsi-price.png", "자료: 한국은행 ECOS 512Y013 (제조업)")

    # ===================================================== 4. 물가
    print("[4/6] 물가")
    section("4. 물가")
    cpi, ppi = ecos("901Y010", "M", ms, me), ecos("404Y014", "M", ms, me)
    pc, pp = pv(cpi), pv(ppi)
    fresh["CPI"], fresh["PPI"] = pc.index.max(), pp.index.max()
    core = next((c for c in pc.columns if c.startswith("식료품 및 에너지제외")), None)
    cc = [c for c in ["총지수", core, "농축수산물", "공업제품", "석유류", "서비스", "집세", "외식"] if c]
    cc = [c for c in cc if c in pc.columns]
    table((pc[cc].pct_change(12) * 100).tail(12).round(2), "CPI 전년동월비(%)")
    table(pd.DataFrame({"PPI": pp["총지수"],
                        "yoy%": pp["총지수"].pct_change(12) * 100}).tail(12).round(2), "PPI 총지수")
    ppi["len"] = ppi["통계항목코드1"].str.len()
    p3 = pv(ppi[(ppi["len"] == 3) & (ppi["통계항목명1"] != "총지수")])
    table((p3.pct_change(12) * 100).tail(6).round(2), "PPI 대분류 전년동월비(%)")

    cpi_y = pc["총지수"].pct_change(12) * 100
    core_y = pc[core].pct_change(12) * 100 if core else None
    ppi_y = pp["총지수"].pct_change(12) * 100

    # 차트 08
    w = cpi_y.index[-22:]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.fill_between(w, cpi_y[w], ppi_y[w], color=NEG, alpha=.13, label="PPI - CPI 격차")
    ax.plot(w, ppi_y[w], color=NEG, marker="o", ms=4, lw=2.4, label="생산자물가(PPI)")
    ax.plot(w, cpi_y[w], color=ACC, marker="o", ms=4, lw=2.4, label="소비자물가(CPI)")
    if core_y is not None:
        ax.plot(w, core_y[w], color=SOFT, marker="^", ms=3.5, lw=1.8, ls="--", label="근원 CPI")
    ax.axhline(2, color=POS, lw=1.2, ls=":")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_title(f"CPI vs PPI 전년동월비 — 격차 {ppi_y.iloc[-1] - cpi_y.iloc[-1]:.1f}%p")
    plt.xticks(rotation=45, ha="right"); ax.legend(loc="upper left")
    finish(fig, "08-cpi-ppi.png", "자료: 한국은행 ECOS 901Y010, 404Y014")

    # ===================================================== 5. 금리
    print("[5/6] 금리")
    section("5. 금리")
    kr = ecos("722Y001", "M", ms, me)
    kr = kr[kr["통계항목명1"] == "한국은행 기준금리"].set_index("시점")["값"].sort_index().rename("기준금리")
    bk = ecos("121Y006", "M", ms, me)
    bk = bk[bk["통계항목명1"].isin(["기업대출", "가계대출", "주택담보대출"])]
    tbl = pv(bk).join(kr).dropna(subset=["기준금리"])
    fresh["기준금리"], fresh["은행대출금리"] = kr.index.max(), pv(bk).index.max()
    for c in ["가계대출", "기업대출", "주택담보대출"]:
        if c in tbl.columns:
            tbl["스프레드_" + c] = tbl[c] - tbl["기준금리"]
    table(tbl.tail(14).round(2), "기준금리 vs 은행 대출금리(%)")

    fm = ecos("902Y006", "M", ms, me)
    fm = fm[fm["통계항목명1"].isin(["미국", "유로 지역", "일본", "중국", "한국"])]
    table(pv(fm).tail(10).round(2), "주요국 정책금리(%)")

    # 차트 09
    w = tbl.index[-22:]
    fig, (ax, axb) = plt.subplots(2, 1, figsize=(11, 7), sharex=True,
                                  gridspec_kw={"height_ratios": [2, 1.1]})
    for col, color in [("가계대출", NEG), ("주택담보대출", WARN), ("기업대출", POS)]:
        if col in tbl.columns:
            ax.plot(w, tbl.loc[w, col], color=color, marker="o", ms=3.5, lw=2.2, label=col)
    ax.step(w, tbl.loc[w, "기준금리"], color=ACC, lw=2.6, where="mid", label="한국은행 기준금리")
    ax.set_ylabel("%"); ax.legend(ncol=4, loc="upper left")
    ax.set_title("기준금리와 은행 대출금리")
    sp = tbl.loc[w, "가계대출"] - tbl.loc[w, "기준금리"]
    axb.bar(w, sp, color=ACC, alpha=.45, width=.65)
    axb.set_ylabel("스프레드 (%p)", fontsize=10)
    axb.set_title("가계대출 - 기준금리 스프레드", fontsize=11, loc="left", pad=6)
    axb.set_ylim(sp.min() - .08, sp.max() + .08)
    plt.xticks(rotation=45, ha="right")
    finish(fig, "09-rates.png", "자료: 한국은행 ECOS 722Y001, 121Y006")

    # ===================================================== 6. 환율·시장
    print("[6/6] 환율·시장")
    section("6. 환율·대외부문·시장")
    import yfinance as yf
    sess = yahoo_session()
    tk = ["^GSPC", "^KS11", "^FVX", "^TNX", "^TYX", "DX-Y.NYB", "USDKRW=X",
          "CL=F", "BZ=F", "GC=F", "HG=F"]
    mk = yf.download(tk, start=f"{date.today().year - 3}-01-01", progress=False,
                     auto_adjust=True, session=sess)["Close"].ffill().dropna()
    mk["30y-5y"] = mk["^TYX"] - mk["^FVX"]
    mk["10y-5y"] = mk["^TNX"] - mk["^FVX"]
    fresh["시장데이터"] = str(mk.index.max().date())
    table(mk.tail(5).round(2), "시장지표 최근 5영업일")
    table(mk.resample("ME").mean().tail(15).round(2), "시장지표 월평균")

    last = mk.iloc[-1]
    chg = {}
    ytd_ref = mk[mk.index >= f"{date.today().year}-01-01"]
    for lbl, ref in [("1M", mk.iloc[-22]), ("3M", mk.iloc[-63]),
                     ("YTD", ytd_ref.iloc[0] if len(ytd_ref) else mk.iloc[0]),
                     ("1Y", mk.iloc[-252] if len(mk) > 252 else mk.iloc[0])]:
        chg[lbl + "_%"] = ((last / ref - 1) * 100).round(2)
        chg[lbl + "_차이"] = (last - ref).round(2)
    table(pd.DataFrame(chg), "기간별 변화 (금리·스프레드는 '차이' 열이 %p)")

    corr = mk[["USDKRW=X", "DX-Y.NYB"]].pct_change().tail(250).corr().iloc[0, 1]
    md.append(f"\n원/달러 vs 달러인덱스 일간 변화율 상관계수(최근 250일): **{corr:.3f}**\n")

    iip = pv(ecos("311Y001", "Q", qs, qe))
    net = (iip["대외금융자산"] - iip["대외금융부채"])
    fresh["국제투자대조표"] = iip.index.max()
    table(pd.DataFrame({"대외금융자산": iip["대외금융자산"], "대외금융부채": iip["대외금융부채"],
                        "순대외금융자산": net}).tail(10).round(0), "국제투자대조표(백만달러)")

    # 차트 10
    m = mk["30y-5y"].resample("ME").mean().tail(34)
    fig, ax = plt.subplots(figsize=(11, 5))
    colors = [ACC] * len(m); colors[-3:] = [NEG] * 3
    ax.bar(m.index.strftime("%y-%m"), m.values, color=colors, width=.68)
    ax.axhline(0, color=TEXT, lw=1.2); ax.set_ylabel("%p")
    ax.set_title("미국채 30년-5년 금리차 (월평균)")
    plt.xticks(rotation=45, ha="right")
    finish(fig, "10-yield-curve.png", "자료: Yahoo Finance (^TYX, ^FVX)")

    # 차트 11
    w = mk.index[mk.index >= pd.Timestamp(f"{date.today().year - 1}-01-01")]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(w, mk.loc[w, "USDKRW=X"], color=NEG, lw=2.2, label="원/달러 (좌)")
    ax.set_ylabel("원/달러", color=NEG)
    ax2 = ax.twinx(); ax2.grid(False)
    ax2.plot(w, mk.loc[w, "DX-Y.NYB"], color=ACC, lw=2.2, label="달러인덱스 (우)")
    ax2.set_ylabel("달러인덱스", color=ACC)
    ax.set_title(f"원/달러 vs 달러인덱스 (일간 상관 {corr:+.2f})")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower left")
    finish(fig, "11-fx.png", "자료: Yahoo Finance (USDKRW=X, DX-Y.NYB)")

    # 차트 12
    ks_q = mk["^KS11"].resample("QE").last()
    ks_q.index = [f"{d.year}Q{d.quarter}" for d in ks_q.index]
    common = [q for q in net.index if q in ks_q.index][-10:]
    if common:
        fig, ax = plt.subplots(figsize=(11, 5))
        nb = net[common] / 1000
        ax.bar(common, nb, color=[NEG if v < nb.max() * .4 else ACC for v in nb], alpha=.75, width=.6)
        ax.set_ylabel("순대외금융자산 (십억달러)", color=ACC)
        ax2 = ax.twinx(); ax2.grid(False)
        ax2.plot(common, ks_q[common], color=WARN, marker="o", ms=5, lw=2.4, label="KOSPI (분기말)")
        ax2.set_ylabel("KOSPI", color=WARN)
        ax.set_title("순대외금융자산 vs KOSPI")
        ax2.legend(loc="upper left")
        plt.xticks(rotation=45, ha="right")
        finish(fig, "12-iip-kospi.png", "자료: 한국은행 ECOS 311Y001, Yahoo Finance (^KS11)")

    # ===================================================== 출력
    header = [f"# 월간 거시 데이터 — {PUB_DATE}", "",
              "`scripts/macro/fetch_and_chart.py` 가 생성한 **원데이터 요약**이다. 해석은 포함하지 않는다.", "",
              "## 계열별 최신 시점", "", "| 계열 | 최신 |", "|---|---|"]
    header += [f"| {k} | {v} |" for k, v in fresh.items()]
    (OUTDIR / "macro-data.md").write_text("\n".join(header) + "\n" + "\n".join(md) + "\n",
                                          encoding="utf-8")
    (OUTDIR / "freshness.json").write_text(json.dumps(fresh, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    print(f"\n✓ 완료 → {OUTDIR}")
    print("  macro-data.md, freshness.json, charts/*.png")


if __name__ == "__main__":
    main()
