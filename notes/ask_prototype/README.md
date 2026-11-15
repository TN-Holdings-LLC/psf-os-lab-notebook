# A deterministic answerer for result lookups (prototype, 2026-11-15)

Owner 2026-11-15 ("プロトタイプ試作"; question type: result lookups only; then the four check families below). No
language model and no probability:

1. entrance: fixed rules read a Japanese question into conditions (date, device, family, run, problem, observable,
   arm, size, U, T, angle, depth, which answer it was checked against). The entrance is closed: every character must
   be taken by a pattern, a dictionary spelling or a listed filler word; a word no rule takes stops the answer
   ("解釈できない語"), and two values for one condition stop it ("条件がぶつかっている");
2. refusals before any lookup: why, the future, approximations, comparisons;
3. core: the conditions select rows of the records (the 179 results of `notes/paper9_yardstick/line_all.json`,
   2026-11-05 to 2026-11-14, each with its job's floor, mirror and sentinel as stored in its score file; and the
   whole-device floor nights, `results/full-floor-*`, per qubit);
4. answer card: fixed sentence templates, each line with its stored verdict (never recomputed), MSE / mean square, r
   and record folder.

    python notes/ask_prototype/ask.py "11月14日の marrakesh で XX 81量子ビット 16ステップ π/4 は読めた？"
    python notes/ask_prototype/ask.py "11月14日の fez で XX 81量子ビット π/4 の対照"       # floor, mirror, sentinel
    python notes/ask_prototype/ask.py "marrakesh 全面フロア 102番"
    python notes/ask_prototype/ask.py --test

## Checks (`checks.py`, 2026-11-15: ALL PASS)

2 now covers 78 spellings and 6006 pairs (with the control words).

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
5. controls: all 179 rows asked with "対照" print their job's floor, mirror and sentinel; the only values not in a
   score file are the sentinels of the twin test (6 rows; the job ran a sentinel, `twin_scores.json` does not store its
   verdict), printed as "記録になし"; all 302 qubits of the two whole-device floor nights answer with the value read
   again from `full_floor.json`.

Control values are printed as recorded, under each record's definition: floor and mirror are the mean <Z> of the
measured qubits (the utility observables: the parity of the observable's qubits; the dual-unitary curves: the mean
over the curve and the range of the mirror over depth); the whole-device floor is 1 - z(|0>) and 1 + z(|1>) per qubit
(ideal 0). The prototype does not compute a verdict a record does not store.

The checks are written by the same hand as the rules: they show the rules do what they say, not that they cover
every question a person may write. What covers the rest is the closed entrance.

## Added the same day

- Relative dates: "最新" / "前回" are the newest / second newest date among the records that match the other
  conditions; "昨日" is the day before the newest date of all records. The answer prints how it read them. Other
  relative words (先週, 一昨日, ...) are refused.
- The daily record: every line of `results/daily/RECORD.md` (days not run and refused problems included), with r
  joined from the yardstick table (the 11-06 "user" tag is FX-A run alone, `results/daily/2026-11-06/README.md`).
- Conditions are printed in one fixed order, so the order of words in a question does not change the answer.
- `shell.py`: an outer shell for questions the closed entrance cannot read. A local model (Ollama) only proposes a
  condition card with the words it read each condition from; the core checks it (schema, the core's own reading,
  numbers both ways, every character accounted for, mirror) and any failure stops the answer ("DEAD"). Refused and
  core-readable questions never reach the model. What no check can do: tell whether the model's reading of its words
  is right; that reading is printed with the answer.

Live run 1 (owner's PC, qwen2.5:7b on Ollama, first form: the model wrote a whole card): 8 paraphrases, answered 0,
stopped 8 (4 changed a condition the core had read, e.g. フェズ as ibm_marrakesh; 2 called a lookup "other"; 2 gave
evidence that took another condition's words). No wrong answer, no use. Second form (same day): the model is asked
only what the words the core could not read mean, one word at a time ({"key", "value"}, {"part_of": key} or null);
4 of the 8 paraphrases now need no model at all (their leftover words are listed fillers). Rules added with it: the
model may not add a display, a date, an arm or a problem; a word with a number must be read as that number; a word
"part of" a condition is at most six characters and touches that condition's words directly or across の / を.

Checks 6 and 7: 18 daily lines and 81 relative-date questions against dates computed independently; 8 paraphrases
with honest stub replies answered (4 without the model), 14 wrong replies all stopped, and stub models that want to
answer anything get 0 of the 116 refusal questions through (before the part-of rule: 9, then 2) (these are questions written by the same hand; in principle such a model can
map an unknown word to a condition, and the printed reading is then the only guard). The live run against a real
local model is `python notes/ask_prototype/shell.py --live-suite` on a machine with Ollama.

Not yet: records outside the yardstick table (stage tests, flows, the Ohm and Schwinger families); relative dates;
numbers in kanji.

## The owner's 20 questions (2026-11-15 13:21 CET, written without seeing the rules; e372bceb, qwen2.5:7b)

Answered with records 8 (2 of them used the model's reading: "やり直した" as the light-cone repeat, "見せて" as part
of the display), answered "no record" 2 (both right: no Hubbard on 11-14 fez, no 999-qubit chain), refused 5 (all
should be: "前回" with one date only, 一昨日, why, future, comparison), stopped 5. Wrong answers: 0. Of the 14 that
could be answered, 10 were; 4 stopped on wording the core lacked ("どうなった", "どうなってる", "いくつ", "読めてる",
"81ビット"). Those were added (fillers and the unit ビット); the 20 are now check 8, so they are no longer unseen: the
next fair test needs new questions.

## Compile, ideal values and estimates (2026-11-15 afternoon; owner: estimates allowed, labelled, with their basis)

`xxtools.py`, XX chain first, routed by "コンパイル" / "理想値" / "見積もり" ("読めそう"):

- compile: the circuit built by `gpu/ffxx91.py` (the path of the declared XX runs) on the newest device record of that
  device in the notebook: chain, CZ count, CZ depth of the compiled circuit, failed elements avoided; about 20 s;
  "置けなかった" with psf-os's reason when no chain fits (e.g. 120 sites on marrakesh: longest 113).
- ideal: noiseless <Z_i> by free fermions, exact at any size, no sampling (pi/2 checked at +-1).
- estimate: r from the recorded XX series on the same device whose depths bracket the asked depth (ln r interpolated),
  same size first, no extrapolation in depth, no estimate on a device without XX records. Printed with its own past
  record: each of the 75 XX results estimated from the other series: recorded r inside the range 23 of 75 (the
  ranges are narrow: one to four series), side of 0.293 right 70 of 75. The rest (shape error) is not estimated.

"昨日" is read from the newest date of all records (results, daily lines, whole-device floors); with the 11-15
records it is now 11-14. The yardstick table (`line_all.json`) stays at the 179 results of paper 9, so the daily
lines of 11-15 carry no r in the answers.
