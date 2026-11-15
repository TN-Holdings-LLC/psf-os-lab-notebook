"""A deterministic answerer for result lookups (prototype, 2026-11-15).

No language model and no probability: a Japanese question is read by fixed rules into conditions (date, device,
family, size, depth, angle, U), the conditions select rows of the notebook's records, and the answer is written from
fixed sentence templates. The same question always gives the same answer, and every line names its record folder.

Scope (prototype): the 179 results with an exact answer and a declared verdict collected in
notes/paper9_yardstick/line_all.json (2026-11-05 to 2026-11-14). Only lookups of recorded results are answered;
anything else (why, predictions, other records) is refused with a fixed sentence.

usage: python notes/ask_prototype/ask.py "11月14日の marrakesh で XX 81量子ビットは読めた？"   (from the repository root)
       python notes/ask_prototype/ask.py --test"""
import json
import re
import sys
import unicodedata

TABLE = "notes/paper9_yardstick/line_all.json"
RTHREAD = "notes/paper9/r_thread_2026-11-13/r_thread.json"
LINE = 1 - 2 ** -0.5

FAMILY_JA = {"XX chain": "XX鎖", "Hubbard": "ハバード", "IBM 2023 utility": "IBM 2023 ユーティリティ",
             "Ising 3D (isingL)": "3次元キックイジング", "daily (P4 chain)": "デイリー記録",
             "dual-unitary (curve)": "双対ユニタリ曲線"}
# Words that name a family in a question (checked on the normalized, lower-cased text).
FAMILY_WORDS = {"XX chain": ["xx", "エックスエックス"], "Hubbard": ["hubbard", "ハバード"],
                "IBM 2023 utility": ["utility", "ユーティリティ", "kim"],
                "Ising 3D (isingL)": ["ising", "イジング"], "daily (P4 chain)": ["daily", "デイリー"],
                "dual-unitary (curve)": ["dual", "双対ユニタリ", "du"]}
DEVICE_WORDS = {"ibm_fez": ["fez", "フェズ"], "ibm_marrakesh": ["marrakesh", "マラケシュ"],
                "ibm_kingston": ["kingston", "キングストン"]}
# Folders of records whose name differs from the folder (the r-thread's names).
FOLDER = {"utility-fez-2026-11-10": "results/utility-2026-11-10",
          "utility-depth-fez-2026-11-11": "results/utility-depth-2026-11-11",
          "isingL-fez-2026-11-10": "results/night-2026-11-10/isingL"}
# Words that mark a question this prototype does not answer.
REFUSE = ["なぜ", "どうして", "理由", "予測", "見積", "なら読める", "どうすれば"]


def norm(s):
    return unicodedata.normalize("NFKC", s).lower()


# ---------------------------------------------------------------- the index (one row per recorded result)
def build_index():
    layers = {(u["result"], u["unit"]): u["cz_layers"] for u in json.load(open(RTHREAD))["units"]}
    rows = []
    for x in json.load(open(TABLE)):
        rec, item = x["record"], x["item"]
        text = rec + " " + item
        m = re.search(r"2026-\d\d-\d\d", rec)
        dev = next((d for d in DEVICE_WORDS if d in text), None)
        if dev is None and rec.startswith("twin-"):
            dev = "ibm_marrakesh"                       # results/twin-2026-11-13: ibm_marrakesh_xx, _hub
        if dev is None and "-fez-" in rec:
            dev = "ibm_fez"
        unit = item.split(":")[-1]
        row = {"family": x["family"], "date": m.group(0) if m else None, "device": dev, "unit": unit,
               "qubits": None, "sites": None, "steps": None, "layers": None, "angle": None, "U": None,
               "variant": "連続極限との比較" if "continuum" in rec else "",
               "r": x["r"], "ratio": x["ratio"], "reads": bool(x["reads"]),
               "folder": FOLDER.get(rec.split("/")[0], "results/" + rec.split("/scores")[0])}
        if (g := re.match(r"N(\d+)_th(\d+)_s(\d+)", unit)):
            row.update(qubits=int(g[1]), angle={"0785": "π/4", "1571": "π/2"}[g[2]], steps=int(g[3]),
                       layers=4 * int(g[3]))
        elif (g := re.match(r"L(\d+)_(?:T[\d.]+_)?s(\d+)(?:_U(\d+))?", unit)):
            row.update(sites=int(g[1]), qubits=2 * int(g[1]), steps=int(g[2]), U=int(g[3]) if g[3] else 4)
        elif (g := re.match(r"(?:z106|w10|w17b?)_t(\d+)", unit)) or (g := re.match(r"q\d+f\d_t(\d+)", unit)):
            row.update(steps=int(g[1]))
        if (g := re.match(r"du(\d+)-", rec)):
            row["qubits"] = int(g[1])
        row["layers"] = row["layers"] or layers.get((rec.split("/")[0], unit))
        rows.append(row)
    return rows


