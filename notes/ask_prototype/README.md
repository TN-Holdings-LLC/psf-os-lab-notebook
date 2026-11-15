# A deterministic answerer for result lookups (prototype, 2026-11-15)

Owner 2026-11-15 ("プロトタイプ試作"; question types: result lookups only). No language model and no probability:

1. entrance: fixed rules read a Japanese question into conditions (date, device, family, size, depth, angle, U);
2. core: the conditions select rows of the records (the 179 results of `notes/paper9_yardstick/line_all.json`,
   2026-11-05 to 2026-11-14);
3. answer card: fixed sentence templates, each line with its verdict, MSE / mean square, r and record folder.

The same question gives the same answer. No match: the count under each condition alone. Too many matches (over 12):
the values that would narrow it. Why-questions and predictions: refused with a fixed sentence.

    python notes/ask_prototype/ask.py "11月14日の marrakesh で XX 81量子ビット 16ステップ π/4 は読めた？"
    python notes/ask_prototype/ask.py --test      # 11 fixed checks

Not yet: records outside the yardstick table (floors, sentinels, the full-floor nights), relative dates (昨日),
numbers in kanji, comparisons, predictions.
