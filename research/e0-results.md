# E0: exact candidate sufficiency and bounded fallback

Reference version: `reference-0.1.0`. Evidence class: **simulation/model**, CPU only.

The oracle sorts the full positive-mass vocabulary using descending mass and ascending token ID,
then takes the smallest prefix whose mass reaches p times the complete distribution mass. This is
an explicit reference contract; matching a runtime's exact cutoff and tie behavior remains E1 work.

The protocol merges local top-K entries, checks the mass of global top-K against that same full
target, expands through bounded budgets, then falls back. The certificate is a direct consequence
of nucleus semantics, not a claimed new theorem. No approximate renormalization is used to decide
sufficiency. Inverse-CDF checks use identical rational input values; a real RNG is not modeled.

Validation on 2026-09-14:

- 242 nonzero mass vectors in `{0,1,2}^5`, four shard counts (1/2/3/7) and three thresholds
  (1/2, 9/10, 1): 2,904 comparisons against an independent full-sort support oracle. Also checks
  every selected interval's left boundary and midpoint in the inverse CDF.
- Flat vocabulary of 512 at p=0.9 needs 461 entries; fixed K=128 is insufficient and the bounded
  protocol falls back to the correct full support.
- A 0.9/0.1 mass pair succeeds at p=0.9 with K=1, but falls back just above that threshold.
- Invalid masses, duplicate IDs, nonfinite/floating inputs, invalid budgets and CDF inputs reject.
- A separate 32-case flat/peaked model sweep using budgets 4/16/64/128 has 24 fallback cases.
  This constructed ratio is not a prediction of real-model fallback rates.

`run_reference.py` writes source SHA values and configuration into a new output directory. It
does not report latency, throughput or collective costs. Candidate-item counters omit normalizer
and control communication and must not be presented as total runtime bytes.

Remaining correctness gaps include floating-point normalizers near cutoffs, processor ordering,
raw versus processed logprobs, real request RNG mapping, rank agreement and execution completion.
Remaining performance question: do saved payload and kernels outweigh extra rounds, packing,
graph constraints and shared batch waiting? E1/E2 must answer before a serving claim.
