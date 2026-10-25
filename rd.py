#!/usr/bin/env python3
"""rd.py: Read & Decide helper. Stdlib only, no network.
--check | normalize URL|--text TEXT | type VALUE [CFG] | decide JSON CFG | actions KEY {"selected","prior"}
| mode [CFG] [--assessment-only] | scan {"page","recent","legacy","terminal","has_next"} | lock acquire|status|release BASE [TOKEN]
| put BASE TOKEN KEY JSON. Exit: 2 bad input, 3 lock held, 4 not owner, 5 state unreadable."""
import json, os, re, sys, time, hashlib, uuid, tempfile, unicodedata
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

VERSION = "1.0.1"
X_HOSTS = {"x.com", "twitter.com", "mobile.twitter.com", "mobile.x.com", "www.x.com", "www.twitter.com"}
TRACKERS = {"s", "t", "ref_src", "ref_url", "fbclid", "gclid", "igshid", "si"}
TYPES = ["tutorial", "tool/demo", "research", "news", "opinion", "opportunity", "reference"]

def normalize(url):
    url = (url or "").strip()
    u = urlsplit(url if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url) else "https://" + url)
    host = (u.hostname or "").lower()
    if host in X_HOSTS:
        m = re.search(r"/(?:i/web/|i/|[^/]+/)status(?:es)?/(\d+)", u.path)
        if m: return "x:" + m.group(1)
    q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True)
         if not (k.lower().startswith("utm_") or k.lower() in TRACKERS)]
    scheme = "https" if u.scheme.lower() in ("http", "https") else u.scheme.lower()
    return urlunsplit((scheme, host + (f":{u.port}" if u.port else ""), u.path.rstrip("/") or "/", urlencode(q), ""))

def normalize_text(text):
    t = re.sub(r"\s+", " ", unicodedata.normalize("NFC", text or "")).strip().lower()
    return "text:" + hashlib.sha256(t.encode()).hexdigest()[:12]

def check_type(v, cfg=None):
    allowed = list((cfg or {}).get("content_types") or TYPES)
    return (True, v) if isinstance(v, str) and v in allowed else (False, f"{v!r} not one of {allowed}")

def score(d):
    for k in "RUAN":
        v = (d or {}).get(k)
        if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 5:
            return None, f"dimension {k}={v!r} invalid or unratable"
    return 7 * d["R"] + 6 * d["U"] + 4 * d["A"] + 3 * d["N"], None

def decide(it):
    prem = it.get("premises") or []
    if not isinstance(prem, list) or not all(isinstance(p, dict) for p in prem):
        raise ValueError("premises must be a list of objects")
    out = dict(verdict=None, research_lead=False, triage="assessed", score=None, notes=[], unknown=[])
    if it.get("unavailable"):
        out.update(triage="needs_review"); out["notes"].append("content unavailable"); return out
    dims = dict(it.get("dims") or {})
    if it.get("goals_confirmed") is False:
        dims["R"] = "?"; out["notes"].append("no confirmed goals: Relevance and total withheld; run goal setup")
    s, why = score(dims)
    if s is None:
        out.update(triage="needs_review"); out["notes"].append(why); return out
    out["score"] = s
    ov = it.get("override") or {}; shift = ov.get("keep_line_shift", 0)
    if ov.get("force"): out["notes"].append(f"override rejected: cannot force {ov['force']}")
    if shift and (abs(shift) > 5 or not ov.get("reason")):
        out["notes"].append(f"override rejected: shift {shift}"); shift = 0
    line = 50 + shift
    ev = it.get("evidence", "Unverified")
    if ev == "Contradicted" or it.get("contradicted_core") or it.get("irrelevant") or it.get("redundant"):
        out["verdict"] = "Skip"; return out
    unsup = any(p.get("essential", True) is not False and p.get("supported") is not True for p in prem)
    risk, eff = it.get("risk"), it.get("effort_ok")
    if risk not in ("Low", "Medium", "High"): out["unknown"].append("risk")
    if eff not in (True, False): out["unknown"].append("effort")
    if (s >= 70 and it["dims"]["A"] >= 3 and ev in ("Verified", "Partly supported") and prem and not unsup
            and risk in ("Low", "Medium") and eff is True and it.get("experiment") is True):
        out["verdict"] = "Try"; return out
    if s >= line and (unsup or risk == "High" or out["unknown"]):
        out.update(verdict="Keep", research_lead=True); return out
    out["verdict"] = "Keep" if s >= line else "Skip"
    return out