# ---------------------------------------------------------------- reading the question (fixed rules)
def parse(q):
    t = norm(q)
    c = {}
    if (g := re.search(r"(?:2026[-/年])?(\d{1,2})[月/-](\d{1,2})日?", t)):
        c["date"] = f"2026-{int(g[1]):02d}-{int(g[2]):02d}"
    for d, ws in DEVICE_WORDS.items():
        if any(w in t for w in ws):
            c["device"] = d
    for f, ws in FAMILY_WORDS.items():
        if any(re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", t) for w in ws):
            c["family"] = f
            break
    if (g := re.search(r"(\d+)\s*(?:量子ビット|qubits?|q\b)", t)) or (g := re.search(r"\bn\s*=\s*(\d+)", t)):
        c["qubits"] = int(g[1])
    if (g := re.search(r"(\d+)\s*サイト", t)) or (g := re.search(r"\bl\s*=\s*(\d+)", t)):
        c["sites"] = int(g[1])
    if (g := re.search(r"(\d+)\s*(?:ステップ|steps?)", t)):
        c["steps"] = int(g[1])
    if (g := re.search(r"(\d+)\s*層", t)):
        c["layers"] = int(g[1])
    if (g := re.search(r"(?:π|pi|パイ)\s*/\s*([24])", t)):
        c["angle"] = f"π/{g[1]}"
    if (g := re.search(r"\bu\s*=?\s*([04])\b", t)):
        c["U"] = int(g[1])
    return c


def select(rows, c):
    return [r for r in rows if all(r.get(k) == v for k, v in c.items())]


# ---------------------------------------------------------------- writing the answer (fixed templates)
def describe(r):
    parts = [r["date"] or "日付なし", r["device"] or "装置不明", FAMILY_JA[r["family"]]]
    if r["sites"]:
        parts.append(f"L={r['sites']}（{r['qubits']}量子ビット）")
    elif r["qubits"]:
        parts.append(f"{r['qubits']}量子ビット")
    if r["U"] is not None:
        parts.append(f"U={r['U']}")
    if r["angle"]:
        parts.append(f"θ={r['angle']}")
    if r["steps"]:
        parts.append(f"{r['steps']}ステップ" + (f"（CZ {r['layers']}層）" if r["layers"] else ""))
    if r["variant"]:
        parts.append(r["variant"])
    if not (r["steps"] or r["qubits"]):
        parts.append(r["unit"])
    verdict = "読めた" if r["reads"] else "読めなかった"
    return (f"・{'、'.join(parts)}：{verdict}（MSE/平均二乗 {r['ratio']:.3f}、残存率 r {r['r']:.3f}）"
            f"　根拠 {r['folder']}")


LABEL = {"date": "日付", "device": "装置", "family": "種類", "qubits": "量子ビット数", "sites": "サイト数",
         "steps": "ステップ数", "layers": "CZ層数", "angle": "角度", "U": "U"}


def answer(q, rows):
    t = norm(q)
    if any(w in t for w in REFUSE):
        return "その型の質問は扱えない。扱えるのは、記録された結果の照会（日付・装置・種類・大きさ・深さ・角度）だけ。"
    c = parse(q)
    if not c:
        return ("条件が読み取れなかった。日付（11月14日）、装置（fez / marrakesh / kingston）、種類（XX、ハバード、"
                "ユーティリティ、イジング、デイリー、双対ユニタリ）、大きさ（81量子ビット、L=20）、深さ（16ステップ、64層）、"
                "角度（π/4）のどれかを入れてほしい。")
    shown = "、".join(f"{LABEL[k]} {FAMILY_JA[v] if k == 'family' else v}" for k, v in c.items())
    hit = select(rows, c)
    if not hit:
        lines = [f"条件（{shown}）に合う記録はない。条件ごとの件数："]
        for k, v in c.items():
            lines.append(f"・{LABEL[k]} {v} だけなら {len(select(rows, {k: v}))} 件")
        return "\n".join(lines)
    n_ok = sum(r["reads"] for r in hit)
    head = f"条件（{shown}）に合う記録は {len(hit)} 件。読めた {n_ok}、読めなかった {len(hit) - n_ok}。"
    note = "（記録の照会として答えた。走らせていない条件の見積もりはしない。）" if re.search(r"読める(?!た)", t) else ""
    if len(hit) > 12:
        out = [head]
        for k in ("date", "device", "family", "qubits", "steps", "angle"):
            if k in c:
                continue
            vals = [str(v) if k != "family" else FAMILY_JA[v]
                    for v in sorted({r[k] for r in hit if r[k] is not None})]
            if 1 < len(vals) <= 12:
                out.append(f"・{LABEL[k]}で絞れる：{' / '.join(vals)}")
        out.append("条件を足せば一件ずつ答える。")
        return "\n".join(out + ([note] if note else []))
    order = sorted(hit, key=lambda r: (r["date"] or "", r["device"] or "", r["family"], r["qubits"] or 0,
                                      r["angle"] or "", r["steps"] or 0, r["variant"], r["unit"]))
    return "\n".join([head] + [describe(r) for r in order] + ([note] if note else []))


# ---------------------------------------------------------------- fixed checks of the prototype
TESTS = [
    ("11月14日の marrakesh で XX 81量子ビット 16ステップ π/4 は読めた？", ["2 件", "読めた 1、読めなかった 1",
     "MSE/平均二乗 0.496", "MSE/平均二乗 0.518"]),
    ("fez の XX 81量子ビット 64層 π/4", ["1 件", "読めなかった（MSE/平均二乗 0.658"]),
    ("ハバード L=30 6ステップ U=4", ["1 件", "読めなかった"]),
    ("11/13 のハバード", ["3 件", "ibm_marrakesh"]),
    ("kingston の双対ユニタリ", ["2 件", "51量子ビット", "71量子ビット"]),
    ("11月14日のデイリー", ["4 件", "読めた 4"]),
    ("ユーティリティ 8ステップ", ["1 件", "読めた"]),
    ("XX", ["75 件", "絞れる", "2 / 4 / 8 / 12 / 16 / 20"]),
    ("12月1日の fez", ["合う記録はない", "装置 ibm_fez だけなら"]),
    ("なぜ81量子ビットの方が悪いの？", ["扱えない"]),
    ("こんにちは", ["条件が読み取れなかった"]),
]


def run_tests(rows):
    bad = 0
    for q, want in TESTS:
        a = answer(q, rows)
        miss = [w for w in want if w not in a]
        bad += bool(miss)
        print(("ok   " if not miss else "FAIL ") + q + ("" if not miss else f"  missing {miss}\n{a}"))
        if answer(q, rows) != a:
            bad += 1
            print("FAIL not the same answer twice: " + q)
    print(f"{len(TESTS) - bad} of {len(TESTS)} checks")
    return bad == 0


if __name__ == "__main__":
    idx = build_index()
    if sys.argv[1:] == ["--test"]:
        sys.exit(0 if run_tests(idx) else 1)
    print(answer(" ".join(sys.argv[1:]), idx))
