import json
import os
import re
import sys

harness = os.environ["HARNESS"]
outfile = os.environ["OUTFILE"]
publish = os.environ["PUBLISH"] == "1"

errors = []
report = None


def note(x):
    if isinstance(x, str) and x.strip():
        errors.append(x.strip())


for raw in sys.stdin:
    line = raw.strip()
    if not line:
        continue
    if not line.startswith("{"):
        if line.startswith("ERROR: ") or line.startswith("Error: "):
            note(line.split(": ", 1)[1])
        continue
    try:
        d = json.loads(line)
    except Exception:
        continue
    t = d.get("type")
    if harness == "codex":
        if t == "error":
            note(d.get("message"))
        elif t == "turn.failed":
            note((d.get("error") or {}).get("message"))
    elif harness == "pi":
        m = d.get("message")
        if isinstance(m, dict) and m.get("role") == "assistant":
            if m.get("stopReason") == "error":
                note(m.get("errorMessage"))
            text = "".join(
                p.get("text", "")
                for p in m.get("content") or []
                if isinstance(p, dict) and p.get("type") == "text"
            )
            if text.strip():
                report = text
    elif harness == "claude" and t == "result":
        if d.get("is_error"):
            note(d.get("result") or d.get("subtype"))
        elif isinstance(d.get("result"), str) and d["result"].strip():
            report = d["result"]


def humanize(s):
    for _ in range(4):
        st = s.strip()
        if not st.startswith("{"):
            break
        try:
            o = json.loads(st)
        except Exception:
            break
        if not isinstance(o, dict):
            break
        e = o.get("error")
        if isinstance(e, dict) and isinstance(e.get("message"), str):
            s = e["message"]
            continue
        if isinstance(o.get("message"), str):
            s = o["message"]
            continue
        break
    return " ".join(s.split())[:300]


AUTH = (
    r"invalid_grant|invalid_rapt|invalid_api_key|incorrect api key|no api key found"
    r"|not logged in|not authenticated|unauthenticated|unauthorized|permission[ _]denied"
    r"|reauthenticat|refresh_token|application default credentials|run .{0,40}login"
    r"|credential|token (has |been )*(expired|revoked)"
)
LIMIT = (
    r"rate.?limit|quota|usage limit|too many requests|resource[ _]exhausted|overloaded"
)
CONFIG = (
    r"not supported|not found|unknown provider|unknown model|invalid_request_error"
    r"|unrecognized|invalid model|does not have access|no such model"
)

errors = list(dict.fromkeys(errors))
blob = " ".join(errors)
low = blob.lower()
codes = {int(c) for c in re.findall(r"(?:status|code)[^0-9]{0,6}([0-9]{3})", low)}

if codes & {401, 403} or re.search(AUTH, low):
    outcome = "auth"
elif 429 in codes or re.search(LIMIT, low):
    outcome = "limit"
elif codes & {400, 404} or re.search(CONFIG, low):
    outcome = "misconfig"
elif errors:
    outcome = "error"
else:
    outcome = "ok"

if publish and report and report.strip():
    open(outfile, "w").write(report)
sys.stdout.write(outcome + "\t" + (humanize(errors[0]) if errors else "") + "\n")
