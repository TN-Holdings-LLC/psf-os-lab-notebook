"""A deterministic answerer for result lookups (prototype, 2026-11-15).

No language model and no probability: a Japanese question is read by fixed rules into conditions, the conditions
select rows of the notebook's records, and the answer is written from fixed sentence templates. The same question
always gives the same answer, and every line names its record folder.

The entrance is closed: every character of a question must be taken by a pattern or by a listed filler word. A word
no rule takes stops the answer ("解釈できない語"), so nothing is silently ignored. Questions of a type the prototype
does not answer (why, the future, approximations, comparisons) are refused before any lookup.

Scope: the 179 results with an exact answer and a declared verdict in notes/paper9_yardstick/line_all.json
(2026-11-05 to 2026-11-14), each with the controls of its job as recorded (floor, mirror, sentinel), and the
whole-device floor nights (results/full-floor-*), and every line of the daily record (results/daily/RECORD.md),
days not run and problems refused included. Relative dates ("最新", "前回", "昨日") are resolved from the records'
own dates and the resolution is printed. The verdict printed is the declared one stored in the record, never
recomputed from r; control values are printed as recorded, under the record's own definition.

usage: python notes/ask_prototype/ask.py "11月14日の marrakesh で XX 81量子ビット 16ステップ π/4 は読めた？"
       python notes/ask_prototype/ask.py --test        (all checks of notes/ask_prototype/checks.py)"""
import json
import math
import os
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
    ("kind", "fullfloor", ["全面フロア", "full-floor", "full floor"]),
    ("show", "floor", ["フロア", "floor"]),
    ("show", "mirror", ["ミラー", "mirror"]),
    ("show", "sentinel", ["センチネル", "sentinel"]),
    ("show", "controls", ["対照", "コントロール"]),
    ("mode", "estimate", ["見積もり", "見積り", "見積", "読めそう"]),
    ("mode", "compile", ["コンパイル結果", "コンパイル", "回路の中身"]),
    ("mode", "ideal", ["理想値", "厳密値", "シミュレータ", "シミュレーション"]),
    ("rel", "latest", ["最新", "いちばん新しい"]),
    ("rel", "previous", ["前回", "ひとつ前", "一つ前"]),
    ("rel", "yesterday", ["昨日", "きのう"]),
]
# Patterns with a number: (condition, regex, converter).
PATTERNS = [
    ("date", r"(?:2026\s*[-/年]\s*)?(\d{1,2})\s*[月/-]\s*(\d{1,2})\s*日?",
     lambda g: f"2026-{int(g[1]):02d}-{int(g[2]):02d}"),
    ("arm", r"q(\d\d)([fl]\d)", lambda g: f"q{g[1]}{g[2]}"),
    ("problem", r"(?<![a-z0-9])(fx-a|d0\d|user)(?![a-z0-9])", lambda g: g[1].upper() if g[1] != "user" else "user"),
    ("qubits", r"(\d+)\s*(?:量子ビット|qubits?|ビット)", lambda g: int(g[1])),
    ("qubits", r"(?<![a-z])n\s*=\s*(\d+)", lambda g: int(g[1])),
    ("sites", r"(\d+)\s*サイト", lambda g: int(g[1])),
    ("sites", r"(?<![a-z])l\s*=\s*(\d+)", lambda g: int(g[1])),
    ("T", r"(?<![a-z])t\s*=\s*(\d+(?:\.\d+)?)", lambda g: float(g[1])),
    ("U", r"(?<![a-z])u\s*=\s*(\d+)", lambda g: int(g[1])),
    ("steps", r"(\d+)\s*(?:ステップ|steps?)", lambda g: int(g[1])),
    ("layers", r"(\d+)\s*層", lambda g: int(g[1])),
    ("qubit", r"(\d+)\s*番", lambda g: int(g[1])),
]
# Words that carry no condition. Removed after every pattern; anything left is an unknown word.
FILLER = ["読めましたか", "読めなかった", "読めたか", "読めた", "読めている", "読めてる", "読める", "結果", "判定", "教えて",
          "ください", "どうだった", "どうなった", "どうなってた", "どうなってる", "いくつ", "ですか", "でした", "記録", "装置", "角度", "腕", "問題", "の", "で", "は", "を", "が", "に",
          "と", "も", "か", "、", "。", "?", "!", "・", ",", "(", ")", "「", "」", ":"]
