# Repetition code: independent check by the workplace VS Claude (2026-11-19, workplace instruction "その2", item 2)

Tool `gpu/repcode_night.py` at 65c7d3fa, psf-os v0.2-proto-2026-11-18 at 11f07b0, both unchanged. Desk only.
Environment: qiskit 2.5.2, qiskit-aer 0.18.0, Windows. Build on the marrakesh record of 2026-11-17: 40 circuits,
47.6 s by the model; the tool's check PASS. `vs_repcode.py` imports qiskit and qiskit_aer only; it runs the tool's
`check` as a subprocess on damaged copies. Result: `vs_repcode.json`, 8 checks, 0 FAIL.

| item | result |
|---|---|
| look-up right in every case (compiled) | every ff arm of lut3, lut1, lut5 for e = none, d0, d1, d2 reads c = 000 in every shot (Aer, the compiled circuits cut to their qubits); every floor all zero; every off arm's c[0] at the value derived here (1, 1/2, 1, 1) |
| the table | read from the compiled lut3: s == 1 -> X d0, s == 3 -> X d1, s == 2 -> X d2, the same in all four lut3 items; it equals the table derived from the parities a0 = d0 + d1, a1 = d1 + d2. lut1 holds the one test of the injected error (s == 1 for none) |
| register condition | every compiled register test reads register s, bits [0, 1] in that order |
| ceiling 0.875 | another method: each off arm written with deferred measurement, its exact distribution from the statevector, every fixed rule on (s, c[1], c[2]) flipping c[0] tried (all 2^16). Per item (the tool's definition) 1, 0.5, 1, 1 -> 0.875; one rule for all four items also 0.875 (s tells the rule where the error was) |
| broadcast record | 144 conditionals, 216 condition bits, 48 broadcasts, 72 broadcast bits: equal to the hand count |
| damage | the s == 1 test compared with 2 instead: check FAIL (ff_lut3_0, ff_lut3_2). The X blocks of s == 1 and s == 3 exchanged: check FAIL (ff_lut3_0, ff_lut3_1) |

## lut1 against lut3, and lut5 against lut3 (the draft's two comparisons)

- **lut1 is told where the error is.** Its one test is chosen by the injected error e. Under noise it never acts on a
  wrong syndrome, and it never corrects an error elsewhere. So lut3 - lut1 compares a decoder against one that knows
  e, besides the number of tests. This is what the instruction says; worded this way, it may be clearer in the draft.
- **lut5's two added tests fire in one item of four.** They test s == 0. Noiselessly s == 0 in every shot of e = none,
  and never for e = d0, d1, d2. So lut5 - lut3, pooled, mixes:
  - for e = none, two more tests that fire (a Z on an ancilla);
  - for e = d0, d1, d2, two more tests that never fire.

  On 2026-11-16 the wait diagnostic found that unfired conditionals cost nothing measurable (D_cond +0.006,
  2 SE 0.022). So on the device the pooled d may come mostly from e = none.
- **The dry runs cannot show this.** The dry noise `dephase_cond` dephases after every conditional, whether or not it
  fires: a cost per test.
- **No broadcast is added.** The added tests read register s, which has not changed, so by IBM's counting lut5 adds no
  broadcast. If the loss of 2026-11-17/18 went with broadcasts, lut5 would not see it; the broadcast record agrees
  (48 broadcasts for the whole job: one of 2 bits per ff and floor arm, two of 1 bit per off arm).
- **What could close these holes** (for the workplace Claude and the owner; nothing changed here):
  - beside the pooled d, score lut5 - lut3 per error group: e = none (the added tests fire) and e = d0, d1, d2 (they
    do not fire);
  - or pad so that every item carries the same number of extra fired tests. For example, one test of s == 0 and a
    duplicate of each table test, each with a Z on an ancilla as its block: noiselessly exactly one extra test fires
    in every shot, whatever the error;
  - and, if the broadcast is the suspect, pad with a test on a second register measured again, which costs one more
    broadcast.
