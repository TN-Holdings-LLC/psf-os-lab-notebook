"""A deterministic answerer for result lookups (prototype, 2026-11-15).

No language model and no probability: a Japanese question is read by fixed rules into conditions, the conditions
select rows of the notebook's records, and the answer is written from fixed sentence templates. The same question
always gives the same answer, and every line names its record folder.

The entrance is closed: every character of a question must be taken by a pattern or by a listed filler word. A word
no rule takes stops the answer ("解釈できない語"), so nothing is silently ignored. Questions of a type the prototype
does not answer (why, the future, approximations, comparisons) are refused before any lookup.

Scope: the 179 results with an exact answer and a declared verdict in notes/paper9_yardstick/line_all.json
(2026-11-05 to 2026-11-14). The verdict printed is the declared one stored in the record, never recomputed from r.

usage: python notes/ask_prototype/ask.py "11月14日の marrakesh で XX 81量子ビット 16ステップ π/4 は読めた？"
       python notes/ask_prototype/ask.py --test        (all checks of notes/ask_prototype/checks.py)"""
import json
import math
import re
import sys
import unicodedata

TABLE = "notes/paper9_yardstick/line_all.json"
RTHREAD = "notes/paper9/r_thread_2026-11-13/r_thread.json"

FAMILY_JA = {"XX chain": "XX鎖", "Hubbard": "ハバード", "IBM 2023 utility": "IBM 2023 ユーティリティ",
             "Ising 3D (isingL)": "3次元キックイジング", "daily (P4 chain)": "デイリー記録",
             "dual-unitary (curve)": "双対ユニタリ曲線"}
OBS_JA = {"z106": "Z_106", "w10": "重み10", "w17": "重み17", "w17b": "重み17b"}
RUN_JA = {"xxsize": "大きさの試験", "xxcone": "光円錐の再試行"}
FOLDER = {"utility-fez-2026-11-10": "results/utility-2026-11-10",
          "utility-depth-fez-2026-11-11": "results/utility-depth-2026-11-11",
          "isingL-fez-2026-11-10": "results/night-2026-11-10/isingL"}

