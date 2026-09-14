"""Reconstruct an experimental Ascend mod from pinned Git objects, offline."""

import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(source, *args):
    result = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(source), *args],
        capture_output=True,
        timeout=120,
        check=True,
    )
    return result.stdout


def load_manifest(bundle):
    manifest = json.loads((bundle / "mod.json").read_text())
    if manifest["schema"] != "stateaxis-source-mod-v1":
        raise ValueError("Unsupported mod schema")
    patch = bundle / "compact-greedy.patch"
    if digest(patch) != manifest["patch_sha256"]:
        raise ValueError("Mod patch SHA mismatch")
    if digest(bundle / "mod.py") != manifest["materializer_sha256"]:
        raise ValueError("Mod materializer SHA mismatch")
    return manifest, patch


def check_sources(manifest, vllm_source, ascend_source):
    # Read committed objects only. Local edits are neither consumed nor changed.
    for key, source in [("vllm_hust", vllm_source),
                        ("vllm_ascend_hust", ascend_source)]:
        head = git(source, "rev-parse", "HEAD").decode().strip()
        if head != manifest["upstream"][key]:
            raise ValueError(f"{key}: HEAD does not match the pinned base")
    commit = manifest["upstream"]["vllm_ascend_hust"]
    for row in manifest["files"]:
        relative = row["path"]
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Invalid source path")
        entry = git(ascend_source, "ls-tree", commit, "--", relative)
        if row["before_sha256"] is None:
            if entry:
                raise ValueError(f"New mod target already exists: {relative}")
        else:
            raw = git(ascend_source, "show", "--no-ext-diff", "--no-textconv",
                      f"{commit}:{relative}")
            if hashlib.sha256(raw).hexdigest() != row["before_sha256"]:
                raise ValueError(f"Original source SHA mismatch: {relative}")


def materialize(bundle, vllm_source, ascend_source, output):
    manifest, patch = load_manifest(bundle)
    check_sources(manifest, vllm_source, ascend_source)
    output = output.absolute()
    resolved = output.resolve()
    data_root = Path("/data/statecentric-builds").resolve()
    if resolved == data_root or not resolved.is_relative_to(data_root):
        raise ValueError("Use a fresh directory under /data/statecentric-builds")
    if resolved != output:
        raise ValueError("Output must not traverse symlinks")
    output.mkdir()  # Refuse an existing path, including an empty directory.
    try:
        archive = output / "original-ascend.tar"
        archive.write_bytes(git(
            ascend_source, "archive", "--format=tar",
            manifest["upstream"]["vllm_ascend_hust"],
        ))
        source = output / "vllm-ascend-hust"
        source.mkdir()
        with tarfile.open(archive) as stream:
            stream.extractall(source, filter="data")
        for mode in [("--check",), ()]:
            result = subprocess.run(
                ["git", "apply", *mode, str(patch)], cwd=source,
                capture_output=True, timeout=60,
            )
            name = "patch-check" if mode else "patch-apply"
            (output / f"{name}.stdout").write_bytes(result.stdout)
            (output / f"{name}.stderr").write_bytes(result.stderr)
            result.check_returncode()
        for row in manifest["files"]:
            if digest(source / row["path"]) != row["after_sha256"]:
                raise ValueError(f"Reconstructed source SHA mismatch: {row['path']}")
        receipt = {
            "schema": "stateaxis-mod-materialization-v1",
            "mod": manifest["name"],
            "mod_version": manifest["version"],
            "runtime_integration_version": manifest["runtime_integration_version"],
            "mod_manifest_sha256": digest(bundle / "mod.json"),
            "upstream": manifest["upstream"],
            "source": str(source),
            "archive_sha256": digest(archive),
            "files_verified": manifest["files"],
            "input_kind": "pinned-git-objects-not-working-tree",
            "installed": False,
            "hardware_execution": False,
            "performance_qualified": False,
            "retained": False,
        }
        (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        return receipt
    except Exception as exc:
        (output / "FAILED.txt").write_text(f"{type(exc).__name__}: {exc}\n")
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["check", "materialize"])
    parser.add_argument("--vllm-source", required=True, type=Path)
    parser.add_argument("--ascend-source", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    bundle = Path(__file__).resolve().parent
    if args.action == "check":
        manifest, _ = load_manifest(bundle)
        check_sources(manifest, args.vllm_source, args.ascend_source)
        print(json.dumps({"source_compatible": True, "installed": False}))
    else:
        if args.output is None:
            parser.error("materialize requires --output")
        print(json.dumps(materialize(
            bundle, args.vllm_source, args.ascend_source, args.output,
        )))


if __name__ == "__main__":
    main()
