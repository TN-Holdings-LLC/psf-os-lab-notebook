"""Preflight of gpu/os_loop.py (19c) on temporary clones (workplace VS Claude, 2026-11-19; instruction "その3"): the
real notebook and psf-os checkouts are never changed. Each case builds a state, calls preflight in a subprocess from
the clone (so that the clone's HEAD is the notebook's), and reads the items it prints (`preflight.json` in OUT).

  python vs_preflight.py NOTEBOOK PSFOS WORK

Cases (a device run, so expect_psf_os and declaration are given):
  ok        a clone with a declaration under prereg/ committed at HEAD, psf-os at the expected commit, both clean
  sha       the same with another expected SHA                                     -> psf-os item FAIL
  psfdirty  psf_os/ changed in the psf-os copy                                      -> psf_os/ unchanged FAIL
  moved     one more notebook commit after the declaration                         -> HEAD item FAIL
  dirty     the notebook checkout changed                                           -> checkout item FAIL
  draft     a draft (prereg/drafts-.../...) given as the declaration, HEAD at its last commit -> expected FAIL
  nodecl    go without --expect-psf-os / --declaration                             -> refused, OUT not made
  failgo    go with a preflight FAIL                                                -> "nothing started", OUT not made
The saved-account item is ignored here (this machine has none by design).
"""
import json
import os
import shutil
import subprocess
import sys

RES = []


def report(name, ok, note=""):
    RES.append(dict(case=name, ok=bool(ok), note=note))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({note})" if note else ""), flush=True)


def git(cwd, *a):
    return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True).stdout.strip()


def commit(cwd, msg):
    subprocess.run(["git", "-C", cwd, "-c", "user.name=The Architect", "-c", "user.email=love.os.architect@proton.me",
                    "commit", "-q", "-m", msg], check=True)


def items_of(nb, psfos, expect, decl):
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([psfos, nb, os.path.join(nb, "gpu")]))
    code = ("import sys, json; sys.path.insert(0, 'gpu'); import os_loop as O; "
            f"ok, items = O.preflight(False, None, None, {expect!r}, {decl!r}); print('JSON' + json.dumps(items))")
    r = subprocess.run([sys.executable, "-c", code], cwd=nb, env=env, capture_output=True, text=True)
    line = next((l for l in r.stdout.splitlines() if l.startswith("JSON")), None)
    if line is None:
        raise RuntimeError(r.stderr[-500:])
    return {i["item"]: i for i in json.loads(line[4:]) if "saved IBM account" not in i["item"]}


def bad(items):
    return [k for k, v in items.items() if not v["ok"]]


def main():
    nb_src, ps_src, work = sys.argv[1:4]
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    nb, ps = os.path.join(work, "nb"), os.path.join(work, "psfos")
    subprocess.run(["git", "clone", "-q", nb_src, nb], check=True)
    subprocess.run(["git", "-C", nb, "checkout", "-q", git(nb_src, "rev-parse", "HEAD")], check=True)
    subprocess.run(["git", "clone", "-q", ps_src, ps], check=True)
    subprocess.run(["git", "-C", ps, "checkout", "-q", git(ps_src, "rev-parse", "HEAD")], check=True)
    sha = git(ps, "rev-parse", "HEAD")[:7]
    decl = "prereg/vs_test_declaration_2026-11-19.md"
    open(os.path.join(nb, decl), "w").write("# test declaration for the preflight check (a temporary clone only)\n")
    subprocess.run(["git", "-C", nb, "add", decl], check=True)
    commit(nb, "test declaration (temporary clone)")

    it = items_of(nb, ps, sha, decl)
    report("ok: everything as declared", not bad(it), f"failing: {bad(it) or '-'}")
    it = items_of(nb, ps, "0000000", decl)
    report("sha: another expected psf-os commit", any(k.startswith("psf-os at") for k in bad(it)), str(bad(it)))
    p = os.path.join(ps, "psf_os", "loop.py")
    open(p, "a").write("\n# changed\n")
    it = items_of(nb, ps, sha, decl)
    report("psfdirty: psf_os/ changed", "psf_os/ unchanged in its checkout" in bad(it), str(bad(it)))
    subprocess.run(["git", "-C", ps, "checkout", "-q", "--", "psf_os/loop.py"], check=True)
    open(os.path.join(ps, "psf_os", "zz_untracked.py"), "w").write("X = 1\n")
    it = items_of(nb, ps, sha, decl)
    report("psfdirty (beside): an untracked new file in psf_os/ is not seen", True,
           f"failing: {bad(it) or '-'} (preflight uses --untracked-files=no)")
    os.remove(os.path.join(ps, "psf_os", "zz_untracked.py"))
    open(os.path.join(nb, "notes", "vs_dirty.txt"), "w").write("x\n")
    subprocess.run(["git", "-C", nb, "add", "notes/vs_dirty.txt"], check=True)
    it = items_of(nb, ps, sha, decl)
    report("dirty: the notebook checkout changed (a staged file)", "notebook checkout unchanged" in bad(it), str(bad(it)))
    commit(nb, "one more commit after the declaration (temporary clone)")
    it = items_of(nb, ps, sha, decl)
    report("moved: a commit after the declaration", "notebook HEAD is the declaration's commit" in bad(it), str(bad(it)))
    draft = "prereg/drafts-2026-11-19/os_loop_DRAFT.md"
    with open(os.path.join(nb, draft), "a") as f:
        f.write("\n")
    subprocess.run(["git", "-C", nb, "add", draft], check=True)
    commit(nb, "touch the draft (temporary clone)")
    it = items_of(nb, ps, sha, draft)
    report("draft: a draft given as the declaration (HEAD at its last commit) is refused", bool(bad(it)),
           f"failing: {bad(it) or 'none: the draft passes'}")
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([ps, nb, os.path.join(nb, "gpu")]))
    out = os.path.join(work, "night_nodecl")
    r = subprocess.run([sys.executable, "gpu/os_loop.py", "go", out, "--zip", os.path.join(work, "z.zip")], cwd=nb,
                       env=env, capture_output=True, text=True)
    report("nodecl: go without --expect-psf-os / --declaration is refused, nothing made",
           "needs --expect-psf-os" in (r.stdout + r.stderr) and not os.path.exists(out), (r.stdout + r.stderr).strip()[-80:])
    out = os.path.join(work, "night_failgo")
    r = subprocess.run([sys.executable, "gpu/os_loop.py", "go", out, "--zip", os.path.join(work, "z.zip"),
                        "--expect-psf-os", "0000000", "--declaration", decl], cwd=nb, env=env, capture_output=True,
                       text=True)
    report("failgo: go with a preflight FAIL starts nothing", "nothing started" in (r.stdout + r.stderr)
           and not os.path.exists(out), (r.stdout + r.stderr).strip()[-60:])
    print(f"{len(RES)} checks, {sum(not r['ok'] for r in RES)} FAIL")
    json.dump(RES, open(os.path.join(work, "vs_preflight.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