# Question types this prototype does not answer, by kind. Checked before anything else.
REFUSE = {
    "理由を問う質問": ["なぜ", "どうして", "なんで", "理由", "原因", "せい", "何が効", "どういう仕組"],
    "未来や予測を問う質問": ["明日", "明後日", "あさって", "来週", "来月", "今後", "これから", "次回", "将来",
                     "予測", "予想", "見込", "読めるだろう", "なら読める"],
    "おおよその要約を問う質問": ["だいたい", "大体", "およそ", "くらい", "ぐらい", "程度", "傾向", "平均", "一般",
                       "普通は", "どこまで", "何層まで", "何ステップまで", "目安", "ざっくり", "全体として", "まあまあ",
                       "要するに"],
    "比較や評価を問う質問": ["どっち", "どちら", "比べ", "比較", "一番", "最も", "良い", "悪い", "良く", "悪く", "おすすめ",
                   "勝", "より"],
    "扱えない相対日付": ["先週", "先月", "去年", "おととい", "一昨日", "さっき", "この前"],
    "操作を頼む文": ["して", "させて", "走らせて", "回して", "やって", "書いて", "作って", "直して", "消して"],
}
LABEL = {"date": "日付", "device": "装置", "family": "種類", "qubits": "量子ビット数", "sites": "サイト数",
         "steps": "ステップ数", "layers": "CZ層数", "angle": "角度", "U": "U", "T": "総時間T", "run": "試験",
         "variant": "照合先", "obs": "観測量", "arm": "腕", "problem": "問題", "kind": "記録の種類",
         "qubit": "量子ビット番号", "show": "表示", "rel": "相対日付", "mode": "求めるもの"}
KEYS = ["family", "date", "device", "run", "problem", "obs", "arm", "qubits", "sites", "U", "T", "angle", "steps",
        "layers", "variant"]


def norm(s):
    return unicodedata.normalize("NFKC", s).lower()


# ---------------------------------------------------------------- the controls of each result's job
def _load(path, cache={}):
    if path not in cache:
        try:
            cache[path] = json.load(open(path))
        except FileNotFoundError:
            cache[path] = None
    return cache[path]


def controls(x, row):
    """Floor, mirror and sentinel of the job of one result, as its record stores them (None where it does not)."""
    rec, item, fam = x["record"], x["item"], x["family"]
    base, unit = rec.split("/")[0], row["unit"]
    out = dict(floor=None, mirror=None, sentinel=None, floor_kind="mean", mirror_range=None)
    if fam in ("XX chain", "Hubbard") and not base.startswith("twin-"):
        d = _load(f"results/{base}/{item.split(':')[0]}/scores.json")
        c = d and d["circuits"].get(unit)
        if c:
            out.update(floor=c.get("floor"), mirror=c.get("mirror"), sentinel=c.get("sentinel"))
    elif base.startswith("twin-"):
        d = _load(f"results/{base}/ibm_marrakesh_{'xx' if fam == 'XX chain' else 'hub'}/twin_scores.json")
        p = d and d["pairs"].get(unit)
        if p:
            out.update(floor=p.get("floor"), mirror=p.get("mirror"))
    elif fam.startswith("daily"):
        d = _load(f"results/{rec}/run/scores.json")
        p = d and d["problems"].get(unit)
        if p:
            out.update(floor=p.get("floor_mean"), mirror=p.get("mirror_mean"), sentinel=d.get("sentinel"))
    elif fam == "IBM 2023 utility":
        d = _load(f"{FOLDER[base]}/ibm_fez/scores.json")
        o = d and d["observables"].get(unit)
        if o:
            out.update(floor=o.get("floor"), mirror=o.get("mirror"), sentinel=d.get("sentinel"), floor_kind="parity")
    elif fam.startswith("Ising"):
        d = _load(f"{FOLDER[base]}/ibm_fez/scores.json")
        a = d and d["arms"].get(unit)
        if a:
            out.update(floor=a.get("floor_mean"), mirror=a.get("mirror_mean"), sentinel=a.get("sentinel"))
    elif fam.startswith("dual"):
        d = _load(f"results/{rec}/run/scores.json")
        if d:
            pts = d["points"].values()
            fl = [p["floor_mean"] for p in pts]
            mi = [p["mirror_mean"] for p in pts]
            out.update(floor=sum(fl) / len(fl), floor_kind="mean over the curve", mirror_range=(min(mi), max(mi)),
                       sentinel="、".join(f"{k} {v}" for k, v in sorted(d["sentinels"].items())))
    return out


