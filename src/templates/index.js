// 글 목록(홈) 및 태그별 목록 페이지
import { layout, escapeHtml } from "./layout.js";

/** 글 카드 하나를 렌더링. root 는 글 링크의 상대 경로 접두사. */
function card(post, root) {
  const { title, description, dateISO, dateLabel, readingTime, tags, slug } = post;
  const tagLinks = (tags || [])
    .map(
      (t) =>
        `<a class="tag" href="${root}tags/${encodeURIComponent(t)}.html">#${escapeHtml(t)}</a>`
    )
    .join(" ");

  return `
      <li class="card">
        <h2 class="card__title">
          <a href="${root}posts/${encodeURIComponent(slug)}.html">${escapeHtml(title)}</a>
        </h2>
        <p class="card__meta">
          <time datetime="${escapeHtml(dateISO)}">${escapeHtml(dateLabel)}</time>
          <span aria-hidden="true">·</span>
          <span>${escapeHtml(readingTime)}</span>
        </p>
        ${description ? `<p class="card__desc">${escapeHtml(description)}</p>` : ""}
        ${tagLinks ? `<p class="card__tags">${tagLinks}</p>` : ""}
      </li>`;
}

function list(posts, root) {
  if (!posts.length) return `<p class="empty">아직 작성된 글이 없습니다.</p>`;
  return `<ul class="card-list">${posts.map((p) => card(p, root)).join("")}\n    </ul>`;
}

/**
 * 미니 웹앱 포트폴리오 목록.
 * 각 항목: /apps/<slug>/ 폴더에 자체 완결된 순수 HTML/CSS/JS 앱.
 */
const APPS = [
  {
    slug: "2048",
    title: "2048",
    desc: "방향키·스와이프로 숫자 타일을 밀어 2048을 만드는 퍼즐. 점수판과 최고 점수(localStorage) 저장 포함.",
  },
];

function appCard(app, root) {
  const href = `${root}apps/${encodeURIComponent(app.slug)}/index.html`;
  return `
      <li class="app-card">
        <a class="app-card__preview" href="${href}" aria-label="${escapeHtml(app.title)} 실행">
          <iframe class="app-card__frame" src="${href}" title="${escapeHtml(app.title)} 미리보기"
                  loading="lazy" scrolling="no" tabindex="-1" aria-hidden="true"></iframe>
        </a>
        <div class="app-card__body">
          <h2 class="app-card__title"><a href="${href}">${escapeHtml(app.title)}</a></h2>
          <p class="app-card__desc">${escapeHtml(app.desc)}</p>
          <p class="app-card__cta"><a href="${href}">플레이하기 →</a></p>
        </div>
      </li>`;
}

/** 웹앱 섹션 (앱이 없으면 렌더링하지 않음) */
function appsSection(root) {
  if (!APPS.length) return "";
  return `
    <section class="apps">
      <p class="intro__eyebrow">웹앱</p>
      <ul class="app-list">${APPS.map((a) => appCard(a, root)).join("")}
      </ul>
    </section>`;
}

/** 홈(전체 글 목록) */
export function index(posts, site) {
  const content = `
    <section class="intro">
      <h1 class="intro__title">${escapeHtml(site.title)}</h1>
      ${site.description ? `<p class="intro__desc">${escapeHtml(site.description)}</p>` : ""}
    </section>
    ${appsSection("")}
    ${list(posts, "")}`;

  return layout({
    title: site.title,
    description: site.description,
    content,
    root: "",
    siteTitle: site.title,
  });
}

/** 특정 태그의 글 목록 (dist/tags/<tag>.html) */
export function tagPage(tag, posts, site) {
  const content = `
    <section class="intro">
      <p class="intro__eyebrow">태그</p>
      <h1 class="intro__title">#${escapeHtml(tag)}</h1>
      <p class="intro__desc">${posts.length}개의 글</p>
    </section>
    ${list(posts, "../")}
    <p class="post__back"><a href="../">← 전체 목록</a></p>`;

  return layout({
    title: `#${tag}`,
    description: `${tag} 태그가 달린 글`,
    content,
    root: "../",
    siteTitle: site.title,
  });
}
