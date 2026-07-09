// 단일 글 페이지
import { layout, escapeHtml } from "./layout.js";

/**
 * @param {object} post - { title, description, dateISO, dateLabel, readingTime, tags, contentHtml, slug }
 * @param {object} site - { title }
 */
export function post(postData, site) {
  const { title, description, dateISO, dateLabel, readingTime, tags, contentHtml } = postData;

  const tagLinks = (tags || [])
    .map(
      (t) =>
        `<a class="tag" href="../tags/${encodeURIComponent(t)}.html">#${escapeHtml(t)}</a>`
    )
    .join(" ");

  const content = `
    <article class="post">
      <header class="post__header">
        <h1 class="post__title">${escapeHtml(title)}</h1>
        <p class="post__meta">
          <time datetime="${escapeHtml(dateISO)}">${escapeHtml(dateLabel)}</time>
          <span aria-hidden="true">·</span>
          <span>${escapeHtml(readingTime)}</span>
        </p>
        ${tagLinks ? `<p class="post__tags">${tagLinks}</p>` : ""}
      </header>
      <div class="prose">
${contentHtml}
      </div>
      <hr class="post__rule" />
      <p class="post__back"><a href="../">← 목록으로</a></p>
    </article>`;

  return layout({
    title,
    description,
    content,
    root: "../",
    siteTitle: site.title,
  });
}