def build_fullfloor():
    """One row per whole-device floor night: medians and the per-qubit values of 1 - z(|0>) and 1 + z(|1>)."""
    import glob
    rows = []
    for f in sorted(glob.glob("results/full-floor-2026-*/*_floor/full_floor.json")):
        d = json.load(open(f))
        dev = f.split("/")[2].rsplit("_floor", 1)[0]
        rows.append(dict(kind="fullfloor", date=re.search(r"2026-\d\d-\d\d", f).group(0), device=dev,
                         m0=d["floor0_median"], m1=d["floor1_median"], n=d["qubits_measured"],
                         qubits={int(q): v for q, v in d["qubits"].items()}, folder=os.path.dirname(f)))
    return rows


def build_daily():
    """Every line of the daily record, as written (days not run and refused problems included)."""
    head, rows = None, []
    for line in open("results/daily/RECORD.md"):
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if line.startswith("| date (CET) | device | problem | RUNS"):
            head = cells
        elif head and not line.startswith("|"):
            break                                       # the judged table ends; later tables are reported beside
        elif head and line.startswith("| 2026-"):
            d = dict(zip(head, cells))
            prob = d["problem"].split(" ")[0]
            rows.append(dict(date=d["date (CET)"], device=d["device"] if d["device"] != "-" else None,
                             problem=prob if prob != "-" else None, runs=d["RUNS"], reads=d["READS"],
                             agrees=d["AGREES"], beats=d["BEATS"], diff=d["M - M_exact"],
                             mse=d["MSE / trivial guess"], floor=d["floor"], sentinel=d["sentinel"], job=d["job"]))
    return rows


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
            # results/daily/2026-11-06/README.md: FX-A run alone is run2d's single-circuit form, tag "user"
            row["problem"] = "FX-A" if unit == "user" else unit
        if (g := re.match(r"du(\d+)-", base)):
            row["qubits"] = int(g[1])
        row["layers"] = row["layers"] or layers.get((base, unit))
        row["controls"] = controls(x, row)
        rows.append(row)
    return rows


# ---------------------------------------------------------------- reading the question (fixed rules, closed)
def parse(q, leftover=False):
    """Return (conditions, unknown words, conflicts). Every character is taken by a rule or reported.
    With leftover=True also the normalised question with every taken character blanked (same length) and the
    character spans each condition was read from."""
    t = norm(q)
    c, conflicts = {}, []

    shows = set()
    spans = {}

    def take(key, val, span):
        nonlocal t
        spans.setdefault(key, []).append(span)
        if key == "show":
            shows.add(val)
            t = t[:span[0]] + " " * (span[1] - span[0]) + t[span[1]:]
            return
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
        t = t.replace(w, " " * len(w))
    unknown = t.split()
    if shows:
        c["show"] = tuple(sorted({"floor", "mirror", "sentinel"} if "controls" in shows else shows))
    return (c, unknown, conflicts, t, spans) if leftover else (c, unknown, conflicts)


