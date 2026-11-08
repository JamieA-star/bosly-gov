#!/usr/bin/env python3
"""Generate TODO.md from PLAN.md. The front door; never hand-edited."""
import sys, re, pathlib, datetime
sys.path.insert(0, "/home/bosly_accord/bosly-gov")
from routers.tools import plan_query

r = plan_query(status="active")["result"]
if r["count"] != 28:
    print(f"ABORT: active is {r['count']}, expected 28"); sys.exit(1)

lines = pathlib.Path("/home/bosly_accord/bosly-gov/PLAN.md").read_text(encoding="utf-8").splitlines()

def block_for(pid):
    for i, l in enumerate(lines):
        m = re.match(r"^\[([ x~])\]\s+(?:\[(?:LIVE|GATED|BLOCKED|DECISION)\]\s+)?(" + re.escape(pid) + r")\b", l)
        if m:
            j = i
            while j + 1 < len(lines) and (lines[j+1].startswith("    ") or (lines[j+1] == "" and j+2 < len(lines) and lines[j+2].startswith("    "))):
                j += 1
            return lines[i:j+1]
    return []

STATUS = re.compile(r"^(FOUND|DECIDED|BUILT|RECORDED|DONE|PART DONE|IN PROGRESS|PARTIAL(?: FIX)?|READ SIDE TESTED)\b[^.:]*[.:]\s*", re.I)

def summary(block):
    if not block: return ""
    # build the whole text first, then cap once — capping during the walk
    # cuts mid-clause and drops the ellipsis
    first = block[0]
    m = re.search(r"—\s*(.*)$", first)
    text = (m.group(1) if m else first).strip()
    for cont in block[1:]:
        if text.endswith((".", "!", "?")):
            break
        text += " " + cont.strip()
    text = STATUS.sub("", text, count=1).strip()
    text = re.sub(r"\s{2,}", " ", text)
    sent = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    if len(sent) > 140:
        sent = sent[:140].rsplit(" ", 1)[0] + "…"
    return sent.rstrip(" .")

def still_open(block):
    for l in block:
        m = re.search(r"STILL OPEN[^.]*\.", l)
        if m: return m.group(0).strip()
    return None

def check_id(block):
    txt = " ".join(x.strip() for x in block)
    m = re.search(r"THE CHECK:?\s*(gov\.[\w.\-]+)", txt) or re.search(r"\bcheck:\s*(gov\.[\w.\-]+)", txt)
    return m.group(1).rstrip(".") if m else None

order = {"gov": 0, "accord": 1, "ops": 2, "keep": 3}
inprog, notstarted = [], []
for row in r["rows"]:
    pid, marker = row["id"], row["marker"]
    b = block_for(pid)
    key = (order.get(pid.split(".")[0], 9), pid)
    tup = (key, pid, summary(b), still_open(b) if marker == "~" else None, check_id(b))
    (inprog if marker == "~" else notstarted).append(tup)

def render(items, tag):
    out = []
    for _, pid, fs, so, ck in sorted(items, key=lambda x: x[0]):
        line = f"- {tag} {pid} — {fs}"
        if so: line += f"  [{so}]"
        if ck: line += f"  check: {ck}"
        out.append(line)
    return out

today = datetime.date.today().isoformat()
doc = [f"# TODO — generated {today} from PLAN.md", "",
       f"**{len(inprog)+len(notstarted)} active: {len(inprog)} in progress, {len(notstarted)} not started.**",
       "Parked and done items are not shown.", "",
       f"## In progress ({len(inprog)})", ""]
doc += render(inprog, "[~]")
doc += ["", f"## Not started ({len(notstarted)})", ""]
doc += render(notstarted, "[ ]")
pathlib.Path("/home/bosly_accord/bosly-gov/TODO.md").write_text("\n".join(doc) + "\n", encoding="utf-8")
print(f"WROTE TODO.md — {len(inprog)} in progress, {len(notstarted)} not started")
