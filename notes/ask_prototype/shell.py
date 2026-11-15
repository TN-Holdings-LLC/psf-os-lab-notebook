"""An outer shell for questions the closed entrance cannot read (prototype, 2026-11-15, second form).

The deterministic core (ask.py) stays as it is and has the last word. The first form asked a local model for a whole
condition card; on the owner's PC qwen2.5:7b answered 0 of 8 paraphrases (8 stopped: it changed the device the core
had read, dropped conditions, called lookups "other", gave whole sentences as evidence). The second form asks the
model much less: only what the words the core could not read mean, one word at a time.

  0. refusals first, on the raw question (ask.REFUSE): refused, no model;
  1. the core next: if the closed entrance reads the question fully, the core answers, no model;
  2. the residue: the runs of characters no pattern or dictionary spelling took, with the listed fillers
     (ask.FILLER, SHELL_FILLER) and edge particles removed. Empty residue: the core answers from what it read, no
     model;
  3. otherwise the model is shown the residue words and the conditions the core read, and says for each word either
     a new condition {"key", "value"}, or {"part_of": key} (the word belongs to a condition the core read), or null;
  4. checks, each one able to stop the answer (DEAD):
     a. every residue word has an answer, none null;
     b. keys and values from the core's dictionary only; a number in a value must be written in its word, and a word
        with a number must be read as that number; the model may not add a date, an arm, a problem or a display;
     c. a new condition never changes one the core read, and two words never give one key two values;
     d. "part_of" names a condition the core read; the word is at most six characters and follows or precedes that
        condition's words directly or across one の or を;
     e. mirror: the card (the core's reading plus the new conditions), written back as a question in the core's own
        spellings, is read by the closed entrance to the same card with no unknown word;
  5. the core answers the mirrored question; the reply prints every word and how the model read it.

What no check can do: tell whether the model read a word right ("もう一回" as the light-cone repeat). That reading is
printed with the answer, word by word.

Backends: "ollama" (local, PSF_ASK_URL or http://localhost:11434, model PSF_ASK_MODEL or qwen2.5:7b, temperature 0,
seed 0, JSON output) or any callable (words, conditions) -> {word: answer} (the checks use stubs).
usage: python notes/ask_prototype/shell.py "フェズでやったXXの81量子ビットのやつ、π/4 はどうなってた？"
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
# Words that name no condition; the shell lets them stand without asking the model.
SHELL_FILLER = ["やったやつ", "やつ", "ところ", "とき", "ほう", "どうなってた", "どうなって", "どうだった", "全部", "値", "まで",
                "について", "って", "やった", "走らせた", "回した", "流した"]
EDGE = "のではをがにと、。?!・,()「」: "

PROMPT = """You read Japanese words from a question about recorded quantum-device results.
Conditions already read from the question: {anchor}
For each word below say what it means, as JSON {{"<word>": answer, ...}} where answer is one of:
  {{"key": K, "value": V}}   the word names a condition not read yet
  {{"part_of": K}}           the word belongs to a condition already read (K is its key)
  null                     the word names no condition you know
Keys and values (use nothing else):
  rel: "latest" | "previous" | "yesterday"     device: "ibm_fez" | "ibm_marrakesh" | "ibm_kingston"
  family: "XX chain" | "Hubbard" | "IBM 2023 utility" | "Ising 3D (isingL)" | "daily (P4 chain)" | "dual-unitary (curve)"
  kind: "fullfloor"    angle: "π/4" | "π/2"    run: "xxsize" (size test) | "xxcone" (light-cone repeat)
  variant: "circuit" | "continuum"    obs: "z106" | "w10" | "w17" | "w17b"
  qubits, sites, steps, layers, U, qubit: integers written in the word
Example: conditions {{"run": "xxcone", "qubits": 81}}, words ["もう一回", "いちばん最近"] ->
  {{"もう一回": {{"part_of": "run"}}, "いちばん最近": {{"key": "rel", "value": "latest"}}}}
