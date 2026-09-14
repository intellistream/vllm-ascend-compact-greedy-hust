# Progress

2026-09-14: user authorized research kickoff, transfer to intellistream and plugin delisting.
Repository transfer completed; repository ID and all Git ref SHAs verified unchanged. Website
delisting prepared independently; 179 targeted Python tests and four desktop/mobile × language
browser cases passed. Website PR #273 created. No accelerator or serving actions performed.

Research charter and prior-work boundary table created. E0 exact rational reference implemented:
four test methods cover 2,904 exhaustive support/CDF combinations plus peaked/flat distributions,
threshold equality, empty shards, ties, zero masses and invalid inputs. All pass. A 32-case model
sweep yields 24 bounded fallbacks. These counts are synthetic correctness/model evidence only.

Reconstructed dev3 from the exact bundled baseline pins; all five patched file hashes match dev9.
All 20 selector tests pass. Original dev2 manifest preserved. Runtime patch, tools and bundles are
unchanged. Reference code uses no Torch, devices or serving environment.

Website PR #273 merged; all five PR checks and Pages deployment succeeded. Four local browser
cases passed. Public checks through both the github.io alias and canonical domain timed out from
this host; public direct-access verification is incomplete. This is separate from successful
local/CI browser checks and the GitHub-reported successful Pages deployment.

Local evidence root: /data/statecentric-builds/compact-sampling-incubation-20260914-r001
(transfer-verified.json, candidate/receipt.json, e0-model/manifest.json,
website/output/playwright/incubation-delisting/result.json). CI also exports its own model manifest.

Research kickoff PR #1: both push and PR GitHub source jobs passed, including fresh public
baseline restoration, reconstruction, selector tests, rational tests and model artifact upload.
Repository homepage now links to research/; owner/visibility read back as intellistream/public.
An independent web fetch can retrieve the public plugin HTML; dynamic catalog verification from
this host still remains limited by the browser connection timeout described above.