def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", str(t).lower()).strip("-")[:24].strip("-") or "x"

def prefix(key):
    if key.startswith("x:"): return "RD-" + key[2:]
    if key.startswith("text:"): return "RD-t" + key[5:]
    return "RD-u" + hashlib.sha1(key.encode()).hexdigest()[:8]

def assign_ids(key, selected, prior=()):
    old = {(a["intent"], a["target"]): a for a in prior if "intent" in a and "target" in a}
    used = {a["id"] for a in prior}; out, seen, keep = [], set(), set()
    for c in selected[:3]:
        ident = (c["intent"], c["target"])
        if ident in seen: continue
        seen.add(ident); a = dict(c, rank=len(out) + 1, recommended=not out)
        if ident in old:
            a.update(id=old[ident]["id"], status=old[ident].get("status", "Suggested")); keep.add(a["id"])
        else:
            base = f"{prefix(key)}-{c['intent']}-{slug(c['target'])}"; aid, n = base, 2
            while aid in used: aid, n = f"{base}-{n}", n + 1
            used.add(aid); a.update(id=aid, status="Suggested")
        out.append(a)
    for p in prior:
        if p["id"] not in keep:
            q = dict(p, rank=None, recommended=False)
            if q.get("status", "Suggested") == "Suggested": q.update(status="Dropped", note="superseded")
            out.append(q)
    return out

def mode(cfg, assessment_only=False):
    # stateful (state, lock, history) needs only setup_complete + state_dir; each feature is a separate opt-in
    # on top of it; an explicit assessment-only request turns every write off. assessment_only == not stateful.
    cfg = cfg if isinstance(cfg, dict) else {}; why = []
    n, k, sw = ((cfg.get(x) if isinstance(cfg.get(x), dict) else {}) for x in ("notion", "kindle", "sweep"))
    ready = cfg.get("setup_complete") is True and bool(cfg.get("state_dir"))
    if not cfg.get("confirmed_goals"): why.append("no confirmed goals: Relevance stays '?'")
    if assessment_only: why.append("explicit assessment-only request: no writes")
    elif not ready: why.append("setup not complete or no state_dir: assessment-only, no writes")
    st = ready and not assessment_only
    filing = st and n.get("enabled") is True and bool(n.get("database")) and bool(n.get("fields"))
    kindle = st and k.get("enabled") is True and bool(k.get("method"))
    sweep = st and sw.get("enabled") is True and bool(sw.get("time"))
    for on, msg in ((filing, "Notion filing off"), (kindle, "long-read routing off"), (sweep, "no bookmark sweep")):
        if not on: why.append(msg)
    return {"assessment_only": not st, "explicit_assessment_only": bool(assessment_only), "stateful": st,
            "filing": filing, "kindle": kindle, "kindle_ledger": kindle and bool(k.get("ledger")), "sweep": sweep, "notes": why}

def scan(page, recent=(), legacy=(), terminal=(), has_next=True):
    # stop at the first CONFIRMED anchor (next key is an anchor in recorded order, or list end). Known limit:
    # re-bookmarked anchors landing in recorded order look like a boundary and mask newer saves.
    recent = list(recent); anc = set(recent) | set(legacy); new, skipped = [], []
    for i, k in enumerate(page):
        if k in anc:
            if i + 1 < len(page):
                nx = page[i + 1]
                ok = nx in anc and not (k in recent and nx in recent and recent.index(nx) < recent.index(k))
            else:
                ok = not has_next
            if ok: return {"new": new, "skipped": skipped, "boundary": i}
            skipped.append(k); continue
        (skipped if k in terminal else new).append(k)
    if not has_next: return {"new": new, "skipped": skipped, "boundary": len(page)}
    return {"new": [], "skipped": skipped, "boundary": None, "gap": "no confirmed anchor on this page: triage nothing"}

class Held(Exception): pass
class NotOwner(Exception): pass
class StateError(Exception): pass

def atomic_write(p, obj, guard=None):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p) or ".", prefix=".tmp-")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, indent=1); f.flush(); os.fsync(f.fileno())
        if guard: guard()
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp): os.remove(tmp)