Words: {words}
JSON only."""


# ---------------------------------------------------------------- backends
def ollama(words, anchor, model=None, url=None):
    url = url or os.environ.get("PSF_ASK_URL", "http://localhost:11434") + "/api/generate"
    prompt = PROMPT.format(anchor=json.dumps(anchor, ensure_ascii=False), words=json.dumps(words, ensure_ascii=False))
    body = json.dumps({"model": model or os.environ.get("PSF_ASK_MODEL", "qwen2.5:7b"), "prompt": prompt,
                       "format": "json", "stream": False, "options": {"temperature": 0, "seed": 0}}).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(json.loads(r.read())["response"])


# ---------------------------------------------------------------- the residue
def residue(question):
    """(core reading, conflicts, residue words with their positions, character spans of each core condition)."""
    c, _, conflicts, _, spans = ask.parse(question, leftover=True)
    raw = ask.norm(question)
    taken = {i for ss in spans.values() for a, b in ss for i in range(a, b)}
    text = "".join(" " if i in taken else ch for i, ch in enumerate(raw))
    for w in sorted(SHELL_FILLER + [f for f in ask.FILLER if len(f) > 1], key=len, reverse=True):
        text = text.replace(w, " " * len(w))
    words = []
    for m in re.finditer(r"\S+", text):
        a, b = m.span()
        while a < b and text[a] in EDGE:
            a += 1
        while b > a and text[b - 1] in EDGE:
            b -= 1
        if a < b:
            words.append((text[a:b], a, b))
    return c, conflicts, words, spans


# ---------------------------------------------------------------- the card
def normal_value(k, v):
    """The value in the core's form, or raise ValueError."""
    if k not in ALLOWED:
        raise ValueError(f"辞書にない条件「{k}」")
    if k in NUMERIC:
        if isinstance(v, bool) or not isinstance(v, (int, float)) or (NUMERIC[k] is int and v != int(v)):
            raise ValueError(f"{k} が数でない（{v!r}）")
        return NUMERIC[k](v)
    if k == "show":
        vals = v if isinstance(v, list) else [v]
        if not vals or any(x not in CHOICES["show"] for x in vals):
            raise ValueError(f"show に辞書にない値（{v!r}）")
        return tuple(sorted(set(vals)))
    if k == "date":
        if not (isinstance(v, str) and re.fullmatch(r"2026-\d\d-\d\d", v)):
            raise ValueError(f"日付の形でない（{v!r}）")
        return v
    if k == "arm":
        if not (isinstance(v, str) and re.fullmatch(r"q\d\d[fl]\d", v)):
            raise ValueError(f"腕の形でない（{v!r}）")
        return v
    if k == "problem":
        if not (isinstance(v, str) and re.fullmatch(r"FX-A|D0\d|user", v)):
            raise ValueError(f"問題の形でない（{v!r}）")
        return v
    if v not in CHOICES[k]:
        raise ValueError(f"{k} に辞書にない値（{v!r}）")
    return v


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


PART_MAX = 6          # a word that is part of a condition is a short qualifier ("曲線", "もう一回", "夜")


def touches(a, b, spans, raw):
    """True when [a, b) follows or precedes one of the spans directly, or across one の or を (no space)."""
    for x, y in spans:
        between = raw[y:a] if y <= a else raw[b:x] if b <= x else None
        if between is not None and between in ("", "の", "を"):
            return True
    return False


