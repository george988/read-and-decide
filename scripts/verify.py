#!/usr/bin/env python3
"""Verify the frozen rc3 baseline and run its tests in an isolated temporary copy."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reviewed" / "rc3"
ARCHIVE = ROOT / "archives" / "read-and-decide-public-1.0.0-rc3.zip"
EXPECTED = {
    "skills/read-and-decide/SKILL.md": "69db2345daf2646836acdb634eec12c9255febf58bc4fe36e19c8ad15479a25b",
    "skills/read-and-decide-getting-started/SKILL.md": "6321e42f2e1139f73d974a9fdabb5fa582048573e479582283079cc42eda9685",
    "share-preview.json": "e17aeae0d97c47fcb8275ee9f7f48453ac5c310ad19ef95a7dd39efdb5d75189",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    require(sha(ARCHIVE.read_bytes()) == "148854d81498b48ff4a1fe3452b9cc5de877865474d3c7eae328aeb3a1f086dd", "Archive hash mismatch")
    with zipfile.ZipFile(ARCHIVE) as archive:
        files = {}
        for entry in archive.infolist():
            parts = Path(entry.filename).parts
            require(parts and parts[0] == "read-and-decide-public" and ".." not in parts, "Unexpected archive path")
            relative = Path(*parts[1:])
            files[relative] = archive.read(entry)
            require((BASE / relative).read_bytes() == files[relative], f"Archive mismatch: {relative}")
    actual = {p.relative_to(BASE) for p in BASE.rglob("*") if p.is_file()}
    require(actual == set(files), "Reviewed directory contains missing or extra files")
    for line in (BASE / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split(None, 1)
        require(sha((BASE / name).read_bytes()) == digest, f"Manifest mismatch: {name}")
    for name, digest in EXPECTED.items():
        require(sha((BASE / name).read_bytes()) == digest, f"Sign-off mismatch: {name}")
    skill = (BASE / "skills/read-and-decide/SKILL.md").read_text()
    blocks = re.findall(r"```python\n(.*?)```", skill, re.S)
    require(len(blocks) == 1, "Expected exactly one helper block")
    helper = blocks[0].encode()
    require(helper == (ROOT / "rd.py").read_bytes(), "Standalone helper differs from reviewed code")
    require(sha(helper) == "ab67893059c42cf29ddaaf0f04401c65eae288a4d40487bf71a4dfec5f810675", "Helper hash mismatch")
    payload = json.loads((BASE / "share-preview.json").read_text())
    require(payload["memory"] == [] and payload["routines"] == [], "Unexpected inherited memory or routines")
    for item in payload["skills"]:
        require(item["content"].encode() == (BASE / "skills" / item["name"] / "SKILL.md").read_bytes(), "Payload skill mismatch")
    print("PASS archive, manifest, sign-off hashes, payload and standalone helper", flush=True)

    with tempfile.TemporaryDirectory(prefix="read-decide-verify-") as directory:
        scratch = Path(directory)
        for name, content in files.items():
            target = scratch / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        for script in ("build_preview.py", "check_packed_helper.py", "test_rd.py"):
            subprocess.run([sys.executable, str(scratch / "tests" / script)], cwd=scratch, check=True)
        require(sha((scratch / "share-preview.json").read_bytes()) == EXPECTED["share-preview.json"], "Rebuilt payload differs")
    print("PASS recovery verification; reviewed files left unchanged", flush=True)


if __name__ == "__main__":
    main()
