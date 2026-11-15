# A deterministic answerer for result lookups (prototype, 2026-11-15)

Owner 2026-11-15 ("プロトタイプ試作"; question type: result lookups only; then the four check families below). No
language model and no probability:

1. entrance: fixed rules read a Japanese question into conditions (date, device, family, run, problem, observable,
   arm, size, U, T, angle, depth, which answer it was checked against). The entrance is closed: every character must
   be taken by a pattern, a dictionary spelling or a listed filler word; a word no rule takes stops the answer
   ("解釈できない語"), and two values for one condition stop it ("条件がぶつかっている");
2. refusals before any lookup: why, the future, approximations, comparisons;
3. core: the conditions select rows of the records (the 179 results of `notes/paper9_yardstick/line_all.json`,
   2026-11-05 to 2026-11-14);
4. answer card: fixed sentence templates, each line with its stored verdict (never recomputed), MSE / mean square, r
   and record folder.

    python notes/ask_prototype/ask.py "11月14日の marrakesh で XX 81量子ビット 16ステップ π/4 は読めた？"
    python notes/ask_prototype/ask.py --test

## Checks (`checks.py`, 2026-11-15: ALL PASS)

1. round trip: 358 questions written mechanically from the 179 rows (two spellings each): every one lists its row and
   only rows equal to it; rows no question can tell apart: 0. It found that the Hubbard time-step records (circuit
   answer and continuum answer of the same circuit) could not be told apart; they now carry "回路の答え" /
   "連続極限の答え".
2. spellings: 67 spellings, 4422 pairs from different entries, each reads to its own value only; no spelling or filler
   contains a refusal word (this found "連続極限との比較" tripping the comparison refusal; renamed); 7 stray-word and
   2 conflict questions stop.
3. edges: 8 rows near the line print their stored verdict, which agrees with MSE <= mean square / 2; the size test
   and the light-cone repeat (same day, same circuits) are both listed and can be asked one by one; NaN and missing
   values print as "値なし" / "判定なし"; 183 questions give the same answers over 10 fixed orders of the index.
4. refusals: 100 questions (25 stems x 4 contexts) that must not be answered: answered 0.

The checks are written by the same hand as the rules: they show the rules do what they say, not that they cover
every question a person may write. What covers the rest is the closed entrance.

Not yet: floors, sentinels, mirrors and the full-floor nights (their counts sit in each run folder in more than one
format, so they need their own collector and answer template); relative dates; numbers in kanji.
