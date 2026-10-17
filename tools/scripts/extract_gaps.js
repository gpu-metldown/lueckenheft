// Reads ../../index.html and writes ../build/gaps.json: every gap word of every text, with context.
// Usage (from the repo root):  node tools/scripts/extract_gaps.js
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..', '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const js = html.split('<script>')[1].split('</script>')[0];
const i = js.indexOf('const TEXTS = ['), j = js.indexOf('const BOOKS');
if (i < 0 || j < 0) throw new Error('TEXTS / BOOKS markers not found in index.html');
// The block defines TEXTS (Band 2) and BAND1; add new book arrays to the list below when you add them.
const data = eval('(() => {' + js.slice(i, j) + '; return {TEXTS, BAND1}; })()');
const all = [...data.TEXTS, ...data.BAND1];
const out = {};
for (const t of all) {
  let k = 0; const words = [];
  const plain = t.raw.replace(/([A-Za-zÄÖÜäöüß]*)\[([^\]]+)\]/g, (m, pre, ans) => {
    k++; const w = pre + ans.split('|')[0]; words.push(w); return '⟨' + k + ':' + w + '⟩';
  });
  out[String(t.id)] = {n: k, words, plain};
}
fs.mkdirSync(path.join(root, 'tools', 'build'), {recursive: true});
fs.writeFileSync(path.join(root, 'tools', 'build', 'gaps.json'), JSON.stringify(out));
console.log(Object.keys(out).length, 'texts,', Object.values(out).reduce((a, v) => a + v.n, 0), 'gaps -> tools/build/gaps.json');
