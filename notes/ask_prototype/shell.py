"""An outer shell for questions the closed entrance cannot read (prototype, 2026-11-15).

The deterministic core (ask.py) stays as it is and has the last word. A local language model only proposes a
condition card; the card is checked by the core, and any failed check stops the answer (DEAD), so a model error
becomes a refusal, never a wrong answer.

  0. refusals first, on the raw question (ask.REFUSE): refused, no model;
  1. the core next: if the closed entrance reads the question fully, the core answers, no model;
  2. otherwise the model proposes a card {"intent": "lookup" | "other", "conditions": {...}, "evidence": {...}},
     where evidence gives, for each condition, the exact words of the question it was read from;
  3. checks, each one able to stop the answer (DEAD):
     a. schema   - intent "lookup"; keys and values from the core's dictionary only;
     b. anchor   - every condition the core can read in the raw question is in the card with the same value;
     c. residual - every number written in the raw question is used by the card, and every number, arm and
                   problem in the card is written in the raw question (a model may not add a number);
     d. coverage - every character of the question is taken by the core, by a listed filler, or by the evidence of
                   a condition the model added; nothing is silently ignored;
     e. mirror   - the card, written back as a question in the core's own spellings, is read by the closed entrance
                   to exactly the same card, with no unknown word;
  4. the core answers the mirrored question; the reply shows the card and which conditions the model added.

What the checks cannot do: tell whether the model's reading of its evidence is right ("もう一回やった" read as the
light-cone repeat). That reading is printed with the answer, word for word, so the reader sees it; a model can only
point at recorded results, never add a number, an arm or a problem the question does not write.

Backends: "ollama" (local, PSF_ASK_URL or http://localhost:11434, model from PSF_ASK_MODEL, default qwen2.5:7b, temperature 0,
seed 0, JSON output) or any callable question -> card (the checks use stubs).
usage: python notes/ask_prototype/shell.py "フェズでやったXXの81量子ビットのやつ、π/4 は？"
       python notes/ask_prototype/shell.py --live-suite      (the paraphrase list against the local model)"""
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ask  # noqa: E402

NUMERIC = {"qubits": int, "sites": int, "steps": int, "layers": int, "U": int, "T": float, "qubit": int}
CHOICES = {}
for _k, _v, _ss in ask.SYNONYMS:
    CHOICES.setdefault(_k, set()).add(_v)
CHOICES["show"].discard("controls")
ALLOWED = set(NUMERIC) | set(CHOICES) | {"date", "arm", "problem"}

PROMPT = """You turn a Japanese question about recorded quantum-device results into a JSON condition card.
Answer with JSON only: {"intent": "lookup" or "other", "conditions": {...}}.
intent is "lookup" only when the question asks what a recorded result was; anything else (why, future, advice,
comparison, approximation) is "other" with no conditions.
Allowed condition keys and values (use nothing else, leave out what the question does not say):
  date: "YYYY-MM-DD" (year 2026)        rel: "latest" | "previous" | "yesterday"   (最新 / 前回 / 昨日)
  device: "ibm_fez" | "ibm_marrakesh" | "ibm_kingston"
  family: "XX chain" | "Hubbard" | "IBM 2023 utility" | "Ising 3D (isingL)" | "daily (P4 chain)" |
          "dual-unitary (curve)"
  kind: "fullfloor" (whole-device floor)    qubits, sites, steps, layers, U, qubit (a qubit's number): integers
  T: number    angle: "π/4" | "π/2"    run: "xxsize" | "xxcone"    variant: "circuit" | "continuum"
  obs: "z106" | "w10" | "w17" | "w17b"    arm: like "q22f0"    problem: like "FX-A", "D05"
  show: list of "floor" | "mirror" | "sentinel"
Also give "evidence": for every condition, the exact words copied from the question that it was read from, e.g.
{"intent": "lookup", "conditions": {"device": "ibm_fez", "qubits": 81},
 "evidence": {"device": "フェズでやった", "qubits": "81量子ビット"}}
Question: """
# Words the shell lets stand without evidence (they name no condition).
SHELL_FILLER = ["やったやつ", "やつ", "ところ", "とき", "ほう", "どうなってた", "どうなって", "どうだった", "全部", "値", "まで",
                "について", "って", "やった", "走らせた", "回した", "流した"]


# ---------------------------------------------------------------- backends
def ollama(question, model=None, url=None):
    url = url or os.environ.get("PSF_ASK_URL", "http://localhost:11434") + "/api/generate"
    body = json.dumps({"model": model or os.environ.get("PSF_ASK_MODEL", "qwen2.5:7b"), "prompt": PROMPT + question,
                       "format": "json", "stream": False, "options": {"temperature": 0, "seed": 0}}).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(json.loads(r.read())["response"])


