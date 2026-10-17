# Opens index.html in a phone-sized browser and fills every text (and every Band 1 exam) with its own
# answer key. Every one must score 100 %. Needs Playwright with Chromium.
# Usage (from the repo root):  python3 tools/scripts/test_answers.py
import os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
URL = 'file://' + os.path.join(ROOT, 'index.html')
bad = []
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(**p.devices['iPhone 13']).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/fonts.googleapis.com/**', lambda r: r.abort())
    pg.goto(URL); pg.wait_for_timeout(400)
    books = pg.evaluate("[['b2', TEXTS.map(t => t.id)], ['b1', BAND1.map(t => t.id)]]")
    for book, ids in books:
        pg.click(f'#book{book.upper()}'); pg.click('#modeU')
        for tid in ids:
            pg.click(f'button[data-id="{tid}"]')
            sols = pg.evaluate(f"TEXTS.concat(BAND1).find(t => t.id == '{tid}').gaps.map(g => g.ans[0])")
            for inp, a in zip(pg.query_selector_all('#passage input'), sols): inp.fill(a)
            pg.click('#submitBtn'); pg.wait_for_timeout(40)
            r = pg.inner_text('.facts div:nth-child(2) b')
            if r != '100 %': bad.append((tid, r))
            pg.click('#backBtn2')
    pg.click('#bookB1'); pg.click('#modeP')
    n_sets = len(pg.query_selector_all('#list button[data-id]'))
    for k in range(1, n_sets + 1):
        pg.click(f'button[data-id="b1-p{k}"]')
        sols = pg.evaluate(f"BAND1.slice({k-1}*4, {k}*4).flatMap(t => t.gaps.map(g => g.ans[0]))")
        for inp, a in zip(pg.query_selector_all('#passage input'), sols): inp.fill(a)
        pg.click('#submitBtn'); pg.wait_for_timeout(40)
        if '100 %' not in pg.inner_text('.facts'): bad.append((f'b1-p{k}', pg.inner_text('.facts')))
        pg.click('#backBtn2')
    missing = pg.evaluate("TEXTS.concat(BAND1).reduce((a, t) => a + t.gaps.filter(g => !g.hint).length, 0)")
    b.close()
print('texts checked:', sum(len(i) for _, i in books), '| exams checked:', n_sets)
print('gaps without hint:', missing)
print('page errors:', errs or 'none')
print('NOT 100 %:', bad or 'none')
sys.exit(1 if bad or errs or missing else 0)
