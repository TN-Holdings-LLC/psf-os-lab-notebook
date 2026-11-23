"""Rebuild the recorded nights of 2026-11-21 and 2026-11-22 with psf-os 0.3.3rc1 (candidate) and read its new checks.

For each night the night's own tool builds its jobs again from the night's device record, as its README's procedure
says, with the psf-os on PYTHONPATH (0.3.3rc1). Two things are made to match the night, and nothing else:
  * psf_os.__version__ reads as the version the night was built with, only so that the tools' version gates pass
    (qpe_long_parked_night and ipe_branch_cost_night require "0.3.1");
  * build()'s park defaults are the night's (psf-os a164fc5 parked nothing; 0.3.0 parked the always-|1> qubits and not
    the likely value; 0.3.1 both), as psf_os.loop.verify sets them for a recorded night.
Every build passes 0.3.3rc1's compiled parking check or is refused (the night is then marked REFUSED). The rebuilt
test circuits are compared with the recorded ones by their gates (psf_os.loop._split_digests, as verify does), and the
new manifest's "compiled" record is read: the parked waits checked, the records whose waits could not be counted.
Nothing under results/ is written.

usage (from the notebook root):  PYTHONPATH=<psf-os 0.3.3rc1> python notes/checks_2026-11-23/recheck_nights.py OUT
"""
import contextlib
import io
import json
import os
import runpy
import sys

NB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# night: (psf-os it was built with, park, park_likely, [(tool, argv with {D} the device record and {O} the out)],
#         [(recorded job folder, rebuilt job folder)])
NIGHTS = {
    "weekend-shared-night-2026-11-21": (
        "a164fc5", False, False,
        [("gpu/weekend_shared_night.py", ["build", "{D}", "{O}/A", "--cands", "A", "--shots", "4000", "--ff-only",
                                          "--layout", "own"]),
         ("gpu/weekend_shared_night.py", ["build", "{D}", "{O}/BC", "--cands", "BC", "--b-n4-from-c", "--ff-only",
                                          "--layout", "own"])],
        [("A/job0/job", "A/job0/job"), ("BC/job0/job", "BC/job0/job"), ("BC/job1/job", "BC/job1/job")]),
    "qpe-parked-night-2026-11-21": (
        "0.3.0", True, False, [("gpu/qpe_parked_night.py", ["build", "{D}", "{O}/qp", "--plan", "subset"])],
        [("qp/job0/job", "qp/job0/job"), ("qp/job1/job", "qp/job1/job")]),
    "rus-fence-night-2026-11-21": (
        "0.3.0", True, False, [("gpu/rus_fence_night.py", ["build", "{D}", "{O}/rf", "--plan", "gamma-one-job"])],
        [("rf/job0/job", "rf/job0/job")]),
    "likely-park-night-2026-11-22": (
        "0.3.1", True, False, [("gpu/likely_park_night.py", ["build", "{D}", "{O}/lp", "--plan", "B"])],
        [("lp/job0/job", "lp/job0/job")]),
    "qpe-n78-night-2026-11-22": (
        "0.3.1", True, True, [("gpu/qpe_long_parked_night.py", ["build", "{D}", "{O}/qn", "--plan", "b"])],
        [("qn/job0/job", "qn/job0/job")]),
    "ipe-branch-cost-night-2026-11-22": (
        "0.3.1", True, True, [("gpu/ipe_branch_cost_night.py", ["build", "{D}", "{O}/bc", "--plan", "d", "--L-dt",
                                                                "4500"])],
        [("bc/job0/job", "bc/job0/job")]),
}


DEVICE = {"weekend-shared-night-2026-11-21": "ibm_marrakesh", "qpe-parked-night-2026-11-21": "ibm_marrakesh",
          "rus-fence-night-2026-11-21": "ibm_fez", "likely-park-night-2026-11-22": "ibm_kingston",
          "qpe-n78-night-2026-11-22": "ibm_fez", "ipe-branch-cost-night-2026-11-22": "ibm_fez"}


