// 개인정보 자동 검사(발행 게이트).
// 발행 대상 리포트(content/**/*.md, _parts 제외)에서 개인 보유/평가 "절대금액" 노출을 차단한다.
// 비중(%)·수익률(%)·주당 목표가(원)는 허용. 개인 금액 맥락어 + 금액 패턴이 함께 나오면 차단.
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, dirname, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CONTENT = join(__dirname, '..', 'content');

// 개인 자산 금액을 가리키는 맥락어
const CONTEXT = /(입금\s*금?액|납입|평가\s*금?액|평가액|보유\s*금?액|잔고|투자\s*원금|총\s*자산|자산\s*총액|총액|매입\s*금액|계좌\s*잔액)/;
// 금액 패턴: 큰 숫자+원 / ₩ / 만원 / 억(원) / KRW
const MONEY = /(₩\s*\d[\d,]*)|(\d[\d,]{2,}\s*원)|(\d[\d,]*\s*만\s*원)|(\d[\d,]*\s*억\s*원?)|(KRW\s*\d[\d,]*)/;

function walk(dir) {
  const out = [];
  if (!existsSync(dir)) return out;
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    const s = statSync(p);
    if (s.isDirectory()) {
      if (name === '_parts') continue; // 중간 초안은 검사 대상 아님(발행 안 되므로)
      out.push(...walk(p));
    } else if (extname(p) === '.md') {
      out.push(p);
    }
  }
  return out;
}

const violations = [];
for (const file of walk(CONTENT)) {
  const lines = readFileSync(file, 'utf-8').split('\n');
  lines.forEach((line, i) => {
    if (CONTEXT.test(line) && MONEY.test(line)) {
      violations.push(`${file}:${i + 1}  ${line.trim()}`);
    }
  });
}

if (violations.length) {
  console.error('✗ 개인정보 검사 실패: 발행 글에 개인 자산 절대금액으로 의심되는 내용이 있습니다.');
  console.error('  비중(%)·수익률(%)로 바꾸거나 금액을 제거하세요.\n');
  violations.forEach(v => console.error('  - ' + v));
  process.exit(1);
}
console.log('✓ 개인정보 검사 통과 (개인 자산 절대금액 미노출)');
