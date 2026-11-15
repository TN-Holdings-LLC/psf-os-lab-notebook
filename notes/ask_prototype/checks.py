"""Checks of the deterministic answerer (prototype, 2026-11-15). Run: python notes/ask_prototype/ask.py --test

1. round trip: for every recorded row, a question is written mechanically from the row's own fields (spellings taken
   in turn from the normalisation dictionary); the answer must list that row, and only rows equal to it on every
   field; rows that no question can tell apart are counted and must be 0;
2. spellings: every spelling of every dictionary entry reads to its own value alone, inside a sentence and paired
   with every spelling of every other entry; stray words stop the answer;
3. edges: rows near the line (MSE / mean square 0.45-0.55 or r 0.27-0.32) print their stored verdict, and the stored
   verdict agrees with MSE <= mean square / 2; two runs on the same day are both listed and can be told apart;
   missing values (NaN, None) print as such; the answers do not depend on the order of the index;
4. refusals: 100 questions that must not be answered (why, the future, approximations, comparisons, words outside
   the rules) all start with "答えない".
Written by the same hand as the rules, so 2 and 4 show the rules do what they say, not that they cover every
question a person may write; the closed entrance (a word no rule takes stops the answer) is what covers the rest."""
import ask

DATE_FORMS = [lambda d: f"{int(d[5:7])}月{int(d[8:])}日", lambda d: d, lambda d: f"{int(d[5:7])}/{int(d[8:])}"]


def spellings(key, val):
    return [ss for k, v, ss in ask.SYNONYMS if k == key and v == val][0]


def question(row, i):
    """A question written from the row's fields; spellings and date forms rotate with i."""
    parts = []
    for k in ask.KEYS:
        v = row[k]
        if v is None:
            continue
        if k == "date":
            parts.append(DATE_FORMS[i % 3](v) + "の")
        elif k in ("device", "family", "angle", "run", "variant", "obs"):
            ss = spellings(k, v)
            parts.append(ss[i % len(ss)])
        elif k == "qubits":
            if row["sites"] is None:
                parts.append(f"{v}量子ビット" if i % 2 == 0 else f"N={v}")
        elif k == "sites":
            parts.append(f"L={v}" if i % 2 == 0 else f"{v}サイト")
        elif k == "U":
            parts.append(f"U={v}")
        elif k == "T":
            parts.append(f"T={v:g}")
        elif k == "steps":
            parts.append(f"{v}ステップ")
        elif k == "layers":
            if i % 2:
                parts.append(f"{v}層")
        elif k == "arm":
            parts.append(f"腕 {v}")
        elif k == "problem":
            parts.append(f"問題 {v}")
    return " ".join(parts) + (" は読めた？" if i % 2 == 0 else " の結果を教えて")


def same(a, b):
    return all(a[k] == b[k] for k in ask.KEYS)


def round_trip(rows):
    bad, twins = [], 0
    for i, row in enumerate(rows):
        if sum(same(row, o) for o in rows) > 1:
            twins += 1
        for j in (i, i + 1):                                     # two spellings per row
            q = question(row, j)
            a = ask.answer(q, rows)
            c, unk, conf = ask.parse(q)
            hit = ask.select(rows, c)
            if (a.startswith("答えない") or ask.describe(row) not in a or unk or conf
                    or any(not same(h, row) for h in hit)):
                bad.append((q, a.splitlines()[0]))
    print(f"1 round trip: {2 * len(rows)} questions from {len(rows)} rows, missed or not unique {len(bad)}; "
          f"rows no question can tell apart {twins}")
    for q, a in bad[:10]:
        print("   ", q, "->", a)
    return not bad and twins == 0


def spelling_checks(rows):
    bad = []
    entries = [(k, v, s) for k, v, ss in ask.SYNONYMS for s in ss]
    for k, v, s in entries:
        for q in (s, f"11月14日の{s}の結果は？", f"{s.upper()} は読めた？"):
            c, unk, conf = ask.parse(q)
            want = {k: v} if q == s or q.startswith(s.upper()) else {k: v, "date": "2026-11-14"}
            if c != want or unk or conf:
                bad.append((q, c, unk, conf))
    for k1, v1, s1 in entries:                                   # every pair from different entries
        for k2, v2, s2 in entries:
            if k1 == k2:
                continue
            c, unk, conf = ask.parse(f"{s1} の {s2}")
            if c != {k1: v1, k2: v2} or unk or conf:
                bad.append((f"{s1} の {s2}", c, unk, conf))
    refuse_words = [w for ws in ask.REFUSE.values() for w in ws]
    for k, v, sp in entries:                                     # a spelling must never trip a refusal
        bad += [("spelling contains a refusal word", sp, w) for w in refuse_words if w in sp]
    bad += [("filler contains a refusal word", f, w) for f in ask.FILLER for w in refuse_words if w in f]
    stray = ["fez の XX 81量子ビット 青い", "marrakesh で XX を速く", "XX 81量子ビット ぜんぶ", "fezz の XX",
             "ハバード L=20 6ステップ 本当に", "11月14日 XX 81量子ビット 64層 たぶん", "XXX は読めた？"]
    for q in stray:
        if not ask.answer(q, rows).startswith("答えない：解釈できない語"):
            bad.append((q, ask.answer(q, rows)))
    for q in ["XX π/4 π/2", "fez marrakesh の XX"]:
        if not ask.answer(q, rows).startswith("答えない：条件がぶつかっている"):
            bad.append((q, ask.answer(q, rows)))
    print(f"2 spellings: {len(entries)} spellings, {len(entries) * (len(entries) - 1)} pairs, {len(stray)} stray-word "
          f"and 2 conflict questions; wrong {len(bad)}")
    for b in bad[:10]:
        print("   ", b)
    return not bad


