#!/usr/bin/env python3
"""Builds share-preview.json (the exact argument payload intended for the template tool) from the staged files
verbatim, then verifies skill contents are byte-identical to the staged SKILL.md bodies and carry no YAML frontmatter."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rd = lambda *p: open(os.path.join(ROOT, *p), encoding="utf-8").read()
desc = rd("description.txt")
storefront = desc.split("STOREFRONT DESCRIPTION:\n", 1)[1].split("\n\n", 1)[0].strip()
SKILL_DESC = {
 "read-and-decide": "When the owner sends an X post, thread, X Article, any article URL, or pasted text for a take, or asks to triage their X bookmarks (or an opted-in sweep runs): rate it, check its evidence, categorize it, and give a Keep, Try or Skip verdict with suggested next steps. Files to Notion or routes long reads only when the owner configured them. Optional bookmark sweep can miss saves hidden behind re-bookmarked posts.",
 "read-and-decide-getting-started": "First conversation with a new owner, or whenever the Read & Decide config is missing: ask one at a time for their name, goals, categories, and optional Notion, long-read and bookmark-sweep choices; write the config, install and check the helper, and offer an assessment-only first triage.",
}
payload = {
 "profile": {"name": "Read & Decide", "description": storefront},
 "memory": [],
 "skills": [{"name": n, "description": SKILL_DESC[n], "content": rd("skills", n, "SKILL.md")} for n in ("read-and-decide", "read-and-decide-getting-started")],
 "routines": [],
 "plugins": [{"pluginId": "49086599", "name": "X"}],
 "gettingStarted": {"skill": "read-and-decide-getting-started"},
 "visibility": "public",
}
out = os.path.join(ROOT, "share-preview.json")
with open(out, "w", encoding="utf-8") as f: json.dump(payload, f, indent=1, ensure_ascii=False); f.write("\n")
back = json.load(open(out, encoding="utf-8")); ok = True
for s in back["skills"]:
    raw = open(os.path.join(ROOT, "skills", s["name"], "SKILL.md"), "rb").read()
    same = s["content"].encode("utf-8") == raw; nofm = not s["content"].lstrip().startswith("---")
    print(f"{'PASS' if same and nofm else 'FAIL'} {s['name']}: byte-identical={same} no-frontmatter={nofm} bytes={len(raw)}")
    ok &= same and nofm
tag = "Evaluate X posts, threads and articles: keep what matters, try what's useful, skip the rest."
print(f"{'PASS' if back['profile']['description'].startswith(tag) else 'FAIL'} storefront starts with exact tagline")
ok &= back["profile"]["description"].startswith(tag)
gs_ok = back["gettingStarted"]["skill"] in [s["name"] for s in back["skills"]] and back["visibility"] == "public"
print(f"{'PASS' if gs_ok else 'FAIL'} gettingStarted names a packed skill; visibility public")
pl_ok = back["plugins"] == [{"pluginId": "49086599", "name": "X"}] and all(not s["name"] == "getting-started" for s in back["skills"])
print(f"{'PASS' if pl_ok else 'FAIL'} plugins = X marketplace plugin; no skill named plain getting-started"); ok &= pl_ok
print(f"payload bytes={os.path.getsize(out)}"); sys.exit(0 if ok and gs_ok else 1)
