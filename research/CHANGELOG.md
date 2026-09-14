# Research and packaging changes

## 0.1.0.dev3 / reference-0.1.0 — 2026-09-14

- Transfer repository ID 1369699524 to intellistream without changing visibility or existing refs.
- Withdraw public listing through [website PR #273](https://github.com/vLLM-HUST/vllm-hust-website/pull/273).
- Add OSDI ’27 research charter, related-work limits, milestones and rational reference prototype.
- Runtime integration remains 0.1.0.dev9; patch, materializer, restoration tool and baseline files
  are byte-identical to dev2. Preserve original manifest at releases/0.1.0.dev2/mod.json.
- Validation: exact source reconstruction (five file hashes), 20 selector tests, four reference
  test methods including 2,904 exhaustive configurations, and a 32-case model-only sweep.
- No runtime interface incompatibility or new serving/performance qualification.
- Code rollback: revert this kickoff commit or checkout prior main
  `73f71644423f668a2c6dd62f888b18ffb20854e3`. No running worker was changed.
  Organization transfer and website delisting are administrative actions and are not reversed by
  checking out code. Re-listing requires a separate explicit publication decision.
