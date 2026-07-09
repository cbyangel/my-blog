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

/** 홈(전체 글 목록) */
export function index(posts, site) {
  const content = `
    <section class="intro">
      <h1 class="intro__title">${escapeHtml(site.title)}</h1>
      ${site.description ? `<p class="intro__desc">${escapeHtml(site.description)}</p>` : ""}
    </section>
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