def load_state(base):
    p = os.path.join(base, "state.json")
    try:
        with open(p) as f: st = json.load(f)
    except FileNotFoundError: return {"lock_epoch": 0, "records": {}}
    except (ValueError, OSError) as e: raise StateError(f"state.json unreadable: {e}")
    if not isinstance(st, dict) or not isinstance(st.get("records"), dict): raise StateError("state.json wrong shape")
    return st

def lock_acquire(base, purpose="run"):
    # mkdir is atomic; an existing lock is never taken over
    st = load_state(base); ld = os.path.join(base, ".lock.d"); tok = uuid.uuid4().hex[:12]
    try: os.mkdir(ld)
    except FileExistsError: raise Held(lock_status(base))
    atomic_write(os.path.join(ld, "owner"), {"token": tok, "purpose": purpose, "started_at": time.time()})
    return tok

def lock_status(base):
    ld = os.path.join(base, ".lock.d")
    if not os.path.isdir(ld): return {"state": "free"}
    try:
        with open(os.path.join(ld, "owner")) as f: return {"state": "held", "owner": json.load(f)}
    except (OSError, ValueError): return {"state": "ownerless"}

def _owner_ok(base, tok):
    if (lock_status(base).get("owner") or {}).get("token") != tok: raise NotOwner(tok)

def lock_release(base, tok):
    _owner_ok(base, tok); ld = os.path.join(base, ".lock.d")
    os.remove(os.path.join(ld, "owner")); os.rmdir(ld)

def put(base, tok, key, rec):
    # single writer: only the lock holder calls put. The lock is advisory (mkdir), not a transaction; the token
    # is re-checked just before os.replace, which narrows but does not close the window for a rogue writer.
    _owner_ok(base, tok); st = load_state(base); st["records"][key] = rec
    atomic_write(os.path.join(base, "state.json"), st, guard=lambda: _owner_ok(base, tok))

def check():
    n = normalize
    for u in ["https://x.com/a/status/1000000000000000001?s=20&t=Q", "twitter.com/a/status/1000000000000000001/photo/1",
              "https://mobile.twitter.com/i/web/status/1000000000000000001#m", "http://x.com/i/status/1000000000000000001/"]:
        assert n(u) == "x:1000000000000000001", u
    assert n("http://Example.com/p/?utm_source=a&ref=b#f") == "https://example.com/p?ref=b"
    assert normalize_text(" Hello\n  World ") == normalize_text("hello world")
    assert check_type("tool/demo")[0] and not check_type("tool+promo")[0]
    d = {"R": 5, "U": 5, "A": 4, "N": 3}; assert score(d)[0] == 90 and score({"R": "?", "U": 1, "A": 1, "N": 1})[0] is None
    p = [{"claim": "works", "essential": True, "supported": True}]
    base = dict(dims=d, evidence="Verified", premises=p, risk="Low", effort_ok=True, experiment=True)
    assert decide(base)["verdict"] == "Try"
    r = decide(dict(base, risk=None)); assert r["verdict"] == "Keep" and r["research_lead"]
    assert decide(dict(base, evidence="Opinion", premises=[]))["verdict"] == "Keep"
    assert decide(dict(base, dims={"R": 1, "U": 1, "A": 1, "N": 1}))["verdict"] == "Skip"
    assert decide(dict(base, dims=dict(d, A="?")))["triage"] == "needs_review"
    g = decide(dict(base, goals_confirmed=False)); assert g["triage"] == "needs_review" and g["score"] is None
    try: decide(dict(base, premises=["works"])); raise AssertionError("string premise")
    except ValueError: pass
    ids = assign_ids("x:1000000000000000001", [{"intent": "verify", "target": "Pricing page"}])
    assert ids[0]["id"] == "RD-1000000000000000001-verify-pricing-page" and ids[0]["recommended"]
    W = ("stateful", "filing", "kindle", "kindle_ledger", "sweep")
    nt, kd, sp = {"enabled": True, "database": "d", "fields": {"T": "N"}}, {"enabled": True, "method": "m"}, {"enabled": True, "time": "8"}
    c0 = {"setup_complete": True, "state_dir": "/s"}; full = dict(c0, notion=nt, kindle=kd, sweep=sp)
    for c, ao, want in [(c0, 0, "01000"), (dict(c0, notion=nt), 0, "01100"), (dict(c0, kindle=kd), 0, "01010"),
                        (dict(c0, sweep=sp), 0, "01001"), (dict(full, setup_complete=False), 0, "10000"),
                        (dict(full, state_dir=""), 0, "10000"), (full, 1, "10000"), ({}, 0, "10000"), (full, 0, "01111")]:
        m = mode(c, assessment_only=bool(ao))
        assert "".join(str(int(m[x])) for x in ("assessment_only", "stateful", "filing", "kindle", "sweep")) == want, (c, ao)
        assert m["assessment_only"] == (not any(m[x] for x in W)), c
    s = scan(["n1", "a1", "a2"], recent=["a1", "a2"]); assert s["new"] == ["n1"] and s["boundary"] == 1
    s = scan(["a2", "n1", "a1", "a3"], recent=["a1", "a2", "a3"]); assert s["new"] == ["n1"] and s["boundary"] == 2
    with tempfile.TemporaryDirectory() as t:
        tok = lock_acquire(t)
        try: lock_acquire(t); raise AssertionError("second lock")
        except Held: pass
        put(t, tok, "x:1", {"verdict": "Keep"}); assert load_state(t)["records"]["x:1"]["verdict"] == "Keep"
        try: atomic_write(os.path.join(t, "state.json"), {}, guard=lambda: _owner_ok(t, "nope")); raise AssertionError("guard")
        except NotOwner: assert load_state(t)["records"] and not [f for f in os.listdir(t) if f.startswith(".tmp-")]
        lock_release(t, tok); assert lock_status(t)["state"] == "free"
        open(os.path.join(t, "state.json"), "w").write("{bad")
        try: lock_acquire(t); raise AssertionError("bad state")
        except StateError: pass
    return f"rd.py {VERSION} check OK"

