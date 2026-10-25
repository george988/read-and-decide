# Evidence report: read-and-decide-public 1.0.0-rc3

Labels: **REAL-TESTED** (executed with Shell in this build; reproducible with the scripts in `tests/`), **SIMULATED** (reasoned from the prose, not executed), **UI-INSPECTED** (seen by the owner in the app's own UI; not an export or import test), **NOT SUPPORTED BY APP** (cannot be done or checked from this environment). All dates are America/New_York.

## rc3 changes (from rc2)
- **Blocker fixed: mode gating.** rc2's `mode()` returned `assessment_only = not filing`, so a Kindle-only or sweep-only setup reported `kindle`/`sweep` true while also being assessment-only (no writes). rc3 adds a **stateful** mode that needs only `setup_complete` true plus a `state_dir` (no Notion). Filing, long-read routing and the sweep are separate opt-ins, each also requiring the stateful mode. An explicit assessment-only request (`mode CFG --assessment-only`) turns every write off. `assessment_only == not stateful`, so when it is true every write flag is false. New keys: `stateful`, `explicit_assessment_only`.
- `decide` with no config (or a missing config file) ignores any caller-supplied `goals_confirmed` and withholds R and the total. Only a config with `confirmed_goals` enables R.
- Malformed `decide` input (a premise that isn't an object, premises not a list, the item not an object, dims not an object) exits 2 with a JSON error instead of a traceback.
- `put()`: documented single-writer use in the code and in skill §1. The lock token is re-checked just before `os.replace`, and a refused write leaves state unchanged with no tmp file.
- Skill prose updated: Invocation "Assessment only", §0 public defaults and degrade list, §1 single writer, §8/§9/§10 each gated by its own `rd.py mode` flag. The getting-started skill's config write and its on/off explanation were updated to match.
- The read-and-decide skill description now ends "Optional bookmark sweep can miss saves hidden behind re-bookmarked posts."
- Helper `VERSION` is 1.0.1 (`--check` prints `rd.py 1.0.1 check OK`). The rubric version stays 1.0.0 (scoring and decision rules are unchanged). Pack `VERSION` is 1.0.0-rc3.
- `staging/` added: `createbotsharejson-rc2-result.txt` (the tool return the parent observed for rc2) and `createbotsharejson-rc3-result.txt` (PENDING, which the parent will overwrite).

## (a) Child-run evidence (this build process)
These were run by the build subagent on the box on 2026-10-24, about 9:15 to 9:30 PM. They test the files and the helper only, not a live bot.

| # | Check | Label | Result |
|---|---|---|---|
| 1 | `python3 tests/test_rd.py`: helper extracted from the shipped `skills/read-and-decide/SKILL.md` (exactly one python block) into a fresh empty temp BASE, `--check`, then driven through its CLI. Full output is in `tests/results-real.txt`; two consecutive runs were byte-identical | REAL-TESTED | 63/63 PASS |
| 1m | Within (1): mode matrix from `fixtures/mode_matrix.json`, 12 cases. Each asserts the full flag tuple (assessment_only, stateful, filing, kindle, kindle_ledger, sweep, explicit_assessment_only) and the invariant "assessment_only iff no write flag". Cases: none, Notion-only, Notion without field mapping, Kindle-only, Kindle-only with ledger, sweep-only, all features, setup_complete false (all features configured), no state_dir (all features configured), no config file, explicit assessment-only (all features configured), explicit assessment-only with no config | REAL-TESTED | 12/12 PASS |
| 1g | Within (1): no confirmed goals (no_goals config, missing config); no config argument; caller `goals_confirmed: true` with no config or a missing config file. All Needs review, score and verdict null | REAL-TESTED | 5/5 PASS |
| 1v | Within (1): malformed decide input exits 2 with no traceback (4 cases) | REAL-TESTED | 4/4 PASS |
| 1l | Within (1): lock tests (second acquire is blocked with exit 3; a wrong-token put is refused with exit 4; atomic put; the token is re-checked before replace and a refused write leaves state unchanged; owner release; unreadable state fails closed with exit 5) | REAL-TESTED | 6/6 PASS |
| 2 | `python3 tests/check_packed_helper.py`: helper extracted from the skill content inside `share-preview.json`, written to a fresh BASE, `--check`, then the same 12-case mode matrix via the CLI | REAL-TESTED | 2/2 PASS (`rd.py 1.0.1 check OK`; matrix 12/12) |
| 3 | `python3 tests/build_preview.py`: rebuilds `share-preview.json` from the staged files. Both skill contents are byte-identical to SKILL.md with no frontmatter, the storefront tagline is exact, `gettingStarted` names a packed skill, and plugins = X | REAL-TESTED | 5/5 PASS |
| 4 | Reviewer's independent matrix `matrix.py` (8 Notion/Kindle/sweep combos × 5 checks + 4 controls), run on a helper freshly extracted into an empty BASE from SKILL.md and again from `share-preview.json` (both copies have sha256 `ab67893059c42cf29ddaaf0f04401c65eae288a4d40487bf71a4dfec5f810675`) | REAL-TESTED | 44/44 PASS for each (rc2 got 41/44) |
| 5 | Negative control: the rc2 bug (`"assessment_only": not filing`) injected into a copy of the rc3 helper makes `--check` fail (AssertionError on the "none" case). The frozen rc2 helper with a Kindle-only config reproduces the contradiction (`assessment_only: true, kindle: true`) | REAL-TESTED | Bug detected |
| 6 | The helper self-test (`--check`) also includes the mode matrix (9 cases + invariant), the string-premise rejection and the put guard | REAL-TESTED | PASS |
| 7 | Privacy scan, case-insensitive, over every pack file including hidden ones, for the owner's name, the creator handle, a webmail marker, the private skill path and three private agent-ID prefixes | REAL-TESTED | 0 hits |
| 8 | `sha256sum -c SHA256SUMS` after regeneration; deterministic ZIP rebuilt twice with identical hashes | REAL-TESTED | All OK |
| 9 | Private-file compatibility manifest (rc2 check f): not re-run for rc3, because this build was told not to touch private files. rc3 wrote only inside this pack, the `-rc2-frozen` backup and the ZIP | NOT RE-RUN | n/a |

**SIMULATED / not tested (helper-level tests do not cover these):**
- **Notion filing (§8) is prose-only and untested.** rd.py has no Notion read-back or verify command. Match-before-write, the `Triage (auto)` section and read-back comparison were never executed against Notion. No Notion call was made.
- Long-read routing hand-off and ledger reconciliation (§9). No message was sent.
- Sweep routine creation, real X bookmark paging, rate limits, and the ~800-bookmark ceiling (stated from X API documentation, not measured).
- Live behaviour of an adopting bot: the getting-started dialogue, real fetching, evidence judgments, output wording, digests. Runtime lock-held and state-unreadable assessment-only are prose rules; `mode()` reads config only.

## (b) Template verification (parent/staging)
- **rc2:** the parent registered both skills with UpdateSkill and called CreateBotShareJson with exactly `share-preview.json`'s content. It got `Staged unpublished version 1 of "Read & Decide"` (recorded verbatim in `staging/createbotsharejson-rc2-result.txt`). Not public. The reviewer confirmed that the registered skill bodies were byte-identical to the staged rc2 files.
- **rc3:** pending re-registration of both skills and re-staging by the parent.

RC3 STAGING (2026-10-24): STAGED, UNPUBLISHED.
- Share tool returned exactly: `Staged unpublished version 2 of "Read & Decide". It is not public until you confirm it.` (saved verbatim in `staging/createbotsharejson-rc3-result.txt`).
- Registered skill bodies (live skill store, frontmatter stripped) are byte-identical to the staged files:
  - read-and-decide: sha256 69db2345daf2646836acdb634eec12c9255febf58bc4fe36e19c8ad15479a25b
  - read-and-decide-getting-started: sha256 6321e42f2e1139f73d974a9fdabb5fa582048573e479582283079cc42eda9685
- The share call's arguments were pasted (the tool takes no file reference), using `share-preview.json` as the source. The tool returns no echo of the staged payload, so byte identity between the staged version and `share-preview.json` is NOT independently verified. The owner's check of the rc3 card is the next verification step.

- A real template import into a fresh bot, and its first conversation: **NOT SUPPORTED BY APP** / untested.
- The plugin entry shape `{pluginId: "49086599", name: "X"}` is unconfirmed until a real import (Integrations showed X on the rc2 card; see below).

## Owner UI inspection (rc2)
**UI-INSPECTED. This is NOT an export or import test.** On 2026-10-24 the owner viewed the actual unpublished rc2 template card. Under View Details > Context, Instructions showed only the public storefront description, plus the skills read-and-decide and read-and-decide-getting-started. No private profile text was displayed, and Integrations showed X. The owner will recheck the rc3 card before publishing. `share-preview.json` keeps `profile.description` explicit and storefront-only.

## Known limitations (disclosed in the skill)
- Bookmark coverage uses list order and anchors only. One re-bookmarked anchor is detected. Two or more re-bookmarked anchors landing in their recorded order can mask newer saves (reproduced in tests). X exposes only roughly the most recent ~800 bookmarks. Not fixed; now also stated in the skill description.
- The state lock is advisory (mkdir) and `put` is single-writer. The pre-replace token re-check narrows but does not close the race window.
- The helper is 16,014 bytes, above the ~12 KB target, because of the mode matrix self-test, input validation and the put guard.

## Reproduce / finalize
`bash tests/finalize.sh` runs build_preview, check_packed_helper and test_rd (and checks the results are deterministic). It then regenerates `SHA256SUMS` (every file except itself, `staging/` included), verifies it, and rebuilds the deterministic ZIP `/workspace/read-and-decide-public-1.0.0-rc3.zip`.
