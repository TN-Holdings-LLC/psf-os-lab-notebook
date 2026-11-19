"""The compounding loop of the RUS chain on psf-os v0.2's loop (psf_os/loop.py; workplace Claude, 2026-11-19, home
handover 2026-11-19 section 4.1). This file is the experiment psf_os.loop.Night runs: the diagnostics Dw and Dc
(gpu/wait_night.py, gpu/ctrl_night.py), round 1 by gpu/os_night.py's rule (as gpu/os2_night.py round1), the rounds
built, checked and scored by gpu/os3_night.py (stacks with +M and +F), R2's offset choice, the compound rows and the
predictions. Every one of those files is imported read only and unchanged; gpu/os2_run.py (declared 2026-11-18) is
not changed either.

  python gpu/os_loop.py preflight [--dry] [--out OUT] [--zip ZIP]
  python gpu/os_loop.py go OUT --zip ZIP --expect-psf-os SHA --declaration PREREG.md [--ledger LEDGER.json]
                                                                                    the night on the device
  python gpu/os_loop.py go OUT --dry DEVDIR [--noise N.json] [--k-max K] [--budget S] [--ledger LEDGER.json]
  python gpu/os_loop.py resume OUT [--zip ZIP]
  python gpu/os_loop.py verify OUT [--resim]
  python gpu/os_loop.py ledger-seed NIGHT LEDGER.json        a ledger line from a recorded night (e.g. 2026-11-18's)

Rungs: +M then +F (psf_os.loop.RUNGS, the home handover). The ledger is used only on the same device with the same
calibration time (the record's time stamp), per L only where tonight's diagnostics agree with the ledger's family of
base (P1 and P2 one family, "hold flipped"). Placement: every item on its given rule-C chain, as os2 (the offsets of +Q
and the probe's positions need the chain); the fixed arms are therefore not packed (pack_fixed places items itself);
no conditional item shares a circuit with another; the build environment is recorded in every manifest (psf-os v0.2).
"""
import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
for d in ("notes/rus_coherent_2026-11-17", "notes/compound_2026-11-17", "notes/os2_2026-11-18"):
    sys.path.insert(0, os.path.join(NB, d))

ORDER = ["ibm_marrakesh", "ibm_fez", "ibm_kingston"]
FAMILY = {"P0": "P0", "P1": "flip", "P2": "flip", "P3": "P3"}
PSF_OS_BRANCH = "v0.2"


def _ns(**k):
    return types.SimpleNamespace(**k)


