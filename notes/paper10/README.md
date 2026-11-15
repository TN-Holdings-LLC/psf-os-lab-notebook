# Paper 10, first test: cut the 81-qubit chain between its 33rd and 34th qubits (design draft, workplace, 2026-11-16)

Draft for the owner and home. Not declared (a declaration is a pushed commit, made at home), no device, no POD. Desk
part: `cut_desk.py` (output `cut_desk.json`). Times CET.

## The question

On 11-14 (ibm_marrakesh, two jobs 34 minutes apart) the first 33 qubits of the 81-qubit XX chain kept less signal
inside the 81-qubit circuit than inside the 33-qubit circuit on the same qubits, and the loss opened next to where the
long chain continues (near block first, then mid, far last). A stim check with uniform local noise gives no gap; worse
elements on the extension make one (`notes/xxcone_2026-11-14/`). Two readings remain:

- **along the chain**: errors made on the extension reach the first 33 qubits through the dynamics, across the bond
  between sites 32 and 33;
- **beside the chain**: the extension's activity harms its neighbours without passing through that bond (crosstalk,
  spectator effects, a shared control line, ...).

Cutting only that bond separates them. The extension keeps running the same gates, so whatever it does beside the
chain is still there; nothing can travel across the bond.

## Circuits (gpu/ffxx91.py's job, theta pi/4 and pi/2, steps 2 / 4 / 8 / 12 / 16 = 8 to 64 CZ layers)

| arm | what | CZ at 8 / 64 layers | placement |
|---|---|---|---|
| N33 | the 33-qubit chain, as 11-14 | 128 / 1024 | first 33 qubits of N81 (checked, as cone.py) |
| N81 | the 81-qubit chain, as 11-14 (equal to the recorded repeat's circuits, 30 of 30 records by gate hash) | 320 / 2560 | rule C |
| N81cut | N81 with the gate on bond (32, 33) replaced by CZ, barrier, CZ: an identity with the same two CZ on the same coupler (the barrier stops the compiler cancelling them, as the Hubbard U = 0 ruler) | 320 / 2560 | equal to N81's |
| N81idle (optional) | N81 with that gate left out; the coupler idles | 316 / 2528 | equal to N81's |

Every other gate is the same as in N81. Exact answers: free fermions; the cut makes the single-particle matrix
block-diagonal, so the first 33 sites of N81cut have exactly the N33 values (checked: difference 0, no amplitude
crosses the cut, every step and angle). The cut and idle arms pass user2d's acceptance (floor and compiled mirror).
N81cut and N81idle differ in the cut qubits' single-qubit pulses (the cut arm has no single-qubit gates of the
XX+YY decomposition on qubits 32 and 33); N81cut keeps that coupler's CZ, N81idle does not.

## What is compared

On the 33 shared qubits, by block (far 0-10, mid 11-21, near 22-32 of the 33-qubit chain), as cone.py:
g81 = r(N33) - r(N81) and gcut = r(N33) - r(N81cut), all arms in the same session, so that the day's device is the
same for both gaps. Beside: the 11-14 values of g81 (two runs), and gidle if run.

## Form of the predictions (to fix in the declaration; the numbers below are proposals)

- **P0 (the effect is still there today)**: theta pi/4, near block, g81 >= 0.05 at 32 layers. If P0 fails, the test
  says nothing about the two readings, and it is recorded as such.
- **P1 (along the chain)**: theta pi/4, gcut near block <= 0.03 at 16, 32 and 48 layers, and gcut(near) <= g81(near) -
  0.05 at 32 and 48 layers.
- **P2 (beside the chain)**: theta pi/4, gcut near block >= 0.05 at two or more of 32, 48, 64 layers.
- Between P1 and P2 (gcut near 0.03-0.05, or P1 at some depths only): "partly", reported as numbers.
- theta pi/2 is reported beside with the same blocks (the stim check below is for that angle).

