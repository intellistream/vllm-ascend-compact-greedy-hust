# Related-work boundaries

Reviewed on 2026-09-14. This is a research decision record, not submission prose.

| Work | Confirmed scope | Consequence for this project |
|---|---|---|
| [FlashSampling v1](https://arxiv.org/html/2603.15854v1) | Fused LM-head and exact sampling, distributed summaries, optional log-normalizer in Appendix E | Do not claim these mechanisms as new. Section 5.6 online experiments use one B200; TP theory is not itself a matched Ascend serving baseline. |
| [SonicSampler v1](https://arxiv.org/html/2607.20475v1) | Mixed greedy/stochastic requests, processors, graphs, logprob modes; TP4 Eagle3 end-to-end experiment | Mixed batching and graph support are already addressed. Section 4.5 explicitly allows nucleus approximation when support exceeds 128; investigate checked sufficiency and bounded distributed recovery, without claiming an exhaustive novelty search. |
| [Qrita v1](https://arxiv.org/html/2602.01518v1) | Pivot-based top-k/top-p selection, real-model logits, H100/4090 measurements | Adaptive selection alone is not novel. Account for whether a baseline returns a sample or a filtered set; do not compare unequal output contracts. |
| [SIMPLE v1](https://arxiv.org/html/2512.00719v1) | Sequence-parallel CPU sampling service, hot-vocabulary sampling, TP/PP evaluation | Sampling offload and pipeline motivation overlap. CPU resources and transfer costs must be matched; no public implementation was located in the inspected paper, so reproduction remains pending. |
| [vLLM logits processors](https://docs.vllm.ai/en/latest/design/logits_processors/) | Batch-granularity stateful processing; documented all-greedy condition for skipping argmax-invariant processors | Concrete engineering seam, not proof that all current runners/backends share the limitation. Pin the actual baseline and inspect its executed path. |
| [vLLM selected logprobs](https://github.com/vllm-project/vllm/blob/main/vllm/v1/worker/gpu/sample/logprob.py) | Avoids a full logprobs tensor when only selected tokens are requested | Reuse this idea; distributed materialization/communication must be demonstrated as additional work. Main is a discovery link, not an experiment pin. |

The proposed candidate-mass check follows directly from nucleus semantics and is not claimed as a
new theorem. Novelty must come from a measured systems trade-off and a reproducible execution
protocol beyond strong existing kernels and simple row partitioning.

Do not infer source absence from a failed keyword search, or equate tensor parallel model execution
with a vocabulary-sharded sampling protocol. Before an implementation claim, inspect published
code and pin it. Differences in sampling distribution, seed mapping, logits dtype, processor order,
top-k ties and graph configuration invalidate naive speed comparisons.
