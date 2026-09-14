"""Write a new, explicitly model-only E0 evidence directory under /data."""

import argparse
import hashlib
import importlib.util
import json
from fractions import Fraction as F
from pathlib import Path

root = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("reference", root / "reference.py")
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(Path("/data")):
        parser.error("evidence must be stored under /data")
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for name, masses in (("flat", [1] * 512), ("peaked", [10000] + [1] * 511)):
        rows = tuple(enumerate(masses))
        for ranks in (1, 2, 4, 8):
            for p in (F(1, 2), F(9, 10), F(99, 100), F(1)):
                result = reference.bounded_nucleus(
                    tuple(rows[r::ranks] for r in range(ranks)), p
                )
                support = result.pop("support")
                results.append(
                    {
                        "distribution": name,
                        "vocabulary": 512,
                        "ranks": ranks,
                        "p": str(p),
                        "support_size": len(support),
                        "support_tokens": [token for token, _ in support],
                        **result,
                    }
                )
    manifest = {
        "evidence_label": "simulation/model",
        "reference_version": reference.VERSION,
        "serving_qualified": False,
        "performance_claim": None,
        "budgets": [4, 16, 64, 128],
        "source_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.glob("*.py"))
        },
        "limitations": [
            "Exact rational masses, not floating-point logits",
            "No device, RNG implementation, graph or collective execution",
            "Candidate counters omit control and normalization traffic",
        ],
        "cases": results,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "cases": len(results),
                "fallback_cases": sum(x["fallback"] for x in results),
                "evidence_label": "simulation/model",
                "output": str(output),
            }
        )
    )


if __name__ == "__main__":
    main()
