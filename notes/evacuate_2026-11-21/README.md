# What waits, and what could be taken out of the wait (desk, 2026-11-21 night)

Home VS Claude, on the home instruction `VSクロードへの指示_待つ量子ビットの退避と遅らせの机上調査_2026-11-21.md` (the
owner's idea of 20:07 JST, "退避させて、深い位置で再度出す"). The report is
`VSから家へ_退避と遅らせの机上調査_2026-11-21.md`.

- psf-os branch `evacuate-study-2026-11-21` (from v0.3.0) adds `psf_os.evacuate`, which nothing in psf-os calls; no
  default changed.
- No device. **The only device record behind any expectation here is psf-os 0.3.0's park: two nights, IPE, the K case
  with |1>.**

## The kinds

At every wait of `fence_waits(conditionals=True)`, each waiting qubit (neither measured there nor inside its
conditionals) is sorted, from its noiseless state over every branch:

| kind | meaning | evacuated form |
|---|---|---|
| 0 | \|0> | — |
| L | delayable: only one-qubit gates so far | its preparation moved after the waits |
| K | the same pure state in every branch | U^dagger before, U after (X for \|1>: the park) |
| B | a basis state by branch: B1 when one bit read gives it; Bn otherwise | B1: a conditional X before and after |
| E | entangled (Ee) or a superposition by branch (Epsi) | none |

Two kinds were added inside the home's four, counted apart:

- **Epsi:** a pure state that changes with the branch. A conditional one-qubit gate could undo it; it is not built here.
- **Bn:** a basis value that needs a function of several bits.

Neither occurs in the RUS chains: there is one Epsi in decoy's Z, and no Bn anywhere.

## The table (`table.py`, `table.txt`, `table.json`; `excited_split.py`, `excited_split.txt`)

Columns are qubit × wait over all items of the tool. The excited count is the expected waiting qubits in |1>, summed
over the waits.

| tool | items | 0 / L / K / B / E | excited at the waits (footprint) | of it: waiting K / B / E | of it: taking part in the wait |
|---|---|---|---|---|---|
| RUS P0 (os3, paired, loopvar) | 3 | 24 / 0 / 0 / 9 / 6 | 20.75 | 0 / 0.31 / 5.46 | 14.98 |
| RUS P3 | 3 | 16 / 0 / 0 / 5 / 5 | 11.88 | 0 / 0.52 / 4.36 | 7.00 |
| RUS P1 (loopvar's x) | 6 | 40 / 0 / 0 / 20 / 50 | 16.75 | 0 / 1.24 / 12.09 | 3.42 |
| RUS P2 | 6 | 40 / 0 / 0 / 20 / 50 | 16.75 | 0 / 1.24 / 12.09 | 3.42 |
| RUS NF (B's other frame) | 6 | 40 / 0 / 0 / 14 / 38 | 36.05 | 0 / 0.83 / 31.79 | 3.42 |
| IPE n = 2-6 | 124 | 0 / 0 / 1032 / 0 / 0 | 1032 | 1032 / 0 / 0 | 0 |
| textbook phase estimation | 60 | no wait | 0 | — | — |
| repetition code F16, F10, F6P, F6 | 4 each | no waiting qubit | 6.0 each | — | 6.0 each |
| decoy rd2 and Z | 2 | 8 / 0 / 0 / 4 / 12 | 3.57 | 0 / 0.87 / 2.60 | 0.11 |

The +M, +F and +Q stacks are these circuits:

- +M is m = 3;
- +F switches the base between P1 and P2;
- +Q moves the item to other qubits (the same circuit);
- the paired loop and loopvar build the same items.

- **The "12 to 36"** were the tools' totals over their items, not per item. Per item they are 2.8 to 6.9.
- **P0 and P3:** most of their excited count is on qubits that take part in the wait (inside the retries'
  conditionals), not on waiting qubits.
- **P1, P2 and NF:** most of it is E, the neuron outputs entangled with the chain's state.
- **B is a few percent everywhere.** Every B is B1: a neuron's ancilla left in |1> after a failed last try, which is
  rare (excited 0.035 per wait).
- **L never occurs:** every qubit stays in |0> until its first use.
- **K occurs only in IPE.** There it is exactly psf-os 0.3.0's park (124 of 124 the same circuit).

## The evacuated forms

- **Checks:** the noiseless distribution is the same in every form (evacuate refuses otherwise), and the compiled CZ
  is the same in every changed item.
- **B1 (RUS, decoy):** compiled depth +4 to +21, and +2 to +18 waits (each conditional X is a wait).
- **K (IPE):** the park itself: depth +0 and waits +0 against 0.3.0.

## Dry runs (`dry.py`, `dry.txt`; ILLUSTRATIVE noise: damping 6 % per read; dephasing 5 % per conditional)

The default (psf-os 0.3.0) parks nothing in the RUS chains, so it is unfenced; the evacuated form is fenced. The fenced
circuit is run beside, and g (|P − exact| nearer) splits into the fence's part and B1's own part.

| item | damping: fence / B1 | dephasing: fence / B1 |
|---|---|---|
| P2 m3 L3 | **+0.043** / +0.007 | **+0.045** / −0.018 |
| P1 m3 L3 | **+0.042** / +0.007 | **+0.046** / −0.019 |
| P2 m2 L3 | +0.020 / +0.004 | +0.014 / −0.009 |
| P0 L3 | **−0.057** / +0.005 | **+0.046** / −0.012 |
| P3 L3 | **−0.069** / +0.004 | +0.018 / −0.006 |
| L2 items | −0.042 to +0.016 / 0.000 | +0.007 to +0.020 / −0.003 to −0.008 |
| decoy rd2 | +0.006 / 0.000 | +0.007 / −0.004 |

(2 SE about 0.007 to 0.010 per difference.)

- **B1's own part is small:** at most +0.007 under damping, within 2 SE. Under dephasing per conditional it costs
  −0.004 to −0.019, since it adds conditionals.
- **The fence alone moves the RUS chains a lot.** The direction depends on the form and the noise: P1 and P2 gain
  under both noises; P0 and P3 lose under damping and gain under dephasing.
- On the device the fence alone read SAME on IPE (the weekend's C, fe − pl −0.0042). For the RUS chains it has never
  been run.

## Device plans (`plan.py`, `plan.txt`, `plan.json`; built on the 2026-11-21 10:39 marrakesh record, never run)

Each plan holds the three forms of each item side by side in one job: default, fenced and evacuated. That gives two
differences: fence (fenced − default) and B1 (evacuated − fenced). It uses ff arms only, 4000 shots and one sentinel
per job. In every item the CZ and the noiseless distribution are the same in all forms.

| plan | items × copies | circuits | s (model) | 2 SE per difference | expected (dry): fence / B1 |
|---|---|---|---|---|---|
| A | P2 m3 L3 × 4 | 16 | 20.9 | 0.0089 | +0.043 to +0.045 / −0.018 to +0.007 |
| B | P2 m3 L2, L3 × 2 | 16 | 20.9 | 0.0126 | L3 as A; L2 +0.015 / −0.006 to 0 |
| C | P2 m3 L3, P0 L3 × 4 | 28 | 34.2 | 0.0089 | P2 as A; P0 −0.057 (damping) or +0.046 (dephasing) / ≈ 0 |
| D | P0, P2 m3 at L 1-3 × 2 | 40 | 47.6 | 0.0126 | as above, with L1 (nothing to evacuate) as a control |

Every plan is within 60 s. Plan C reads the fence on two forms whose sign depends on the noise. Its sign on the device
would say which noise type the RUS chains meet in their waits.
