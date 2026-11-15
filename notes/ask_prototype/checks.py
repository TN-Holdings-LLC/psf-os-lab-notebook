"""Checks of the deterministic answerer (prototype, 2026-11-15). Run: python notes/ask_prototype/ask.py --test

1. round trip: for every recorded row, a question is written mechanically from the row's own fields (spellings taken
   in turn from the normalisation dictionary); the answer must list that row, and only rows equal to it on every
   field; rows that no question can tell apart are counted and must be 0;
2. spellings: every spelling of every dictionary entry reads to its own value alone, inside a sentence and paired
   with every spelling of every other entry; stray words stop the answer;
3. edges: rows near the line (MSE / mean square 0.45-0.55 or r 0.27-0.32) print their stored verdict, and the stored
   verdict agrees with MSE <= mean square / 2; two runs on the same day are both listed and can be told apart;
   missing values (NaN, None) print as such; the answers do not depend on the order of the index;
6. the daily record and relative dates: every line of results/daily/RECORD.md (days not run and refused problems
   included) answers with its own line; "最新" / "前回" / "昨日" give the same answer as the date they stand for,
   computed here independently, for every family and device;
5. controls: every row's question with "対照" prints its floor, mirror and sentinel or says "記録になし"; every
   qubit of every whole-device floor night answers with the value read again from its file;
4. refusals: 100 questions that must not be answered (why, the future, approximations, comparisons, words outside
   the rules) all start with "答えない".
Written by the same hand as the rules, so 2 and 4 show the rules do what they say, not that they cover every
question a person may write; the closed entrance (a word no rule takes stops the answer) is what covers the rest."""
import ask

DATE_FORMS = [lambda d: f"{int(d[5:7])}月{int(d[8:])}日", lambda d: d, lambda d: f"{int(d[5:7])}/{int(d[8:])}"]


def spellings(key, val):
    return [ss for k, v, ss in ask.SYNONYMS if k == key and v == val][0]


def question(row, i, reverse=False):
    """A question written from the row's fields; spellings and date forms rotate with i."""
    parts = question_parts(row, i)
    end = " は読めた？" if i % 2 == 0 else " の結果を教えて"
    return (end.strip() + " " + " ".join(reversed(parts))) if reverse else " ".join(parts) + end


def question_parts(row, i):
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
    return parts


def same(a, b):
    return all(a[k] == b[k] for k in ask.KEYS)


def daily_line(row, a):
    """The daily answer lists the row when one line names its date, device, problem and r."""
    return any(row["date"] in ln and row["device"] in ln and f"問題 {row['problem']}：" in ln
               and f"残存率 r {ask.num(row['r'])}" in ln for ln in a.splitlines())


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
            listed = daily_line(row, a) if row["family"].startswith("daily") else ask.describe(row) in a
            if a.startswith("答えない") or not listed or unk or conf or any(not same(h, row) for h in hit):
                bad.append((q, a.splitlines()[0]))
    print(f"1 round trip: {2 * len(rows)} questions from {len(rows)} rows, missed or not unique {len(bad)}; "
          f"rows no question can tell apart {twins}")
    for q, a in bad[:10]:
        print("   ", q, "->", a)
    return not bad and twins == 0


def expect(k, v):
    if k == "show":
        return {"show": ("floor", "mirror", "sentinel") if v == "controls" else (v,)}
    return {k: v}


def spelling_checks(rows):
    bad = []
    entries = [(k, v, s) for k, v, ss in ask.SYNONYMS for s in ss]
    for k, v, s in entries:
        for q in (s, f"11月14日の{s}の結果は？", f"{s.upper()} は読めた？"):
            c, unk, conf = ask.parse(q)
            want = dict(expect(k, v)) if q == s or q.startswith(s.upper()) else {**expect(k, v), "date": "2026-11-14"}
            if c != want or unk or conf:
                bad.append((q, c, unk, conf))
    for k1, v1, s1 in entries:                                   # every pair from different entries
        for k2, v2, s2 in entries:
            if k1 == k2:
                continue
            c, unk, conf = ask.parse(f"{s1} の {s2}")
            if c != {**expect(k1, v1), **expect(k2, v2)} or unk or conf:
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
    for i, r in enumerate(rows):                                 # phrase order does not change the answer
        if ask.answer(question(r, i, reverse=True), rows) != ref[i]:
            bad.append(("word order", question(r, i, reverse=True)))
    print(f"3 edges: {len(near)} rows near the line, same-day runs, 2 rows with missing values, "
          f"{len(qs)} questions over 10 orders of the index, the row questions also in reversed phrase order; wrong {len(bad)}")
    for b in bad[:10]:
        print("   ", b)
    return not bad


