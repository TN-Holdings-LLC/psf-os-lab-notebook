"""Read what can be read of a thin git pack (no base commit): every full object, and deltas whose base is in the pack
or in a given repository's objects. Writes blobs as out/<sha>. Workplace Claude, 2026-11-24 (desk; no network)."""
import hashlib, os, subprocess, sys, zlib

pack, out, base_repo = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else None)
os.makedirs(out, exist_ok=True)
d = open(pack, "rb").read()
assert d[:4] == b"PACK"
n = int.from_bytes(d[8:12], "big")
TYPES = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}
pos = 12
raw = {}          # offset -> (type, data) or ('ofs', base_off, delta) / ('ref', base_sha, delta)
for _ in range(n):
    start = pos
    c = d[pos]; pos += 1
    t = (c >> 4) & 7; size = c & 15; shift = 4
    while c & 0x80:
        c = d[pos]; pos += 1; size |= (c & 0x7f) << shift; shift += 7
    if t == 6:
        c = d[pos]; pos += 1; off = c & 0x7f
        while c & 0x80:
            c = d[pos]; pos += 1; off = ((off + 1) << 7) | (c & 0x7f)
        base = ("ofs", start - off)
    elif t == 7:
        base = ("ref", d[pos:pos + 20].hex()); pos += 20
    else:
        base = None
    z = zlib.decompressobj(); data = z.decompress(d[pos:]); pos = len(d) - len(z.unused_data)
    raw[start] = (t, base, data)


def apply(src, delta):
    i = 0
    def varint():
        nonlocal i
        r = s = 0
        while True:
            c = delta[i]; i += 1; r |= (c & 0x7f) << s; s += 7
            if not c & 0x80:
                return r
    varint(); varint()
    outb = bytearray()
    while i < len(delta):
        c = delta[i]; i += 1
        if c & 0x80:
            off = sz = 0
            for k in range(4):
                if c & (1 << k): off |= delta[i] << (8 * k); i += 1
            for k in range(3):
                if c & (1 << (4 + k)): sz |= delta[i] << (8 * k); i += 1
            outb += src[off:off + (sz or 0x10000)]
        else:
            outb += delta[i:i + c]; i += c
    return bytes(outb)


def from_repo(sha):
    if not base_repo:
        return None
    r = subprocess.run(["git", "-C", base_repo, "cat-file", "-p", sha], capture_output=True)
    if r.returncode:
        return None
    t = subprocess.run(["git", "-C", base_repo, "cat-file", "-t", sha], capture_output=True, text=True).stdout.strip()
    return (t, r.stdout)


done, bysha = {}, {}
def resolve(off, depth=0):
    if off in done:
        return done[off]
    t, base, data = raw[off]
    if base is None:
        res = (TYPES[t], data)
    else:
        if base[0] == "ofs":
            b = resolve(base[1], depth + 1)
        else:
            b = bysha.get(base[1]) or from_repo(base[1])
        res = None if b is None else (b[0], apply(b[1], data))
    done[off] = res
    if res:
        sha = hashlib.sha1(f"{res[0]} {len(res[1])}".encode() + b"\0" + res[1]).hexdigest()
        bysha[sha] = res
    return res

for _pass in range(3):
    for off in sorted(raw):
        if done.get(off) is None:
            done.pop(off, None)
            resolve(off)
ok = sum(1 for v in done.values() if v)
for sha, (t, data) in bysha.items():
    open(os.path.join(out, f"{t}_{sha}"), "wb").write(data)
print(f"{n} objects, {ok} read, {n - ok} not readable (base outside)")