# ---------------------------------------------------------------- the card, checked by the core
def normal_card(card):
    """The card in the core's form (show as a sorted tuple), or a reason it is not a card."""
    if not isinstance(card, dict) or card.get("intent") != "lookup":
        return None, "モデルが照会ではないと読んだ（intent が lookup でない）"
    cond = card.get("conditions")
    if not isinstance(cond, dict) or not cond:
        return None, "条件カードが空"
    out = {}
    for k, v in cond.items():
        if k not in ALLOWED:
            return None, f"辞書にない条件「{k}」"
        if k in NUMERIC:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or (NUMERIC[k] is int and v != int(v)):
                return None, f"{k} が数でない（{v!r}）"
            out[k] = NUMERIC[k](v)
        elif k == "show":
            vals = v if isinstance(v, list) else [v]
            if not vals or any(x not in CHOICES["show"] for x in vals):
                return None, f"show に辞書にない値（{v!r}）"
            out[k] = tuple(sorted(set(vals)))
        elif k == "date":
            if not (isinstance(v, str) and re.fullmatch(r"2026-\d\d-\d\d", v)):
                return None, f"日付の形でない（{v!r}）"
            out[k] = v
        elif k == "arm":
            if not (isinstance(v, str) and re.fullmatch(r"q\d\d[fl]\d", v)):
                return None, f"腕の形でない（{v!r}）"
            out[k] = v
        elif k == "problem":
            if not (isinstance(v, str) and re.fullmatch(r"FX-A|D0\d|user", v)):
                return None, f"問題の形でない（{v!r}）"
            out[k] = v
        else:
            if v not in CHOICES[k]:
                return None, f"{k} に辞書にない値（{v!r}）"
            out[k] = v
    return out, None


def mirror_question(card):
    """The card written back as a question in the core's own first spellings."""
    first = {}
    for k, v, ss in ask.SYNONYMS:
        first.setdefault((k, v), ss[0])
    parts = []
    for k in ["kind", "rel", "date", "device", "family", "run", "problem", "obs", "arm", "qubits", "sites", "U", "T",
              "angle", "steps", "layers", "variant", "qubit"]:
        if k not in card:
            continue
        v = card[k]
        if k == "date":
            parts.append(v)
        elif (k, v) in first:
            parts.append(first[(k, v)])
        elif k == "qubits":
            parts.append(f"{v}量子ビット")
        elif k == "sites":
            parts.append(f"L={v}")
        elif k in ("U", "T"):
            parts.append(f"{k}={v:g}" if isinstance(v, float) else f"{k}={v}")
        elif k == "steps":
            parts.append(f"{v}ステップ")
        elif k == "layers":
            parts.append(f"{v}層")
        elif k == "qubit":
            parts.append(f"{v}番")
        elif k == "arm":
            parts.append(f"腕 {v}")
        elif k == "problem":
            parts.append(f"問題 {v}")
    parts += [first[("show", s)] for s in card.get("show", ())]
    return " ".join(parts)


ANGLE_NUMBERS = {"π/4": {"4", "0.25", "45"}, "π/2": {"2", "0.5", "90"}}


def numbers_used(card, mq):
    """Digits a card accounts for: those of its mirrored question, plus the other ways to write its angle."""
    nums = set(re.findall(r"\d+(?:\.\d+)?", mq))
    nums |= {str(int(x)) for x in list(nums) if re.fullmatch(r"\d+", x)}
    nums |= ANGLE_NUMBERS.get(card.get("angle"), set())
    if "date" in card:
        y, m, d = card["date"].split("-")
        nums |= {y, str(int(m)), str(int(d)), m, d}
    if "T" in card:
        nums |= {f"{card['T']:g}", str(card["T"])}
    return nums