NEG_STEMS = [
    "先週のfezは？", "おとといのデイリーは？", "最新の明日の予定は？", "前回より良くなった？",
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
    print(f"4 refusals: {len(qs)} questions ({len(NEG_STEMS)} stems x {len(NEG_CONTEXT)} contexts) that must not be "
          f"answered; answered {len(bad)}")
    for b in bad[:10]:
        print("   ", b)
    return not bad


def control_checks(rows):
    import json
    bad, missing = [], {}
    for i, row in enumerate(rows):
        q = question(row, i).replace(" は読めた？", " の対照").replace(" の結果を教えて", " の対照")
        a = ask.answer(q, rows)
        line = ask.describe(row, ("floor", "mirror", "sentinel"))
        if row["family"].startswith("daily"):
            if not daily_line(row, a) or "センチネル" not in a:
                bad.append((q, a.splitlines()[0]))
        elif line not in a or "［" not in line:
            bad.append((q, a.splitlines()[0]))
        for part in ask.control_text(row, ("floor", "mirror", "sentinel")).split("、"):
            if "記録になし" in part:
                missing[(row["folder"], part.split(" ")[0])] = missing.get((row["folder"], part.split(" ")[0]), 0) + 1
    ff = ask.build_fullfloor()
    nq = 0
    for night in ff:
        d = json.load(open(night["folder"] + "/full_floor.json"))
        for qb, v in d["qubits"].items():
            nq += 1
            a = ask.answer(f"{night['date']} の {night['device']} 全面フロア {qb}番", rows, ff)
            want = f"量子ビット {qb}：1 − z(|0⟩) {v['floor0']:.4f}、1 + z(|1⟩) {v['floor1']:.4f}　根拠 {night['folder']}"
            if want not in a or "1 件" not in a:
                bad.append((qb, a.splitlines()[0]))
    for q, start in [("全面フロア XX", "答えない：全面フロアには使えない条件"), ("XX 27番", "答えない：量子ビット番号"),
                     ("フロア", "答えない：表示だけ"), ("12月1日の全面フロア", "全面フロアの記録で条件")]:
        if not ask.answer(q, rows).startswith(start):
            bad.append((q, ask.answer(q, rows).splitlines()[0]))
    print(f"5 controls: {len(rows)} rows with their job's controls, {nq} qubits of {len(ff)} whole-device floor "
          f"nights, 4 edge questions; wrong {len(bad)}; not in the record: " +
          ("; ".join(f"{k[0]} {k[1]} x{n}" for k, n in sorted(missing.items())) or "none"))
    for b in bad[:10]:
        print("   ", b)
    return not bad


def daily_and_relative(rows):
    import datetime
    bad = []
    daily = ask.build_daily()
    for d in daily:
        if d["device"] is None:
            q, want = f"{d['date']} のデイリー", f"・{d['date']}：走らせていない"
        else:
            q = f"{d['date']} の {d['device']} のデイリー 問題 {d['problem']}"
            want = (f"問題 {d['problem']}：送らなかった（REFUSED）" if d["runs"] == "REFUSED"
                    else f"問題 {d['problem']}：実行 {d['runs']}、{d['reads']}、{d['agrees']}、{d['beats']}")
        a = ask.answer(q, rows, daily=daily)
        if want not in a or ("1 行" not in a and d["device"] is not None):
            bad.append((q, a.splitlines()[0]))
    n_rel = 0
    top = max(r["date"] for r in rows if r["date"])
    yday = (datetime.date.fromisoformat(top) - datetime.timedelta(days=1)).isoformat()
    for fam in list(ask.FAMILY_JA) + [None]:
        for dev in ["ibm_fez", "ibm_marrakesh", "ibm_kingston", None]:
            cond = " ".join(x for x in (spellings("family", fam)[0] if fam else "",
                                        spellings("device", dev)[0] if dev else "") if x)
            if not cond:
                continue
            if fam == "daily (P4 chain)":
                pool = [d["date"] for d in daily if d["device"] is not None and (dev is None or d["device"] == dev)]
                pool += [] if dev else [d["date"] for d in daily if d["device"] is None]
            else:
                pool = [r["date"] for r in rows if r["date"] and (fam is None or r["family"] == fam)
                        and (dev is None or r["device"] == dev)]
            ds = sorted(set(pool), reverse=True)
            for word, k in (("最新", 0), ("前回", 1), ("昨日", None)):
                n_rel += 1
                a = ask.answer(f"{word}の {cond}", rows, daily=daily)
                date = yday if k is None else (ds[k] if len(ds) > k else None)
                if date is None:
                    if not a.startswith("答えない"):
                        bad.append((word, cond, "should not resolve", a.splitlines()[0]))
                    continue
                ref = ask.answer(f"{date} の {cond}", rows, daily=daily)
                body = [ln for ln in a.splitlines() if not ln.startswith("（「")]
                if body != ref.splitlines() or f"{date} と読んだ" not in a:
                    bad.append((word, cond, a.splitlines()[0], ref.splitlines()[0]))
    if not ask.answer("最新 11月14日 XX", rows).startswith("答えない：日付"):
        bad.append(("date and relative date", ask.answer("最新 11月14日 XX", rows)))
    print(f"6 daily and relative dates: {len(daily)} lines of the daily record, {n_rel} relative-date questions; "
          f"wrong {len(bad)}")
    for b in bad[:10]:
        print("   ", b)
    return not bad


STUB_CARDS = {    # question: (conditions, evidence), as an honest model would give them
    "フェズでやったXXの81量子ビットのやつ、π/4 はどうなってた？":
        ({"device": "ibm_fez", "family": "XX chain", "qubits": 81, "angle": "π/4"}, {}),
    "マラケシュで光円錐をもう一回やったときの 81量子ビット 16ステップ π/4":
        ({"device": "ibm_marrakesh", "run": "xxcone", "qubits": 81, "steps": 16, "angle": "π/4"},
         {"run": "光円錐をもう一回やった"}),
    "kingston で走らせた双対ユニタリの曲線、51量子ビットのほうはどうだった":
        ({"device": "ibm_kingston", "family": "dual-unitary (curve)", "qubits": 51}, {"family": "双対ユニタリの曲線"}),
    "11月11日にフェズで回したハバードの120量子ビット、4ステップは":
        ({"date": "2026-11-11", "device": "ibm_fez", "family": "Hubbard", "qubits": 120, "steps": 4}, {}),
    "いちばん最近のデイリーの結果を全部": ({"rel": "latest", "family": "daily (P4 chain)"}, {"rel": "いちばん最近"}),
    "全面フロアの102番の量子ビット、最新の夜の値":
        ({"kind": "fullfloor", "qubit": 102, "rel": "latest"}, {"qubit": "102番の量子ビット", "rel": "最新の夜"}),
    "ユーティリティの Z_106 を8ステップまでやったやつ": ({"family": "IBM 2023 utility", "obs": "z106", "steps": 8}, {}),
    "11/14 の fez の XX、33量子ビットの π/2 で 64層のところ":
        ({"date": "2026-11-14", "device": "ibm_fez", "family": "XX chain", "qubits": 33, "angle": "π/2", "layers": 64},
         {}),
}


def liars(cond):
    """Wrong cards made from a right one: each must be stopped."""
    out = []
    other = {"ibm_fez": "ibm_marrakesh", "ibm_marrakesh": "ibm_fez", "ibm_kingston": "ibm_fez"}
    if "device" in cond:
        out.append(("device swapped", {**cond, "device": other[cond["device"]]}))
    for k in ("qubits", "steps", "layers", "qubit"):
        if k in cond:
            out.append((f"{k} + 1", {**cond, k: cond[k] + 1}))
    out.append(("number added", {**cond, "layers": 999}))
    out.append(("key invented", {**cond, "colour": "blue"}))
    out.append(("value invented", {**cond, "family": "XXX"}))
    out.append(("show invented", {**cond, "show": ["everything"]}))
    out.append(("date invented", {**cond, "date": "2026-11-09"} if "date" not in cond else {**cond, "date": "2026-11-09"}))
    for k in cond:
        out.append((f"{k} dropped", {kk: vv for kk, vv in cond.items() if kk != k}))
    return out


def card(cond, ev):
    return {"intent": "lookup", "conditions": dict(cond), "evidence": dict(ev)}


def shell_checks(rows):
    import shell
    bad, n_ok, n_dead, n_liars = [], 0, 0, 0
    for q, (cond, ev) in STUB_CARDS.items():
        a = shell.answer(q, lambda _q, x=card(cond, ev): x, rows)
        mq = shell.mirror_question(shell.normal_card(card(cond, ev))[0])
        if a.startswith("DEAD") or not a.endswith(ask.answer(mq, rows)):
            bad.append(("honest card stopped or wrong", q, a.splitlines()[0]))
        else:
            n_ok += 1
        anchor = ask.parse(q)[0]
        wrong = liars(cond) + [("evidence not in the text", {**cond, "obs": "w10"})]
        for name, cc in wrong:
            ev2 = {k: v for k, v in ev.items() if k in cc}
            if name == "evidence not in the text":
                ev2["obs"] = "重み10"
            elif name in ("number added", "date invented"):
                ev2["layers" if name == "number added" else "date"] = q[:4]
            a = shell.answer(q, lambda _q, x=card(cc, ev2): x, rows)
            survived = not a.startswith("DEAD")
            dropped = name.endswith("dropped") and name.split()[0] not in anchor
            n_liars += 1
            if survived and not dropped:
                bad.append((f"liar passed: {name}", q, a.splitlines()[0]))
            n_dead += not survived
        for k in [k for k in cond if k not in anchor]:           # an added condition without its evidence
            if not shell.answer(q, lambda _q, x=card(cond, {kk: v for kk, v in ev.items() if kk != k}): x,
                                rows).startswith("DEAD"):
                bad.append(("added condition without evidence passed", q, k))
        if not shell.answer(q, lambda _q: {"intent": "other", "conditions": {}}, rows).startswith("DEAD"):
            bad.append(("intent other passed", q))
        if not shell.answer(q, lambda _q: (_ for _ in ()).throw(RuntimeError("down")), rows).startswith("DEAD"):
            bad.append(("model failure passed", q))
    calls = []

    def spy(qq):
        calls.append(qq)
        return {"intent": "other", "conditions": {}}
    for i, r in enumerate(rows):                                 # the core reads these alone: the model is not asked
        if shell.answer(question(r, i), spy, rows) != ask.answer(question(r, i), rows):
            bad.append(("core-readable question changed", question(r, i)))
    negs = [ctx + stem for stem in NEG_STEMS for ctx in NEG_CONTEXT]
    for q in negs:                                               # an honest model says "other"
        a = shell.answer(q, spy, rows)
        if not (a.startswith("答えない") or a.startswith("DEAD")):
            bad.append(("refusal answered through the shell", q, a.splitlines()[0]))
    refusal_calls = [c for c in calls if any(w in ask.norm(c) for ws in ask.REFUSE.values() for w in ws)]
    core_calls = [c for c in calls if not ask.parse(c)[1] and ask.parse(c)[0]]
    if refusal_calls or core_calls:
        bad.append(("model asked about a refused or core-readable question", (refusal_calls + core_calls)[:3]))

    def adversary(qq):
        """A model that wants to answer anything: the core's own reading, plus one condition whose evidence is the
        longest run of words nobody took."""
        c, _, _, left, _ = ask.parse(qq, leftover=True)
        words = left.split()
        if not words:
            return {"intent": "lookup", "conditions": c}
        w = max(words, key=len)
        extra = ("show", ["floor"]) if "show" not in c else ("variant", "circuit")
        return {"intent": "lookup", "conditions": {**c, extra[0]: extra[1]}, "evidence": {extra[0]: w}}
    through = [q for q in negs if not (lambda a: a.startswith("答えない") or a.startswith("DEAD"))(
        shell.answer(q, adversary, rows))]
    print(f"7 outer shell (stub models): {len(STUB_CARDS)} paraphrases with honest cards answered {n_ok}; "
          f"{n_liars} wrong cards, stopped {n_dead} (the rest drop a condition the question does not name); "
          f"refused and core-readable questions never sent to the model; with an honest model the {len(negs)} "
          f"refusal questions all stop; a model that wants to answer anything gets {len(through)} of them through "
          f"(as a lookup of real records, its reading printed); wrong {len(bad)}")
    for q in through[:8]:
        print("    through an adversary:", q)
    for b in bad[:10]:
        print("   ", b)
    return not bad


def main():
    rows = ask.build_index()
    ok = [round_trip(rows), spelling_checks(rows), edge_checks(rows), refusal_checks(rows), control_checks(rows),
          daily_and_relative(rows), shell_checks(rows)]
    print("ALL PASS" if all(ok) else "FAIL")
    return all(ok)
