# Replaces the HINTS line in index.html with tools/build/hints.json (run build_hints.py first, with 0 problems).
# Usage (from the repo root):  python3 tools/scripts/inject_hints.py
import json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
html_path = os.path.join(ROOT, 'index.html')
hints = json.load(open(os.path.join(ROOT, 'tools', 'build', 'hints.json'), encoding='utf8'))
lines = open(html_path, encoding='utf8').read().split('\n')
idx = [k for k, l in enumerate(lines) if l.startswith('const HINTS = ')]
if len(idx) != 1: sys.exit(f'expected exactly one "const HINTS = " line, found {len(idx)}')
lines[idx[0]] = 'const HINTS = ' + json.dumps(hints, ensure_ascii=False, separators=(',', ':')) + ';'
open(html_path, 'w', encoding='utf8').write('\n'.join(lines))
print(f'HINTS updated: {len(hints)} texts')
