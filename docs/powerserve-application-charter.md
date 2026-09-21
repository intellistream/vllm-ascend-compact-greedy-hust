# PowerServe application charter

## Positioning

PowerServe studies how a power enterprise can deploy and operate LLM
applications on domestic accelerators under business-correctness, SLO,
privacy, auditability, recovery, and operations-cost constraints. The current
application-program owner is Wu Jian (`TreeNewWind`), an in-service China
Huaneng employee and part-time doctoral student.

That background provides access to practical questions only. It does not by
itself authorize company data, represent China Huaneng endorsement, or turn a
single-enterprise observation into a general research result.

## Representative application paths

The first intake should select at least two authorized, privacy-safe paths:

1. enterprise knowledge-base question answering or RAG over regulations and
   operating procedures;
2. production-operation or maintenance assistance;
3. report generation and batch document analysis.

Each path needs a workload contract covering input/output semantics, arrival
and length distributions, business-correctness oracle, latency/SLO envelope,
hardware resources, failure modes, audit retention, and rollback requirements.

## M0: application baseline before mechanism

For each selected path, preserve an executable baseline and report:

- task quality or business correctness;
- TTFT, end-to-end p50/p95/p99, throughput, accelerator utilization, and peak
  memory;
- deployment topology, concurrency and peak/valley arrival behavior;
- restart, partial failure, stale-result, audit-log, and rollback behavior;
- operator steps and time needed to deploy, diagnose, and recover the service.

M0 passes only when the baseline exposes a repeatable application bottleneck
and a reversible proof-of-concept improves a preregistered metric without
weakening correctness, privacy, auditability, or recovery.

## Mechanism and evidence boundary

The existing Ascend compact-greedy source mod is a candidate component, not
the topic definition. It may enter an experiment only if profiling shows that
distributed sampling materially limits one of the admitted application paths.
Batching, routing, model selection, quantization, caching, or operational
changes require the same evidence-based admission.

No historical source-mod result or score is inherited. Enterprise raw data,
business secrets, credentials, and unauthorized logs must not enter this
repository. Formal evidence must use authorized de-identified data or a public,
reproducible equivalent workload and must state its external-validity limits.

## First deliverables

1. Reply to the [PowerServe contract issue](https://github.com/intellistream/vllm-ascend-compact-greedy-hust/issues/2)
   with two candidate workflows and their authorization/de-identification plan.
2. Commit the workload contracts, baseline manifests, correctness oracles, and
   rollback tests before implementing a new optimization.
3. Deliver a privacy-safe proof-of-concept plus a deployment, monitoring,
   incident-response, and rollback runbook executable by non-developer
   operators.
