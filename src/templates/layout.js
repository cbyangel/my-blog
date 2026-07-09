// 공통 HTML 골격. 모든 페이지가 이 레이아웃을 통과한다.

/** HTML 특수문자 이스케이프 (템플릿에 값을 넣을 때 사용) */
export function escapeHtml(str = "") {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * @param {object} opts
 * @param {string} opts.title       - <title> 및 og:title
 * @param {string} [opts.description]- 메타 설명
 * @param {string} opts.content     - <main> 안에 들어갈 본문 HTML
 * @param {string} [opts.root]      - 루트까지의 상대 경로 접두사 ("" 또는 "../")
 * @param {string} opts.siteTitle   - 사이트 이름
 */
export function layout({ title, description = "", content, root = "", siteTitle }) {
  const assets = `${root}assets`;
  const pageTitle = title === siteTitle ? title : `${title} · ${siteTitle}`;

  return `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHtml(pageTitle)}</title>
  <meta name="description" content="${escapeHtml(description)}" />
  <meta property="og:title" content="${escapeHtml(title)}" />
  <meta property="og:description" content="${escapeHtml(description)}" />
  <meta property="og:type" content="website" />
  <link rel="alternate" type="application/rss+xml" title="${escapeHtml(siteTitle)}" href="${root}feed.xml" />
  <link rel="stylesheet" href="${assets}/style.css" />
  <!-- FOUC 방지: 저장된 테마를 렌더 전에 <html>에 반영 -->
  <script>
    (function () {
      try {
        var t = localStorage.getItem("theme");
        if (t) document.documentElement.setAttribute("data-theme", t);
      } catch (e) {}
    })();
  </script>
</head>
<body>
  <a class="skip-link" href="#main">본문으로 건너뛰기</a>
  <header class="site-header">
    <div class="wrap site-header__inner">
      <a class="site-title" href="${root || "./"}">${escapeHtml(siteTitle)}</a>
      <button
        id="theme-toggle"
        class="theme-toggle"
        type="button"
        aria-label="다크 모드 전환"
        title="테마 전환"
      >
        <span class="theme-toggle__icon" aria-hidden="true"></span>
      </button>
    </div>
  </header>
  <main id="main" class="wrap">
${content}
  </main>
  <footer class="site-footer">
    <div class="wrap">
      <p>© ${escapeHtml(siteTitle)} · <a href="${root}feed.xml">RSS</a></p>
    </div>
  </footer>
  <script src="${assets}/theme.js"></script>
</body>
</html>
`;
}
