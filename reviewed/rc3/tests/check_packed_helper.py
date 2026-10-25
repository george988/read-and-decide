#!/usr/bin/env python3
"""Extracts the helper from the read-and-decide skill content inside share-preview.json (as it would be packed),
writes it to a fresh empty BASE, runs --check, then runs the fixtures/mode_matrix.json cases through its CLI."""
import json, os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = json.load(open(os.path.join(ROOT, "share-preview.json"), encoding="utf-8"))
c = next(s["content"] for s in p["skills"] if s["name"] == "read-and-decide")
b = re.findall(r"```python\n(.*?)```", c, re.S); base = tempfile.mkdtemp(prefix="rd-packed-")
open(os.path.join(base, "rd.py"), "w", encoding="utf-8").write(b[0])
r = subprocess.run([sys.executable, os.path.join(base, "rd.py"), "--check"], capture_output=True, text=True)
ok = len(b) == 1 and r.returncode == 0 and r.stdout.strip().endswith("check OK")
print(f"{'PASS' if ok else 'FAIL'} packed helper --check: {r.stdout.strip() or r.stderr.strip()}")
W = ("stateful", "filing", "kindle", "kindle_ledger", "sweep"); n = 0
for i, c in enumerate(json.load(open(os.path.join(ROOT, "fixtures", "mode_matrix.json")))["cases"]):
    cp = os.path.join(base, f"m{i}.json")
    if c["config"] is None: cp = os.path.join(base, "missing.json")
    else: json.dump(json.loads(json.dumps(c["config"]).replace("__BASE__", base)), open(cp, "w"))
    r = subprocess.run([sys.executable, os.path.join(base, "rd.py"), "mode", cp] + (["--assessment-only"] if c["assessment_only_flag"] else []),
                       capture_output=True, text=True); m = json.loads(r.stdout)
    good = r.returncode == 0 and {k: m[k] for k in c["expect"]} == c["expect"] and m["assessment_only"] == (not any(m[k] for k in W))
    n += good; ok &= good
    if not good: print(f"FAIL packed matrix: {c['name']} :: {r.stdout.strip()}")
print(f"{'PASS' if ok else 'FAIL'} packed helper mode matrix: {n}/{i + 1} cases"); sys.exit(0 if ok else 1)
