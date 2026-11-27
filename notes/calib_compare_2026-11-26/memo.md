# Our records against IBM's calibration: how we compare (fixed before any calibration number is seen)

Workplace VS, 2026-11-26 (author The Architect), on the owner's decision of 2026-11-25 21:59 JST and home's instruction
"職場VSへの指示_IBMの校正との比較_2026-11-26". This memo is committed **before** any calibration snapshot is fetched or
read; home passes this file to `fetch_calib_history.py`, which writes its sha256 into the fetch's index. No calibration
number enters a verdict, a placement or a correction: the snapshots are compared with the records afterwards, and what
the comparison suggests is tried only as a ruler inside the circuit or a declaration rule on a later night.

Counting is done by `tools/calib_compare.py` exactly as written here (`findings` from the records now; `score` once the
snapshots exist). Every number in the result names its source file.

## 1. What we found (from `results/` only; one row per kind)

Each finding is (night, device, job id, job time, kind, qubits) with the record file it comes from, and each comes with
the **set** it was found in (the qubits our circuit could see there): a qubit of the set that is not a finding of that
kind is "normal" for that kind on that job.

| kind | rule (from the record alone) | set | source |
|---|---|---|---|
| `mirror_low` | a qubit whose |0> mirror reads mean <Z> below **0.3** (the tau of the third night), in a mirror whose median <Z> over its qubits is **0.6** or more | the mirror circuit's measured qubits | the job's raw counts; mirror pubs whose cell role is `mirror` and whose run record is `user2d_mirror` (ideal |0> on every qubit); clbits from the sent circuit's measures |
| `r_low` | a window position of a cell whose one-factor word is NOT UNIFORM, with (r_q - r_pool) / SE_q below **-2** | the window positions the test read | `scores.json` / `scores3.json` `uniform` of the Ohm ruler nights; position -> qubit from `build.json` |
| `sentinel_dead` | the qubits of a DEAD run of the ring sentinel | the sentinel's ring | `psf_os.sentinel.verdict` on the job (psf-os 0.3.3), from the record |
| `sentinel_weak` | the qubits of a WEAK run (not in a DEAD run) | the sentinel's ring | as above |
| `scan_listed` | the qubits of a path the self-check scan listed on that job | the scanned ring | `list_after.json` `observations[].dead` of the coverage days |

