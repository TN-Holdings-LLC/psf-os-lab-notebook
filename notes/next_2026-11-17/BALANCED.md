# A frame-balanced neuron chain against decay bias (home, 2026-11-17 night; desk only, not declared)

Why: decay moves |1> to |0> only. The third design (rd: logical 1 waits and is read as |0>) turns it into a lift toward
success; on the device it overshot its own noiseless value (N2 at L = 1 and 7; the OS loop at L = 1). The guard set
before the data took those L out, but a design should not lean on the guard.

Design (`gpu/balanced_night.py`): every L in two complementary frames in one job, rd{L} (logical 1 held and read as
|0>) and nf{L} (the same barriers and waits, no flips, logical 1 held and read as |1>); the verdict on the pooled value
(P_rd + P_nf) / 2. In the pool every logical value spends the same time as |1>, so one-sided decay acts like a
symmetric flip that pulls toward 1/2: for values above 1/2 it cannot lift the pool above its noiseless value.

Desk check with the workplace VS's illustrative decay model (`notes/feedforward_2026-11-16/rus_decay_desk.py`:
uniform gate noise CZ 0.3 %, readout 0.015, decay gamma per mid-circuit wait; NOT fitted to any device), m = 2:

| gamma per wait | readout of \|1> | L | D3 (rd) - noiseless | D1 (no flips) - noiseless | pooled - noiseless |
|---|---|---|---|---|---|
| 0.00 | symmetric 0.015 | 1 | -0.023 | -0.023 | -0.023 |
| 0.00 | symmetric 0.015 | 2 | -0.032 | -0.031 | -0.031 |
| 0.00 | symmetric 0.015 | 3 | -0.036 | -0.035 | -0.035 |
| 0.00 | symmetric 0.015 | 4 | -0.037 | -0.036 | -0.036 |
| 0.00 | symmetric 0.015 | 5 | -0.035 | -0.034 | -0.035 |
| 0.05 | symmetric 0.015 | 1 | -0.017 | -0.096 | -0.057 |
| 0.05 | symmetric 0.015 | 2 | -0.010 | -0.161 | -0.086 |
| 0.05 | symmetric 0.015 | 3 | +0.007 | -0.201 | -0.097 |
| 0.05 | symmetric 0.015 | 4 | +0.030 | -0.221 | -0.095 |
| 0.05 | symmetric 0.015 | 5 | +0.058 | -0.227 | -0.085 |
| 0.10 | symmetric 0.015 | 1 | -0.011 | -0.166 | -0.089 |
| 0.10 | symmetric 0.015 | 2 | +0.009 | -0.274 | -0.132 |
| 0.10 | symmetric 0.015 | 3 | +0.043 | -0.329 | -0.143 |
| 0.10 | symmetric 0.015 | 4 | +0.084 | -0.350 | -0.133 |
| 0.10 | symmetric 0.015 | 5 | +0.128 | -0.349 | -0.110 |
| 0.14 | symmetric 0.015 | 1 | -0.007 | -0.220 | -0.113 |
| 0.14 | symmetric 0.015 | 2 | +0.024 | -0.351 | -0.164 |
| 0.14 | symmetric 0.015 | 3 | +0.069 | -0.409 | -0.170 |
| 0.14 | symmetric 0.015 | 4 | +0.120 | -0.424 | -0.152 |
| 0.14 | symmetric 0.015 | 5 | +0.173 | -0.413 | -0.120 |
| 0.05 | 0.17 lost | 1 | +0.001 | -0.221 | -0.110 |
| 0.05 | 0.17 lost | 2 | +0.022 | -0.260 | -0.119 |
| 0.05 | 0.17 lost | 3 | +0.050 | -0.279 | -0.114 |
| 0.05 | 0.17 lost | 4 | +0.082 | -0.284 | -0.101 |
| 0.05 | 0.17 lost | 5 | +0.116 | -0.278 | -0.081 |

- The pool stays at or below its noiseless value everywhere (rd alone overshoots from L = 3 at gamma 0.05, from L = 2
  at 0.1, and at L = 1 with a lossy |1> readout).
- The cost: the pool loses more than rd (the nf frame holds the likely 1 as |1>). Against the ceiling c(L) the pooled
  margin g = c - |pool - exact| stays positive in this model at gamma 0.05 (L = 1: +0.040; L = 3: +0.108) and nearly
  vanishes at L = 1 for gamma 0.1 (+0.008). The balanced pool is the honest, conservative number; rd alone is beside.
- Circuit-level and fixed (two declared circuits, a fixed pooling); no random twirling and no correction. It is close
  in spirit to readout twirling, so whether it fits the standing rule "twirling off" (a runtime option) is the owner's
  call.

Tool: 34 circuits, 40.9 s by the model (L = 1 .. 5). Try-build on the 2026-11-17 marrakesh record: check PASS; noiseless
run end to end: pooled within 0.008 of noiseless at every L, BEYOND at every L, slope COMPOUNDS. Draft declaration:
`prereg/drafts-2026-11-17/balanced_DRAFT.md`.
