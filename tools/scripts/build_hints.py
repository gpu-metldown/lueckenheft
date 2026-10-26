# Checks every hint file in tools/hints against the gaps in index.html and writes tools/build/hints.json.
# Usage (from the repo root):  python3 tools/scripts/build_hints.py   [-s <text id>  to print one text]
import json, re, glob, sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
G = json.load(open(os.path.join(ROOT, 'tools', 'build', 'gaps.json'), encoding='utf8'))
POS = {'bA':'Bestimmter Artikel','uA':'Unbestimmter Artikel','N':'Nomen','EN':'Name','V':'Verb','MV':'Modalverb','HV':'Hilfsverb',
 'Adj':'Adjektiv','Adv':'Adverb','Prp':'Präposition','Prp+bA':'Präposition + Artikel','Kj':'Konjunktion','Sj':'Subjunktion (leitet einen Nebensatz ein)',
 'PPr':'Personalpronomen','Rfl':'Reflexivpronomen','Pos':'Possessivartikel','Dem':'Demonstrativartikel','DemP':'Demonstrativpronomen',
 'Rel':'Relativpronomen','Idf':'Indefinitpronomen','Neg':'Negationsartikel','NegP':'Negationswort','P2':'Partizip II','P1':'Partizip I','Inf':'Infinitiv',
 'Zu':'Infinitiv mit „zu“','Num':'Zahlwort','Frg':'Fragewort','Ptk':'Partikel','VPt':'Verbzusatz (Teil eines trennbaren Verbs)',
 'Vgl':'Vergleichswort','Abk':'Abkürzung','Pab':'Pronominaladverb'}
FEAT = {'Nom':'Nominativ','Akk':'Akkusativ','Dat':'Dativ','Gen':'Genitiv','Sg':'Singular','Pl':'Plural','m':'maskulin','f':'feminin','n':'neutrum',
 'Präs':'Präsens','Prät':'Präteritum','Perf':'Perfekt','Fut':'Futur','KII':'Konjunktiv II','KI':'Konjunktiv I','Pass':'Passiv','Imp':'Imperativ',
 'Komp':'Komparativ','Sup':'Superlativ','+Akk':'danach Akkusativ','+Dat':'danach Dativ','+Gen':'danach Genitiv','+Dat/Akk':'danach Dativ oder Akkusativ',
 '1Sg':'1. Person Singular','2Sg':'2. Person Singular','3Sg':'3. Person Singular','1Pl':'1. Person Plural','2Pl':'2. Person Plural','3Pl':'3. Person Plural'}
def expand(g):
    m = re.match(r'^(\S+)\s*(.*)$', g.strip()); pos, rest = m.group(1), m.group(2)
    paren = ''
    pm = re.search(r'\((.*)\)\s*$', rest)
    if pm: paren = pm.group(1); rest = rest[:pm.start()].strip()
    feats = [FEAT.get(t, t) for t in rest.split()] if rest else []
    out = POS.get(pos, pos)
    if feats:
        txt = ' '.join(feats)
        txt = re.sub(r' (\d\. Person)', r', \1', txt)
        out += ' · ' + txt
    if paren: out += ' (' + paren + ')'
    return out
def mask_ref(ref, tid, i):
    # Show the referenced words the way the learner sees them: a word that is itself a later gap
    # becomes its printed beginning + "…" (e.g. "Natur" -> "Na…").
    if tid not in G: return ref
    plain = G[tid]['plain']; k = plain.find('⟨%d:' % i)
    after = plain[k:].split('⟩', 1)[1] if k >= 0 else ''
    out = []
    for tok in ref.split():
        m = re.search(r'⟨(\d+):' + re.escape(tok) + r'⟩|(?<![A-Za-zÄÖÜäöüß])' + re.escape(tok) + r'(?![A-Za-zÄÖÜäöüß])', after)
        if m and m.group(1):
            j = int(m.group(1)); pre = G[tid]['pres'][j-1]
            out.append((pre or '') + '…')
            after = after[m.end():]
        else:
            out.append(tok)
            if m: after = after[m.end():]
    return ' '.join(out)
def mask_quotes(s, tid, i):
    # Inside quoted text snippets („…“), a word that is another gap's answer is shown as the learner
    # sees it on the page (printed beginning + "…"), using the nearest such gap.
    if tid not in G: return s
    words, pres = G[tid]['words'], G[tid]['pres']
    def fix_quote(m):
        def fix_word(w):
            tok = w.group(0)
            # only gaps close to this one (the snippet quotes the nearby sentence), and only if the word
            # is not printed in full in that same stretch of text
            plain = G[tid]['plain']; k = plain.find('⟨%d:' % i)
            window = plain[max(0, k - 160): k + 200]
            near = [int(j) for j in re.findall(r'⟨(\d+):' + re.escape(tok) + r'⟩', window) if int(j) != i]
            printed = re.search(r'(?<![A-Za-zÄÖÜäöüß:])' + re.escape(tok) + r'(?![A-Za-zÄÖÜäöüß⟩])', re.sub(r'⟨\d+:[^⟩]*⟩', '#', window))
            if not near or printed: return tok
            j = min(near, key=lambda j: abs(j - i))
            return pres[j-1] + '…' if pres[j-1] else tok
        return '„' + re.sub(r'[A-Za-zÄÖÜäöüß]+', fix_word, m.group(1)) + '“'
    s = re.sub(r'„([^“]*)“', fix_quote, s)
    # A context pattern without quotes ("Ausnahmen ___ einer Regel") is treated like a quote,
    # up to an " = " explanation.
    if '___' in s and '„' not in s:
        left, sep, right = s.partition(' = ')
        s = fix_quote(re.match(r'(.*)', left, re.S))[1:-1] + sep + right
    return s
