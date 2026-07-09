// my-blog 정적 사이트 빌드 스크립트
// content/*.md  ->  dist/(index, posts, tags, feed.xml, assets)
import { readdir, readFile, writeFile, mkdir, rm, copyFile, cp } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { marked } from "marked";
import { post as renderPost } from "./src/templates/post.js";
import { index as renderIndex, tagPage as renderTagPage } from "./src/templates/index.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// 사이트 전역 설정
const SITE = {
  title: "My Blog",
  description: "마크다운으로 쓰는 개인 블로그",
};

const CONTENT_DIR = path.join(__dirname, "content");
const DIST_DIR = path.join(__dirname, "dist");
const STYLES_DIR = path.join(__dirname, "src", "styles");
const SCRIPTS_DIR = path.join(__dirname, "src", "scripts");
const APPS_DIR = path.join(__dirname, "apps");

marked.setOptions({ gfm: true, breaks: false });

/**
 * 아주 단순한 frontmatter 파서.
 * `---` 로 둘러싸인 앞부분에서 key: value 를 읽는다.
 * 지원 값: 문자열, 그리고 [a, b] 형태의 인라인 배열(tags 용).
 */
function parseFrontmatter(raw) {
  const match = /^---\s*\r?\n([\s\S]*?)\r?\n---\s*\r?\n?/.exec(raw);
  if (!match) return { data: {}, body: raw };

  const data = {};
  for (const line of match[1].split(/\r?\n/)) {
    if (!line.trim() || /^\s*#/.test(line)) continue;
    const idx = line.indexOf(":");
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();

    if (value.startsWith("[") && value.endsWith("]")) {
      value = value
        .slice(1, -1)
        .split(",")
        .map((s) => s.trim().replace(/^["']|["']$/g, ""))
        .filter(Boolean);
    } else {
      value = value.replace(/^["']|["']$/g, "");
    }
    data[key] = value;
  }
  return { data, body: raw.slice(match[0].length) };
}

/** 한국어 날짜 라벨 (예: 2026년 7월 9일) */
function formatDate(iso) {
  const d = new Date(iso);
  if (isNaN(d)) return iso || "";
  return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일`;
}

/** 대략적인 읽기 시간 (한국어/영어 혼용 대응: 300자 또는 200단어/분) */
function readingTime(text) {
  const chars = text.replace(/\s/g, "").length;
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  const minutes = Math.max(1, Math.round(Math.max(chars / 500, words / 200)));
  return `${minutes}분 읽기`;
}

async function loadPosts() {
  if (!existsSync(CONTENT_DIR)) return [];
  const files = (await readdir(CONTENT_DIR)).filter((f) => f.endsWith(".md"));
  const posts = [];

  for (const file of files) {
    const raw = await readFile(path.join(CONTENT_DIR, file), "utf8");
    const { data, body } = parseFrontmatter(raw);
    const slug = file.replace(/\.md$/, "");
    const tags = Array.isArray(data.tags) ? data.tags : data.tags ? [data.tags] : [];

    posts.push({
      slug,
      title: data.title || slug,
      description: data.description || "",
      dateISO: data.date || "",
      dateLabel: formatDate(data.date),
      readingTime: readingTime(body),
      tags,
      contentHtml: marked.parse(body),
    });
  }

  // 날짜 내림차순
  posts.sort((a, b) => (a.dateISO < b.dateISO ? 1 : a.dateISO > b.dateISO ? -1 : 0));
  return posts;
}

function buildRss(posts) {
  const items = posts
    .map(
      (p) => `    <item>
      <title>${escapeXml(p.title)}</title>
      <link>posts/${encodeURIComponent(p.slug)}.html</link>
      <guid isPermaLink="false">${escapeXml(p.slug)}</guid>
      ${p.dateISO ? `<pubDate>${new Date(p.dateISO).toUTCString()}</pubDate>` : ""}
      <description>${escapeXml(p.description)}</description>
    </item>`
    )
    .join("\n");

  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>${escapeXml(SITE.title)}</title>
    <description>${escapeXml(SITE.description)}</description>
    <link>./</link>
${items}
  </channel>
</rss>
`;
}

function escapeXml(str = "") {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

async function copyDir(srcDir, destDir) {
  await mkdir(destDir, { recursive: true });
  for (const name of await readdir(srcDir)) {
    await copyFile(path.join(srcDir, name), path.join(destDir, name));
  }
}

async function build() {
  // 산출물 초기화
  await rm(DIST_DIR, { recursive: true, force: true });
  await mkdir(path.join(DIST_DIR, "posts"), { recursive: true });
  await mkdir(path.join(DIST_DIR, "tags"), { recursive: true });

  const posts = await loadPosts();

  // 글 페이지
  for (const p of posts) {
    await writeFile(
      path.join(DIST_DIR, "posts", `${p.slug}.html`),
      renderPost(p, SITE)
    );
  }

  // 홈
  await writeFile(path.join(DIST_DIR, "index.html"), renderIndex(posts, SITE));

  // 태그 페이지
  const byTag = new Map();
  for (const p of posts) {
    for (const t of p.tags) {
      if (!byTag.has(t)) byTag.set(t, []);
      byTag.get(t).push(p);
    }
  }
  for (const [tag, tagPosts] of byTag) {
    await writeFile(
      path.join(DIST_DIR, "tags", `${tag}.html`),
      renderTagPage(tag, tagPosts, SITE)
    );
  }

  // RSS
  await writeFile(path.join(DIST_DIR, "feed.xml"), buildRss(posts));

  // 에셋 복사
  const assetsDir = path.join(DIST_DIR, "assets");
  await copyDir(STYLES_DIR, assetsDir);
  await copyDir(SCRIPTS_DIR, assetsDir);

  // 웹앱 복사: /apps/**  ->  dist/apps/** (개발 문서 .md 는 배포 제외)
  let appCount = 0;
  if (existsSync(APPS_DIR)) {
    await cp(APPS_DIR, path.join(DIST_DIR, "apps"), {
      recursive: true,
      filter: (src) => !src.endsWith(".md"),
    });
    appCount = (await readdir(APPS_DIR, { withFileTypes: true })).filter((d) =>
      d.isDirectory()
    ).length;
  }

  console.log(
    `✓ 빌드 완료: 글 ${posts.length}개, 태그 ${byTag.size}개, 앱 ${appCount}개 → dist/`
  );
}

build().catch((err) => {
  console.error("빌드 실패:", err);
  process.exit(1);
});
