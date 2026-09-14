# Compatibility boundary

The admitted static configuration is the audited Qwen3.5 language-only direct
logits delegate, TP2/PP2, DP1, PCP1/DCP1, BF16 equal unpadded vocabulary shards,
asynchronous scheduling and FULL_DECODE_ONLY graphs. The historical served
model identifier was Qwen/Qwen3.8-27B; its architecture was Qwen3.5.

Other model delegates, padded shards, LoRA, speculative decoding, transfer,
custom processors and unsupported broadcast arrangements use FULL mode.
Prefill, random/mixed sampling, sample or prompt logprobs (including zero),
selected-token logprobs, structured outputs, thinking budgets, penalties,
logit bias, allowed/bad words and non-text requests also use FULL mode.

Mode selection precedes logits projection and uses the existing scheduler
broadcast. An immutable plan carries strong request references and exact row
order into sampling. One initialization-time world CPU agreement establishes
static eligibility; there is no new per-step CPU collective. Compact sampling
uses two TP gathers, for float32 maxima and int64 global IDs. Errors after
compact projection abort rather than choosing inconsistent rank-local fallback.

These are implemented boundaries, not an assertion that full-worker/NPU/API
qualification has passed. Keep the switch off until the candidate is validated
on the intended service configuration.
