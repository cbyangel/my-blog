---
name: kor-bank-analysis
description: 한국은행 보도자료를 수집·요약하고 시사점을 정리하는 서브에이전트
output: content/reports/_parts/{주차}/kor-bank.md
---

# 한국은행 보도자료 요약

## 작업 순서 (WebFetch / fetch 사용 — 무인 자동화용, 브라우저 불필요)

1. WebFetch로 다음 URL을 가져와 최근 보도자료 목록을 수집한다:
   - https://www.bok.or.kr/portal/singl/newsData/list.do?pageIndex=1&targetDepth=&menuNo=201150&syncMenuChekKey=2&depthSubMain=&subMainAt=&searchCnd=1&searchKwd=&date=&sdate=&edate=&sort=1&pageUnit=100
   - 목록이 JS 렌더링/차단으로 안 잡히면 fetch MCP로 재시도. 그래도 실패 시 해당 항목을 "수집 불가"로 표기하고 계속 진행.

2. 각 목록에서 이번 주(최근 7일) 발표된 보도자료의 제목, 날짜, nttId를 추출한다.
   개별 기사 본문은 view URL(nttId 사용)을 WebFetch로 가져와 읽는다.

3. 경제전망, 통화정책방향, 소비자동향조사, 현지정보, 생산자물가지수, 동향분석,
   금융통화위원회 의사록 등 주요 보고자료를 위주로 기사 내용을 읽고
   핵심 수치와 시사점을 파악한다.

4. 중요도 기준으로 우선순위를 정한다.

5. WebFetch가 막히면 WebSearch로 보도자료 제목·수치를 교차 확인한다(뉴스 1곳 이상). 확인 못 한 항목은 "수집 불가".

## 출력 구성 (kor-bank.md) — 글쓰기 규칙은 agents/_style.md
```
## 2. 시장 배경 ① 한국은행
> **이 섹션 핵심** — 3줄 (가장 중요한 발표+숫자 / 내 계좌에 뜻하는 것 / 지난주 대비 변화)

### 이번 주 주요 발표 (표: 발표 | 날짜 | 핵심 숫자 | 한 줄 의미) — 중요도 순
### 2-1, 2-2 … 주요 발표 풀이 (각 4~6문장, 결론 먼저. 상위 2~3건만 깊게)
### 내 계좌에 주는 의미 — 한국 자산(은행고배당·200TR) / 원화·환율 / 금리 (3~5줄)
### 수집 불가 항목 · 참고 링크
```
