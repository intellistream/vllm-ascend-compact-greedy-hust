# Active research goal

Target OSDI ’27 with exact distributed sampling for mixed output contracts, checked candidate
sufficiency and bounded fallback. No serving qualification is currently granted.

1. Transfer to intellistream and withdraw website listing: transfer verified; website PR #273 merged,
   all CI and Pages deployment passed. Local four-case browser check passed.
2. Freeze research question, related-work limits and milestones: recorded in README.md.
3. Implement E0 exact rational reference protocol and adversarial tests: complete; 2,904 exhaustive
   distribution/sharding/threshold combinations plus boundary and invalid-input tests pass.
4. Validate source reconstruction and CI, publish research kickoff: local reconstruction and
   20 selector tests pass; GitHub push and PR source jobs passed. Delivery is tracked in
   [PR #1](https://github.com/intellistream/vllm-ascend-compact-greedy-hust/pull/1).
5. Next: define the real-logits interchange format and frozen per-request output contract; audit
   actual baseline sampler and choose a single runtime integration slice before any NPU run.

Scope this session: independent repository, website delisting and CPU reference. No main StateAxis
worktree mutation, no service/NPU execution. Runtime dev9 remains unchanged; no inherited score.