def device_dir(night):
    """The night's device record (fetch_in/<the device the night ran on>/dev), checked against the recorded manifest."""
    d = os.path.join(NB, "results", night, "fetch_in", DEVICE[night], "dev")
    if not os.path.isdir(d):
        raise SystemExit(f"{night}: no device record at {d}")
    return d


def read_compiled(job):
    m = json.load(open(os.path.join(job, "manifest.json")))
    if "compiled" not in m:
        return dict(compiled="none (a psf-os before 0.3.3rc1)", psf_os_build=m.get("psf_os_build"))
    recs = (m.get("compiled") or {}).get("records") or {}
    waits = qubits = records = uncounted = 0

    def one(r):
        nonlocal waits, qubits, records, uncounted
        pc = r.get("park_checked") or {}
        if pc.get("waits"):
            records += 1
            waits += pc["waits"]
            qubits += pc["qubits"]
        if (r.get("waits") or {}).get("counted") is False:
            uncounted += 1
    for name, r in recs.items():
        if "park_checked" in r:
            one(r)
        else:                                       # a bundle's or a packed arm's records per sub-item
            for t, x in r.items():
                if not t.startswith("_"):
                    one(x)
    return dict(records_with_parking=records, parked_waits_checked=waits, parked_qubit_waits_checked=qubits,
                records_not_counted=uncounted, circuits=len(m["compiled"]["summary"]),
                psf_os_build=m.get("psf_os_build"))


def main(out):
    import psf_os
    from psf_os import feedforward as FF
    from psf_os import loop as LP
    real = psf_os.__version__
    os.makedirs(out)
    sys.path[:0] = [NB, os.path.join(NB, "gpu")]
    report = {}
    for night, (ver, park, likely, cmds, jobs) in NIGHTS.items():
        D, O = device_dir(night), os.path.join(out, night)
        os.makedirs(O)
        row = dict(built_with=ver, park=park, park_likely=likely, psf_os_here=real)
        log = io.StringIO()
        try:
            psf_os.__version__ = ver
            with FF.park_default(park, likely=likely), contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                for tool, argv in cmds:
                    sys.argv = [tool] + [a.replace("{D}", D).replace("{O}", O) for a in argv]
                    try:
                        runpy.run_path(os.path.join(NB, tool), run_name="__main__")
                    except SystemExit as e:
                        if e.code not in (0, None):
                            raise RuntimeError(f"{tool} exited with {e.code}") from None
        except Exception as e:  # noqa: BLE001
            row.update(result="REFUSED" if isinstance(e, FF.Refused) else "FAILED", why=f"{type(e).__name__}: {e}",
                       log=log.getvalue()[-800:])
        finally:
            psf_os.__version__ = real
        if "result" not in row:
            per = []
            for rec, new in jobs:
                rj, nj = os.path.join(NB, "results", night, rec), os.path.join(O, new)
                ta, sa = LP._split_digests(rj)
                tb, sb = LP._split_digests(nj)
                same_bytes = open(os.path.join(rj, "circuits.qpy"), "rb").read() == \
                    open(os.path.join(nj, "circuits.qpy"), "rb").read()
                per.append(dict(job=rec, test_gates_same=ta == tb, sentinel_gates_same=sa == sb,
                                bytes_same=same_bytes, summary=LP.summary_line(rj, nj) if hasattr(LP, "summary_line") else None, **read_compiled(nj)))
            row.update(result="BUILT", jobs=per)
        report[night] = row
        print(f"{night:36} {row['result']}" + ("" if row["result"] != "BUILT" else "  " + "; ".join(
            f"{j['job']}: gates {'SAME' if j['test_gates_same'] else 'DIFFERENT'}, parked waits checked "
            f"{j.get('parked_waits_checked', '-')} in {j.get('records_with_parking', '-')} records"
            for j in row["jobs"])))
        if row["result"] != "BUILT":
            print("   ", row["why"])
    json.dump(report, open(os.path.join(out, "recheck.json"), "w"), indent=1, default=str)
    return report


if __name__ == "__main__":
    main(sys.argv[1])
