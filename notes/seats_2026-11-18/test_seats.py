"""Hand-checkable cases for seats.py (line, ring, a failed qubit, a failed coupler) and a brute-force comparison of
the integer programme on small random graphs."""
import random

import seats as S


def dev(n, edges, fq=(), fc=()):
    return dict(name="t", n=n, couplers=list(edges), failed_couplers=list(fc), failed_qubits=list(fq), fetched=None)


def mx(d, L):
    return S.maximum(d, S.blocks(d, L))[0]


def brute(d, L):
    """Exhaustive search with pruning: each block is taken or not, in order; a branch stops when it cannot beat the
    best so far."""
    bl = S.blocks(d, L)
    nb = {q: set() for q in range(d["n"])}
    for a, b in d["couplers"]:
        nb[a].add(b); nb[b].add(a)
    zone = [set(b) | {x for q in b for x in nb[q]} for b in bl]
    best = [0]

    def go(i, taken, k):
        if k + (len(bl) - i) <= best[0]:
            return
        if i == len(bl):
            best[0] = k
            return
        if not (zone[i] & taken):
            go(i + 1, taken | set(bl[i]), k + 1)
        go(i + 1, taken, k)
    go(0, set(), 0)
    return best[0]


line = lambda n: [(i, i + 1) for i in range(n - 1)]
assert mx(dev(11, line(11)), 5) == 2            # 5 + gap + 5
assert mx(dev(10, line(10)), 5) == 1            # 5 + gap + 4: no second block
assert mx(dev(12, line(12) + [(11, 0)]), 5) == 2   # ring of 12: 5 + 1 + 5 + 1
assert mx(dev(11, line(11), fq=[5]), 5) == 2    # the failed qubit is the gap
assert mx(dev(11, line(11), fq=[4]), 5) == 1    # 0-3 too short; 5-10 holds one
assert mx(dev(11, line(11), fc=[(5, 6)]), 5) == 1   # 5 and 6 are suspect: 0-4 and 7-10 (too short)
assert len(S.blocks(dev(5, line(5)), 5)) == 1   # a path and its reverse are one block
random.seed(1)
for t in range(30):
    n = random.randint(8, 12)
    e = sorted({tuple(sorted(random.sample(range(n), 2))) for _ in range(n)})
    d = dev(n, e)
    for L in (3, 5):
        assert mx(d, L) == brute(d, L), (n, e, L)
print("seats tests: all pass")