def lcg_orders(n, k):
    """k fixed permutations of range(n) from a linear congruential generator (no randomness)."""
    out, s = [], 12345
    for _ in range(k):
        idx = list(range(n))
        for i in range(n - 1, 0, -1):
            s = (1103515245 * s + 12345) % 2 ** 31
            j = s % (i + 1)
            idx[i], idx[j] = idx[j], idx[i]
        out.append(idx)
    return out


def edge_checks(rows):
    bad = []
    near = [r for r in rows if 0.45 <= r["ratio"] <= 0.55 or 0.27 <= r["r"] <= 0.32]
    for r in near:
        line = ask.describe(r)
        want = "読めた" if r["reads"] else "読めなかった"
        if f"：{want}（" not in line:
            bad.append(("verdict printed", line))
        if r["reads"] != (r["ratio"] <= 0.5):
            bad.append(("stored verdict against MSE <= msq / 2", line))
    a = ask.answer("11月14日の marrakesh で XX 81量子ビット 16ステップ π/4", rows)
    if not ("2 件" in a and "大きさの試験" in a and "光円錐の再試行" in a):
        bad.append(("same-day runs", a))
    for run in ("大きさの試験", "光円錐の再試行"):
        if "1 件" not in ask.answer(f"11月14日の marrakesh で XX 81量子ビット 16ステップ π/4 {run}", rows):
            bad.append(("one run", run))
    fake = [dict(rows[0], ratio=float("nan"), r=float("nan"), reads=None, folder="results/fake-nan"),
            dict(rows[0], ratio=None, r=None, reads=None, folder="results/fake-none")]
    for f in fake:
        line = ask.describe(f)
        if "判定なし" not in line or "値なし" not in line:
            bad.append(("missing values", line))
    qs = [question(r, i) for i, r in enumerate(rows)] + ["XX", "ハバード", "11月14日", "fez の XX π/4"]
    ref = [ask.answer(q, rows) for q in qs]
    for order in lcg_orders(len(rows), 10):
        shuffled = [rows[i] for i in order]
        if [ask.answer(q, shuffled) for q in qs] != ref:
            bad.append(("order", "answers changed with the order of the index"))
            break
    if [ask.answer(q, rows) for q in qs] != ref:
        bad.append(("twice", "answers changed on a second call"))
    print(f"3 edges: {len(near)} rows near the line, same-day runs, 2 rows with missing values, "
          f"{len(qs)} questions over 10 orders of the index; wrong {len(bad)}")
    for b in bad[:10]:
        print("   ", b)
    return not bad


NEG_STEMS = [
    "なぜ12ステップで読めなくなった？", "どうして81量子ビットの方が悪いの？", "読めなかった理由は？", "原因は何？",
    "明日のfezは読める？", "来週のmarrakeshは読める？", "次回は読めそう？", "今後どうなる？",
    "だいたい何層までいける？", "およそ何ステップまで読める？", "平均の r は？", "全体として傾向は？",
    "fezとmarrakeshどっちが良い？", "一番読めた装置は？", "比べてどう？", "おすすめの装置は？",
    "これは本当に正しい？", "r を 0.3 にするには？", "64層を読めるようにして", "論文に書いていい？",
    "このノイズの正体は？", "XX をもう一度走らせて", "答えを推測して", "まあまあ読めた？", "要するにどういうこと？",
]
NEG_CONTEXT = ["", "fez の XX ", "11月14日の marrakesh で ", "ハバード L=20 "]


def refusal_checks(rows):
    qs = [ctx + stem for stem in NEG_STEMS for ctx in NEG_CONTEXT]
    bad = [(q, ask.answer(q, rows).splitlines()[0]) for q in qs if not ask.answer(q, rows).startswith("答えない")]
    print(f"4 refusals: {len(qs)} questions that must not be answered; answered {len(bad)}")
    for b in bad[:10]:
        print("   ", b)
    return not bad


def main():
    rows = ask.build_index()
    ok = [round_trip(rows), spelling_checks(rows), edge_checks(rows), refusal_checks(rows)]
    print("ALL PASS" if all(ok) else "FAIL")
    return all(ok)
