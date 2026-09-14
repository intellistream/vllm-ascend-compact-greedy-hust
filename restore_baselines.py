"""Restore exact experimental Git pins from public anchors and small bundles."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def restore(output):
    manifest_path = ROOT / "baselines/manifest.json"
    mod = json.loads((ROOT / "mod.json").read_text())
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != mod["baseline_manifest_sha256"]:
        raise ValueError("Baseline manifest identity changed")
    manifest = json.loads(manifest_path.read_text())
    for row in manifest["repositories"]:
        raw = (ROOT / row["bundle"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["bundle_sha256"]:
            raise ValueError(f"Bundle identity changed: {row['name']}")
    output = output.absolute()
    if output.resolve() != output or not output.is_relative_to("/data/statecentric-builds"):
        raise ValueError("Use a fresh directory under /data/statecentric-builds")
    output.mkdir()
    receipts = []

    def run(source, *args):
        argv = ["git", "-C", str(source), *args]
        result = subprocess.run(argv, capture_output=True, timeout=180)
        index = len(receipts)
        (output / f"{index:02d}.stdout").write_bytes(result.stdout)
        (output / f"{index:02d}.stderr").write_bytes(result.stderr)
        receipts.append(dict(argv=argv, exit_code=result.returncode))
        result.check_returncode()
        return result.stdout.decode().strip()

    try:
        for row in manifest["repositories"]:
            source = output / row["name"]
            source.mkdir()
            run(source, "init", "--initial-branch=baseline")
            run(source, "remote", "add", "origin", row["repository"])
            run(source, "fetch", "--depth=1", "origin", row["public_anchor"])
            run(source, "bundle", "verify", str(ROOT / row["bundle"]))
            run(source, "fetch", str(ROOT / row["bundle"]), "HEAD")
            run(source, "checkout", "--detach", row["commit"])
            if run(source, "rev-parse", "HEAD") != row["commit"]:
                raise ValueError("Restored commit differs from the runtime pin")
        (output / "receipt.json").write_text(json.dumps({
            "schema": "compact-greedy-baseline-restoration-v1",
            "repositories": manifest["repositories"], "commands": receipts,
            "installed": False, "hardware_execution": False,
        }, indent=2) + "\n")
    except Exception as exc:
        (output / "FAILED.json").write_text(json.dumps({
            "error": f"{type(exc).__name__}: {exc}", "commands": receipts,
        }, indent=2) + "\n")
        raise
    print(json.dumps({"restored": True, "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    restore(parser.parse_args().output)
