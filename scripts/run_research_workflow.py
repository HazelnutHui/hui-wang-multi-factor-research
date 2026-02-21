import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


WORKFLOW_TO_SCRIPT = {
    "train_test": ROOT / "scripts" / "run_with_config.py",
    "segmented": ROOT / "scripts" / "run_segmented_factors.py",
    "walk_forward": ROOT / "scripts" / "run_walk_forward.py",
    "institutional_gates": ROOT / "scripts" / "run_institutional_gates.py",
    "statistical_gates": ROOT / "scripts" / "run_statistical_gates.py",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unified governed entrypoint for core research workflows."
    )
    parser.add_argument(
        "--workflow",
        required=True,
        choices=sorted(WORKFLOW_TO_SCRIPT.keys()),
        help="Workflow type: train_test / segmented / walk_forward",
    )
    parser.add_argument(
        "workflow_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to target workflow script. Use '--' before forwarded args.",
    )
    args = parser.parse_args()

    script = WORKFLOW_TO_SCRIPT[args.workflow]
    forwarded = list(args.workflow_args)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]

    cmd = [sys.executable, str(script)] + forwarded
    print("[dispatch]", " ".join(cmd), flush=True)
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT) if not existing else f"{ROOT}:{existing}"
    res = subprocess.run(cmd, cwd=str(ROOT), env=env)
    raise SystemExit(res.returncode)


if __name__ == "__main__":
    main()
