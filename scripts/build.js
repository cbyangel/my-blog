// 정적 블로그 빌드: content/**/*.md → dist/
// 프레임워크 없음. marked(GFM) + gray-matter 만 사용.
import { readFileSync, writeFileSync, readdirSync, statSync, mkdirSync, rmSync, existsSync, copyFileSync } from 'node:fs';
import { join, dirname, basename, extname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { marked } from 'marked';
import matter from 'gray-matter';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const CONTENT = join(ROOT, 'content');
const DIST = join(ROOT, 'dist');
const STYLE_SRC = join(ROOT, 'src', 'styles', 'style.css');

marked.setOptions({ gfm: true, breaks: false });

// --- 파일 수집 (재귀), _parts 폴더는 발행 대상에서 제외 ---
function walk(dir) {
  const out = [];
  if (!existsSync(dir)) return out;
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    const s = statSync(p);
    if (s.isDirectory()) {
      if (name === '_parts') continue; // 중간 초안은 발행 안 함
      out.push(...walk(p));
    } else {
      out.push(p);
    }
  }
  return out;
}

function ensureDir(p) { mkdirSync(p, { recursive: true }); }

// frontmatter date를 항상 YYYY-MM-DD 문자열로 정규화 (gray-matter가 Date 객체로 파싱하는 경우 대응)
function normDate(d) {
  if (!d) return '';
  if (d instanceof Date) {
    const y = d.getUTCFullYear();
    const m = String(d.getUTCMonth() + 1).padStart(2, '0');
    const day = String(d.getUTCDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
  return String(d).slice(0, 10);
}

// YYYY-MM-DD → ISO 8601 주차 {year, week}
function isoWeek(dateStr) {
  const [y, m, dd] = dateStr.split('-').map(Number);
  if (!y || !m || !dd) return null;
  const date = new Date(Date.UTC(y, m - 1, dd));
  const dayNum = (date.getUTCDay() + 6) % 7;          // 월=0 ... 일=6
  date.setUTCDate(date.getUTCDate() - dayNum + 3);    // 해당 주의 목요일
  const firstThursday = date.getTime();
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 4));
  const ysDayNum = (yearStart.getUTCDay() + 6) % 7;
  yearStart.setUTCDate(yearStart.getUTCDate() - ysDayNum + 3);
  const week = 1 + Math.round((firstThursday - yearStart.getTime()) / (7 * 24 * 3600 * 1000));
  return { year: date.getUTCFullYear(), week };
}

// 표시용 주차 라벨: "2026년 28주차"
function weekLabel(dateStr) {
  const w = isoWeek(dateStr);
  return w ? `${w.year}년 ${w.week}주차` : (dateStr || '');
}

// <table>을 가로 스크롤 컨테이너로 감싸 모바일 가독성 확보
function wrapTables(html) {
  return html.replace(/<table>/g, '<div class="table-wrap"><table>').replace(/<\/table>/g, '</table></div>');
}

function layout({ title, description, body, isHome }) {
  const desc = (description || '한국은행·거시지표·차트·ETF 주간 통합 투자 리포트').replace(/"/g, '&quot;');
  const home = isHome ? '' : '<a class="back" href="../index.html">← 목록으로</a>';
  return `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
<meta name="description" content="${desc}">
<link rel="stylesheet" href="${isHome ? '' : '../'}style.css">
</head>
<body>
<header class="site-header">
  <a class="brand" href="${isHome ? '' : '../'}index.html">📈 주간 투자 리포트</a>
  <span class="tagline">한국은행 · 거시지표 · 차트추세 · ETF 평가</span>
</header>
<main class="container">
${home}
${body}
</main>
<footer class="site-footer">
  <p class="disclaimer">본 글은 정보 제공·개인 기록 목적이며 투자 자문이 아닙니다. 특정 종목의 매수·매도 권유가 아니며, 투자 판단과 책임은 전적으로 본인에게 있습니다. 데이터는 수집 시점 기준이며 오류가 있을 수 있습니다.</p>
  <p class="copyright">© 주간 투자 리포트 · 정적 빌드</p>
</footer>
</body>
</html>`;
}

function build() {
  // dist 초기화
  if (existsSync(DIST)) rmSync(DIST, { recursive: true, force: true });
  ensureDir(DIST);

  // 스타일 복사
  if (existsSync(STYLE_SRC)) copyFileSync(STYLE_SRC, join(DIST, 'style.css'));

  const files = walk(CONTENT).filter(f => extname(f) === '.md');
  const posts = [];

  for (const file of files) {
    const raw = readFileSync(file, 'utf-8');
    const { data, content } = matter(raw);
    const slug = basename(file, '.md');
    const html = wrapTables(marked.parse(content));
    const title = data.title || slug;
    const date = normDate(data.date);
    const week = weekLabel(date);
    const tagList = Array.isArray(data.tags) ? data.tags : (data.tags ? [data.tags] : []);

    // 발행 경로: dist/posts/{slug}.html
    const outDir = join(DIST, 'posts');
    ensureDir(outDir);
    const body = `<article class="post">
  <h1 class="post-title">${title}</h1>
  <p class="post-meta">${week}${date ? ` · ${date}` : ''}${tagList.length ? ' · ' + tagList.map(t => `<span class="tag">${t}</span>`).join(' ') : ''}</p>
  ${html}
</article>`;
    writeFileSync(join(outDir, `${slug}.html`), layout({ title, description: data.description, body, isHome: false }));

    // 글에 딸린 이미지 폴더(content/reports/{slug}/) 복사 → dist/posts/{slug}/
    const assetDir = join(dirname(file), slug);
    if (existsSync(assetDir) && statSync(assetDir).isDirectory()) {
      for (const asset of walk(assetDir)) {
        const rel = relative(assetDir, asset);
        const dest = join(outDir, slug, rel);
        ensureDir(dirname(dest));
        copyFileSync(asset, dest);
      }
    }

    posts.push({ slug, title, date, week, description: data.description || '', tags: tagList });
  }

  // 최신순 정렬 (date 문자열 YYYY-MM-DD 기준)
  posts.sort((a, b) => (b.date || '').localeCompare(a.date || ''));

  // 홈(index)
  const cards = posts.map(p => `<a class="card" href="posts/${p.slug}.html">
    <span class="card-date">${p.week}${p.date ? ` · ${p.date}` : ''}</span>
    <h2 class="card-title">${p.title}</h2>
    <p class="card-desc">${p.description}</p>
    ${p.tags.length ? `<p class="card-tags">${p.tags.map(t => `<span class="tag">${t}</span>`).join(' ')}</p>` : ''}
  </a>`).join('\n');

  const homeBody = `<section class="hero">
  <h1>주간 투자 리포트</h1>
  <p>매주 주말, 한국은행 보도자료 · 거시지표 · 지수/ETF 차트추세 · 내 포트폴리오 평가를 하나로 묶은 통합 리포트를 발행합니다. 안전마진 기반 가치투자자 관점.</p>
</section>
<section class="post-list">
${cards || '<p class="empty">아직 발행된 리포트가 없습니다.</p>'}
</section>`;
  writeFileSync(join(DIST, 'index.html'), layout({ title: '주간 투자 리포트', body: homeBody, isHome: true }));

  console.log(`✓ 빌드 완료: 리포트 ${posts.length}건 → dist/`);
}

build();
