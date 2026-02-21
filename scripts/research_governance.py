import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"), default=str)


def stable_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def current_git_commit(root: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            stderr=subprocess.DEVNULL,
            text=True,
        )
        s = out.strip()
        return s if s else None
    except Exception:
        return None


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)


def build_manifest(
    *,
    root: Path,
    runner: str,
    config_hash: str,
    run_scope: Dict[str, Any],
    cli_args: Dict[str, Any],
    output_root: Path,
) -> Dict[str, Any]:
    return {
        "runner": runner,
        "run_at": datetime.now().isoformat(),
        "git_commit": current_git_commit(root),
        "config_hash": config_hash,
        "run_scope": run_scope,
        "cli_args": cli_args,
        "output_root": str(output_root.resolve()),
    }


def enforce_freeze(
    *,
    freeze_file: str | None,
    manifest: Dict[str, Any],
    write_freeze: bool,
) -> None:
    if not freeze_file:
        return
    p = Path(freeze_file).expanduser().resolve()
    if p.exists():
        frozen = json.loads(p.read_text())
        frozen_hash = frozen.get("config_hash")
        frozen_commit = frozen.get("git_commit")
        cur_hash = manifest.get("config_hash")
        cur_commit = manifest.get("git_commit")
        if frozen_hash and frozen_hash != cur_hash:
            raise SystemExit(
                f"Freeze mismatch: config_hash differs. frozen={frozen_hash} current={cur_hash}"
            )
        if frozen_commit and cur_commit and frozen_commit != cur_commit:
            raise SystemExit(
                f"Freeze mismatch: git_commit differs. frozen={frozen_commit} current={cur_commit}"
            )
        return
    if not write_freeze:
        raise SystemExit(
            f"Freeze file not found: {p}. Re-run with --write-freeze to create it from current run."
        )
    write_json(
        p,
        {
            "frozen_at": datetime.now().isoformat(),
            "runner": manifest.get("runner"),
            "git_commit": manifest.get("git_commit"),
            "config_hash": manifest.get("config_hash"),
            "run_scope": manifest.get("run_scope"),
            "notes": "Created by research governance freeze flow.",
        },
    )


def check_non_negative_int(name: str, value: Any, errors: list[str]) -> None:
    if value is None:
        return
    try:
        iv = int(value)
    except Exception:
        errors.append(f"{name} must be int-like, got {value!r}")
        return
    if iv < 0:
        errors.append(f"{name} must be >= 0, got {iv}")


def check_path_exists(name: str, path_value: Any, errors: list[str], must_be_dir: bool = True) -> None:
    if path_value is None or str(path_value).strip() == "":
        errors.append(f"{name} is required but missing")
        return
    p = Path(str(path_value)).expanduser().resolve()
    if not p.exists():
        errors.append(f"{name} path does not exist: {p}")
        return
    if must_be_dir and not p.is_dir():
        errors.append(f"{name} must be a directory: {p}")
