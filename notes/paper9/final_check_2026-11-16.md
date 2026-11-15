# Paper 9 v1: final check against the records (workplace, 2026-11-16, before release; nothing in the paper changed)

Checked: `論文9_v1_公開予定2026-11-16.pdf` (8 pages; text = notes/paper9/paper9.tex of draft 2, 7cb10b85, with the title
of e61ad1e2; the text differs from the draft-2 PDF only in the title lines). Each number was copied from the record
named, or recomputed from the record's rows where said. Numbers, verdicts and title are not changed here; the list at
the end is for the owner.

## Checked and equal

| section | statement | record | result |
|---|---|---|---|
| abstract, 5.1 | 179 results; r >= 0.293: 160 read, 6 not; r < 0.293: 0 read, 13 not; line gives the verdict in 173 | notes/paper9_yardstick/line_all.txt | equal |
| 5.1 table | XX 75 / 63 / 72; Hubbard 31 / 26 / 28; utility 11 / 9 / 11; 3D 48 / 48 / 48; daily 11 / 11 / 11; dual-unitary 3 / 3 / 3 | line_all.txt | equal |
| 5.1 composition | XX 12 (11-12) + 40 (size) + 20 (repeat) + 3 (twin); Hubbard 12 + 8 + 4 + 4 (continuum) + 3; utility 7 + 4; 3D 48 isingL-fez-2026-11-10 | line_all.json rows | equal |
| 5.1 misses | Hubbard 6 steps r 0.416 / 0.375 / 0.514 ("0.38-0.51"), rest 0.304 / 0.321 / 0.269 ("0.27-0.32"); XX ratio 0.506 / 0.504 / 0.518 ("0.504-0.518") | line_all.txt | equal (see list, item 6) |
| 2, 160/166 | 96% | 160 / 166 = 0.964 | equal |
| 3.1 | 564 / 705 / 690 CZ; weight-10 +0.61 of +1; weight-17 and Fig. 4a -0.09 / -0.07 of -1 ("7 to 9%"); mirror parity 0.504 / 0.122 / -0.004, -0.009 | results/utility-2026-11-10/BUILD.md | equal |
| 3.2 table | all seven rows (CZ, cone, MSE / mean square, AGREES); 137 circuits; 11-10 anchors 0.0207, 0.0226; curves differ by at most 0.11 | results/utility-depth-2026-11-11/README.md | equal |
| 4.1 | dt 0.25, J 1, Neel; 10L - 8 CZ, 12 layers; MPS check 2.5e-8, 7.8e-8, 1024 / 2048 within 8e-10 (5.9-8.0e-10) | notes/hubbard_2026-11-11/pod_result.md | equal |
| 4.2 table | all ten rows (CZ, CZ per qubit, both arms' MSE / mean square, verdicts); CZ per qubit recomputed from CZ / 2L | results/hubbard-2026-11-11, hubbard-big-2026-11-11 READMEs | equal |
| 4.2 | ratio at 2 steps 0.935, 0.900, 0.899, 0.906 ("0.90-0.94"); at 4 / 6 steps 1.30, 3.40, 1.38, 1.77, 1.000, 1.142 ("1.00-3.40") | same | equal |
| 4.3 | 0.0009 (1.7 SE), 0.0172 (SE 0.0010, 17 SE), Trotter error 0.0164 | results/hub-dt-2026-11-12/README.md | equal |
| 5.2 | r_twin - r +0.017 / +0.018 / +0.007, -0.051 / -0.047 / +0.039; bound failed at Hubbard 2 steps; 5 of 6 | results/twin-2026-11-13/README.md | equal |
| 6 | angle 12 of 20, largest 0.074; size 7 of 20, largest 0.181, lower at 81 in 20 of 20 (checked cell by cell); line 20 of 20; readable depth 64 / 64, 64 / 32 | notes/xxsize_2026-11-14/verdicts.txt | equal |
| 6 | lambda pooled 78 / 43; per size 88 / 71 and 57 / 35 | notes/xxsize_2026-11-14/README.md | equal (see item 3) |
| 7.1 | shared qubits 0.617 / 0.558 at 32 layers, 0.411 / 0.343 at 64; others 0.527, 0.347 | notes/xxsize_2026-11-14/split.txt | equal |
| 7.2 | (1) +0.061 at 48 layers, others +0.007 to +0.021; (2) +0.098, +0.168; (3) -0.005 / +0.007 / +0.002, +0.108; 13:04 CET | results/xxcone-2026-11-14/README.md | equal (near - far recomputed: 0.108 - 0.010, 0.189 - 0.021) |
| 7.3 | stim within +-0.004; device up to +0.13 (repeat, pi/2, near block 48 layers +0.134); illustration far +0.024 only at 64, mid above near from 16; readout 0.039 / 0.020 | notes/xxcone_2026-11-14/stim_noise.txt, stim_ext.txt, README.md, cone_result | equal |
| 8 oracle | 160 -> 170; 11 gained (r 0.077-0.327); 1 lost (0.496 -> 0.562); larger for 26; nine still not reading, Hubbard 6 steps rest / r^2 1.02-11.2 | notes/paper9_posthoc/rescale.txt | equal |
| 8 ruler | 30 circuits, 27 -> 28; marrakesh 0.362 -> 0.086; fez 81 0.539 -> 0.723, 0.658 -> 1.429; ruler below pi/4 there (0.236 < 0.292, 0.130 < 0.201) | rescale.txt | equal |
| 8 twin | no verdict changed; 0.282 -> 0.095; 0.184 -> 0.238; 0.506 -> 0.886 | rescale.txt | equal |
| 1, 10, data | paper 7 doi 24046673, paper 8 doi 24136512; psf-os 0.1.1 doi 24211405, concept 24211404; 43 of 43 | notes/paper7/ZENODO.md, notes/paper8/ZENODO.md, handover 11-16 | equal |
| refs | arXiv:2510.26845 and 2510.26300: titles as printed (looked up 2026-11-16) | arXiv listing | equal (author lists not re-checked) |

## For the owner: points to consider (not changed)

1. **Section 9 (Limits), a wrong date**: "twin and the light-cone runs: ibm_marrakesh, both on 14 November". The twin
   test ran on 13 November (results/twin-2026-11-13, declaration pushed 2026-11-13 11:33 CET; section 5.1 itself
   says "the twin test of 11-13"). Suggested: "twin: ibm_marrakesh, 13 November; the light-cone runs: ibm_marrakesh,
   14 November".
2. **References not cited in the text**: Tindall et al., Arute et al., both Alam et al. (Phasecraft) and Gidney (stim)
   are in the list but nowhere in the text (only Kim et al. is cited). Possible places: Tindall in 3.1 (a classical
   simulation of the same experiment), Gidney at "stim" in 7.3, the three Hubbard papers in section 4 or 8 (they use
   the U = 0 circuit to correct or train; here it stays beside, and section 8 is about exactly that question).
3. **Section 6, "equal to the 91-qubit values"**: the 91-qubit value on ibm_marrakesh is 79 (11-13, pi/4, 16-48 layers),
   against 78 pooled; fez 43 = 43. "close to (79 and 43)" would match the record.
4. **Section 5.1, "rest 0.49-0.52 of the ratio" for Hubbard U = 4**: these are group means (notes/paper9/r_thread:
   U = 4 mean 0.52, two step sizes mean 0.49); single results range 0.41-0.65 (line_all.json). "on average" would
   say what the numbers are.
5. **Section 4.2, site charge "0.05-0.10 on average"**: the 90 / 120-qubit job records 0.057-0.106, i.e. up to 0.11.
6. **Section 5.1, XX at the line "rest 0.03-0.06"**: the values are 0.025, 0.053, 0.063 (0.025 written as 0.03). Rounding
   only.
7. **Abstract, "at none at 6"**: only the 40- and 60-qubit sizes were run at 6 steps (section 4.2 says so). A reader
   may take the abstract to mean every size was run at 6. E.g. "...at 4 Trotter steps; the two sizes run at 6 steps
   did not read".
8. Small: 7.3 gives the readout means without their night (11-14); section 6's path is written "results
   xxsize-2026-11-14-marrakesh" where other sections write "results/..."; 3.1's "agreement 2 x 10^-15" comes from paper
   8's text (the 11-10 build records 1.2e-15 between the two answer files; consistent as a bound).
9. Not the paper: notes/xxcone_2026-11-14/README.md says the device gap is "up to +0.12"; the paper's +0.13 matches the
   repeat's own numbers (+0.134).
10. Zenodo form: keyword "light cone" while section 7.3 says the light-cone form is not supported by the desk check;
    the owner may keep it (the section is about it) or write "light-cone test".

## How this was read

The 11-16 handover's notebook bundle (92d62d57..d267f205) could not be fetched here: its base 92d62d57 (home's merge
after the 11-13 takehome) is not in the workplace clone (63b23acb), so git refused the bundle. The objects that could
be unpacked from it gave the files used above (the root trees could not be rebuilt). The handover's `データ/` copies
equal the unpacked files (line_all.txt, rescale.txt, verdicts.txt, the xxcone README); the 11-11 / 11-12 records were
read from the workplace clone.
