# Lines up an exercise transcription (E:) with its solution (S:) word by word and builds the gap markup.
# Usage (from the repo root):  python3 tools/scripts/align_transcription.py tools/sources/<file>.txt
# Output: tools/build/aligned.json (id, num, short, title, raw) plus a list of every mismatch to fix first.
import re, json, sys
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
src = open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'tools', 'sources', 'band1-kapitel6.txt'), encoding='utf8').read()
PREFIX = sys.argv[2] if len(sys.argv) > 2 else 'b1-'   # id prefix of the book, e.g. b1- or b3-
# Extra accepted answers the solution page doesn't show: {text number: {book answer: 'answer|alternative'}}
ALTS = {113: {'este': 'este|e'}, 99: {'zial': 'zial|tial'}}
blocks = [b for b in src.split('### ')[1:]]
out, problems, counts = [], [], {}
for b in blocks:
    head, rest = b.split('\n', 1)
    tid, title, short = head.strip().split('|')
    tid = int(tid)
    E = re.search(r'^E: (.*)$', rest, re.M).group(1).split()
    S = re.search(r'^S: (.*)$', rest, re.M).group(1).split()
    if len(E) != len(S):
        problems.append(f'({tid}) word count differs: exercise {len(E)} vs solution {len(S)}')
    raw, n = [], 0
    for i, (e, s) in enumerate(zip(E, S)):
        if '_' in e:
            pre, after = e.split('_', 1)
            if not s.startswith(pre) or (after and not s.endswith(after)):
                problems.append(f'({tid}) gap "{e}" does not fit solution word "{s}"'); raw.append(e); continue
            ans = s[len(pre):len(s) - len(after)] if after else s[len(pre):]
            if not ans or not re.fullmatch(r"[A-Za-zÄÖÜäöüß]+", ans):
                problems.append(f'({tid}) odd answer for "{e}" -> "{ans}" (solution "{s}")')
            ans = ALTS.get(tid, {}).get(ans, ans)
            raw.append(f'{pre}[{ans}]{after}'); n += 1
        else:
            if e != s: problems.append(f'({tid}) word differs: exercise "{e}" vs solution "{s}"')
            raw.append(e)
    text = ' '.join(raw)
    # typographic German quotes
    text = re.sub(r'(^|\s)"', r'\1„', text); text = text.replace('"', '“')
    counts[tid] = n
    out.append({'id': f'{PREFIX}{tid}', 'num': tid, 'short': short, 'title': title, 'raw': text})
print('texts:', len(out), ' gaps total:', sum(counts.values()))
print('gap counts not 25:', {k: v for k, v in counts.items() if v != 25})
for g in range(71, 119, 4): print(f'set {g}-{g+3}:', sum(counts[x] for x in range(g, g+4)), end=' | ')
print('\nPROBLEMS:', len(problems)); print('\n'.join(problems))
os.makedirs(os.path.join(ROOT, 'tools', 'build'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'tools', 'build', 'aligned.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=0)