Scale for the bands: on 11-14 the far block's |g| at pi/4 stayed within 0.021 in four of five depths of each run and
reached 0.061 once (the repeat); the near block reached +0.19 to +0.22. So 0.03 / 0.05 sit above the far block's
usual spread and well below the near block's effect. The declaration should state whether one far-block cell above
0.03 voids a verdict (11-14 had one).

## Desk check (stim, theta pi/2, nothing taken from the device)

Uniform local noise (CZ depolarising 0.003, single-qubit 0.0003, readout 0.015, as stim_noise.py), 20000 shots,
gap g = r(N33) - r(arm) on the shared qubits, blocks far / mid / near:

| layers | N81 | N81cut | N81idle |
|---|---|---|---|
| 8 | +0.000 +0.000 +0.000 | +0.000 -0.000 +0.000 | +0.001 -0.001 -0.000 |
| 16 | +0.001 +0.003 +0.000 | +0.001 +0.001 -0.001 | +0.001 +0.001 -0.001 |
| 32 | +0.001 +0.001 +0.003 | +0.001 +0.002 +0.004 | +0.001 -0.000 -0.001 |
| 48 | +0.000 +0.004 +0.002 | -0.000 +0.003 +0.001 | -0.001 -0.000 +0.000 |
| 64 | +0.003 +0.001 +0.003 | +0.001 +0.003 +0.005 | -0.000 -0.000 +0.000 |

Under uniform noise the gap is zero with and without the cut (within +-0.005), as asked.

Illustration only, not a fit (the factor 3 is stim_ext.py's, not tuned): CZ error tripled on couplers touching the
extension, the cut coupler counted as touching it:

| layers | N81 | N81cut | N81idle |
|---|---|---|---|
| 16 | +0.001 +0.018 +0.001 | +0.001 +0.005 +0.001 | -0.000 -0.000 -0.000 |
| 32 | +0.001 +0.037 +0.027 | -0.000 +0.004 +0.008 | +0.001 -0.000 -0.001 |
| 48 | -0.000 +0.068 +0.061 | +0.001 +0.007 +0.006 | +0.001 -0.001 +0.000 |
| 64 | +0.024 +0.098 +0.084 | +0.005 +0.005 +0.007 | -0.000 +0.000 +0.000 |

In this model the loss travels only along the chain (Pauli errors moved by the circuit), so the cut removes it
(what is left, up to +0.008, comes from the cut coupler's own CZ errors on qubit 32; the idle arm has none). A model
with errors that act beside the chain would keep a gap in N81cut; such a model is not built here (it would need the
device's crosstalk, which the policy does not read).

## Device time (the project's time model)

34 circuits, 40.9 s per job (each arm: 10 circuits x user, floor, mirror + the ring sentinel). Options:

| plan | jobs | seconds by the model | note |
|---|---|---|---|
| minimal | N81cut | 41 | compared with the 11-14 records only: another day, so g81 is not today's |
| proposed | N33, N81, N81cut | 123 | all gaps from the same session |
| full | + N81idle | 164 | separates the cut coupler's own CZ from the rest |
| pi/4 only | N33, N81, N81cut | 73 | 19 circuits per job; loses the pi/2 rows |

ibm_marrakesh only (on 11-14 it was the device where the 33-qubit chain is the first 33 of the 81-qubit chain); not
run if the night's record does not give that (cone.py's check), or if any arm does not build. The handover's "about
one minute" is the minimal plan; the proposed plan is about two minutes.

## Not claimed, and limits

One device, one session. A null in N81cut would show the loss needs the bond; it would not say which elements of the
extension are worse. A gap in N81cut would show something beside the chain; it would not say which mechanism. The
stim models are ours, chosen before any device data of this test and not fitted to the device.

## Reproduce the desk part

`PYTHONPATH=<psf-os>:<notebook>:<notebook>/gpu python notes/paper10/cut_desk.py
results/xxcone-2026-11-14/fetch_in/ibm_marrakesh/dev WORK results/xxcone-2026-11-14/ibm_marrakesh_n81/runs`
(stim 1.16.0, psf-os at the workplace head e1ba249; about 3 minutes on one core).
