// 로컬 개발 서버 (의존성 없음)
//  - 시작 시 1회 빌드
//  - content/ 와 src/ 변경 감지 시 자동 재빌드
//  - dist/ 를 정적 서빙
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { watch } from "node:fs";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_DIR = path.join(__dirname, "dist");
const PORT = process.env.PORT || 4000;

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
};

function runBuild() {
  return new Promise((resolve) => {
    const proc = spawn("node", ["build.js"], { cwd: __dirname, stdio: "inherit" });
    proc.on("close", resolve);
  });
}

// 변경 감지 시 디바운스 재빌드
let building = false;
let pending = false;
async function rebuild() {
  if (building) {
    pending = true;
    return;
  }
  building = true;
  await runBuild();
  building = false;
  if (pending) {
    pending = false;
    rebuild();
  }
}

function watchDir(dir) {
  try {
    watch(dir, { recursive: true }, () => rebuild());
  } catch (e) {
    // recursive 미지원 플랫폼 대비: 무시
  }
}

const server = createServer(async (req, res) => {
  try {
    let urlPath = decodeURIComponent(req.url.split("?")[0]);
    if (urlPath.endsWith("/")) urlPath += "index.html";

    // 경로 탈출 방지
    const filePath = path.join(DIST_DIR, path.normalize(urlPath));
    if (!filePath.startsWith(DIST_DIR)) {
      res.writeHead(403);
      res.end("Forbidden");
      return;
    }

    const data = await readFile(filePath);
    const type = MIME[path.extname(filePath)] || "application/octet-stream";
    res.writeHead(200, { "Content-Type": type });
    res.end(data);
  } catch (e) {
    res.writeHead(404, { "Content-Type": "text/html; charset=utf-8" });
    res.end("<h1>404 Not Found</h1>");
  }
});

await runBuild();
watchDir(path.join(__dirname, "content"));
watchDir(path.join(__dirname, "src"));

server.listen(PORT, () => {
  console.log(`▶ 개발 서버: http://localhost:${PORT}  (Ctrl+C 로 종료)`);
});
