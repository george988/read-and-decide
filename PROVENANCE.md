# Recovery and provenance

Recovered on **2026-10-25** from the local archive retained during the original review, without relying on the current Grok Bot account.

| Artifact | SHA-256 |
| --- | --- |
| Original ZIP (51,910 bytes) | `148854d81498b48ff4a1fe3452b9cc5de877865474d3c7eae328aeb3a1f086dd` |
| Main skill body | `69db2345daf2646836acdb634eec12c9255febf58bc4fe36e19c8ad15479a25b` |
| Setup skill body | `6321e42f2e1139f73d974a9fdabb5fa582048573e479582283079cc42eda9685` |
| Share payload | `e17aeae0d97c47fcb8275ee9f7f48453ac5c310ad19ef95a7dd39efdb5d75189` |
| Embedded / extracted Python helper | `ab67893059c42cf29ddaaf0f04401c65eae288a4d40487bf71a4dfec5f810675` |

All archived files are preserved verbatim under `reviewed/rc3/`. The original manifest covers those files, excluding the manifest itself. The repository verification script additionally compares the directory to every ZIP entry and checks the standalone helper against the embedded Python block.

The original reviewer, dr eggbot, signed off rc3 on 2026-10-24 after checking registered skill bodies, a fresh helper installation, a 44-check mode matrix, input validation, locking behavior, and private-data exclusions. This is historical review evidence, not a claim that the current transferred account has those files. Registered skill files contained frontmatter; this archive holds the body text, so the full registered-file hash prefixes are not reproducible from these body-only files.

The preserved evidence document contains intermediate statements such as “pending” and “unpublished.” Later in that same document it records staging version 2. After review, the actual version-2 card was published on 2026-10-24 and the public page at <https://x.ai/bot/ndCgEghC1Blcy-eABmk7T> was checked. The old evidence is intentionally not rewritten because it is part of the hashed baseline.

The share tool returned a staging confirmation rather than echoing the stored payload. The local payload, saved skill hashes, and actual template-card inspection were checked together; a full stored-payload export and a fresh-account import were not verified.

Recovery additions are limited to repository documentation, the exact helper extraction, an ignore file, and a verification script. No scoring, routing, skill, fixture, or original test behavior was changed. Publication of this repository does not change any bot, account connection, private state, or schedule.

## New template publication

On October 25, 2026, a new template was published and its public page verified at <https://x.ai/bot/p23Ddk9YaomESF7ujUDw0>. This is the current link. The original archived tool outputs prove staging only; later publication notes and the old public page are separate evidence. The original bot could not stage updates to the older template. See [PUBLICATION.md](PUBLICATION.md) for the new card, source checks, and verification limits.
