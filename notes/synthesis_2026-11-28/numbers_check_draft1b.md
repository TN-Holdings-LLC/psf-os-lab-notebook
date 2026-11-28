# Draft 1b: every number against its source (home VS, 2026-11-28)

Checked on draft.tex at 27a7d6f1; draft.tex is not changed. Part 1 by the home VS; parts 2 and 3 read by two assistant
instances under the home VS (papers and READMEs; outside references on arXiv / journal pages), their main
mismatches re-read by the home VS in paper7.tex / paper8.tex (151 qubits; N = 51, 71 on kingston; no 0.30 / 0.41;
no router comparison in paper 8).

## Part 1: analyses A to E, the records and C (home VS)

Sources are files of this branch (27a7d6f1) unless named. "line" = line of `draft.tex`.

| draft place (line) | draft number | source (file: line) | source's number | word |
|---|---|---|---|---|
| abstract (35-36), A text (208-211), table 4 | 287 declared, 158 held, 78 failed, 15 not read, 36 unclear | results_a2_d.md, "A, all periods" table (d59a5b03) | 287 / 158 / 78 / 15 / 36 | MATCH |
| abstract (35), A (208-209) | from 8 October to 27 November | same; ledger_a2.json first notebook row 2026-10-08, ledger_a.json last 2026-11-27 | 10-08 to 11-27 | MATCH |
| abstract (36-37), A (211-213) | about a third failed in every period; none of 17 decided | results_a2_d.md | 0.35, 0.37, 0.35; 0 of 17 | MATCH |
| abstract (38), A (214) | declared models failed 20 of 35 decided ("most often") | results_a2_d.md kinds table | 20 failed of 15 + 20 = 35; 0.57, the highest rate of the kinds | MATCH |
| table 4 row 1 | 139 / 70 / 38 / 9 / 22, 0.35 | ledger_a2_tables.txt (source rows) | 139 / 70 / 38 / 9 / 22; 38 / 108 = 0.352 | MATCH |
| table 4 row 2 | 73 / 34 / 20 / 5 / 14, 0.37 | ledger_a2_tables.txt | 73 / 34 / 20 / 5 / 14; 20 / 54 = 0.370 | MATCH |
| table 4 row 3 | 57 / 37 / 20 / 0 / 0, 0.35 | results_ab.md A | 57 (37 held, 20 failed); 0.351 | MATCH |
| table 4 row 4 | 18 / 17 / 0 / 1 / 0, 0.00 | results_ab.md A | 18 declared, 17 held, none failed, 1 not read | MATCH |
| table 4 all | 0.33 | computed | 78 / 236 = 0.331 | MATCH |
| A (210-211) | 75: 54 held, 20 failed, 1 not read | results/ohm-ruler5-night-2026-11-27/README.md (predictions line) | 75 declared; 54 held, 20 failed, 1 not read | MATCH |
| A (215-216) | psf-zero 1,207 rows, 105 failed | ledger_a2_tables.txt | 1,207; 105 failed | MATCH |
| table 4 caption | source results_a2_d.md | results_a2_d.md (d59a5b03 section) | the table is there | MATCH |
| B (126-129), abstract (38-40) | 48 cells, 96 units; 0.964 - 2 SE = 0.935; 94 of 96 (0.979) | results_ab.md B | 48 cells, 96 units; 160/166 = 0.964, threshold 0.935; 94 of 96 (0.979) | MATCH |
| B (130) | A2 t = 4, 26 November, 0.529 and 0.526 | results_ab.md B; ohm-ruler4 README | 0.529 / 0.526 | MATCH |
| B (131) | r = 0.94 to 1.58 | results_ab.md B | 0.939 to 1.575 | MATCH (rounded) |
| B (131-132) | at t = 3 and 4 all 60 have r > 1 | results_ab.md B | all 60 units at t = 3 and 4 have r above 1 | MATCH |
| B (126) | results after 16 November judged by the same reading = the Ohm window and ruler nights | outline.md B (423b8f3d) | the declared set also named "the real-time nights' uncontrolled arms where a mean-square reading applies"; results_ab.md B scores the Ohm nights only and does not say why the others are out | NO SOURCE for the narrowing (see report) |
| C (142), abstract (40), table 2 caption (162) | 191 jobs | calib_compare memo.md A4; findings.json targets 191 | 191 jobs listed and snapshots fetched; the counts come from **136** jobs (findings.json: 136 job ids with a counted kind; tables.md section 5: 35 + 34 + 67 = 136 jobs); 73 earlier-layout jobs read for the scan only, some not read | MISMATCH in what "over 191 jobs" covers |
| C (146), abstract (41) | CZ 2.29 x chance; per-qubit 0.71 to 2.17 | result_2026-11-27.md: 35 | cz 2.29 x, against 2.17, 1.62, 0.71 | MATCH |
| C (146), abstract (42), discussion (245) | 291 of 721; "about two in five" | result: 30 | 291 of 721 (0.404) | MATCH |
| C (146-147) | one fez qubit found 68 times with no IBM mark | result: 56; tables.md section 4 | fez mirror_low 104: 68 (times found with no IBM mark on any column) | MATCH |
| C (147-148), abstract (42) | map median 0.41 to 0.63 h; 17 of 67 marrakesh jobs over a day; largest 93 h | result: 44-45; tables.md 5 | 0.41-0.63 h; 17 of 67; 93.01 h | MATCH |
| C (148-149) | "a qubit's readout error moved by a median factor of 3.30 to 7.81" | result: 46-47 | for a qubit **of our sets**: 3.30 / 3.54 / 7.81 (fez / kingston / marrakesh) | MATCH (add "of our sets") |
| C (143) | a scoring memo committed before the seal was opened | memo.md 21f86bf8 (11-26, before any fetch) and addendum A 0b13c8fb (11-27, before opening) | as said | MATCH |
| table 2 | the three rows, all ten pairs, and IBM misses 291 / 225 / 364 | result: 22-31 | equal in every cell | MATCH |
| rulers (166), method (88-89) | rulers "from 23 November"; string mirrors and readout pairs | results/ohm-window-night-2026-11-23 (floor and mirror on 4 items, no ruler); ohm-ruler-night-2026-11-24 (rulers (a), (b) first); string mirrors from 11-25, readout pairs from 11-26 | rulers from **24** November; string mirrors 25, readout 26 | MISMATCH (date) |
| rulers (168-170) | (de) four of six (fez 26 Nov), five of six (kingston 27 Nov); (e) none of six on either night | ohm-ruler4 README; ohm-ruler5 README | 4 of 6; 5 of 6; (e) 0 of 6 both | MATCH |
| rulers (170-171) | "On ibm_fez every ruler left a positive residue at three cycles on three nights" | ohm-ruler-night-2026-11-24 README: 50-56; ohm-ruler3-night-2026-11-25 README: 48-54; ohm-ruler4 README | 11-24: ruler (a) d = -0.116 / -0.083 / -0.067 at t = 3 (negative), (b) +0.009 / +0.037 / +0.043. 11-25: (a) A0 -0.003, (b) A1 -0.015 (negative), (c), (d) positive. 11-26: every ruler positive (+0.021 to +0.110) | MISMATCH |
| rulers (171-172) | kingston: the readout-corrected ruler left a residue beyond its width in one arm of three | ohm-ruler5 README | (de) DIFFERS at A0 t = 3 (+0.023, width 0.015) | MATCH |
| rulers (172-173) | two named qubits below the threshold a third night (held); next prediction not read on another device | ohm-ruler4 README OR4-2; ohm-ruler5 README OR5-2 | held; NOT READ | MATCH |
| D (177), abstract (43), discussion (251) | 14 of 16 units; copies 0 of 9 | results_a2_d.md D; spread_d.json summary | 14 of 16; 0 of 9 | MATCH |
| D (177-179), table 3 | raw W 8 of 9; divided by the string-mirror ruler 0 of 9; its error the wider | results_a2_d.md D | 8 of 9; 0 of 9; (d)'s SE carries the mirrors' shot noise | MATCH |
| table 3 | 5 / 2.71 / yes; 3 / 1.03 / no; 1.1-4.4, 8 of 9; 0.05-1.7, 0 of 9; 12-24, 5 of 5; 0.13-1.8, 0 of 9 | spread_d.json | equal | MATCH |
| table 3 row 3 / 4 | "(25, 26 Nov.)" | spread_d.json | 11-25 and 11-26 | MATCH |
| E (236-238), abstract (43-44) | 98 of 98, to 1e-9, psf-os 0.3.3, 28 November; scorers only | results_ab.md E; reproduce_all_2026-11-28.txt (last lines) | 98 of 98 reproduced; scorers only, `--gate-hash` not run | MATCH |
| method (98-100), limits (269) | an independent re-count of each night from 18 November | results/*2026-11-1[89]* and *2026-11-2* READMEs | every night folder of 11-18 to 11-27 (22) names an independent check | MATCH |
| intro (72-73) | five analyses declared in outline.md (423b8f3d) before each was run | outline.md: 34-58; result_2026-11-27.md | outline (11-28 12:06 JST) names C as "done at the workplace on 11-27": C was declared by its own memo (21f86bf8, 11-26) before it ran, not by the outline; D's counting was fixed in home's instruction of 11-28 | MISMATCH for C (and D's counting) |
| limits (266) | kinds in A by hand up to 15 November, by fixed rules after | results_a2_d.md | as said | MATCH |
| A text (208) | "Every prediction with a stated expected outcome declared in the notebook" | ledger_a.py reads the nights' "Against the declaration" sections (11-16 on); ledger_a2 by hand | the 11-16 to 11-27 part is read by a different rule (the records' own verdict rows) | MATCH in count; wording (see report) |
| discussion (258) | the ledger gives "a base rate for how often a stated expectation about a cloud device holds" | ledger_a2.json device column | 60 of the 212 rows up to 11-15 are simulations or compile-only runs (FakeFez + noise model 27, FakeTorino compile-only 11, stand-ins and noiseless 19, not run 3) | MISMATCH in scope |

## Part 2: papers 1 to 11 and the DOIs


Sources: PDFs as published (paper7_v1, paper8_v1, paper9_v1, paper10_v1, paper11_v1 in notes/paperN; Paper3_v1.3, Paper4_v1.3, Paper5_v1.1, readable_depth_self_check_v1.0 on the Desktop); psf-zero README at 8769aa5 (found in /home/psf/rel030_psfzero, not in psf_zero_79b70ad); psf-os README at 42617f4 (in Desktop bundle psf-os_readme-top-2026-11-28c.bundle, prerequisite from /home/psf/psfos_poc_push). Page numbers are PDF pages.

| draft place | draft number or claim | source | source's number/words | verdict |
|---|---|---|---|---|
| Abstract l45 | raw circuits "of up to 153 qubits" | p7 p2 sec 3.1; p7 p7 table (a) | the largest practice problem is P5 with "151 qubits"; P4 is 33, P6 35; no 153 anywhere in papers 7-9 | MISMATCH |
| Abstract l45 | "came within 0.05 of sealed exact answers" | p7 p3 sec 4; table (a) | true only for P5 at theta = 0.8, 1.0 and P4; "P5 at theta = 0.4 is short by -0.06 to -0.07 on both devices at every depth from t = 4" (that is the 151-qubit problem) | MISMATCH (overstated) |
| Abstract l46 | 91-site chain, decay rates within 0.0037 of theory | p8 p1 abstract; p8 p6 table 1 | "largest abs(k - cos 2h) 0.0037"; fez rerun also +0.0037 | MATCH |
| Abstract l46 | to 2,205 CZ | p8 p1 abstract | "every depth up to t = 24 (2 205 CZ) is readable" | MATCH |
| Sec 2 l83-84 | paper 3: formula placement "could not be told apart from Qiskit's search" | p3 p1 abstract | "Formula placement could not be told apart from the search ... it did not beat it" | MATCH |
| Sec 2 l84-85 | paper 8: "three-dimensional prototype needs several times what a search-based router needs" | p8 whole text (grep router/SABRE/search/Qiskit) | no comparison with any router; only "it is not a search" (rule C) and the fold/carry/line CZ counts (table 4) | NO SOURCE |
| Sec 2 l87-88 | floor: non-diagonal 1q gates removed, same CZ, "ideal <Z> = 1" | p7 p2 sec 2.2 | "the same circuit without its non-diagonal one-qubit gates (ideal: every qubit reads its input)" (inputs can be 1; p8 p3 reports "1-floor marks") | MISMATCH (minor) |
| Sec 2 l88 | mirror: compiled circuit and its inverse | p7 p2 sec 2.2 | "the compiled circuit followed by its inverse (ideal: the input back)" | MATCH |
| Sec 2 l88 | ring sentinel | p7 p2 sec 2.2 | "One ring sentinel per job, a 40-qubit echo on a fixed ring" | MATCH |
| Sec 2 l92-93 | READS: MSE at most half the mean square of the exact answer (papers 7-9) | p7 p3 sec 6; p9 p2 sec 2 | "mean squared error ... at most half the mean square of the exact values"; "reads iff MSE <= 1/2 mean e^2" | MATCH |
| Sec 2 l93-94 | AGREES: inside a stated width (2 SE or t quantile) | p7 p3 sec 6; p7 p1 | du chain: "abs(k - cos 2h) <= max(2 SE, 0.005)"; practice/daily: absolute "abs(M - Mexact) <= c", c = 0.05 | MISMATCH (incomplete: omits the absolute 0.05 width) |
| Tab 1 r1 l112 | 22 practice circuits in plain Qiskit | p7 p1, p3 sec 4 | "22 practice circuits", "written in plain Qiskit" | MATCH |
| Tab 1 r1 | 33 to 153 qubits | p7 p2 sec 3.1 | P4 33-site chain, P5 151 qubits (table (a) has only P4 and P5) | MISMATCH (153 -> 151) |
| Tab 1 r1 | paper 7; marrakesh, fez | p7 p3 sec 4 | "on ibm marrakesh and on ibm fez" | MATCH |
| Tab 1 r1 | 22 / 22 READ on both | p7 p3 sec 4 | "READS 22/22 on both devices" | MATCH |
| Tab 1 r1 | 19 and 18 AGREE | p7 p3 sec 4 | "AGREES 19/22 (marrakesh) and 18/22 (fez)" | MATCH |
| Tab 1 r1 | 2D kicked Ising theta 0.8, 1.0 within 0.05 to t = 8 | p7 p7 table (a) | largest abs diff: marrakesh 0.048 (tx0.8 t8), fez 0.023 | MATCH |
| Tab 1 r1 | worst on fez 0.023 | p7 p7 table (a) | fez p5 tx0.8 t2 -0.023 (largest at theta 0.8/1.0) | MATCH |
| Tab 1 r1 | theta = 0.4 misses by -0.04 to -0.07 on both | p7 p3 sec 4; table (a) | "short by -0.06 to -0.07 on both devices at every depth from t = 4"; t = 2 (-0.046, -0.041) AGREES, not a miss | MISMATCH |
| Tab 1 r1 | 33-qubit chain's signal site falls behind with depth (0.30 against 0.41 at t = 16) | p7 whole text and tables; paper7.tex | no 0.30 or 0.41; P4 t16: diff -0.031 (R 0.799) marrakesh, -0.060 (R 0.612) fez | NO SOURCE |
| Tab 1 r1 | one day | p7 p3 sec 4 | "Result 1: practice problems (4 November)" | MATCH |
| Tab 1 r2 l113 | paper 7, 8; marrakesh, fez | p7 p4 table 1; p8 p2, p6 table 1 | N = 51 and 71 ran on ibm_kingston ("Dual-unitary chain on ibm kingston, raw"); N = 91 on marrakesh and fez | MISMATCH (add kingston) |
| Tab 1 r2 | within 0.0045, 0.0017, 0.0037 of cos 2h | p7 p1; p8 p1 | "0.0045 at N = 51, 0.0017 at N = 71"; "0.0037" at 91 | MATCH |
| Tab 1 r2 | every depth to t = 24 readable | p7 p4 table 1; p8 p6 table 1 | 24 at every h for 51, 71, 91 marrakesh; fez rerun "readable depth 24 (16 for h = 0.10)" | MATCH (fez rerun excepted) |
| Tab 1 r2 | 2,205 CZ at N = 91 | p8 p6 table 1 | CZ (t 24) 2205 | MATCH |
| Tab 1 r2 | h = 0.15 sat +0.0037 above cos 2h on both devices | p8 p1 abstract | "h = 0.15 sat +0.0037 above cos 2h on both devices" | MATCH |
| Tab 1 r3 l114 | 3D: kicked Ising 4x4x3, Heisenberg 4x2x2; paper 8; marrakesh, fez | p8 p3-4 | physics A and B on fez; light cone on marrakesh; layout comparison also on kingston | MATCH |
| Tab 1 r3 | Ising read at every angle and depth | p8 p1, p3 sec 4 | "kicked Ising on 4x4x3 read at every angle and depth" | MATCH |
| Tab 1 r3 | Heisenberg read | p8 p3 sec 5 | "READS at t = 1-4, DIFFERS" | MATCH |
| Tab 1 r3 | light-cone test failed as predicted (every front late) | p8 p1; p8 p4 sec 8 | "A light-cone test failed as predicted: every front arrived late"; sec 8: failure was predicted "beyond distance 1", and distance 1 was also late | MATCH (abstract wording) |
| Tab 1 r3 | 46% fewer CZ came farther on 4x3x2 | p8 p4 sec 6.4 | "line was farther in all 8 place-and-t cells with 46% fewer CZ" | MATCH |
| Tab 1 r4 l115 | paper 9; fez | p9 p2-3 | utility and Hubbard on ibm_fez | MATCH |
| Tab 1 r4 | Z106 read raw to 8 steps | p9 p1, p2 sec 3.2 | "reading to 8 steps for Z106" | MATCH |
| Tab 1 r4 | Hubbard read at every size 40 to 120 qubits at 4 Trotter steps | p9 p3 sec 4.2 | "Every size from 40 to 120 qubits read at 2 and 4 steps" | MATCH |
| Tab 1 r4 | Hubbard read at neither size run at 6 steps | p9 p3 sec 4.2 | "neither size run at 6 steps (72 layers) read" | MATCH |
| Tab 1 r5 l116 | paper 5; marrakesh, kingston | p5 p1 | "ibm marrakesh and ibm kingston (29 October)"; fez on the next day | MATCH |
| Tab 1 r5 | L* = 56-57 (marrakesh), 81-90 (kingston) against 15-26 | p5 p1 | "56-57 steps on marrakesh and 81-90 on kingston, against 15-26 for the others" | MATCH |
| Tab 1 r5 | for the folded ring and blind search | p5 p1 | others = zipper (ring folded) and blind Qiskit | MATCH |
| Tab 1 r5 | 71 wins, 11 ties, no loss in 144 comparisons | p5 p1 | "71 wins, 11 ties and no loss in 144 comparisons (62 not judged)" | MATCH |
| Tab 1 r5 | the declared noise model did not hold | p5 p1 | "The noise model we declared did not hold" | MATCH |
| Tab 1 r5 | 18 sites on kingston's n = 40 ring "dead" while calibration showed nothing | p5 p1 | "a run of 18 sites whose echo was near random or inverted ... while the calibration showed nothing there" | MATCH (paper says near random or inverted) |
| Tab 1 caption l119 | "as published [p5,p7,p8,p9]" | - | all rows' devices from those papers | MATCH |
| Sec 3 B l125 | r < 0.293 means does not read by construction | p9 p1 | "r < 1 - 1/sqrt2 ~ 0.293 means does not read by construction" | MATCH |
| Sec 3 B l125-126 | 160 of the 166 results with r >= 0.293 read | p9 p4 sec 5.1 | "Of the 166 with r >= 0.293, 160 read (96%)" | MATCH |
| Sec 3 B l126 | table assembled after the results | p9 p3 sec 5.1; p4 | "(written after all were scored)"; "the rest of the table is an after-the-fact collection" | MATCH |
| Sec 3 B l129 | 0.964 (the declared share) | p9 p4 | 160/166 = 0.964 ("96%") | MATCH |
| Sec 3 B l130-131 | "as in paper 9's six, the error that is not a shrink decided" | p9 p1, p4 sec 5.1 | only 3 of the 6 (Hubbard 6 steps, rest 0.27-0.32 "as large as the shrink"); the other 3 are "the XX chain at the line itself ... rest 0.025-0.063" | MISMATCH |
| Sec 3 B l132-133 | "the region near 0.293, where paper 9's misses sat" | p9 p4 sec 5.1 | Hubbard misses at "r = 0.38-0.51"; XX misses at the MSE line 0.5, r not stated as near 0.293 | NO SOURCE |
| Sec 4 l136 | 18 sites, kingston n = 40 | p5 p1 | "run of 18 sites" on "the rule's n = 40 ring" | MATCH |
| Sec 4 l137 | near random or inverted in three runs of the byte-identical circuit over three hours | p5 p1 | "the same 18 sites in three runs of the byte-identical circuit over three hours" | MATCH |
| Sec 4 l137-138 | calibration showed nothing | p5 p1 | "while the calibration showed nothing there" | MATCH |
| Sec 4 l138 | gate twirling turned the inverted part random, so the cause is on the device | p5 p1 | "Gate twirling ... turned the inverted part random: the cause is on the device, not in the circuit" | MATCH |
| Sec 4 l139 | scanned, listed dead paths, placed around them | p6 p1 | "tests the rings ... keeps a list of the paths it found dead ... places the next ring around them" | MATCH |
| Sec 4 l139-140 | 22 to 40 usable sites on three days | p6 p1; p6 p4 table 3 | "kingston n = 40: 22 of 40 to 40 of 40 on three days" | MATCH |
| Sec 4 l140 | 6 of 6 declared comparisons WIDER | p6 p5 sec 5.1 | "C WIDER in 6 of 6 and NARROWER in none" (3 days x n = 40 and n = 72) | MATCH |
| Sec 4 l140 | widened rings on two more devices | p6 p1 | "on two more devices the same scan-then-avoid widened the ring (fez ..., marrakesh ...)" (verdict word there: HELPS) | MATCH |
| Sec 5 l201 | RUS chains crossed the ceiling with a margin growing per neuron | p10 p1 | "crossed the ceiling and the margin grew with the chain length" | MATCH |
| Sec 5 l201-202 | IPE 0.903 against 0.471 at n = 4 | p10 p1, p4 | "0.903 against 0.471 at n = 4" (ibm_marrakesh) | MATCH |
| Sec 5 l202-203 | waiting qubit in 1 turned to 0 kept +0.029 to +0.052 more on three devices | p11 p1, p7 table 2 | "+0.029 to +0.052", marrakesh, fez, kingston | MATCH |
| Sec 5 l203-204 | IPE parked beyond its ceiling to eight bits (0.424 against 0.201) | p11 p1 | "stayed beyond its ceiling to n = 8 (0.424 against 0.201)" | MATCH |
| Sec 5 l204-205 | rule 4: same circuits drift between jobs, copies inside one job agree | p11 p1, p7 table 2 | "(4) The same circuits drift between jobs sent seconds apart (one of three chain lengths, p = 0.006) while copies inside one job agree"; one night | MATCH (qualifiers dropped) |
| Discussion l249-250 | paper 3 could not be told apart; paper 8 "costs several times a router" | p3 p1; p8 | paper 3 as above; paper 8 no router comparison | p3 MATCH; p8 NO SOURCE |
| Discussion l247-248 | where the shape is wrong, dividing by a measured share does not undo it (paper 9) | p9 p1; p7 sec 8 | "dividing raw values by a measured share ... cannot undo what is not a shrink, and ... made some results worse"; "a wrong shape is not a scale" | MATCH |
| Discussion l256 | paper 7's bias in both directions | p7 p1, p5 sec 8 | "an absolute criterion ... is biased in both directions" | MATCH |
| Bib p1 l284 | title, v2, doi 22977930 | psf-os README 42617f4 l117; psf-zero README 8769aa5 l195 | same title; "1 (v2)"; 10.5281/zenodo.22977930 | MATCH |
| Bib p2 l285 | title, v2, doi 22978090 | psf-os README l116; psf-zero l198 | same; v2; 22978090 | MATCH |
| Bib p3 l286 | title, v1.3, doi 23826596 | psf-os README l115; psf-zero l202 | same; v1.3; 23826596 | MATCH |
| Bib p4 l287 | title, v1.3, doi 23826764 | psf-os README l114; psf-zero l209 | same; v1.3; 23826764 | MATCH |
| Bib p5 l288 | title, v1.1, doi 23827536 | psf-os README l113; psf-zero l217 | same; v1.1; 23827536 | MATCH |
| Bib p6 l289 | title "What Sets the Readable Depth of a Placed Ring, and How Far a Self-Checking Layer Pushes It" | psf-os README l112; psf-zero README; p6 PDF p1 | "... Pushes It: Scan, Register, Avoid and Repair on Three Heavy-Hex Devices Without the Calibration Map" | MISMATCH (subtitle missing) |
| Bib p6 | v1.0, doi 23883938 | psf-zero l225 | "version 1.0"; 23883938 | MATCH |
| Bib p7 l290 | title, v1, doi 24046673 | psf-os README l111; psf-zero l232 | same; "version 1"; 24046673 | MATCH |
| Bib p8 l291 | title, v1.0, doi 24136512 | psf-os README l110; psf-zero l240 | same; "version 1.0"; 24136512 | MATCH |
| Bib p9 l292 | title, v1, doi 24278888 | psf-os README l109; psf-zero l246 | same; "version 1"; 24278888 | MATCH |
| Bib p10 l293 | title, v1, doi 24367001 | psf-os README l108; psf-zero l250 | same; "version 1"; 24367001 | MATCH |
| Bib p11 l300 | title, doi 24496368 | psf-os README l107 | same; 24496368 (not in psf-zero README at 8769aa5) | MATCH |
| Bib p11 | v1 | READMEs give no version; notes/paper11/ZENODO.md l3 | "doi:10.5281/zenodo.24496368 (version 1)" | MATCH (not in READMEs) |
| Data l277 | psf-os 0.3.3, doi:10.5281/zenodo.24496267 | psf-os README 42617f4 (only 24211404 all-versions, 24211405 for 0.1.1); psf-zero README (0.3.1, 24438701); p11 PDF p6 l340 | p11: "psf-os 0.3.3 ... (doi:10.5281/zenodo.24496267)" | MATCH to paper 11; NO SOURCE in either README |

## Part 3: the outside references


Sources: the arxiv.org/abs pages; arxiv.org/html/2312.14107; ar5iv.labs.arxiv.org/html/2008.11294; the nature.com page for [2]; the arXiv PDF text of 1907.13608.

## Bibliographic fields
| # | Title | 1st author | Year | Journal | Vol | Art./page | arXiv |
|---|---|---|---|---|---|---|---|
| 1 | OK | OK (Timothy Proctor) | OK | OK PRL | OK 129 | OK 150502 | OK |
| 2 | OK | OK | OK | OK Nat. Phys. | OK 18 | OK 75 (pages 75–79, nature.com) | OK |
| 3 | OK | OK (Jordan Hines) | see note | see note | – | – | OK |
| 4 | OK | OK | OK | OK Nat. Commun. | OK 11 | OK 5396 | OK |
| 5 | OK | OK | OK | OK PRA | OK 94 | OK 052325 | OK |
| 6 | OK | OK | OK | OK PRX | OK 11 | OK 041039 | OK |

Note on [3]: the arXiv citation is correct (v1 posted 21 Dec 2023), but the paper is now published. The arXiv abs page gives IEEE Trans. Quantum Eng. 5, 1–12 (2024), DOI 10.1109/TQE.2024.3404502. Cite the published version. CANNOT CONFIRM the IEEE article number because I did not read the IEEE page.

## Uses in the draft
**[1,2] mirror circuits: OVERSTATES (imprecise).** [2] does start from C followed by C⁻¹, but the circuits it actually runs are randomized mirror circuits. Each one is a random single-qubit Clifford layer L0, then C, then a random Pauli layer, then a quasi-inverse of C (each layer inverted up to a random Pauli), then L0⁻¹ (ar5iv 2008.11294). The circuits in [1] are randomized in the same way. "Circuits of a user's shape" is fair. [2] defines shape as (w, d), meaning width and depth, and builds benchmarks "based on any program" (abstract). "Benchmark of error rates" fits [1].
Suggested wording: "Randomized mirror circuits (a circuit, a random Pauli layer, then its quasi-inverse, with random single-qubit Clifford layers on each side) are an established benchmark of error rates [1] and of a device's capability on circuits of a given shape (width, depth) [2]."

**[3] IBM heavy-hex: FITS.** The paper says: "We ran MQV and QV on ibm_hanoi, an IBM Q processor with heavy-hexagon connectivity". Its method "runs mirror circuits of three types", with widths up to n = 10. Consider naming ibm_hanoi in the text.

**[4] drift between calibrations: OVERSTATES.** [4] did not use routine or production data from the device. It ran dedicated time-resolved Ramsey and gate-set tomography (GST) experiments on a single ¹⁷¹Yb⁺ ion qubit in a Sandia surface trap. The GST runs lasted about 5.5 h and about 40 h. The first run had no periodic recalibration and showed drift. The authors then added periodic recalibration, and the second run showed the qubit was stabilized. The paper does say the method "can be applied to data gathered primarily for other purposes". So "the device's own data" fits only in that general sense, and "between calibrations" does not describe what they did.
Suggested wording: "Spectral analysis of time-series data can detect and track drift in a quantum processor; it was demonstrated on a trapped-ion qubit and applies to data from any circuits [4]."

**[5,6] twirling coherent to stochastic: FITS (minor caveat).** The abstract of [5] says the random single-qubit gates tailor noise into stochastic Pauli errors, and [6] says randomized compiling converts coherent errors into stochastic noise. Caveats: [5] and [6] call the method "randomized compiling" (Pauli twirling inside a compiled circuit), and the conversion is exact only in the average over random compilations. Suggested wording: "randomized compiling (Pauli twirling) tailors coherent errors into stochastic Pauli noise on average [5,6]."
