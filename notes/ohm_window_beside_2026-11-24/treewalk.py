"""List and extract a path prefix from a commit using the objects packread.py wrote (and a base repo for the rest)."""
import os, subprocess, sys
objs, base_repo, commit, prefix, out = sys.argv[1:6]

def get(sha):
    for t in ("commit", "tree", "blob"):
        p = os.path.join(objs, f"{t}_{sha}")
        if os.path.exists(p):
            return t, open(p, "rb").read()
    r = subprocess.run(["git", "-C", base_repo, "cat-file", "-t", sha], capture_output=True, text=True)
    if r.returncode:
        return None, None
    t = r.stdout.strip()
    data = subprocess.run(["git", "-C", base_repo, "cat-file", t, sha], capture_output=True).stdout
    return t, data

def tree_entries(data):
    i = 0
    while i < len(data):
        sp = data.index(b" ", i); nul = data.index(b"\0", sp)
        mode = data[i:sp].decode(); name = data[sp + 1:nul].decode(); sha = data[nul + 1:nul + 21].hex()
        yield mode, name, sha; i = nul + 21

t, c = get(commit)
tree = c.split(b"\n")[0].split()[1].decode()
missing = []
def walk(sha, path):
    t, data = get(sha)
    if data is None:
        missing.append(path); return
    for mode, name, s in tree_entries(data):
        p = f"{path}/{name}" if path else name
        if not (p.startswith(prefix) or prefix.startswith(p)):
            continue
        if mode.startswith("4"):
            walk(s, p)
        else:
            tt, blob = get(s)
            if blob is None:
                missing.append(p); continue
            dst = os.path.join(out, p); os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, "wb").write(blob)
            print(len(blob), p)
walk(tree, "")
print("missing:", missing)