def select(rows, c):
    return [r for r in rows if all(r.get(k) == v for k, v in c.items() if k != "show")]


# ---------------------------------------------------------------- writing the answer (fixed templates)
def num(v):
    return "値なし" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.3f}"


def show(k, v):
    return {"family": FAMILY_JA.get(v, v), "obs": OBS_JA.get(v, v), "run": RUN_JA.get(v, v),
            "variant": {"continuum": "連続極限の答え", "circuit": "回路の答え"}.get(v, v),
            "kind": {"fullfloor": "全面フロア"}.get(v, v), "rel": {"latest": "最新", "previous": "前回",
                                                              "yesterday": "昨日"}.get(v, v), "T": f"{v:g}" if isinstance(v, float) else v}.get(k, v)


ORDER = ["kind", "date", "device", "family", "run", "problem", "obs", "arm", "qubits", "sites", "U", "T", "angle",
         "steps", "layers", "variant", "qubit"]


def cond_text(c, skip=("show",)):
    """The conditions in one fixed order, whatever the order of the words in the question."""
    return "、".join(f"{LABEL[k]} {show(k, c[k])}" for k in ORDER if k in c and k not in skip)


def signed(v):
    return "記録になし" if v is None else f"{v:+.3f}"


def control_text(r, show):
    k = r["controls"]
    out = []
    if "floor" in show:
        out.append({"mean": "フロア ", "parity": "フロア（偶奇） ", "mean over the curve": "フロア（曲線の平均） "}
                   [k["floor_kind"]] + signed(k["floor"]))
    if "mirror" in show:
        out.append(f"ミラー {signed(k['mirror_range'][0])}〜{signed(k['mirror_range'][1])}（深さで変わる）"
                   if k["mirror_range"] else ("ミラー（偶奇） " if k["floor_kind"] == "parity" else "ミラー ")
                   + signed(k["mirror"]))
    if "sentinel" in show:
        out.append(f"センチネル {k['sentinel'] or '記録になし'}")
    return "、".join(out)


def describe(r, show=()):
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
    ctl = f"［{control_text(r, show)}］" if show else ""
    return (f"・{'、'.join(p)}：{verdict}（MSE/平均二乗 {num(r['ratio'])}、残存率 r {num(r['r'])}）{ctl}"
            f"　根拠 {r['folder']}")


def sort_key(r):
    return tuple("" if r[k] is None else (f"{r[k]:012.4f}" if isinstance(r[k], (int, float)) else str(r[k]))
                 for k in KEYS) + (r["unit"], r["folder"])


FF_NOTE = "（全面フロア：何もしない回路で、1 − z(|0⟩) と 1 + z(|1⟩) を量子ビットごとに測った値。理想は 0。）"
CONTROL_NOTE = ("（フロア：同じ回路から非対角の1量子ビットゲートを外した回路、ミラー：回路のあとに逆回路を続けた回路。"
                "値は測った量子ビットの ⟨Z⟩ の平均で、ユーティリティでは観測量の量子ビットの偶奇。どちらも理想は +1。"
                "センチネル：同じジョブの見張り回路の、記録どおりの判定。）")


