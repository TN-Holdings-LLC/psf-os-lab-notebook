# How a value beside the verdicts is written (2026-11-23; home instruction C)

A value **beside** is a number that is not one of the declared differences:

- a difference of forms that the declaration did not judge;
- a per-n value;
- a cut made after the declaration.

It gets no verdict word. It is written in one fixed form, so that the words never claim more than the number holds.

## The form

> **+0.0045 (2 SE 0.0055): not separated from 0. The upper end of 2 SE is about +0.01.**

| part | rule |
|---|---|
| value and 2 SE | the value with its sign and 4 decimals, then its 2 SE in brackets |
| separation | "separated from 0" when \|value\| ≥ 2 SE, otherwise "not separated from 0" |
| the end of 2 SE | for a value not separated from 0, the far end of value ± 2 SE, rounded to one significant figure ("about +0.01") |
| where it comes from | "beside" or "beside, after the declaration" when it was cut after the declaration was written |

A value separated from 0 is written the same way, without "not": "+0.0349 (2 SE 0.0072): separated from 0".

## Words not used

Do not use words that claim what was not measured:

- **"at most", "at least"**: they turn a 2 SE end into a bound. Write the end of 2 SE as above.
- **"only", "merely", "just"**: they rank the size of a cost that was not compared with anything.
- **"far longer", "much smaller", "negligible", "a few thousandths" (as a bound)**: they compare with a quantity that
  was not measured, such as the device's own wait. A size measured with its 2 SE may be named: "+0.0045 (2 SE 0.0055)".
- **"lies elsewhere", "is caused by", "is due to"**: a value beside does not locate a cause.

## Guesses

A guess, such as a reading of why a number came out as it did, is labelled **"guess (not measured)"** and sits after
the numbers.

> F lost +0.0045 (2 SE 0.0055) against S: not separated from 0. The upper end of 2 SE is about +0.01. Guess (not
> measured): the device's wait for a conditional is shorter than the 18 µs of L.

## Checked by a machine

`tools/check_readme_numbers.py` compares the numbers of each `results/*/README.md` with the night's records:

- job tables;
- the charge;
- delays;
- 4-decimal values against the score files.

The wording is checked by a reader against this note.
