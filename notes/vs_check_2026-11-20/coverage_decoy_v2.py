"""The decoy reading table of 2026-11-20 morning (prereg/drafts-2026-11-20/decoy_DRAFT.md at 74f479cc), counted from
the table's text alone, without the tool (workplace VS, 2026-11-20; author The Architect). No data.

Words per conditional sub-item: LESS ("loses"), SAME or MORE ("keeps"). The table reads D0 A, D0 B, D1 A, D1 B,
D2 A; D2 B is beside but enumerated too (3^6 = 729 outcomes). Each row is written as its own condition, NOT relying on
the order the table is read in, so "exactly one row" is checked as mutual exclusion plus coverage.

  python coverage_decoy_v2.py
"""
import itertools

W = ("LESS", "SAME", "MORE")


def rows(o):
    L = {k: v == "LESS" for k, v in o.items()}
    control = L["D0A"] and not L["D0B"]          # "A loses, B keeps" (rows 1, 2, 3, 5, 6)
    hit = []
    if (not L["D0A"]) or L["D0B"]:               # row 4: "A keeps, or B loses too"; D1, D2 "-"
        hit.append(4)
    if control and L["D1A"] and L["D2A"]:        # row 2: D1 "A loses (B either)", D2 "A loses"
        hit.append(2)
    if control and L["D1A"] and not L["D2A"]:    # row 6: D1 "A loses (B either)", D2 "A keeps"
        hit.append(6)
    if control and not L["D1A"] and L["D1B"]:    # row 3: D1 "A keeps, B loses"; D2 "-"
        hit.append(3)
    if control and not L["D1A"] and not L["D1B"] and L["D2A"]:      # row 1: D1 "A and B keep", D2 "A loses"
        hit.append(1)
    if control and not L["D1A"] and not L["D1B"] and not L["D2A"]:  # row 5: D1 "A and B keep", D2 "A keeps"
        hit.append(5)
    return hit


def main():
    keys = ["D0A", "D0B", "D1A", "D1B", "D2A", "D2B"]
    count, none, many = {}, 0, 0
    for ws in itertools.product(W, repeat=len(keys)):
        h = rows(dict(zip(keys, ws)))
        none += not h
        many += len(h) > 1
        for r in h:
            count[r] = count.get(r, 0) + 1
    print(f"outcomes 729; on no row {none}; on more than one row {many}")
    print("per row: " + ", ".join(f"row {r} {count.get(r, 0)}" for r in (4, 2, 6, 3, 1, 5)))
    # the owner's priority case: D1's A and B both lose
    for d2a in ("LESS", "SAME"):
        o = dict(D0A="LESS", D0B="SAME", D1A="LESS", D1B="LESS", D2A=d2a, D2B="SAME")
        print(f"D0 A loses, B keeps; D1 A and B lose; D2 A {'loses' if d2a == 'LESS' else 'keeps'} -> row {rows(o)}")


if __name__ == "__main__":
    main()