# ---------------------------------------------------------------- the normalisation dictionary
# Each entry: (condition, value, spellings). Spellings are matched on the NFKC, lower-cased question, longest first,
# and only where they are not part of a longer latin word.
SYNONYMS = [
    ("device", "ibm_fez", ["ibm_fez", "ibm fez", "fez", "フェズ"]),
    ("device", "ibm_marrakesh", ["ibm_marrakesh", "ibm marrakesh", "marrakesh", "マラケシュ"]),
    ("device", "ibm_kingston", ["ibm_kingston", "ibm kingston", "kingston", "キングストン"]),
    ("family", "XX chain", ["xx鎖", "xxチェーン", "xx", "エックスエックス"]),
    ("family", "Hubbard", ["フェルミハバード", "ハバード模型", "ハバード", "hubbard"]),
    ("family", "IBM 2023 utility", ["ユーティリティ", "utility"]),
    ("family", "Ising 3D (isingL)", ["3次元キックイジング", "キックイジング", "イジング", "ising"]),
    ("family", "daily (P4 chain)", ["デイリー記録", "デイリー", "daily"]),
    ("family", "dual-unitary (curve)", ["双対ユニタリ曲線", "双対ユニタリ", "dual-unitary", "dual unitary"]),
    ("angle", "π/4", ["θ=π/4", "π/4", "pi/4", "パイ/4", "0.25π", "0.25pi", "45度"]),
    ("angle", "π/2", ["θ=π/2", "π/2", "pi/2", "パイ/2", "0.5π", "0.5pi", "90度"]),
    ("run", "xxsize", ["大きさの試験", "xxsize"]),
    ("run", "xxcone", ["光円錐の再試行", "光円錐", "再試行", "xxcone"]),
    ("variant", "continuum", ["連続極限の答え", "連続極限"]),
    ("variant", "circuit", ["回路の答え"]),
    ("obs", "z106", ["z_106", "z106"]),
    ("obs", "w10", ["重み10", "weight-10", "w10"]),
    ("obs", "w17b", ["重み17b", "weight-17b", "w17b"]),
    ("obs", "w17", ["重み17", "weight-17", "w17"]),
]
# Patterns with a number: (condition, regex, converter).
PATTERNS = [
    ("date", r"(?:2026\s*[-/年]\s*)?(\d{1,2})\s*[月/-]\s*(\d{1,2})\s*日?",
     lambda g: f"2026-{int(g[1]):02d}-{int(g[2]):02d}"),
    ("arm", r"q(\d\d)([fl]\d)", lambda g: f"q{g[1]}{g[2]}"),
    ("problem", r"(?<![a-z0-9])(fx-a|d0\d|user)(?![a-z0-9])", lambda g: g[1].upper() if g[1] != "user" else "user"),
    ("qubits", r"(\d+)\s*(?:量子ビット|qubits?)", lambda g: int(g[1])),
    ("qubits", r"(?<![a-z])n\s*=\s*(\d+)", lambda g: int(g[1])),
    ("sites", r"(\d+)\s*サイト", lambda g: int(g[1])),
    ("sites", r"(?<![a-z])l\s*=\s*(\d+)", lambda g: int(g[1])),
    ("T", r"(?<![a-z])t\s*=\s*(\d+(?:\.\d+)?)", lambda g: float(g[1])),
    ("U", r"(?<![a-z])u\s*=\s*(\d+)", lambda g: int(g[1])),
    ("steps", r"(\d+)\s*(?:ステップ|steps?)", lambda g: int(g[1])),
    ("layers", r"(\d+)\s*層", lambda g: int(g[1])),
]
# Words that carry no condition. Removed after every pattern; anything left is an unknown word.
FILLER = ["読めましたか", "読めなかった", "読めたか", "読めた", "読める", "結果", "判定", "教えて", "ください",
          "どうだった", "ですか", "でした", "記録", "装置", "角度", "腕", "問題", "の", "で", "は", "を", "が", "に",
          "と", "も", "か", "、", "。", "?", "!", "・", ",", "(", ")", "「", "」", ":"]
# Question types this prototype does not answer, by kind. Checked before anything else.
REFUSE = {
    "理由を問う質問": ["なぜ", "どうして", "なんで", "理由", "原因", "せい", "何が効", "どういう仕組"],
    "未来や予測を問う質問": ["明日", "明後日", "あさって", "来週", "来月", "今後", "これから", "次回", "将来",
                     "予測", "予想", "見込", "見積", "読めそう", "読めるだろう", "なら読める"],
    "おおよその要約を問う質問": ["だいたい", "大体", "およそ", "くらい", "ぐらい", "程度", "傾向", "平均", "一般",
                       "普通は", "どこまで", "何層まで", "何ステップまで", "目安", "ざっくり", "全体として"],
    "比較や評価を問う質問": ["どっち", "どちら", "比べ", "比較", "一番", "最も", "良い", "悪い", "おすすめ", "勝"],
}
LABEL = {"date": "日付", "device": "装置", "family": "種類", "qubits": "量子ビット数", "sites": "サイト数",
         "steps": "ステップ数", "layers": "CZ層数", "angle": "角度", "U": "U", "T": "総時間T", "run": "試験",
         "variant": "照合先", "obs": "観測量", "arm": "腕", "problem": "問題"}
KEYS = ["family", "date", "device", "run", "problem", "obs", "arm", "qubits", "sites", "U", "T", "angle", "steps",
        "layers", "variant"]


def norm(s):
    return unicodedata.normalize("NFKC", s).lower()


