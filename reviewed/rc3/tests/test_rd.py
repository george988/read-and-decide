#!/usr/bin/env python3
"""Real tests for the staged Read & Decide pack. Extracts the helper exactly as shipped in
skills/read-and-decide/SKILL.md into a fresh temp BASE and drives it through its CLI.
Usage: python3 tests/test_rd.py   (run from the pack root). Prints PASS/FAIL per test."""
import json, os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "read-and-decide", "SKILL.md")
FX = lambda n: json.load(open(os.path.join(ROOT, "fixtures", n)))
results = []
BASE = tempfile.mkdtemp(prefix="rd-fresh-")
def redact(t):
    t = t.replace(BASE, "<BASE>")
    t = re.sub(r'"token": "[0-9a-f]{12}"', '"token": "<TOKEN>"', t)
    return re.sub(r'"started_at": [0-9.]+', '"started_at": <TIME>', t)
def rec(name, ok, detail=""):
    results.append((name, ok)); print(redact(("PASS " if ok else "FAIL ") + name + (f" :: {detail}" if detail else "")))

text = open(SKILL, encoding="utf-8").read()
blocks = re.findall(r"```python\n(.*?)```", text, re.S)
RD = os.path.join(BASE, "rd.py")
def run(*args):
    p = subprocess.run([sys.executable, RD, *args], capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

# (a) clean setup
rec("a1 exactly one python block in shipped skill", len(blocks) == 1, f"{len(blocks)} blocks")
rec("a2 fresh BASE is empty before install", os.listdir(BASE) == [])
open(RD, "w", encoding="utf-8").write(blocks[0])
rc, out, err = run("--check")
rec("a3 rd.py --check from shipped text", rc == 0 and out.endswith("check OK"), out or err)
rec("a4 helper size bytes", True, str(len(blocks[0].encode())))

# config files in BASE
cf = FX("configs.json")
def cfgpath(name):
    p = os.path.join(BASE, f"config.{name}.json")
    json.dump(json.loads(json.dumps(cf[name]).replace("__BASE__", BASE)), open(p, "w")); return p
goals_cfg = cfgpath("no_integrations")

# (b) scoring / decision / action IDs
for it in FX("posts.json")["items"]:
    rc, out, err = run("decide", json.dumps(it["input"]), goals_cfg); d = json.loads(out); e = it["expect"]
    ok = rc == 0 and d["triage"] == e["triage"] and d["verdict"] == e["verdict"] and d["research_lead"] == e["research_lead"] and d["score"] == e["score"]
    cands = it["candidates"]
    if d["triage"] == "needs_review": cands = [c for c in cands if c["intent"] == "retry-access"][:1]
    elif d["verdict"] == "Skip": cands = []
    rc2, out2, _ = run("actions", "x:" + it["id"], json.dumps({"selected": cands}))
    ids = [a["id"] for a in json.loads(out2)]
    rec(f"b {it['id']} -> {e['verdict'] or 'Needs review'}{' (research lead)' if e['research_lead'] else ''}",
        ok and ids == e["ids"], f"score={d['score']} verdict={d['verdict']} ids={ids}")
rc, out, _ = run("actions", "x:1000000000000000001", json.dumps({"selected": [{"intent": "verify", "target": "Pricing page"}],
    "prior": [{"id": "RD-1000000000000000001-verify-pricing-page", "intent": "verify", "target": "Pricing page", "status": "Done"},
              {"id": "RD-1000000000000000001-read-blog", "intent": "read", "target": "blog", "status": "Suggested"}]}))
a = json.loads(out)
rec("b action status carries to identical ID; unselected Suggested -> Dropped",
    a[0]["status"] == "Done" and a[1]["status"] == "Dropped" and a[0]["recommended"], out[:160])
rc, out, _ = run("type", "prompt-plus-promo"); rec("b content type compound rejected", rc == 2)
rc, out, _ = run("decide", json.dumps({"dims": {"R": 2.5, "U": 3, "A": 3, "N": 3}}), goals_cfg)
rec("b half point withholds score", json.loads(out)["triage"] == "needs_review" and json.loads(out)["score"] is None)
rc, out, _ = run("decide", json.dumps(dict(FX("posts.json")["items"][1]["input"], override={"force": "Try"})), goals_cfg)
rec("b override cannot force Try", json.loads(out)["verdict"] == "Keep" and "override rejected" in out)

# (c) key normalization
u = FX("urls.json")
bad = [(i, rc, o) for i, x in [(c[0], c[1]) for c in u["cases"]] for rc, o, _ in [run("normalize", i)] if o != x]
rec(f"c URL normalization ({len(u['cases'])} forms)", not bad, str(bad))
keys = [run("normalize", "--text", t)[1] for t, _ in u["text_cases"]]
rec("c pasted text -> text:<12 hex>, whitespace/case-insensitive",
    len(set(keys)) == 1 and re.fullmatch(r"text:[0-9a-f]{12}", keys[0]) is not None, str(keys))
rc, out, _ = run("actions", keys[0], json.dumps({"selected": [{"intent": "verify", "target": "Source"}]}))
rec("c text key action ID prefix RD-t", json.loads(out)[0]["id"] == "RD-t" + keys[0][5:] + "-verify-source", out[:120])
rc, out, _ = run("actions", "https://blog.example.com/post/slug?ref=home", json.dumps({"selected": [{"intent": "read", "target": "Article"}]}))
rec("c non-X URL action ID prefix RD-u<8 hex>", re.fullmatch(r"RD-u[0-9a-f]{8}-read-article", json.loads(out)[0]["id"]) is not None, out[:120])

# (d) optional integrations absent
W = ("stateful", "filing", "kindle", "kindle_ledger", "sweep")
for name in ("no_integrations", "empty"):
    p = cfgpath(name) if name != "empty" else os.path.join(BASE, "does-not-exist.json")
    rc, out, err = run("mode", p); m = json.loads(out)
    want_st = name == "no_integrations"
    rec(f"d mode with {name}: {'stateful' if want_st else 'assessment-only'}, filing/kindle/sweep off, no error",
        rc == 0 and not err and m["stateful"] == want_st and m["assessment_only"] == (not want_st)
        and not (m["filing"] or m["kindle"] or m["sweep"]), out)
rc, out, _ = run("decide", json.dumps(FX("posts.json")["items"][0]["input"]), cfgpath("no_integrations"))
d = json.loads(out)
rec("d full assessment still runs with no Notion/no Kindle", rc == 0 and d["verdict"] == "Try" and d["score"] == 90, out)
rc, out, _ = run("mode", cfgpath("all_opted_in")); m = json.loads(out)
rec("d positive control: opted-in config enables filing/kindle/sweep, ledger absent",
    m["stateful"] and m["filing"] and m["kindle"] and m["sweep"] and not m["kindle_ledger"] and not m["assessment_only"], out)

# (m) mode matrix, driven through the CLI of the helper extracted from the shipped SKILL.md
for i, c in enumerate(FX("mode_matrix.json")["cases"]):
    p = os.path.join(BASE, f"matrix-{i}.json")
    if c["config"] is None: p = os.path.join(BASE, "does-not-exist.json")
    else: json.dump(json.loads(json.dumps(c["config"]).replace("__BASE__", BASE)), open(p, "w"))
    rc, out, err = run("mode", p, *(["--assessment-only"] if c["assessment_only_flag"] else []))
    m = json.loads(out); got = {k: m[k] for k in c["expect"]}
    inv = m["assessment_only"] == (not any(m[k] for k in W))
    flags = " ".join(f"{k}={int(v)}" for k, v in got.items())
    rec(f"m {c['name']}", rc == 0 and not err and got == c["expect"] and inv, f"{flags} invariant={'ok' if inv else 'BROKEN'}")

# no confirmed goals (reviewer check 2)
for name in ("no_goals", "empty"):
    p = cfgpath(name) if name != "empty" else os.path.join(BASE, "does-not-exist.json")
    rc, out, _ = run("decide", json.dumps(FX("posts.json")["items"][0]["input"]), p); d = json.loads(out)
    rec(f"g no confirmed goals ({name}): Needs review, score withheld, points to goal setup",
        d["triage"] == "needs_review" and d["verdict"] is None and d["score"] is None and "goal setup" in out, out)

rc, out, _ = run("decide", json.dumps(FX("posts.json")["items"][0]["input"])); d = json.loads(out)
rec("g decide with no config argument fails closed (R withheld)", rc == 0 and d["triage"] == "needs_review" and d["score"] is None, out)
rc, out, _ = run("decide", json.dumps(dict(FX("posts.json")["items"][0]["input"], goals_confirmed=True))); d = json.loads(out)
rec("g decide with no config ignores caller goals_confirmed=true (R and total withheld)",
    rc == 0 and d["triage"] == "needs_review" and d["score"] is None and d["verdict"] is None, out)
rc, out, _ = run("decide", json.dumps(dict(FX("posts.json")["items"][0]["input"], goals_confirmed=True)), os.path.join(BASE, "does-not-exist.json"))
rec("g decide with missing config file ignores caller goals_confirmed=true", rc == 0 and json.loads(out)["score"] is None, out)

# malformed input exits 2 cleanly (no traceback)
for label, item in [("string premise", dict(FX("posts.json")["items"][0]["input"], premises=["it works"])),
                    ("premises not a list", dict(FX("posts.json")["items"][0]["input"], premises="it works")),
                    ("item not an object", "just a string"), ("dims not an object", {"dims": [1, 2]})]:
    rc, out, err = run("decide", json.dumps(item), goals_cfg)
    rec(f"v decide with {label}: exit 2, no traceback", rc == 2 and "Traceback" not in err and '"error"' in out, out)

# bookmark coverage fixtures
bm = FX("bookmarks.json")
for c in bm["cases"]:
    rc, out, _ = run("scan", json.dumps({"page": c["page"], "recent": bm["recent"], "terminal": c.get("terminal", []), "has_next": c["has_next"]}))
    s = json.loads(out)
    ok = s["new"] == c["expect_new"] and s["boundary"] == c["expect_boundary"]
    if c.get("masked"): ok = ok and not set(c["masked"]) & set(s["new"])
    rec("s " + c["name"], ok, out)

# lock + state
rc, out, _ = run("lock", "acquire", BASE); tok = json.loads(out)["token"]
rc2, out2, _ = run("lock", "acquire", BASE)
rec("l second acquire blocked (exit 3), never taken over", rc == 0 and rc2 == 3, out2)
rc, out, _ = run("put", BASE, "wrong-token", "x:1000000000000000001", "{}"); rec("l put with wrong token refused (exit 4)", rc == 4)
rc, out, _ = run("put", BASE, tok, "x:1000000000000000001", json.dumps({"verdict": "Try"}))
st = json.load(open(os.path.join(BASE, "state.json")))
rec("l atomic put writes record, no tmp files left", rc == 0 and st["records"]["x:1000000000000000001"]["verdict"] == "Try"
    and not [f for f in os.listdir(BASE) if f.startswith(".tmp-")])
import importlib.util
spec = importlib.util.spec_from_file_location("rd_packed", RD); rdm = importlib.util.module_from_spec(spec); spec.loader.exec_module(rdm)
before = open(os.path.join(BASE, "state.json")).read()
try: rdm.atomic_write(os.path.join(BASE, "state.json"), {"records": {}}, guard=lambda: rdm._owner_ok(BASE, "wrong-token")); g_ok = False
except rdm.NotOwner: g_ok = True
rec("l put re-checks owner just before replace: refused write leaves state unchanged, no tmp files",
    g_ok and open(os.path.join(BASE, "state.json")).read() == before and not [f for f in os.listdir(BASE) if f.startswith(".tmp-")])
rc, out, _ = run("lock", "release", BASE, tok); rec("l release by owner", rc == 0 and json.loads(run("lock", "status", BASE)[1])["state"] == "free")
open(os.path.join(BASE, "state.json"), "w").write('{"records": ')
rc, out, _ = run("lock", "acquire", BASE); rec("l unreadable state fails closed (exit 5)", rc == 5, out)

# prose checks on the shipped skills
gs = open(os.path.join(ROOT, "skills", "read-and-decide-getting-started", "SKILL.md"), encoding="utf-8").read()
both = text + gs
rec("p no YAML frontmatter in either skill", not text.startswith("---") and not gs.startswith("---"))
rec("p coverage limitation disclosed (re-bookmark masking + ~800)", "re-bookmarked" in text and "~800" in text and "not fixed" in text)
rec("p invocation covers non-X URLs and pasted text", "plain article or web URL" in text and "pasted text with no link" in text.lower())
rec("p lock recovery/approvals use 'the owner'", "only on the owner's explicit word" in text and "needs the owner's yes" in text)
rec("p no legacy PT- action IDs", "PT-" not in both)
rec("p onboarding skill referenced by its new name", "read-and-decide-getting-started" in text)
rec("p assessment-only/stateful mode not tied to Notion filing",
    "opted into filing" not in text and "opts into filing" not in text and "does not depend on Notion" in text
    and "--assessment-only" in text and "--assessment-only" in gs and "stateful" in gs)
rec("p single-writer use documented in skill and helper", "Single writer:" in text and "single writer: only the lock holder calls put" in text)
rec("p sections 8, 9, 10 gated by their own mode flag", all(f"`rd.py mode` reports `{f}` true" in text for f in ("filing", "kindle", "sweep")))
print(f"\nSUMMARY {sum(o for _, o in results)}/{len(results)} passed")
sys.exit(0 if all(o for _, o in results) else 1)