- **Mirrors too deep to place a fault:** a |0> mirror whose median <Z> is below 0.6 is kept as `mirror_too_deep`
  (its set, no finding): there the whole circuit has shrunk, and no qubit stands out from it. Mirrors that are not
  |0> mirrors (other run kinds, e.g. the third night's string mirrors) are kept as `mirror_other` and not counted.
  (Why 0.6, fixed before any calibration number: with every mirror counted, 14550 qubits read below 0.3 over 1080
  mirrors, most of them in deep circuits where the whole mirror is low; a fault is a qubit low among a mirror that
  otherwise reads.)
- **A ring dead over more than half its length** (DEAD runs covering more than half the sentinel's ring) places no
  fault either: it is kept as `sentinel_dead_wide` (its set, no finding), and that ring's WEAK runs are still read.
  (Fixed before any calibration number: of 109 sentinel cells, many rings read DEAD almost end to end.)
- **Records not read:** jobs of the list whose record has no manifest or no raw counts in the layout
  `independent_recount.load_job` reads (73 of 191, mostly before 2026-11-03) are listed in the findings file with the
  reason, and not counted.
- **Sentinels not read:** a job whose sentinel psf-os's `verdict` cannot read from the record (four jobs of 10-26 to
  10-28, earlier record layouts) is kept as `sentinel_error` with the reason, not counted.
- **The findings file:** `findings.json` beside this memo, written by `tools/calib_compare.py findings` from the
  records before any snapshot is fetched (its counts per kind are in the report of 2026-11-26).
- **Not counted (decide later):** "a place that did not read on a readable-depth night". No record writes per-site
  words that this rule could use without a new choice; it is left out, and named in the report.
- A finding is counted once per (job, kind, qubit). A qubit found on several jobs counts on each job (each job has its
  own snapshot).
- Only the jobs of the targets list are read: `calib_targets_2026-11-26_v2.json` (191 jobs; the first list's 118 and
  73 earlier ones, among them the coverage days that hold the scan's LISTED paths).

## 2. IBM's columns (fixed now)

From the snapshot `BackendProperties.to_dict()` whose time is the job's creation time (home's fetch):
- per qubit: `readout_error` (larger is worse), `T1` and `T2` (smaller is worse);
- per edge: the `cz` gate's `gate_error` (larger is worse). The edges of a set are the device's couplers with both
  ends in the set (the couplers as the job's manifest records them: the device's shape, not a calibration number).
- A missing value (or a qubit / edge absent from the snapshot) is NOT AVAILABLE for that column; it is neither a hit
  nor a miss, and is counted apart.

**IBM marks** a qubit in a set when it is among the worst **k** of the set on a column, k = max(1, round(n / 8)) for n
qubits (or n edges) in the set (window 5 -> 1, cone 16 -> 2, cone 22 -> 3, ring 40 -> 5). A qubit is marked by the
edge column when an edge of the set touching it is among the worst k edges. Ties at the k-th value are all marked.

## 3. What is counted (both ways), per kind and per device, per column and for "any column"

- **IBM hit:** a finding whose qubit IBM marks.
- **IBM miss:** a finding whose qubit IBM does not mark on any column.
- **Our miss:** a qubit IBM marks (any column) that is normal in our record for that kind on that job.
- Beside: the hit rate a random set of the same size would get (k / n per column), so a hit count is read against
  what chance gives.

## 4. Expectation (written now; never a verdict)

- Per-qubit columns will mark our findings rarely; the edge (CZ) column will mark them more often. Ground: on 11-24,
  qubit 104's mirror read normally at t = 3 and failed only at t = 4, when 102 and 101 entered the cone (an edge or
  neighbourhood effect, not one qubit's number).

## 5. IBM's tendencies (how we will look)

- Age of the map: job time minus the snapshot's `last_update_date`, in hours, per job.
- Day to day on one device: the same qubits' columns across the nights we ran there.
- The headline numbers (device medians over all qubits) against the values on our sets: the headline is the "vanity"
  number, our set's value the "essence" number, side by side.

## 6. Our improvements (how we will look)

- Among our misses, is there a kind a ruler inside the circuit could catch? E.g. a readout error with a one-sided
  bias would show in ruler (e) (the readout ruler of the fourth night's draft); a CZ-edge mark next to a qubit we read
  as normal would show in the string mirror per qubit.
- What it suggests is written as a candidate for a later declaration; the owner decides.

## What this memo does not do

- It reads no calibration number, and `tools/calib_compare.py findings` reads none (it opens no `fetch_in/*/dev`
  file and no `calib_history` file). `score` reads the snapshots only after home has fetched them.
- It changes no declaration, no `results/`, no psf-os.

## Addendum A (2026-11-27, workplace VS; written before the sealed bundle is opened)

Home fetched the 191 snapshots on 2026-11-26 evening after this memo (sha256 a11c510b...) was fixed, and sealed them
(`封印_校正の束_2026-11-26.zip`, sha256 d5bccf2e...9827). This addendum is committed before the seal is opened. **The
definitions (sections 1 to 3) and the expectation (section 4) above are unchanged**; only what is read and how it is
read are added.

- **A1. Records in the layout before 2026-11-03.** Of the 191 jobs, 73 were not read on 2026-11-26. Their records keep
  the counts as `raw_counts.json.gz`, the circuits outside the job folder and cells without roles. None of them holds a
  |0> mirror, a sentinel cell or an Ohm ruler cell, so `mirror_low`, `sentinel_*` and `r_low` do not apply to them;
  each is read for the scan (A2) and listed with the reason "old layout: read for the scan only". A job with no
  manifest at all stays unread and listed.
- **A2. The scan, read from every job.** `scan_listed` is read from each job of the list by psf-os's own scan reading
  (`psf_os.scan.observe`, psf-os 0.3.3), the reading that wrote the coverage days' `observations` used on 2026-11-26.
  It gives, per echo-scan ring of the job, the ring and its dead runs; the definition (the qubits of the runs the scan
  lists on that job, the ring as the set) is section 1's. A job's ring read both ways (`list_after.json` and the job
  itself) is counted once, per (job, ring size). A job whose scan cannot be read is kept as `scan_error`.
- **A3. Edges without couplers.** The records before 2026-11-03 hold no coupler list. For a ring (scan, sentinel) the
  set's edges are then the ring's neighbouring pairs, cyclic: a ring is built on couplers, so these are couplers. A set
  that is not a ring and has no coupler list gets no edge column (NOT AVAILABLE, as section 2).
- **A4. The list.** `calib_targets_2026-11-26_v2.json`, all 191 jobs; the snapshot of each job is the one home fetched
  for its job id (the fetch's `index.json`). Nothing else is chosen after the snapshots exist.
- **A5. Still not counted:** "a place that did not read on a readable-depth night" (section 1): no definition was fixed
  before the data, and none is added here.
- **A6. Findings file.** `findings.json` is written again by `tools/calib_compare.py findings` with A1 to A3, before
  the seal is opened; its counts per kind and device are in the report of 2026-11-27.