def check(question, reply):
    """Return (card, mirrored question, readings) or raise ValueError(reason)."""
    c, conflicts, words, spans = residue(question)
    if conflicts:
        raise ValueError("元の文の中で条件がぶつかっている")
    raw = ask.norm(question)
    if not isinstance(reply, dict):
        raise ValueError("モデルの返事が辞書でない")
    card, readings = dict(c), []
    for w, a, b in words:
        ans = reply.get(w)
        if ans is None:
            raise ValueError(f"「{w}」をモデルが条件として読めなかった")
        if not isinstance(ans, dict):
            raise ValueError(f"「{w}」への返事の形が違う（{ans!r}）")
        if "part_of" in ans:
            k = ans["part_of"]
            if re.search(r"\d", w):
                raise ValueError(f"数を含む「{w}」を、読めた条件の一部とした")
            if k not in c:
                raise ValueError(f"「{w}」を、読めていない条件「{k}」の一部とした")
            if len(w) > PART_MAX:
                raise ValueError(f"「{w}」は、読めた条件の一部としては長すぎる（{PART_MAX}文字まで）")
            if not touches(a, b, spans.get(k, []), raw):
                raise ValueError(f"「{w}」が {ask.LABEL.get(k, k)} の語から離れている")
            readings.append(f"「{w}」→ {ask.LABEL[k]}（{ask.show(k, c[k])}）の一部")
            continue
        k, v = ans.get("key"), ans.get("value")
        if k == "show":
            raise ValueError("表示（フロア・ミラー・センチネル）はモデルが補えない（元の文の語でだけ読む）")
        v = normal_value(k, v)
        if re.search(r"\d", w) and k not in NUMERIC:
            raise ValueError(f"数を含む「{w}」を数でない条件として読んだ")
        if k in NUMERIC and str(v if NUMERIC[k] is int else f"{v:g}") not in w:
            raise ValueError(f"「{w}」に {ask.LABEL[k]} {v} の数が書かれていない")
        if k in ("date", "arm", "problem"):
            raise ValueError(f"{ask.LABEL[k]} はモデルが補えない（元の文に書かれた形でだけ読む）")
        if k in card and card[k] != v:
            raise ValueError(f"「{w}」→ {ask.LABEL[k]} {ask.show(k, v)} が、すでにある {ask.show(k, card[k])} とぶつかる")
        card[k] = v
        readings.append(f"「{w}」→ {ask.LABEL[k]} {ask.show(k, v)}")
    if not [k for k in card if k != "show"]:
        raise ValueError("条件が一つもない")
    mq = mirror_question(card)
    back, unknown, conf = ask.parse(mq)
    if unknown or conf or back != card:
        raise ValueError(f"鏡の照合が合わない（カード {card} → 文「{mq}」→ {back}）")
    return card, mq, readings


def answer(question, model, rows=None):
    rows = ask.build_index() if rows is None else rows
    t = ask.norm(question)
    if any(w in t for ws in ask.REFUSE.values() for w in ws):
        return ask.answer(question, rows)                       # refused by the core, the model is not asked
    c, unknown, conflicts = ask.parse(question)
    if not unknown and not conflicts and c:
        return ask.answer(question, rows)                       # the core reads it alone
    c, conflicts, words, _ = residue(question)
    if conflicts:
        return f"答えない：条件がぶつかっている（{'；'.join(conflicts)}）。"
    reply = {}
    if words:
        try:
            reply = model([w for w, _, _ in words], c)
        except Exception as e:                                  # noqa: BLE001 - any model failure is a stop
            return f"DEAD：モデルに聞けなかった（{type(e).__name__}）。答えない。"
    try:
        card, mq, readings = check(question, reply)
    except ValueError as e:
        return f"DEAD：検証で止めた（{e}）。答えない。"
    head = [("モデルの読み（検証で確かめられるのは、語が元の文にあり辞書の値であることまで）：" + "、".join(readings))
            if readings else "モデルには聞いていない（読めなかった語は決まった言い回しだけ）",
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
    n_dead = n_nomodel = 0
    for q in PARAPHRASES:
        a = answer(q, ollama, rows)
        n_dead += a.startswith("DEAD")
        n_nomodel += a.startswith("モデルには聞いていない")
        print("Q:", q)
        print(a)
        print()
    print(f"{len(PARAPHRASES)} paraphrases: answered {len(PARAPHRASES) - n_dead} "
          f"({n_nomodel} without the model), stopped (DEAD) {n_dead}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--live-suite"]:
        live_suite()
    else:
        print(answer(" ".join(sys.argv[1:]), ollama))
