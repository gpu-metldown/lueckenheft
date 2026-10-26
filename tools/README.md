# Lückenheft – Werkstatt (tools)

Everything needed to add new C-test exercises to the game and keep them consistent.
The game itself is the single file `index.html` in the repository root, served by GitHub Pages
at **emenahometech.online/lueckenheft** (also reachable as gpu-metldown.github.io/lueckenheft).
Nothing in this folder is loaded by the game.

A second copy of the game is published as a Claude artifact (claude.ai/artifact/N9TU2zC8Cq8pj9orVj5SDq).
It is `index.html` without the three `<link>` lines for `apple-touch-icon.png`, `icon.png` and
`manifest.webmanifest`, and it declares the `db` + `user` capabilities so results save to the Claude account.

## What is where

```
index.html                      the game (texts, hints, logic, styles – one file)
icon.png, apple-touch-icon.png  home-screen icons
manifest.webmanifest            "add to home screen" settings
tools/
  sources/band1-kapitel6.txt    Mut zur Lücke 1, texts 71–118: exercise (E:) and solution (S:) transcriptions
  sources/band2-texte21-36.txt  Mut zur Lücke 2, texts 21–36 (texts 1–20 exist only inside index.html)
  hints/b1*.txt, b2*.txt        hint sources for every gap (Band 1 and Band 2)
  scripts/align_transcription.py  E:/S: transcription -> gap markup, reports every mismatch
  scripts/extract_gaps.js       index.html -> tools/build/gaps.json (all gap words with context)
  scripts/build_hints.py        checks all hint files, writes tools/build/hints.json
  scripts/inject_hints.py       writes hints.json into the HINTS line of index.html
  scripts/test_answers.py       fills every text and exam with its answer key; all must score 100 %
  build/                        generated files (not committed)
```

## How the texts are stored in index.html

- `TEXTS` = Mut zur Lücke 2, texts 1–36 (50 gaps each; text 31 has 49, as printed), ids `"1"`…`"36"`.
  Ids never change, so saved results remain attached.
- `BAND1` = Mut zur Lücke 1, Kapitel 6, texts 71–118 (about 25 gaps each), ids `b1-71` … `b1-118`.
- `BOOKS` = tab names, intro text and exam description per book.
- `SETS` = Band 1 exams, built automatically from 4 consecutive texts, 25 minutes (as the book prescribes).
- `HINTS` = one line: `{text id: [[grammar, meaning], …]}`, one pair per gap, in order.
- Gap markup in `raw`: `Deutschla[nd]` = given part + missing part. Several accepted answers: `verfa[sste|ßte]`.
  Checking ignores case and treats ß and ss as equal.

## Adding new exercises (checklist)

1. **Transcribe** exercise pages and solution pages separately into `tools/sources/<name>.txt`:
   ```
   ### 119|Long title|Short title
   E: Text with gaps written as Schla_ gibt e_ viele …
   S: The full solution text, word for word …
   ```
2. **Align**: `python3 tools/scripts/align_transcription.py tools/sources/<name>.txt <id prefix>`
   (prefix `b1-` for Band 1, `""` for Band 2)
   It must report `PROBLEMS: 0`. Every problem is either a transcription slip or a real difference between
   exercise and solution page – check the scan before fixing. Unusual gap counts per text are normal
   if the book prints them that way (Band 1: texts 85, 90, 103 have 24 gaps, 99 has 26).
3. **Add the texts** from `tools/build/aligned.json` to the right array in `index.html`
   (new book: new array, new entry in `BOOKS`, new tab button, and add it in `extract_gaps.js`).
4. **Write hints** in `tools/hints/<file>.txt` (format below), then run
   `node tools/scripts/extract_gaps.js` and `python3 tools/scripts/build_hints.py` until `PROBLEMS: 0`.
5. **Inject**: `python3 tools/scripts/inject_hints.py`.
6. **Test**: `python3 tools/scripts/test_answers.py` – every text and exam 100 %, no gap without hint.
7. **Publish**: commit `index.html` (and these sources) to `main`; GitHub Pages updates within a minute.
   Then republish the Claude artifact from the same file without the three icon/manifest `<link>` lines.

Before larger changes, keep a backup branch (example: `backup-vor-neuen-tipps` = state before the stepwise hints).

## Hint file format

One block per text, one line per gap: `number|grammar code|meaning`

```
## b1-72
1|bA Nom Pl|@Bundesländer
4|Prp +Akk|„sich einigen ___ etwas“
6|P2|eine gemeinsame Entscheidung getroffen
```

- **Grammar** = word-type code + features. Codes: `bA` bestimmter Artikel, `uA` unbestimmter Artikel,
  `N` Nomen, `EN` Name, `V` Verb, `MV` Modalverb, `HV` Hilfsverb, `Adj`, `Adv`, `Prp` Präposition,
  `Prp+bA` Präposition + Artikel, `Kj` Konjunktion, `Sj` Subjunktion, `PPr` Personalpronomen,
  `Rfl` Reflexivpronomen, `Pos` Possessivartikel, `Dem` Demonstrativartikel, `DemP` Demonstrativpronomen,
  `Rel` Relativpronomen, `Idf` Indefinitpronomen, `Neg` Negationsartikel (kein), `NegP` Negationswort (nicht),
  `P2`/`P1` Partizip, `Inf`, `Zu` Infinitiv mit zu, `Num`, `Frg`, `Ptk` Partikel, `VPt` Verbzusatz,
  `Vgl` Vergleichswort, `Abk`, `Pab` Pronominaladverb.
  Features: `Nom Akk Dat Gen`, `Sg Pl`, `m f n`, `Präs Prät Perf KI KII`, `1Sg … 3Pl`, `Komp Sup`,
  `+Akk +Dat +Gen` (case after a preposition). Free text in brackets at the end is kept as is.
- **Meaning** = short German clue that must not contain the answer word. `@Wort` expands to
  „Bezugswort: „Wort““ – required for articles, possessives, demonstratives and `kein`; the checker verifies
  that the noun really follows the gap.
- Automatic masking: in `@` references, in quoted snippets („…“) and in unquoted patterns with `___`,
  a word that is itself a nearby gap is shown the way the learner sees it (`Natur` → `Na…`), so a hint never
  gives the next answer away.
- The checker rejects: missing or extra gaps, hints containing the answer, articles without `@noun`,
  `@noun` not found after the gap. It also lists WARNINGS: a meaning that names another gap's answer
  which is not printed anywhere in the text. Rephrase those unless the word is a common function word.

## Rules the game follows

- Scoring like the Studienkolleg entrance tests: 1 point per fully correct gap, result in percent,
  no school grades. Verdicts: under 60 % not passed, 60 % passed, 75 % competitive, 85 % excellent.
- Tipp (practice only): 1st tap grammar, 2nd tap meaning (both free), then letters one by one
  (that gap counts ½ point). Exams have no Tipp.
- Progress: saved in the browser; on the Claude artifact also in the viewer's Claude account;
  backup codes (`LH1-…`) move progress between devices.