# ---------------------------------------------------------------- the index (one row per recorded result)
def build_index():
    layers = {(u["result"], u["unit"]): u["cz_layers"] for u in json.load(open(RTHREAD))["units"]}
    rows = []
    for x in json.load(open(TABLE)):
        rec, item = x["record"], x["item"]
        base = rec.split("/")[0]
        text = rec + " " + item
        m = re.search(r"2026-\d\d-\d\d", rec)
        dev = next((d for d in ("ibm_fez", "ibm_marrakesh", "ibm_kingston") if d in text), None)
        if dev is None and base.startswith("twin-"):
            dev = "ibm_marrakesh"                       # results/twin-2026-11-13: ibm_marrakesh_xx, _hub
        if dev is None and "-fez-" in base:
            dev = "ibm_fez"
        unit = item.split(":")[-1]
        row = dict.fromkeys(KEYS)
        row.update(family=x["family"], date=m.group(0) if m else None, device=dev, unit=unit,
                   run=next((k for k in RUN_JA if base.startswith(k)), None),
                   variant="continuum" if "continuum" in rec else ("circuit" if base.startswith("hub-dt") else None),
                   r=x["r"], ratio=x["ratio"], reads=x["reads"],
                   folder=FOLDER.get(base, "results/" + rec.split("/scores")[0]))
        if (g := re.fullmatch(r"N(\d+)_th(\d+)_s(\d+)", unit)):
            row.update(qubits=int(g[1]), angle={"0785": "π/4", "1571": "π/2"}[g[2]], steps=int(g[3]),
                       layers=4 * int(g[3]))
        elif (g := re.fullmatch(r"L(\d+)_(?:T([\d.]+)_)?s(\d+)(?:_U(\d+))?", unit)):
            row.update(sites=int(g[1]), qubits=2 * int(g[1]), T=float(g[2]) if g[2] else None, steps=int(g[3]),
                       U=int(g[4]) if g[4] else 4)
        elif (g := re.fullmatch(r"(z106|w10|w17b?)_t(\d+)x?", unit)):
            row.update(obs=g[1], steps=int(g[2]))
        elif (g := re.fullmatch(r"q(\d\d)([fl]\d)_t(\d+)", unit)):
            row.update(arm=f"q{g[1]}{g[2]}", steps=int(g[3]))
        elif x["family"].startswith("daily"):
            row["problem"] = unit
        if (g := re.match(r"du(\d+)-", base)):
            row["qubits"] = int(g[1])
        row["layers"] = row["layers"] or layers.get((base, unit))
        rows.append(row)
    return rows


# ---------------------------------------------------------------- reading the question (fixed rules, closed)
def parse(q):
    """Return (conditions, unknown words, conflicts). Every character is taken by a rule or reported."""
    t = norm(q)
    c, conflicts = {}, []

    def take(key, val, span):
        nonlocal t
        if key in c and c[key] != val:
            conflicts.append(f"{LABEL[key]} {c[key]} と {val}")
        c[key] = val
        t = t[:span[0]] + " " * (span[1] - span[0]) + t[span[1]:]

    for key, rx, conv in PATTERNS:
        for g in list(re.finditer(rx, t)):
            take(key, conv(g), g.span())
    spell = sorted(((s, k, v) for k, v, ss in SYNONYMS for s in ss), key=lambda z: -len(z[0]))
    for s, k, v in spell:
        rx = (r"(?<![a-z0-9_])" if s[0].isascii() and s[0].isalnum() else "") + re.escape(s) + \
             (r"(?![a-z0-9_])" if s[-1].isascii() and s[-1].isalnum() else "")
        for g in list(re.finditer(rx, t)):
            take(k, v, g.span())
    for w in sorted(FILLER, key=len, reverse=True):
        t = t.replace(w, " ")
    unknown = t.split()
    return c, unknown, conflicts


def select(rows, c):
    return [r for r in rows if all(r.get(k) == v for k, v in c.items())]


# ---------------------------------------------------------------- writing the answer (fixed templates)
def num(v):
    return "値なし" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.3f}"


def show(k, v):
    return {"family": FAMILY_JA.get(v, v), "obs": OBS_JA.get(v, v), "run": RUN_JA.get(v, v),
            "variant": {"continuum": "連続極限の答え", "circuit": "回路の答え"}.get(v, v), "T": f"{v:g}" if isinstance(v, float) else v}.get(k, v)


