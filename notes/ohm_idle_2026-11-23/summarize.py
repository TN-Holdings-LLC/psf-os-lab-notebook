"""Per device, arm and cycle count: (a) idle share of all qubit-time, (b) share of the idle time with P(|1>) above one
half, (c) the idle time weighted by P(|1>) (and its share of all qubit-time), for both schedules; from ohm_idle.py's
output. Lengths in dt and microseconds use the fake backends' values (not the devices' records).

usage: python notes/ohm_idle_2026-11-23/summarize.py IDLE.json OUT.json [IDLE_CHECK.json]
"""
import json
import sys
from collections import defaultdict

DT = 4e-9   # both fake backends (FakeFez, FakeKingston): dt 4 ns


def cells(doc):
    g = defaultdict(list)
    for r in doc["circuits"]:
        arm, t, _ = r["tag"].split("_")
        g[(r["device"], arm, t[1:])].append(r)
    return g


def main(src, out, check=None):
    doc = json.load(open(src))
    res = dict(note=doc["note"], chi=doc["chi"], cutoff=doc["cutoff"], cells={})
    worst = max(r["mps"]["final_z_vs_exact_max"] for r in doc["circuits"])
    res["final_z_vs_exact_worst"] = worst
    for (dev, arm, t), rs in sorted(cells(doc).items()):
        row = dict(circuits=len(rs), cz=sorted({r["cz"] for r in rs}), one_qubit_gates_mean=sum(r["one_qubit"] for r in rs) / len(rs))
        for h in ("asap", "alap"):
            s = {k: sum(r[h][k] for r in rs) for k in ("qubit_time_dt", "idle_dt", "idle_p1_over_half_dt",
                                                      "idle_p1_weighted_dt", "park_gain_dt", "spans",
                                                      "spans_p1_over_half", "parkable", "parkable_dt")}
            n = len(rs)
            row[h] = dict(length_us_mean=round(sum(r[h]["length_dt"] for r in rs) / n * DT * 1e6, 3),
                          a_idle_share=s["idle_dt"] / s["qubit_time_dt"],
                          b_p1_over_half_share_of_idle=s["idle_p1_over_half_dt"] / s["idle_dt"],
                          c_weighted_us_per_circuit=s["idle_p1_weighted_dt"] / n * DT * 1e6,
                          c_share_of_qubit_time=s["idle_p1_weighted_dt"] / s["qubit_time_dt"],
                          park_gain_share_of_qubit_time=s["park_gain_dt"] / s["qubit_time_dt"],
                          qubit_time_us_per_circuit=s["qubit_time_dt"] / n * DT * 1e6,
                          spans_per_circuit=s["spans"] / n, spans_p1_over_half_per_circuit=s["spans_p1_over_half"] / n,
                          parkable_per_circuit=s["parkable"] / n, parkable_dt_per_circuit=s["parkable_dt"] / n)
        res["cells"][f"{dev}_{arm}_t{t}"] = row
    if check:
        c = json.load(open(check))
        by = {(r["device"], r["tag"]): r for r in c["circuits"]}
        d = 0.0
        for r in doc["circuits"]:
            o = by.get((r["device"], r["tag"]))
            if o:
                for h in ("asap", "alap"):
                    d = max(d, abs(o[h]["idle_p1_weighted_dt"] - r[h]["idle_p1_weighted_dt"]) / max(1, r[h]["idle_dt"]),
                            abs(o[h]["idle_p1_over_half_dt"] - r[h]["idle_p1_over_half_dt"]) / max(1, r[h]["idle_dt"]))
        res["check"] = dict(against=check, chi=c["chi"], cutoff=c["cutoff"], circuits=len(by),
                            largest_change_as_share_of_idle=d)
    json.dump(res, open(out, "w"), indent=1)
    print(f"final Z against the exact answers, worst {worst:.1e}")
    print("cell                 sched  (a) idle  (b) P1>1/2  (c) us/circ  (c)/qubit-time  gain/qt  parkable/circ  length us")
    for k, row in res["cells"].items():
        for h in ("asap", "alap"):
            x = row[h]
            print(f"{k:20} {h:5}  {x['a_idle_share']:8.3f}  {x['b_p1_over_half_share_of_idle']:10.3f}  "
                  f"{x['c_weighted_us_per_circuit']:10.2f}  {x['c_share_of_qubit_time']:14.4f}  "
                  f"{x['park_gain_share_of_qubit_time']:7.4f}  {x['parkable_per_circuit']:13.2f}  {x['length_us_mean']:8.2f}")
    if check:
        print("check:", res["check"])


if __name__ == "__main__":
    main(*sys.argv[1:])