def mean(s, tid=None, i=None):
    s = s.strip()
    if tid is not None and '@' not in s: s = mask_quotes(s, tid, i)
    s = re.sub(r'@(.+)$', lambda m: 'Bezugswort: „' + mask_ref(m.group(1).strip(), tid, i) + '“', s)
    return s
hints, problems, raw_lines = {}, [], {}
for f in sorted(glob.glob(os.path.join(ROOT, 'tools', 'hints', '*.txt'))):
    cur = None
    for line in open(f, encoding='utf8'):
        line = line.rstrip('\n')
        if not line.strip(): continue
        if line.startswith('## '): cur = line[3:].strip(); hints[cur] = {}; continue
        parts = line.split('|')
        if len(parts) != 3: problems.append(f'{cur}: bad line {line!r}'); continue
        n, g, mn = parts; n = int(n)
        if n in hints[cur]: problems.append(f'{cur}: duplicate gap {n}')
        hints[cur][n] = [expand(g), mean(mn, cur, n)]
        raw_lines.setdefault(cur, {})[n] = parts
out = {}
for tid, h in hints.items():
    if tid not in G: problems.append(f'unknown text {tid}'); continue
    n = G[tid]['n']; words = G[tid]['words']
    missing = [i for i in range(1, n+1) if i not in h]
    extra = [i for i in h if i > n]
    if missing or extra: problems.append(f'{tid}: missing {missing} extra {extra}')
    for i, (g, mn) in h.items():
        if i > n: continue
        w = words[i-1]
        txt = (g + ' ' + mn)
        if re.search(r'(?<![A-Za-zÄÖÜäöüß])' + re.escape(w) + r'(?![A-Za-zÄÖÜäöüß])', txt, re.I):
            problems.append(f'{tid}#{i} "{w}": hint contains the answer -> {mn}')
    # article-like gaps must name their noun, and that noun must follow soon after the gap
    plain = G[tid]['plain']
    import re as _re
    for i, line in raw_lines.get(tid, {}).items():
        if i > n: continue
        pos = line[1].split()[0] if line[1].split() else ''
        mn = line[2]
        at = _re.search(r'@(.+)$', mn)
        if pos in ('bA','uA','Dem','Pos','Neg') and not at:
            problems.append(f'{tid}#{i} "{words[i-1]}": article without @noun')
        if at:
            noun = at.group(1).strip()
            k = plain.find('⟨%d:' % i)
            after = _re.sub(r'⟨\d+:([^⟩]*)⟩', r'\1', plain[k:k+400])
            if noun == words[i-1] or noun.split()[0] not in after.split(' ', 1)[1][:160]:
                problems.append(f'{tid}#{i} "{words[i-1]}": @{noun} not found right after the gap')
    out[tid] = [h.get(i, ['', '']) for i in range(1, n+1)]
done = sum(G[t]['n'] for t in out); total = sum(v['n'] for v in G.values())
print(f'texts with hints: {len(out)}/{len(G)}, gaps {done}/{total}')
print('PROBLEMS:', len(problems)); print('\n'.join(problems[:80]))
# Warnings: a hint that names another gap's answer from the same text (words of 4+ letters).
warnings = []
for tid, h in hints.items():
    if tid not in G: continue
    words = G[tid]['words']
    for i, (g, mn) in h.items():
        txt = mn
        for j, w in enumerate(words, 1):
            visible = re.sub(r'⟨\d+:[^⟩]*⟩', ' ', G[tid]['plain'])
            if j != i and len(w) >= 4 and w != words[i-1] and not re.search(r'(?<![A-Za-zÄÖÜäöüß])' + re.escape(w) + r'(?![A-Za-zÄÖÜäöüß])', visible, re.I) and re.search(r'(?<![A-Za-zÄÖÜäöüß])' + re.escape(w) + r'(?![A-Za-zÄÖÜäöüß])', txt, re.I):
                warnings.append(f'{tid}#{i} hint names the answer of gap {j} ("{w}"): {mn}')
print('WARNINGS (other gaps given away):', len(warnings)); print('\n'.join(warnings))
json.dump(out, open(os.path.join(ROOT, 'tools', 'build', 'hints.json'), 'w', encoding='utf8'), ensure_ascii=False)
if '-s' in sys.argv:
    t = sys.argv[sys.argv.index('-s')+1]
    for i,(g,mn) in enumerate(out[t],1): print(i, G[t]['words'][i-1], '|', g, '|', mn)
