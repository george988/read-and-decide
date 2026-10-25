# Read & Decide

Evaluate X posts, threads, articles, web links, and pasted text: keep what matters, try what's useful, skip the rest.

Read & Decide combines an agent skill with a small, standard-library Python helper. It provides relevance, usefulness, actionability, and novelty ratings; evidence checks; categories; a **Keep / Try / Skip** recommendation; and up to three suggested actions. Recommendations do not execute actions.

This repository recovers the independently reviewed **1.0.0-rc3** package from a local archive. The reviewed skill bodies and share payload are preserved byte-for-byte. The helper reports **1.0.1**, while the rubric remains **1.0.0**; these are distinct version numbers from the original package.

## Start here

- [Review skill and embedded helper](reviewed/rc3/skills/read-and-decide/SKILL.md)
- [First-run setup skill](reviewed/rc3/skills/read-and-decide-getting-started/SKILL.md)
- [Standalone helper](rd.py), extracted unchanged from the review skill
- [Original reviewed ZIP](archives/read-and-decide-public-1.0.0-rc3.zip)
- [Original share payload](reviewed/rc3/share-preview.json)

**[Add Read & Decide to Grok Bot](https://x.ai/bot/p23Ddk9YaomESF7ujUDw0)** — a new public template, published and verified on October 25, 2026 from the unchanged rc3 payload. Its Context contains the store description and two public skills; its only integration is X. No personal memory or routines are included. See [publication evidence and limits](PUBLICATION.md). The older template link is superseded because its original bot could no longer stage updates after the account transfer.

## Verify and try the helper

Python 3 and its standard library are sufficient; no API credentials or third-party packages are required for these checks. The recovery checks were run with Python 3.15.1 on macOS.

```sh
git clone https://github.com/george988/read-and-decide.git
cd read-and-decide
python3 scripts/verify.py
python3 rd.py --check
python3 rd.py normalize 'https://x.com/example/status/1000000000000000001?s=20'
python3 rd.py mode
```

`mode` without a configuration reports assessment-only mode with all write features off. The helper calculates and validates structured inputs. It does **not** fetch articles, make evidence judgments, connect to Notion, send to Kindle, or run a bot service by itself. Those tasks are described in the skills and require an agent with the appropriate capabilities.

## Restore into a bot

1. Supply the two skill bodies above to your bot. Their registered names are `read-and-decide` and `read-and-decide-getting-started`; their descriptions are in `share-preview.json`. These files are the original Grok Bot skill bodies, without YAML frontmatter, rather than a drop-in Codex skill installation.
2. Have the bot register both through its supported skill-management interface and verify that both load by name. If restoring an existing setup, back up its state and configuration first; do not overwrite them with examples.
3. Start the getting-started skill. Confirm your goals and categories, then choose any optional integrations. Missing goals withhold the relevance and total scores. Notion filing, long-read routing, and bookmark sweeps are separate opt-ins.
4. Install the embedded helper in the bot's own configured workspace and run its self-check. Start with an assessment-only item before enabling normal processing.

Example prompts:

```text
Use read-and-decide-getting-started to set up my reading goals.
Read & Decide: <article URL>
Assessment only: what do you make of this? <pasted text>
```

No private configuration, bookmark history, account destinations, delivery records, credentials, or live routines are included. The share payload has empty memory and routine lists. The X plugin entry is historical metadata from the reviewed template; verify availability in the destination account before connecting it.

## Validation and limitations

The reproducible suite contains **63 checks**, a packed-helper self-check, and a **12-case integration-mode matrix**. `scripts/verify.py` also checks the archive, manifest, signed-off hashes, extracted helper, and reproducibility of the share payload in a temporary copy. It does not mutate the reviewed package.

The original independent reviewer reported a separate **44/44** mode matrix. That reviewer script was not included in the archive, so the repository does not claim to rerun it. See [provenance](PROVENANCE.md) and the [original evidence](reviewed/rc3/EVIDENCE.md).

- Notion filing and read-back are agent instructions, not implemented or integration-tested in the Python helper. Live Kindle delivery, live bookmark sweeps, and fresh-account template import remain untested.
- Bookmark sweeps can miss newer saves hidden behind multiple re-bookmarked anchors. The original skill documents an approximately 800-bookmark API window; this recovery has not revalidated that service limit. Do not claim complete bookmark coverage.
- The lock is advisory and requires a single writer. It is not a general multi-process transaction mechanism.
- `mode` reports configuration-derived permissions. Runtime lock and corrupt-state behavior must also follow the skill rules. An explicit assessment-only request disables all writes for that request.

## Repository layout and maintenance

`reviewed/rc3/` and `archives/` are the frozen review baseline. `rd.py` is an exact extraction for easy inspection and execution. `scripts/verify.py`, this README, and `PROVENANCE.md` were added for the GitHub recovery on October 25, 2026.

The original `finalize.sh` and `make_zip.py` are preserved as historical build tools. Do not run them on the repository root or use them to overwrite the reviewed archive; they regenerate manifests or recursively package their working directory. Use `scripts/verify.py` for verification.

Future functional edits need a new version and new review evidence. Do not silently alter the signed-off rc3 baseline. No additional software license has been selected for this initial source publication.
