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

## 미정/보완 필요 (사용자 확인 대기)
- STEP 4 이후 우선순위 기준과 최종 출력 형식(표/요약 문단/시사점)이 원문에서 잘려 있음.
- 통합 리포트에 넣을 출력 포맷 확정 필요.
