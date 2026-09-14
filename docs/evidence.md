# Evidence and limits

The five-file runtime patch is byte-identical to StateAxis integration
0.1.0.dev9. Local checks completed before this extraction:

- 20 CPU selector/context/plan/guard cases, including request identity reuse,
  row reordering, reference retention and whole-batch fallback.
- 112 actual frozen sampler-method calls with CPU tensors across 14 patterns,
  two batch sizes, two dtypes and two TP shard positions. Communication was a
  CPU test double; no real collective or NPU behavior was qualified.
- Reconstruction from original Git objects and a full archive comparison:
  only the declared five files differ, and all postimage SHA values match.
- Seven source-mod checks covering pins, relocation, patch corruption,
  refusal to overwrite existing output and the development storage boundary.

`tests/test_sampling_mode.py` can reproduce the 20 selector tests against the
materialized backend by setting `STATEAXIS_COMPACT_DRAFT_SOURCE` to its root.
No runtime imports or accelerator access are performed by these tests.

## Earlier mechanism screen — not this mod's result

The separate dev8 experiment enabled the existing HUST `enable_reduce_sample`
switch on unchanged runtime sources. Four U/C/C/U runs totaled 512 requests;
all six output comparisons were exact. O64/c4 pooled throughput was
60.4407 → 63.1126 output tokens/s (+4.4207%). The reverse O16/c4 comparison
regressed 1.4399%; it is preserved in
[the aggregate data](legacy-configuration-screen.json).

This supports investigating the mechanism for fixed greedy workloads. It does
not qualify this mod, establish a novel algorithm, prove a saturated throughput
ceiling or imply general sampling/API superiority. Full worker activation,
NPU numerical/collective tests, compact/full API transitions and independent
matched end-to-end trials are still required. No production deployment or
performance qualification is claimed.
