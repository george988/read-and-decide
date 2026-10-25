#!/usr/bin/env python3
"""Deterministic ZIP of the pack: sorted entries, fixed date 2026-10-24 00:00:00, mode 0644, prefix
read-and-decide-public/, no __pycache__/.pyc. Usage: python3 tests/make_zip.py [OUT.zip]"""
import os, sys, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ver = open(os.path.join(ROOT, "VERSION")).read().split()[-1]
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(ROOT), f"read-and-decide-public-{ver}.zip")
files = sorted(os.path.relpath(os.path.join(d, f), ROOT) for d, ds, fs in os.walk(ROOT) for f in fs
               if "__pycache__" not in d and not f.endswith(".pyc"))
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for rel in files:
        zi = zipfile.ZipInfo("read-and-decide-public/" + rel.replace(os.sep, "/"), date_time=(2026, 10, 24, 0, 0, 0))
        zi.external_attr = 0o100644 << 16; zi.compress_type = zipfile.ZIP_DEFLATED; zi.create_system = 3
        z.writestr(zi, open(os.path.join(ROOT, rel), "rb").read())
print(f"{out} entries={len(files)}")
