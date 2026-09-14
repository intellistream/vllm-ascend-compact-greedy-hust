# Ascend Compact Greedy

**Author and maintainer: [Shuhao Zhang (张书豪)](https://github.com/ShuhaoZhangTony).**

A default-off, experimental **source mod** for vLLM-HUST and vLLM-Ascend-HUST.
Plain greedy decode exchanges shard maxima and token IDs instead of gathering
the full vocabulary. Unsupported batches retain the original full-logits
sampling path. No StateAxis governance module or vLLM core patch is required.

**Status:** source reconstruction and CPU checks pass. Actual worker activation,
NPU numerical/collective behavior, API transitions and end-to-end performance
remain unqualified. This is not a hot-loadable plugin, PyPI package or an
Extension Manager activation bundle. The website lists it as a source-mod preview.

[中文说明](docs/README.zh.md) · [Compatibility](docs/compatibility.md) ·
[Evidence](docs/evidence.md) · [License](LICENSE)

## Exact baseline

| Runtime | Experimental pin | Public ancestor |
|---|---|---|
| vLLM-HUST | `c8d7449de35538995b22f114f64502151b9fd29c` | `92237c2abd46d91c750e14f20fb53f8050795e21` |
| vLLM-Ascend-HUST | `5d3849215ca78fc15df4785ea692671441d108cc` | `913841ce6cbeed2e23a29ea40a8d91b158a9ebe0` |

The final pins include two and three baseline corrections respectively that
were not published in the runtime repositories. Small incremental Git bundles
in `baselines/` preserve those exact commits; adjacent readable patches expose
their changes. These baseline corrections are separate from the five-file mod.
The restoration tool fetches public ancestors and applies the bundles locally.
It does not push or alter either upstream repository.

## Reconstruct a candidate

Use Python 3.12+ and Git; no Torch import or device access is needed.
Create an isolated Python environment if needed. On the development host all
artifacts must stay under `/data/statecentric-builds`. Each output must be new.

```bash
git clone https://github.com/vLLM-HUST/vllm-ascend-compact-greedy-hust.git
cd vllm-ascend-compact-greedy-hust

python restore_baselines.py --output /data/statecentric-builds/compact-greedy-base
python mod.py materialize \
  --vllm-source /data/statecentric-builds/compact-greedy-base/vllm-hust \
  --ascend-source /data/statecentric-builds/compact-greedy-base/vllm-ascend-hust \
  --output /data/statecentric-builds/compact-greedy-candidate
```

If the exact pins are already available, skip restoration and point `mod.py`
at those repositories. It reads committed Git objects, not dirty working trees.
`mod.py check` accepts the same source arguments for read-only compatibility
checking. Reconstruction preserves the original archive, patch logs and a
receipt verifying every modified file. Nested gitlinks are not expanded by
the source archive; obtain their pinned dependencies before a source build.

Build the reconstructed backend into a separate candidate environment/image
with the pinned vLLM and matching Ascend dependencies. Reconstruction does not
install packages, launch inference, change drivers or replace a shared service.

## Enable or roll back

After installing the candidate, merge this setting into the existing
`--additional-config` JSON and restart all workers together:

```json
{"stateaxis_compact_greedy": true}
```

Keep all unrelated launch settings. Do not combine it with the legacy
`enable_reduce_sample=true`; the candidate rejects that combination.
Set the new key to `false` or remove it to disable the path on the next start.
For a complete source rollback, use the original pinned backend artifact and
remove the mod key. There is no per-rank or in-flight toggle.

## Version and authorship

Mod `0.1.0.dev2` packages the byte-identical StateAxis integration `0.1.0.dev9`
runtime patch. This publication changes packaging and baseline availability,
not the runtime algorithm. Future runtime changes receive a new mod version
and independent qualification. Historical scores are not inherited.

Shuhao Zhang is the sole project author and maintainer; this project has no
advisor role. Upstream licenses and original contribution attribution remain
in force. See [MAINTAINERS.md](MAINTAINERS.md) and [NOTICE](NOTICE).