def check(question, card):
    """Return (card in the core's form, mirrored question, conditions the model added, evidence) or raise
    ValueError(reason)."""
    c, why = normal_card(card)
    if c is None:
        raise ValueError(why)
    anchor, _, conflicts, left, spans = ask.parse(question, leftover=True)
    if conflicts:
        raise ValueError("元の文の中で条件がぶつかっている")
    for k, v in anchor.items():
        if c.get(k) != v:
            raise ValueError(f"元の文から読める {ask.LABEL[k]} {ask.show(k, v)} がカードと違う（カード：{c.get(k)!r}）")
    mq = mirror_question(c)
    used = numbers_used(c, mq)
    raw_nums = re.findall(r"\d+(?:\.\d+)?", ask.norm(question))
    loose = [n for n in raw_nums if n not in used and str(int(float(n))) not in used]
    if loose:
        raise ValueError(f"元の文の数がカードで使われていない（{'、'.join(loose)}）")
    raw_set = {str(int(float(n))) if float(n) == int(float(n)) else n for n in raw_nums}
    card_nums = [str(c[k]) if NUMERIC[k] is int else f"{c[k]:g}" for k in NUMERIC if k in c]
    if "date" in c:
        card_nums += [str(int(x)) for x in c["date"].split("-")[1:]]
    added_nums = [n for n in card_nums if n not in raw_set]
    if added_nums:
        raise ValueError(f"カードの数が元の文にない（{'、'.join(added_nums)}）")
    for k in ("arm", "problem"):
        if k in c and c[k].lower() not in ask.norm(question):
            raise ValueError(f"カードの{ask.LABEL[k]} {c[k]} が元の文にない")
    added = [k for k in c if k not in anchor]
    ev = card.get("evidence") if isinstance(card.get("evidence"), dict) else {}
    raw = ask.norm(question)
    mask = [ch == " " for ch in left]                           # True where the core or a filler took the character
    owner = {}                                                  # character -> condition that took it
    for k, ss in spans.items():
        for a, b in ss:
            for i in range(a, b):
                owner[i] = k
    for k in added:
        if not isinstance(ev.get(k), str) or not ev[k].strip():
            raise ValueError(f"モデルが補った {ask.LABEL[k]} に根拠の語がない")
    for k, e in ev.items():
        if k not in c or not isinstance(e, str) or not e.strip():
            raise ValueError(f"根拠「{e}」の条件「{k}」がカードにない")
        e = ask.norm(e)
        if e not in raw:
            raise ValueError(f"{ask.LABEL[k]} の根拠「{e}」が元の文にない")
        if k in NUMERIC and k in added and str(c[k] if NUMERIC[k] is int else f"{c[k]:g}") not in e:
            raise ValueError(f"{ask.LABEL[k]} の根拠「{e}」にその数がない")
        for m in re.finditer(re.escape(e), raw):
            for i in range(*m.span()):
                if owner.get(i, k) != k:
                    raise ValueError(f"{ask.LABEL[k]} の根拠「{e}」が別の条件（{ask.LABEL[owner[i]]}）の語を含む")
                owner[i] = k
                mask[i] = True
    for w in SHELL_FILLER:
        for m in re.finditer(re.escape(w), raw):
            for i in range(*m.span()):
                mask[i] = True
    rest = "".join(ch if not ok else " " for ch, ok in zip(raw, mask)).split()
    if rest:
        raise ValueError(f"モデルが説明していない語がある（{'、'.join('「' + r + '」' for r in rest)}）")
    back, unknown, conf = ask.parse(mq)
    if unknown or conf or back != c:
        raise ValueError(f"鏡の照合が合わない（カード {c} → 文「{mq}」→ {back}）")
    return c, mq, added, {k: ask.norm(ev[k]) for k in ev}


def answer(question, model, rows=None):
    rows = ask.build_index() if rows is None else rows
    t = ask.norm(question)
    if any(w in t for ws in ask.REFUSE.values() for w in ws):
        return ask.answer(question, rows)                       # refused by the core, the model is not asked
    c, unknown, conflicts = ask.parse(question)
    if not unknown and not conflicts and c:
        return ask.answer(question, rows)                       # the core reads it alone
    try:
        card = model(question)
    except Exception as e:                                      # noqa: BLE001 - any model failure is a stop
        return f"DEAD：モデルに聞けなかった（{type(e).__name__}）。答えない。"
    try:
        cc, mq, added, ev = check(question, card)
    except ValueError as e:
        return f"DEAD：モデルの読みを検証で止めた（{e}）。答えない。"
    head = [f"モデルの条件カード（検証済み）：{ask.cond_text(cc) or 'なし'}" +
            (f"、表示 {'・'.join(cc['show'])}" if "show" in cc else "") +
            (f"、相対日付 {ask.show('rel', cc['rel'])}" if "rel" in cc else ""),
            "モデルが補った条件：" + ("、".join(f"{ask.LABEL[k]} {ask.show(k, cc[k])}" for k in added) if added else "なし"),
            "モデルの読み（検証で確かめられるのは、語が元の文にあることまで）：" +
            ("、".join(f"「{e}」→ {ask.LABEL[k]} {ask.show(k, cc[k])}" for k, e in ev.items()) if ev else "なし"),
            f"照合した質問文：{mq}"]
    return "\n".join(head + [ask.answer(mq, rows)])


# ---------------------------------------------------------------- paraphrases for the live run
PARAPHRASES = [
    "フェズでやったXXの81量子ビットのやつ、π/4 はどうなってた？",
    "マラケシュで光円錐をもう一回やったときの 81量子ビット 16ステップ π/4",
    "kingston で走らせた双対ユニタリの曲線、51量子ビットのほうはどうだった",
    "11月11日にフェズで回したハバードの120量子ビット、4ステップは",
    "いちばん最近のデイリーの結果を全部",
    "全面フロアの102番の量子ビット、最新の夜の値",
    "ユーティリティの Z_106 を8ステップまでやったやつ",
    "11/14 の fez の XX、33量子ビットの π/2 で 64層のところ",
]


def live_suite():
    rows = ask.build_index()
    n_dead = 0
    for q in PARAPHRASES:
        a = answer(q, ollama, rows)
        n_dead += a.startswith("DEAD")
        print("Q:", q)
        print(a)
        print()
    print(f"{len(PARAPHRASES)} paraphrases: answered {len(PARAPHRASES) - n_dead}, stopped (DEAD) {n_dead}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--live-suite"]:
        live_suite()
    else:
        print(answer(" ".join(sys.argv[1:]), ollama))