def _quiet(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn(*a)


class RusLoop:
    name = "rus-chain loop (os3 rungs +M, +F; ledger)"
    order = ORDER

    def __init__(self):
        import os2_night as O2
        self.k_max, self.budget_s = O2.K_MAX, O2.BUDGET_S

    # -------------------------------------------------------------------------------------- device records
    def fetch(self, base):
        r = subprocess.run([sys.executable, os.path.join(HERE, "daily_fetch.py"), base], capture_output=True, text=True)
        print(f"fetch -> {r.stdout.strip()} {r.stderr.strip()}")
        return r.returncode == 0

    @staticmethod
    def calibration_time(devdir):
        d = json.load(open(os.path.join(devdir, "device.json")))
        return (d.get("source") or {}).get("calibration_time")

    # -------------------------------------------------------------------------------------- diagnostics, round 1
    def diagnostics(self):
        import ctrl_night as CN
        import wait_night as WN

        def builder(mod):
            def build(devdir, folder, dry):
                from psf_os import feedforward as FF
                from psf_os.device import Device
                FF.build(Device.load(devdir), mod.items(), folder, shots=4000,
                         sentinel_spec=dict(kind="echo_clifford", D=24) if dry else None)
            return build
        return [("dw", builder(WN), lambda f: WN.check(_ns(out=f)), lambda f: WN.score(_ns(out=f)), "wait_scores.json"),
                ("dc", builder(CN), lambda f: CN.check(_ns(out=f)), lambda f: CN.score(_ns(out=f)), "ctrl_scores.json")]

    def first_rule(self, out, diag, device):
        """gpu/os_night.py's rule on the diagnostics, then round 1 as gpu/os2_night.py's round1 (unchanged)."""
        import os2_night as O2
        import os_night as ON
        import tempfile
        tmp = tempfile.mkdtemp(prefix="osloop_r1_")
        osr = os.path.join(out, "os_rule.json")
        if not os.path.exists(osr):
            ON.rule(_ns(dw=diag[0], dc=diag[1], rule_json=osr))
        else:
            # verify: re-rule into a temporary file and use that
            osr2 = os.path.join(tmp, "os_rule.json")
            ON.rule(_ns(dw=diag[0], dc=diag[1], rule_json=osr2))
            osr = osr2
        r1 = os.path.join(tmp, "RULE1.json")
        O2.round1(_ns(os_rule=osr, out_rule=r1, device=device, diag=diag))
        R = json.load(open(r1))
        R["pick"] = json.load(open(osr))["pick"]
        return R

    @staticmethod
    def family(base):
        return FAMILY.get(base, base)

    # -------------------------------------------------------------------------------------- rounds
    def build(self, devdir, folder, rule_path, dry):
        import os3_night as O3
        return O3.build(_ns(devdir=devdir, out=folder, rule_json=rule_path, dry_clifford_sentinel=dry))

    def check(self, folder):
        import os3_night as O3
        return O3.check(_ns(out=folder))

    def score(self, folder):
        import os3_night as O3
        return O3.score(_ns(out=folder))

    def q_choice(self, round_folder, key, row, dr):
        """R2: the offset whose last output qubit has the smallest readout gap on the probe's chain (as os3)."""
        import os2_night as O2
        chain_full = json.load(open(os.path.join(round_folder, "build.json")))["items"]["dr"]["chain"]
        L = int(key)
        cands = [(dr[str(chain_full[o + 2 * L - 1])]["gap"], o) for o in O2.OFFSETS
                 if o + 2 * L - 1 < len(chain_full) and str(chain_full[o + 2 * L - 1]) in dr]
        best = min(cands) if cands else None
        return best[1] if best and best[1] != 0 else None

    def compound(self, rounds):
        import os2_night as O2
        return O2.compound_rows(rounds)

    def predictions(self, out):
        """Draft predictions (prereg/drafts-2026-11-19/os_loop_DRAFT.md; [OWNER]): LOOP-1 the rule changes at least one
        stack between round 1 and round 2; LOOP-2 no L overshoots in the last round run; beside: the ledger's use,
        the rungs climbed, the OS's own compounding (numbers only)."""
        import os2_night as O2
        ds = sorted([d for d in os.listdir(out) if d.startswith("r") and d[1:].isdigit() and
                     os.path.exists(os.path.join(out, d, "round_scores.json"))], key=lambda d: int(d[1:]))
        rs = [json.load(open(os.path.join(out, d, "round_scores.json"))) for d in ds]
        R1 = json.load(open(os.path.join(out, "RULE1.json")))
        p2 = os.path.join(out, "RULE2.json")
        r2 = json.load(open(p2))["stacks"] if os.path.exists(p2) else None
        ran2 = os.path.exists(os.path.join(out, "r2", "round_scores.json"))
        changed = bool(r2 is not None and ran2 and any(R1["stacks"][k] != r2[k] for k in R1["stacks"]))
        last = rs[-1] if rs else None
        over = [k for k, v in last["rows"].items() if v.get("overshoot")] if last else None
        climbed = sorted({x for r in rs for v in r["rows"].values() for x in v["stack"][1:] if x in ("M", "F")})
        comp = O2.compound_rows(rs) if rs else dict(verdict="NOT JUDGEABLE", why="no round")
        return {
            "LOOP-1 the rule changes at least one stack between round 1 and round 2": "held" if changed else "failed",
            "LOOP-2 no L overshoots in the last round run": ("held" if not over else "failed") if last else
            "failed (no round ran)",
            "last_round": last["round"] if last else None, "overshoot_in_last_round": over,
            "beside_ledger": dict(used=R1.get("ledger", {}).get("used"), why=R1.get("ledger", {}).get("why")),
            "beside_rungs_climbed": climbed,
            "beside_os_compounding (numbers only, not a prediction)": {k: v for k, v in comp.items()
                                                                       if k not in ("per_L", "verdict")},
        }

    # -------------------------------------------------------------------------------------- dry runs
    def simulate(self, folder, noise, seed):
        import branch_noise as BN
        BN.noisy_run_local(folder, dict(noise or {}), seed=seed, stride=BN.WIDE_CIRCUIT)

    def dry_seed(self, tag):
        import branch_noise as BN
        if tag in ("dw", "dc"):
            return BN.job_seed(tag, 0, "wide")
        return BN.job_seed("round", int(tag[1:]), "wide")


def preflight(dry=False, out=None, zip_path=None, expect_psf_os=None, declaration=None):
    """The checks before a night; prints one line each. A device run needs the expected psf-os commit and the
    declaration file (2026-11-19, after the review: os2_run checked both; a night must not run on another psf-os or a
    notebook that is not the declaring commit): psf-os HEAD starts with expect_psf_os and its psf_os/ is unchanged;
    the notebook HEAD is the last commit that touched the declaration and its checkout is unchanged; a saved account
    file exists (not read)."""
    items = []

    def add(name, ok, detail=""):
        items.append(dict(item=name, ok=bool(ok), detail=str(detail)))

    def git(*a):
        return subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()
    for mod in ("qiskit", "qiskit_aer", "psf_os"):
        try:
            m = __import__(mod)
            add(f"import {mod}", True, getattr(m, "__version__", ""))
        except Exception as exc:  # noqa: BLE001
            add(f"import {mod}", False, type(exc).__name__)
    try:
        import psf_os
        import psf_os.loop  # noqa: F401
        add("psf_os.loop (psf-os v0.2)", True)
        root = os.path.dirname(os.path.dirname(os.path.abspath(psf_os.__file__)))
        head = git("-C", root, "rev-parse", "HEAD")
        # untracked files count too (after 2026-11-19, the workplace VS's side point): a new module placed in psf_os/
        # would be imported without changing any tracked file; ignored files (__pycache__, *.pyc) are not listed
        dirty = git("-C", root, "status", "--porcelain", "--untracked-files=all", "--", "psf_os")
        if dry and not expect_psf_os:
            add("psf-os commit", True, f"not checked (dry); HEAD {head[:8]}")
        else:
            add(f"psf-os at {expect_psf_os}", bool(expect_psf_os) and bool(head) and head.startswith(expect_psf_os),
                head[:12] or "not a git checkout")
            add("psf_os/ unchanged in its checkout (no new files)", dirty == "", dirty or "clean")
    except Exception as exc:  # noqa: BLE001
        add("psf_os.loop (psf-os v0.2)", False, type(exc).__name__)
    for f in ("daily_fetch.py", "wait_night.py", "ctrl_night.py", "os_night.py", "os2_night.py", "os3_night.py"):
        add(f"gpu/{f}", os.path.exists(os.path.join(HERE, f)))
    head = git("-C", NB, "rev-parse", "HEAD")
    if dry and not declaration:
        add("notebook HEAD is the declaration's commit", True, f"not checked (dry); HEAD {head[:8]}")
    else:
        decl = git("-C", NB, "log", "-1", "--format=%H", "--", declaration) if declaration else ""
        add(f"the declaration {declaration} exists", bool(declaration) and os.path.exists(os.path.join(NB, declaration)))
        # 2026-11-19 (the workplace VS): a declaration sits directly in prereg/ (drafts below it are not declarations)
        norm = os.path.normpath(declaration or "")
        add("the declaration is directly in prereg/ (not a draft)", os.path.dirname(norm) == "prereg"
            and norm.endswith(".md"), norm)
        add("notebook HEAD is the declaration's commit", bool(decl) and head == decl,
            f"HEAD {head[:8]}, the declaration last changed in {decl[:8] or 'no commit'}")
        dirty = git("-C", NB, "status", "--porcelain", "--untracked-files=no")
        add("notebook checkout unchanged", dirty == "", dirty or "clean")
    if not dry:
        acct = os.path.join(os.path.expanduser("~"), ".qiskit", "qiskit-ibm.json")
        add("a saved IBM account exists (the file only, not read)", os.path.exists(acct))
    if out is not None:
        add("OUT does not exist yet", not os.path.exists(out))
    if zip_path is not None:
        zd = os.path.dirname(os.path.abspath(zip_path))
        add("the zip's folder is writable", os.path.isdir(zd) and os.access(zd, os.W_OK))
        add("the zip does not exist yet", not os.path.exists(zip_path))
    ok = all(x["ok"] for x in items)
    for x in items:
        print(f"{'ok  ' if x['ok'] else 'FAIL'} {x['item']}: {x['detail']}")
    print("PREFLIGHT PASS" if ok else "PREFLIGHT FAIL")
    return ok, items


def ledger_seed(night, ledger):
    """A ledger line from a recorded night (os2_run's or this file's): its device, the device record's calibration
    time, the last scored round's stacks, g and verdicts. Appended to LEDGER (created when missing); refused when the
    night is already in it. Reads the records only."""
    from psf_os import loop as LP
    night = os.path.abspath(night)
    cfg = json.load(open(os.path.join(night, "run.json")))
    dev = cfg["device"]
    cal = RusLoop.calibration_time(os.path.join(night, "fetch_in", dev, "dev"))
    ds = sorted([d for d in os.listdir(night) if d.startswith("r") and d[1:].isdigit() and
                 os.path.exists(os.path.join(night, d, "round_scores.json"))], key=lambda d: int(d[1:]))
    rounds = [json.load(open(os.path.join(night, d, "round_scores.json"))) for d in ds]
    if not rounds:
        raise SystemExit(f"{night}: no scored round")
    R1 = json.load(open(os.path.join(night, "RULE1.json")))
    name = os.path.basename(night)
    led = LP.ledger_load(ledger)
    if any(e.get("night") == name for e in led):
        raise SystemExit(f"{name} is already in {ledger}")
    e = LP.ledger_entry(name, dev, cal, cfg.get("rungs", []), rounds, R1.get("ledger", {"used": False, "why": "os2"}))
    e["seeded_from_records"] = True
    json.dump(led + [e], open(ledger, "w"), indent=1, default=str)
    print(json.dumps(e, indent=1))
    return e


def main():
    from psf_os import loop as LP
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preflight")
    p.add_argument("--dry", action="store_true")
    p.add_argument("--out")
    p.add_argument("--zip")
    g = sub.add_parser("go")
    g.add_argument("out")
    g.add_argument("--zip")
    g.add_argument("--dry", metavar="DEVDIR")
    g.add_argument("--noise")
    g.add_argument("--k-max", type=int)
    g.add_argument("--budget", type=float)
    g.add_argument("--ledger")
    g.add_argument("--expect-psf-os", help="device runs (required): the psf-os commit declared")
    g.add_argument("--declaration", help="device runs (required): the declaration file, e.g. prereg/os_loop_night_2026-11-19.md")
    p.add_argument("--expect-psf-os")
    p.add_argument("--declaration")
    sd = sub.add_parser("ledger-seed")
    sd.add_argument("night")
    sd.add_argument("ledger")
    r = sub.add_parser("resume")
    r.add_argument("out")
    r.add_argument("--zip")
    v = sub.add_parser("verify")
    v.add_argument("out")
    v.add_argument("--resim", action="store_true")
    a = ap.parse_args()
    exp = RusLoop()
    if a.cmd == "preflight":
        return 0 if preflight(a.dry, a.out, a.zip, a.expect_psf_os, a.declaration)[0] else 1
    if a.cmd == "ledger-seed":
        ledger_seed(a.night, a.ledger)
        return 0
    if a.cmd == "verify":
        return 0 if LP.verify(a.out, exp, a.resim) else 1
    if a.cmd == "go":
        if not a.dry and not (a.expect_psf_os and a.declaration):
            raise SystemExit("a device run needs --expect-psf-os and --declaration")
        ok, items = preflight(bool(a.dry), out=a.out, zip_path=a.zip, expect_psf_os=a.expect_psf_os,
                              declaration=a.declaration)
        if not ok:
            raise SystemExit("preflight FAIL: nothing started")
        n = LP.start(a.out, exp, dry_devdir=a.dry, noise=json.load(open(a.noise)) if a.noise else None, k_max=a.k_max,
                     budget=a.budget, ledger=a.ledger, zip_path=a.zip,
                     extra=dict(preflight=items, expect_psf_os=a.expect_psf_os, declaration=a.declaration))
    else:
        n = LP.Night(a.out, exp)
        if a.zip:
            n.set_cfg(zip=os.path.abspath(a.zip))
        c = n.cfg()
        if not preflight(c["dry"], expect_psf_os=c.get("expect_psf_os"), declaration=c.get("declaration"))[0]:
            raise SystemExit("preflight FAIL: not resumed")
    print(json.dumps(n.go(), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