def answer_fullfloor(c, ff):
    extra = [k for k in c if k not in ("kind", "date", "device", "qubit", "show")]
    if extra:
        return f"答えない：全面フロアには使えない条件がある（{'、'.join(LABEL[k] for k in extra)}）。"
    hit = [r for r in ff if all(r[k] == c[k] for k in ("date", "device") if k in c)]
    shown = cond_text(c, skip=("kind", "show"))
    if not hit:
        return f"全面フロアの記録で条件（{shown or 'なし'}）に合うものはない。記録がある夜：" + \
            " / ".join(f"{r['date']} {r['device']}" for r in ff) + "。"
    out = [f"全面フロアの記録で条件（{shown or 'なし'}）に合うものは {len(hit)} 件。"]
    for r in sorted(hit, key=lambda r: (r["date"], r["device"])):
        if "qubit" in c:
            v = r["qubits"].get(c["qubit"])
            body = ("その量子ビットは測っていない" if v is None else
                    f"量子ビット {c['qubit']}：1 − z(|0⟩) {v['floor0']:.4f}、1 + z(|1⟩) {v['floor1']:.4f}")
        else:
            body = f"{r['n']}量子ビット、1 − z(|0⟩) 中央値 {r['m0']:.4f}、1 + z(|1⟩) 中央値 {r['m1']:.4f}"
        out.append(f"・{r['date']}、{r['device']}、全面フロア：{body}　根拠 {r['folder']}")
    return "\n".join(out + [FF_NOTE])


def resolve_rel(c, dates_all, dates_hit):
    """Turn "最新" / "前回" / "昨日" into a date. Returns (date or None, sentence saying how it was read)."""
    rel = c.pop("rel")
    if "date" in c:
        return None, f"答えない：日付 {c['date']} と相対日付が両方ある。"
    if rel == "yesterday":
        import datetime
        top = max(dates_all)
        d = (datetime.date.fromisoformat(top) - datetime.timedelta(days=1)).isoformat()
        return d, f"（「昨日」は、記録の最も新しい日 {top} の前日 {d} と読んだ。）"
    ds = sorted(set(dates_hit), reverse=True)
    k = 0 if rel == "latest" else 1
    if len(ds) <= k:
        return None, f"答えない：条件に合う記録の日付が {len(ds)} 日分しかなく、「{'最新' if k == 0 else '前回'}」が決まらない。"
    return ds[k], f"（「{'最新' if k == 0 else '前回'}」は、条件に合う記録の日付のうち{'最も新しい' if k == 0 else '2番目に新しい'}日 {ds[k]} と読んだ。）"


def answer_daily(c, rows, daily):
    extra = [k for k in c if k not in ("family", "date", "device", "problem", "show")]
    if extra:
        return f"答えない：デイリー記録には使えない条件がある（{'、'.join(LABEL[k] for k in extra)}）。"
    sel = [d for d in daily if all(d[k] == c[k] for k in ("date", "device", "problem") if k in c)
           or (d["device"] is None and "date" in c and d["date"] == c["date"] and set(c) <= {"family", "date", "show"})]
    shown = cond_text(c)
    if not sel:
        return f"デイリー記録で条件（{shown}）に合う行はない。"
    rmap = {(r["date"], r["device"], r["problem"]): r for r in rows if r["family"].startswith("daily")}
    out = [f"デイリー記録で条件（{shown}）に合う行は {len(sel)} 行。"]
    for d in sel:
        if d["device"] is None:
            out.append(f"・{d['date']}：走らせていない　{d['job']}　根拠 results/daily/RECORD.md")
            continue
        if d["runs"] == "REFUSED":
            out.append(f"・{d['date']}、{d['device']}、デイリー記録、問題 {d['problem']}：送らなかった（REFUSED）　{d['job']}"
                       f"　根拠 results/daily/RECORD.md")
            continue
        r = rmap.get((d["date"], d["device"], d["problem"]))
        rtxt = f"、残存率 r {num(r['r'])}" if r else ""
        out.append(f"・{d['date']}、{d['device']}、デイリー記録、問題 {d['problem']}：実行 {d['runs']}、{d['reads']}、"
                   f"{d['agrees']}、{d['beats']}、M − M_exact {d['diff']}、MSE / 自明な推測 {d['mse']}、"
                   f"フロア {d['floor']}、センチネル {d['sentinel']}{rtxt}　根拠 results/daily/RECORD.md（ジョブ {d['job']}）")
    return "\n".join(out + ["（AGREES：|M − M_exact| ≤ 0.05。BEATS：MSE が自明な推測より小さい。記録どおり。）"])


_BACKTEST = {}


