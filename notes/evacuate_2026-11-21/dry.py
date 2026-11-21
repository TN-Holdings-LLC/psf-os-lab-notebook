"""Dry runs of the evacuated forms against psf-os 0.3.0's default, under ILLUSTRATIVE noise written by hand (never
fitted; no device). Only the items where an evacuated form differs from the default are run: the RUS chains and
decoy's rd2 (a RUS chain read flipped) with their B1 qubits evacuated (a conditional X before and after each wait). IPE's evacuated form is the
parked circuit itself (K = park), so its difference is zero by construction.

Noises (the two types of the weekend's test C):
  wait  amplitude damping 6 % on every other qubit at each mid-circuit read (gpu's branch_noise)
  cond  dephasing 5 % on every qubit after each conditional (cond_noise)
RUS: g = |P(default) - exact| - |P(evacuated) - exact| (positive: the evacuated form is nearer exact), P read as
declared (P2 and decoy's rd2 read their output flipped). The evacuated form is fenced (fence_waits(conditionals=True))
and the default is not, where it parks nothing (the RUS chains): the fence alone moves gates out of the waits too, so
the fenced circuit is run beside, and g splits into the fence's part (fenced against the default) and B1's part
(evacuated against fenced).
The device record behind any of this is psf-os 0.3.0's park only (two nights, IPE, K = |1>).

  python notes/evacuate_2026-11-21/dry.py OUT.txt [PREFIX]      PREFIX: only the items whose tag starts so (appended)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
for d in ("gpu", "notes/ffapps_2026-11-17", "notes/rus_coherent_2026-11-17", "notes/os2_2026-11-18",
          "notes/early_2026-11-17", "notes/compound_2026-11-17", "notes/timebudget_2026-11-17"):
    sys.path.insert(0, os.path.join(NB, d))
import branch_noise as BN  # noqa: E402
import cond_noise as CN  # noqa: E402
from psf_os import feedforward as FF  # noqa: E402
from psf_os.evacuate import evacuate  # noqa: E402
from psf_os.footprint import fence_waits, park_waits  # noqa: E402

SHOTS = 20000
NOISES = {"wait": dict(gamma=0.06), "cond": dict(dephase_cond=0.05)}


def items():
    import rus2_night as R2
    import rus3_night as R3
    import parallel_night as PN
    out = []
    for L in (1, 2, 3):
        out.append((f"P0 L{L}", *FF.rus_chain(L, 1.1, m=3), True))
        out.append((f"P3 L{L}", *FF.rus_chain(L, 1.1, m=2), True))
        for m in (2, 3):
            out.append((f"P1 L{L} m{m}", *R2.flip_chain(L, 1.1, m=m), True))
            out.append((f"P2 L{L} m{m}", *R3.chain(L, 1.1, m=m), False))
            out.append((f"NF L{L} m{m}", *R2.flip_chain(L, 1.1, m=m, flip=False), True))
    qc, sp = PN.rd2()
    out.append(("decoy rd2", qc, sp, False))                  # a RUS chain read flipped (rd: P2's frame), L 2, m 2
    return out


def run(qc, noise, seed):
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    cc = transpile(qc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=1, seed_transpiler=0)
    nc = CN.dephase_conditionals(BN.noisy_circuit(cc, float(noise.get("gamma", 0.0))),
                                 float(noise.get("dephase_cond", 0.0)))
    sim = AerSimulator(method="density_matrix")
    return sim.run(nc, shots=SHOTS, seed_simulator=seed).result().get_counts()


def share(cnt, test):
    tot = sum(cnt.values())
    return sum(v for k, v in cnt.items() if test(k.replace(" ", ""))) / tot


def main():
    only = sys.argv[2] if len(sys.argv) > 2 else None
    lines = (open(sys.argv[1]).read().rstrip("\n").split("\n") if only and os.path.exists(sys.argv[1]) else
             ["ILLUSTRATIVE noise, never fitted; no device. 20000 shots per circuit; the default = psf-os 0.3.0 (parked)"])
    for tag, qc, spec, one in items():
        if only and not tag.startswith(only):
            continue
        low = FF.lower(qc)
        base = park_waits(low)[0]
        ev, info = evacuate(low, ("L", "K", "B"))
        if not info["changed"]:
            lines.append(f"{tag}: nothing to evacuate")
            continue
        n = low.num_clbits
        fen = fence_waits(low, conditionals=True)
        for nz, noise in NOISES.items():
            cb, ce, cf = run(base, noise, 11), run(ev, noise, 11), run(fen, noise, 11)
            if one is None:
                succ = {int(b): v for b, v in spec["success"].items()}
                t = lambda k: all(int(k[n - 1 - b]) == v for b, v in succ.items())
                pb, pe = share(cb, t), share(ce, t)
                se = math.sqrt(pb * (1 - pb) / SHOTS + pe * (1 - pe) / SHOTS)
                lines.append(f"{tag} {nz}: default {pb:.4f}, evacuated {pe:.4f}, d {pe - pb:+.4f} (2 SE {2 * se:.4f}); "
                             f"B1 {info['B1']}")
            else:
                ob, ex = spec["out_bit"], spec["exact"]
                t = (lambda k: k[n - 1 - ob] == "1") if one else (lambda k: k[n - 1 - ob] == "0")
                pb, pe, pf = share(cb, t), share(ce, t), share(cf, t)
                se = math.sqrt(pb * (1 - pb) / SHOTS + pe * (1 - pe) / SHOTS)
                g = abs(pb - ex) - abs(pe - ex)
                gf = abs(pb - ex) - abs(pf - ex)
                gb = abs(pf - ex) - abs(pe - ex)
                lines.append(f"{tag} {nz}: default {pb:.4f}, fenced {pf:.4f}, evacuated {pe:.4f} (exact {ex:.4f}); "
                             f"g {g:+.4f} = fence {gf:+.4f} + B1 {gb:+.4f} (2 SE of each about {2 * se:.4f}); "
                             f"B1 {info['B1']}")
        print("\n".join(lines[-2:]), flush=True)
        open(sys.argv[1], "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
