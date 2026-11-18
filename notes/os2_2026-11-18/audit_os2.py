"""Static audit of the compounding OS's tools (workplace VS Claude, 2026-11-18; home instruction, section 2). It lists,
with line numbers, every place a file could touch the network, a key, IBM, or a source of nondeterminism, for a person
to read; it decides nothing by itself (a listed line can be fine, e.g. the one allowed queue line).

  python audit_os2.py FILE.py [FILE.py ...]

Allowed by the instruction: IBM only through psf-os submit / collect, gpu/daily_fetch.py and the one queue-count line;
no key read; no git network operation; the rule, scores and stop decided from recorded files only.
"""
import re
import sys

CHECKS = {
    "git network": r"\bgit\b[^\n]*\b(push|pull|fetch|clone|ls-remote|remote)\b",
    "network library": r"\b(requests|urllib|http\.client|socket|httpx|aiohttp)\b",
    "key / account": r"(token|api_?key|QISKIT_IBM|save_account|qiskit-ibm\.json|credential|password|channel=)",
    "IBM access": r"(QiskitRuntimeService|SamplerV2|EstimatorV2|least_busy|pending_jobs|\.status\(\)|"
                  r"psf_os[\"' ,]+(submit|collect)|-m\", \"psf_os|daily_fetch|ibm\.(submit|collect|fetch))",
    "nondeterminism": r"\b(random|time\.time|datetime\.now|datetime\.utcnow|uuid|_stamp|os\.urandom|hash\()",
    "subprocess": r"\b(subprocess|os\.system|os\.popen)\b",
}


def audit(path):
    rows = []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        s = line.split("#", 1)[0] if not line.lstrip().startswith(('"', "'")) else line
        for name, rx in CHECKS.items():
            if re.search(rx, s, re.I):
                rows.append((name, n, line.rstrip()[:140]))
    return rows


def main():
    for p in sys.argv[1:]:
        rows = audit(p)
        print(f"== {p}: {len(rows)} line(s) to read")
        for name, n, line in rows:
            print(f"  {name:16s} {n:5d}  {line}")


if __name__ == "__main__":
    main()
