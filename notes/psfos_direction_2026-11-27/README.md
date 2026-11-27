# psf-os after 0.3.3: where to fix, which way to go (a proposal; workplace Claude, 2026-11-27)

A proposal for the owner, written after the four Ohm ruler nights (11-23 to 11-26) and the workplace VS's checks. It
changes nothing: psf-os, the declarations and `results/` are untouched. Every item below is to be decided by the owner
and, where it touches a judged word, declared before a night.

## Two layers, kept apart

- **psf-os 0.3.3** (the package): placement without the calibration map (chains, rings, 2D patterns of a lattice,
  4 x M x N cubic lattices, and the dynamic circuits of Papers 10 and 11); the checks in the same job (floor, mirror,
  ring sentinel, Clifford twin); waiting qubits parked in |0>; decisions made inside one job; refusal with a reason.
- **The lab notebook** (this repository): the Ohm rulers ((d), (e), (de), (a')), the declarations and their checker,
  the independent re-count, the qubit-by-qubit record, the predictions (OR4-2).
Most of what the four nights showed lives in the notebook, not in psf-os. The direction below is mostly about moving
what has been shown from the second layer into the first.

## What to fix, in order

1. **Nothing passes on zero items.** Every checker that finds 0 items, or 0 overlap, stops or says so in words: the
   notebook's tools (`declaration_check.py beside` read 0 items on a heading without a colon; the workplace VS fixes it
   in tools6, 2026-11-27), and psf-os's answer card, which should write "NOT ON USER QUBITS" itself when the sentinel
   shares no qubit with the user's circuit (the notebook's score3 writes it; on 11-24, 11-25 and 11-26 the overlap was
   0). psf-os already has `sentinel_fallback="same_qubits"` (off by default); whether to turn it on is a separate choice.
2. **The mirrors' blind spot.** At t = 3 every ruler's d stayed positive on 11-26 (+0.02 to +0.11). Guess (not
   measured): an error fixed in direction (a coherent over- or under-rotation) cancels in U U^dagger, so no mirror
   carries it. The workplace VS's twirl dry runs (2026-11-27) test this. If twirled mirrors carry it, a twirled mirror
   is a candidate for a declared night ([OWNER]); if not, the blind spot is written as a limit of every mirror ruler,
   and of any claim to audit with them.
3. **Leave qubits out by the test, not by the mirror.** On 11-26 (A0, t = 4) physical 104 had |0> mirror 0.05 while
   its own r on the test was 0.846 and its readout e 0.989: the mirror passes the gates twice and waits otherwise, so it
   overstates a qubit's fault, and (a') left 104 out of its mean (not out of the circuit or the placement). The fifth
   night's qubits.csv adds r / e (beside). A rule that leaves a qubit out by r or r / e is declared for a later night,
   from dry runs, never from these records.
4. **Move the shown rulers into psf-os** (a 0.4 candidate): the string mirror, the readout pair at the job's head and
   tail, (de) = sqrt(m_q e_q), and a fixed answer-card schema (the word, the ruler, its expected class, the qubit
   record). A string mirror needs only the compiled circuit and its inverse, and the readout circuits need no circuit
   at all, so "bring your circuit; psf-os adds the rulers to the same job" widens without new placement families.
   This, rather than a general OS, is the proposed direction: the value is a result returned with how far it can be
   trusted, measured in the same job.
5. **The time model.** psf-os's model gave 55.9 s for the 11-26 job, the usual formula 49.1 s, IBM charged 48 s. The
   model's per-shot term can be refitted on the charged jobs already recorded (a small, separate change).

## What not to do

- Not to widen the shapes psf-os places just to look general; a shape it does not recognise is refused with the reason.
- Not to read calibration error numbers into placement, rulers or corrections (the calibration comparison stays a
  comparison, after the memo).
- Not to change a ruler or a rule after its night's data; every change above goes through a declaration.
