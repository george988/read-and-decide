#!/usr/bin/env bash
# Re-run after editing EVIDENCE.md or staging/*: rerun tests, regenerate SHA256SUMS, verify it, rebuild the ZIP.
set -euo pipefail
cd "$(dirname "$0")/.."
find . -name __pycache__ -type d -prune -exec rm -rf {} +
python3 tests/build_preview.py
python3 tests/check_packed_helper.py
python3 tests/test_rd.py > tests/results-real.txt
python3 tests/test_rd.py > /tmp/rd-results-recheck.txt
cmp tests/results-real.txt /tmp/rd-results-recheck.txt && echo "results-real.txt deterministic"
tail -1 tests/results-real.txt
find . -type f ! -name SHA256SUMS ! -path '*/__pycache__/*' ! -name '*.pyc' | sed 's|^\./||' | LC_ALL=C sort | xargs sha256sum > SHA256SUMS
sha256sum -c --quiet SHA256SUMS && echo "SHA256SUMS OK ($(wc -l < SHA256SUMS) files)"
ZIP=../read-and-decide-public-$(awk '{print $NF}' VERSION).zip
python3 tests/make_zip.py "$ZIP"
sha256sum "$ZIP" share-preview.json skills/read-and-decide/SKILL.md skills/read-and-decide-getting-started/SKILL.md
