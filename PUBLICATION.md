# Public template publication — October 25, 2026

Current template: **[Read & Decide](https://x.ai/bot/p23Ddk9YaomESF7ujUDw0)**.

A new template, version 1, was staged by the dedicated **Read & Decide rc3 Publisher** bot at 10:47:28 AM ET. The original bot returned “Grok Bot template not found” when attempting to stage updates to the older link. The older public page still opened; it was not edited or deleted. Use the new link above.

## Source and checks

The publisher fetched `reviewed/rc3/share-preview.json` from commit `388eaf4cc7a64af85ecf8818ae8a67ee79e7f109` and reported these matching source hashes:

- Payload: `e17aeae0d97c47fcb8275ee9f7f48453ac5c310ad19ef95a7dd39efdb5d75189`
- Main skill body: `69db2345daf2646836acdb634eec12c9255febf58bc4fe36e19c8ad15479a25b`
- Setup skill body: `6321e42f2e1139f73d974a9fdabb5fa582048573e479582283079cc42eda9685`

Read & Decide separately reported successful load-by-name for both saved public skills, 63/63 passing repository tests, and the helper self-check. Local recovery verification had already passed the 63 tests and 12-case mode matrix. No functional code changed for this publication.

## UI verification

Before publication, Codex opened the actual new card and inspected Context and both skill-detail views. Instructions showed only the store description. The listed skills were `read-and-decide` and `read-and-decide-getting-started`, with the expected descriptions. The template overview showed X as the integration.

Codex clicked Publish. The app displayed “Your Bot was successfully published,” and the card changed to Published. The copied link was the new URL above. Its public page was then opened independently and showed “Read & Decide by George,” the expected description, and an Add to Grok Bot link carrying the new template ID.

The source payload specifies empty memory and routines, only the X plugin, and `read-and-decide-getting-started` as the first-run skill. The UI inspection is not a complete server-side payload export: full stored-body hash equality and an actual fresh-account template import were not verified. Live Notion, Kindle, and bookmark-sweep behavior were not retested in this publication.

Future template updates should use the dedicated publisher conversation. The reviewed rc3 files and archive remain unchanged.