def answer_tools(c, rows):
    """Compile, ideal values and the estimate, XX chain only (notes/ask_prototype/xxtools.py)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import xxtools as X
    mode = c["mode"]
    name = {"estimate": "見積もり", "compile": "コンパイル", "ideal": "理想値"}[mode]
    if c.get("family", "XX chain") != "XX chain":
        return f"答えない：{name}は、今は XX 鎖だけ扱える。"
    bad = [k for k in c if k not in ("mode", "family", "device", "qubits", "angle", "steps", "layers")]
    if bad:
        return f"答えない：{name}には使えない条件がある（{'、'.join(LABEL[k] for k in bad)}）。記録を見るなら照会の形で聞いてほしい。"
    steps = c.get("steps")
    if "layers" in c:
        if c["layers"] % 4:
            return "答えない：XX 鎖の CZ 層数は 4 の倍数（1ステップ 4 層）。"
        if steps is not None and steps * 4 != c["layers"]:
            return f"答えない：{steps}ステップは CZ {steps * 4} 層で、{c['layers']}層とぶつかる。"
        steps = c["layers"] // 4
    need = ["qubits", "angle"] + (["device"] if mode != "ideal" else [])
    missing = [LABEL[k] for k in need if k not in c] + (["ステップ数か CZ 層数"] if steps is None else [])
    if missing:
        return f"答えない：{name}には {'、'.join(missing)} が要る。"
    n, angle, dev = c["qubits"], c["angle"], c.get("device")
    if n < 2:
        return "答えない：量子ビット数が小さすぎる。"
    title = f"XX鎖 {n}量子ビット、θ={angle}、{steps}ステップ（CZ {4 * steps}層）" + (f"、{dev}" if dev else "")
    out = []
    if mode in ("compile", "estimate"):
        comp, why = X.compile_xx(dev, n, angle, steps)
        if comp is None:
            return f"{name}：{title}\n・コンパイル：{why}"
        lab = comp["labels"]
        out.append(f"・コンパイル（{dev} のノートブック内で最新の装置記録 {comp['fetched'].split('(')[-1].rstrip(')')}、"
                   f"校正 {comp['calibration']}）：鎖 {len(lab)}量子ビット（{lab[0]}〜{lab[-1]}）、CZ {comp['cz']}、"
                   f"CZ の深さ {comp['cz_depth']}、記録の故障量子ビット {comp['failed_qubits']} と故障結合 "
                   f"{comp['failed_couplers']} を避けて配置、1ジョブのモデル時間 {comp['model_seconds']} 秒　根拠 {comp['record']}")
    if mode in ("ideal", "estimate"):
        ide = X.ideal_xx(n, angle, steps)
        head = "、".join(f"{v:+.4f}" for v in ide["z"][:8])
        out.append(f"・理想値（自由フェルミオンの厳密計算、雑音なし、標本化なし）：⟨Z⟩ の平均二乗 {ide['mean_square']:.4f}、"
                   f"平均 {ide['mean']:+.4f}、鎖の先頭から {head} …")
    if mode == "estimate":
        est, why = X.estimate_xx(rows, dev, n, angle, 4 * steps)
        if est is None:
            out.append(f"・残存率 r の見積もり：出さない（{why}）")
        else:
            if "bt" not in _BACKTEST:
                _BACKTEST["bt"] = X.backtest(rows)
            b = _BACKTEST["bt"]
            ser = "、".join(f"{d} {RUN_JA.get(run, '') or '記録'} {q}量子ビット θ={a}" for d, run, q, a in est["series"])
            out.append(f"・残存率 r の見積もり（測った値ではない）：{est['lo']:.3f}〜{est['hi']:.3f}、{est['side']}"
                       f"（{est['basis']}の記録 {est['n_series']} 系列を CZ 層で補間：{ser}）")
            out.append(f"・この見積もり方の過去の当たり方（XX の記録 {b['results']} 件を、それぞれ自分の系列を除いた記録で見積もった"
                       f"場合）：実際の r が幅に入った {b['in_range']} 件、0.293 のどちら側かが当たった {b['side_right']} / {b['sided']} 件")
            notes = ["形のずれ（rest）は見積もっていない", "装置の日ごとの違いは記録の系列の分しか入っていない"]
            if est["beyond_size"]:
                notes.append("記録より大きい（小さい）鎖：大きさの試験では大きい鎖ほど r が低く、下に外れうる")
            out.append(f"・見積もりに入っていないもの：{'、'.join(notes)}")
    return "\n".join([f"{name}：{title}"] + out)


def answer(q, rows, ff=None, daily=None):
    t = norm(q)
    for kind, words in REFUSE.items():
        if any(w in t for w in words):
            return f"答えない：{kind}は扱えない。扱えるのは、記録された結果の照会と、XX 鎖のコンパイル・理想値・見積もりだけ。"
    c, unknown, conflicts = parse(q)
    if unknown:
        return f"答えない：解釈できない語が含まれている（{'、'.join('「' + u + '」' for u in unknown)}）。"
    if conflicts:
        return f"答えない：条件がぶつかっている（{'；'.join(conflicts)}）。"
    if not c:
        return ("答えない：条件が読み取れなかった。日付（11月14日）、装置（fez / marrakesh / kingston）、種類（XX、ハバード、"
                "ユーティリティ、イジング、デイリー、双対ユニタリ）、大きさ（81量子ビット、L=20）、深さ（16ステップ、64層）、"
                "角度（π/4）のどれかを入れてほしい。")
    if "mode" in c:
        return answer_tools(c, rows)
    pre = ""
    daily = build_daily() if daily is None else daily
    if "rel" in c:
        ff = build_fullfloor() if ff is None else ff
        # "昨日": the day before the newest date of all records the answerer reads (results, daily lines, floors)
        dates_all = [r["date"] for r in rows if r["date"]] + [d["date"] for d in daily] + [r["date"] for r in ff]
        if c.get("kind") == "fullfloor":
            pool = [r for r in ff if all(r[k] == c[k] for k in ("device",) if k in c)]
        elif c.get("family") == "daily (P4 chain)":
            pool = [d for d in daily if all(d[k] == c[k] for k in ("device", "problem") if k in c)]
        else:
            pool = select(rows, {k: v for k, v in c.items() if k != "rel"})
        d, pre = resolve_rel(c, dates_all, [r["date"] for r in pool if r["date"]])
        if d is None:
            return pre
        c["date"] = d
    if c.get("kind") == "fullfloor":
        return "\n".join(x for x in (answer_fullfloor(c, build_fullfloor() if ff is None else ff), pre) if x)
    if c.get("family") == "daily (P4 chain)":
        return "\n".join(x for x in (answer_daily(c, rows, daily), pre) if x)
    if "qubit" in c:
        return "答えない：量子ビット番号（〜番）は全面フロアの照会でだけ使える。"
    want = c.get("show", ())
    if not [k for k in c if k != "show"]:
        return "答えない：表示だけで条件がない。日付・装置・種類などの条件を入れてほしい。"
    shown = cond_text(c)
    hit = select(rows, c)
    if not hit:
        lines = [f"条件（{shown}）に合う記録はない。条件ごとの件数："]
        lines += [f"・{LABEL[k]} {show(k, c[k])} だけなら {len(select(rows, {k: c[k]}))} 件" for k in ORDER if k in c]
        return "\n".join(lines + ([pre] if pre else []))
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
        return "\n".join(out + ["条件を足せば一件ずつ答える。"] + note + ([pre] if pre else []))
    return "\n".join([head] + [describe(r, want) for r in sorted(hit, key=sort_key)] + note +
                     ([CONTROL_NOTE] if want else []) + ([pre] if pre else []))


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import checks
        sys.exit(0 if checks.main() else 1)
    print(answer(" ".join(sys.argv[1:]), build_index()))
