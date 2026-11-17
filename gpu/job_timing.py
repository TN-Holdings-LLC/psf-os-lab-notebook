"""Job timing from the recorded raw counts (desk tool, workplace Claude 2026-11-18; home handover 2026-11-17 night,
section 2). Reads only files already fetched (job/raw_counts.json: the runtime's metrics) and the night's queue record
(fetch_in/queue.json); touches no service.

For every job folder under the given result folders: created, running, finished (CET), the wait (running - created),
the run (finished - running), the device's circuit execution time, and its share of the run's wall-clock time; the
queue read before submission. The pending count right after submission is not in any record: it needs the line in the
owner's send procedure (notes/os2_2026-11-18/QUEUE_RECORD_DRAFT.md).

  python gpu/job_timing.py RESULT_DIR [RESULT_DIR ...] [--md] [--json FILE]
"""
import argparse
import datetime as dt
import json
import os

CET = dt.timezone(dt.timedelta(hours=1))      # November: CET = UTC+1 (no summer time)


def _t(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def jobs(result_dir):
    out = []
    for dp, dn, fn in os.walk(result_dir):
        if "raw_counts.json" in fn and os.path.basename(dp) == "job":
            d = json.load(open(os.path.join(dp, "raw_counts.json")))
            m = d.get("metrics", {})
            ts = m.get("timestamps", {})
            row = dict(folder=os.path.relpath(os.path.dirname(dp), result_dir) or ".", job=d.get("job_id"),
                       status=d.get("status"))
            if ts.get("created") and ts.get("running") and ts.get("finished"):
                c, r, f = _t(ts["created"]), _t(ts["running"]), _t(ts["finished"])
                ex = m.get("circuits_execution_time_ns")
                row.update(created=c.astimezone(CET).strftime("%H:%M:%S"), running=r.astimezone(CET).strftime("%H:%M:%S"),
                           finished=f.astimezone(CET).strftime("%H:%M:%S"), wait_s=(r - c).total_seconds(),
                           run_s=(f - r).total_seconds(), exec_s=ex / 1e9 if ex else None,
                           exec_share_of_run=(ex / 1e9) / (f - r).total_seconds() if ex and f > r else None,
                           charged_s=m.get("usage", {}).get("qpu_charge_time_seconds"))
            out.append(row)
    return out


def queue(result_dir, name="queue.json"):
    """The queue read before submission (queue.json, gpu/daily_fetch.py) or, with name="queue_after.json", the read
    right after submission (the drafted line of the send procedure), if recorded."""
    for dp, dn, fn in os.walk(result_dir):
        if name in fn:
            q = json.load(open(os.path.join(dp, name)))
            return dict(read=_t(q["read"]).astimezone(CET).strftime("%H:%M:%S"), pending=q["pending"])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--json", help="write every folder's rows into one JSON file")
    a = ap.parse_args()
    allrows = {}
    for d in a.dirs:
        name = os.path.basename(os.path.normpath(d))
        rows, q, qa = jobs(d), queue(d), queue(d, "queue_after.json")
        allrows[name] = dict(queue_before=q, queue_after=qa, jobs=rows)
        if a.md:
            print(f"\n**{name}** queue before submission: {q}; right after: {qa or 'not recorded'}\n")
            print("| folder | job | created | running | finished | wait s | run s | executing s | share | charged s |")
            print("|---|---|---|---|---|---|---|---|---|---|")
            for r in sorted(rows, key=lambda r: r.get("created", "")):
                if "created" not in r:
                    print(f"| {r['folder']} | {r['job']} | (no timestamps) |||||||| ")
                    continue
                print(f"| {r['folder']} | {r['job']} | {r['created']} | {r['running']} | {r['finished']} | "
                      f"{r['wait_s']:.0f} | {r['run_s']:.0f} | {r['exec_s']:.1f} | {r['exec_share_of_run']:.2f} | "
                      f"{r['charged_s']} |")
        elif not a.json:
            print(json.dumps(allrows[name], indent=1))
    if a.json:
        json.dump(allrows, open(a.json, "w"), indent=1)
    return allrows


if __name__ == "__main__":
    main()
