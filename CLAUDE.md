# my-blog — 주간 투자 리포트

## 프로젝트 개요
한국은행 보도자료·거시지표·지수/ETF 차트추세·내 ETF 포트폴리오를 분석해
매주 주말 **하나의 통합 리포트**로 묶어 발행하는 정적 블로그.
HTML/CSS/JS + 마크다운만 사용(프레임워크 없음). 최종 관점은 **안전마진 기반 가치투자자**.

전체 설계는 `spec.md` 참조.

## 아키텍처 — 4개 서브에이전트
잡 = 서브에이전트. 각자 `agents/*.md` 지침만 따르고, 자기 섹션 마크다운을 `content/reports/_parts/{발행일}/`에 출력한다.
```
① kor-bank-analysis  ┐
② macro-analysis     ├─(통합 정보)→ ④ etf-analysis(평가·예측) → 통합 글 조립 → 빌드 → 발행
③ trend-analysis     ┘
```
- ①②③ 병렬 실행 가능. ④는 ①②③ 결과를 입력으로 받음.
- Build 서브에이전트와 Review 서브에이전트는 분리한다.

## 주간 자동 워크플로우 (완전 자동)
매주 주말 예약 작업이 무인 실행:
1. ①②③ 병렬 실행 → 섹션 md + 차트 PNG
2. ④ 실행 → 포트폴리오 평가·예측
3. `content/reports/{발행일}.md`로 통합 글 조립
4. `npm run check` (개인정보 게이트) → 절대금액 노출 시 발행 중단
5. `npm run build` → dist/
6. 통과 시 커밋 + 푸시 → Pages 배포

## 폴더 구조
```
agents/                  서브에이전트 지침 (수정 시 신중)
content/reports/
  _parts/{날짜}/         섹션 초안 + charts/ (커밋 안 함, .gitignore)
  {날짜}.md              발행 글
  {날짜}/                발행 글에 딸린 이미지(차트 등)
src/styles/style.css     디자인(CSS 변수) — 모든 색은 여기서
scripts/build.js         마크다운→HTML 빌드
scripts/check-privacy.js 개인정보 게이트
dist/                    빌드 결과(배포 대상, .gitignore)
.github/workflows/pages.yml
```

## 규칙 (중요)
- **개인정보**: 발행 글에 개인 자산 **절대금액 금지**. 비중(%)·수익률(%)·정성 평가만. 포트폴리오 원본은 커밋 금지.
- **면책**: 모든 글은 투자 자문이 아님(템플릿 푸터에 자동 삽입).
- **글 형식**: frontmatter(title/date/tags/description) + 마크다운 본문. 파일명 `YYYY-MM-DD`.
- **표기**: 목록·글에 ISO 주차("YYYY년 N주차")를 앞세워 표시(빌드가 date로 자동 계산). 디자인은 **라이트 모드 고정**(다크 미사용).
- **차트**: matplotlib PNG. 발행 글 이미지는 `content/reports/{날짜}/`에 두고 상대경로로 삽입.
- `.docx`/PDF/통합본 파일 생성 없음 — 블로그 글 자체가 리포트.
- 프레임워크 추가 금지. 외부 라이브러리 최소화(marked, gray-matter만).
- 모바일 가독 필수(표는 가로 스크롤).

## 빌드/발행
- `npm run build` (prebuild로 개인정보 검사 자동 실행) → `dist/`
- main 푸시 시 GitHub Pages 자동 배포. 원격: https://github.com/cbyangel/my-blog.git
- 커밋·푸시·배포는 자동 워크플로우 또는 사용자 요청 시에만.