def _cfg(p):
    if not p or not os.path.exists(p): return {}
    with open(p) as f: return json.load(f)

if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a == ["--check"]: print(check())
        elif a[:2] == ["normalize", "--text"]: print(normalize_text(" ".join(a[2:])))
        elif a[:1] == ["normalize"]: print(normalize(a[1]))
        elif a[:1] == ["type"]:
            ok, v = check_type(a[1], _cfg(a[2] if len(a) > 2 else None)); print(json.dumps({"ok": ok, "value": v}))
            sys.exit(0 if ok else 2)
        elif a[:1] == ["decide"]:
            it = json.loads(a[1])
            if not isinstance(it, dict): raise ValueError("item must be an object")
            # only a config with confirmed goals enables R; a caller-supplied goals_confirmed is ignored
            it["goals_confirmed"] = bool(_cfg(a[2]).get("confirmed_goals")) if len(a) > 2 else False
            print(json.dumps(decide(it)))
        elif a[:1] == ["actions"]:
            j = json.loads(a[2]); print(json.dumps(assign_ids(a[1], j.get("selected", []), j.get("prior", []))))
        elif a[:1] == ["mode"]:
            p = [x for x in a[1:] if x != "--assessment-only"]
            print(json.dumps(mode(_cfg(p[0] if p else None), assessment_only="--assessment-only" in a)))
        elif a[:1] == ["scan"]:
            j = json.loads(a[1]); print(json.dumps(scan(j["page"], j.get("recent", []), j.get("legacy", []),
                                                       set(j.get("terminal", [])), j.get("has_next", True))))
        elif a[:2] == ["lock", "acquire"]: print(json.dumps({"token": lock_acquire(a[2])}))
        elif a[:2] == ["lock", "status"]: print(json.dumps(lock_status(a[2])))
        elif a[:2] == ["lock", "release"]: lock_release(a[2], a[3]); print("released")
        elif a[:1] == ["put"]: put(a[1], a[2], a[3], json.loads(a[4])); print("written")
        else: sys.exit(__doc__)
    except Held as e: print(json.dumps({"held": e.args[0]})); sys.exit(3)
    except NotOwner as e: print(json.dumps({"not_owner": str(e)})); sys.exit(4)
    except StateError as e: print(json.dumps({"state_error": str(e)})); sys.exit(5)
    except (IndexError, ValueError, KeyError, TypeError) as e: print(json.dumps({"error": repr(e)})); sys.exit(2)