def describe(r):
    p = [r["date"] or "日付なし", r["device"] or "装置不明", FAMILY_JA[r["family"]]]
    if r["run"]:
        p.append(RUN_JA[r["run"]])
    if r["problem"]:
        p.append(f"問題 {r['problem']}")
    if r["obs"]:
        p.append(f"観測量 {OBS_JA[r['obs']]}")
    if r["arm"]:
        p.append(f"腕 {r['arm']}")
    if r["sites"]:
        p.append(f"L={r['sites']}（{r['qubits']}量子ビット）")
    elif r["qubits"]:
        p.append(f"{r['qubits']}量子ビット")
    if r["U"] is not None:
        p.append(f"U={r['U']}")
    if r["T"] is not None:
        p.append(f"T={r['T']:g}")
    if r["angle"]:
        p.append(f"θ={r['angle']}")
    if r["steps"]:
        p.append(f"{r['steps']}ステップ" + (f"（CZ {r['layers']}層）" if r["layers"] else ""))
    if r["variant"]:
        p.append({"continuum": "連続極限の答えと照合", "circuit": "回路の答えと照合"}[r["variant"]])
    verdict = {True: "読めた", False: "読めなかった"}.get(r["reads"], "判定なし")
    return f"・{'、'.join(p)}：{verdict}（MSE/平均二乗 {num(r['ratio'])}、残存率 r {num(r['r'])}）　根拠 {r['folder']}"


def sort_key(r):
    return tuple("" if r[k] is None else (f"{r[k]:012.4f}" if isinstance(r[k], (int, float)) else str(r[k]))
                 for k in KEYS) + (r["unit"], r["folder"])


def answer(q, rows):
    t = norm(q)
    for kind, words in REFUSE.items():
        if any(w in t for w in words):
            return f"答えない：{kind}は扱えない。扱えるのは、記録された結果の照会だけ。"
    c, unknown, conflicts = parse(q)
    if unknown:
        return f"答えない：解釈できない語が含まれている（{'、'.join('「' + u + '」' for u in unknown)}）。"
    if conflicts:
        return f"答えない：条件がぶつかっている（{'；'.join(conflicts)}）。"
    if not c:
        return ("答えない：条件が読み取れなかった。日付（11月14日）、装置（fez / marrakesh / kingston）、種類（XX、ハバード、"
                "ユーティリティ、イジング、デイリー、双対ユニタリ）、大きさ（81量子ビット、L=20）、深さ（16ステップ、64層）、"
                "角度（π/4）のどれかを入れてほしい。")
    shown = "、".join(f"{LABEL[k]} {show(k, v)}" for k, v in c.items())
    hit = select(rows, c)
    if not hit:
        lines = [f"条件（{shown}）に合う記録はない。条件ごとの件数："]
        lines += [f"・{LABEL[k]} {show(k, v)} だけなら {len(select(rows, {k: v}))} 件" for k, v in c.items()]
        return "\n".join(lines)
    n_ok = sum(r["reads"] is True for r in hit)
    n_no = sum(r["reads"] is False for r in hit)
    head = f"条件（{shown}）に合う記録は {len(hit)} 件。読めた {n_ok}、読めなかった {n_no}。"
    if len(hit) - n_ok - n_no:
        head += f" 判定なし {len(hit) - n_ok - n_no}。"
    note = ["（記録の照会として答えた。走らせていない条件の見積もりはしない。）"] if re.search(r"読める(?!た)", t) else []
    if len(hit) > 12:
        out = [head]
        for k in KEYS:
            if k in c:
                continue
            vals = sorted({r[k] for r in hit if r[k] is not None}, key=lambda v: (str(type(v)), v))
            if 1 < len(vals) <= 12:
                out.append(f"・{LABEL[k]}で絞れる：{' / '.join(str(show(k, v)) for v in vals)}")
        return "\n".join(out + ["条件を足せば一件ずつ答える。"] + note)
    return "\n".join([head] + [describe(r) for r in sorted(hit, key=sort_key)] + note)


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import checks
        sys.exit(0 if checks.main() else 1)
    print(answer(" ".join(sys.argv[1:]), build_index()))
