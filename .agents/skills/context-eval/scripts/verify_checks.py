#!/usr/bin/env python3
"""Grader self-validation gate for a context-eval corpus.

Stages every task in a throwaway workspace and proves each grader can fail
before anything bills: the reference overlay must score exactly 1.0, and the
bare fixture, the naive overlay, and every decoy-* overlay must score below
1.0. Any miss exits 1. Run this before any agent run.

Gate discipline ported from [ECC](https://github.com/affaan-m/ECC) (MIT),
`docker/context-profiles/complex-eval/verify-checks.js`.

Corpus layout (one directory per task):

    tasks/<id>/files/      fixture repo the agent works on
    tasks/<id>/grader.py   hidden grader; prints one EVAL_SCORE line
    tasks/<id>/meta.json   optional: {"timeout_s": 60}
    tasks/<id>/reference/  correct solution overlaid on files/
    tasks/<id>/naive/      plausible-but-wrong overlay
    tasks/<id>/decoy-*/    right shape, wrong content

Usage:
    python3 verify_checks.py [corpus_dir] [--timeout SECONDS]
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SENTINEL = re.compile(r"^\s*EVAL_SCORE\s+(\{.*\})\s*$", re.MULTILINE)
GRADER_NAME = ".eval-grader.py"


def copy_tree(source: Path, destination: Path) -> None:
    """Copy every entry under source into destination, creating directories."""
    for entry in sorted(source.rglob("*")):
        target = destination / entry.relative_to(source)
        if entry.is_dir():
            target.mkdir(exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, target)


def score(workspace: Path, grader_source: str, timeout: float) -> float:
    """Run one grader inside a staged workspace and parse its sentinel line.

    The grader is copied in under a name the fixture never mentions, run, and
    deleted. Exit 0 with no sentinel line is a grader that died mid-run: a
    zero, never a silent pass. Nonzero exits and scores outside 0..1 score 0.
    """
    planted = workspace / GRADER_NAME
    if planted.exists():  # the workspace itself must not ship a grader
        return 0.0
    planted.write_text(grader_source)
    try:
        run = subprocess.run([sys.executable, planted.name], cwd=workspace,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 0.0
    finally:
        planted.unlink(missing_ok=True)
    match = SENTINEL.search(run.stdout)
    if run.returncode != 0 or match is None:
        return 0.0
    try:
        value = json.loads(match.group(1)).get("score")
    except json.JSONDecodeError:
        return 0.0
    if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
        return 0.0
    return float(value)


def run_overlay(task: Path, grader_source: str, overlay, timeout: float):
    """Stage files/ plus an optional overlay in a fresh temp dir and score it."""
    with tempfile.TemporaryDirectory(prefix="context-eval-") as tmp:
        workspace = Path(tmp)
        copy_tree(task / "files", workspace)
        if overlay is not None:
            copy_tree(overlay, workspace)
        return score(workspace, grader_source, timeout)


def check_task(task: Path, grader_source: str, timeout: float):
    """Score the bare fixture and every overlay. Return (ok, {name: score})."""
    if not (task / "files").is_dir():
        return False, {}
    names = ["reference", "naive"] + [d.name for d in sorted(task.glob("decoy-*"))]
    results = {"fixture": run_overlay(task, grader_source, None, timeout)}
    for name in names:
        if (task / name).is_dir():
            results[name] = run_overlay(task, grader_source, task / name, timeout)
    ok = results.get("reference") == 1.0 and all(
        value < 1.0 for name, value in results.items() if name != "reference"
    )
    return ok, results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Grader self-validation gate.")
    parser.add_argument("corpus", nargs="?", default="tasks", type=Path,
                        help="corpus dir with one task dir per task (default: tasks)")
    parser.add_argument("--timeout", type=float, default=60.0,
                        help="grader timeout in seconds (default: 60)")
    args = parser.parse_args(argv)
    if not args.corpus.is_dir():
        parser.error(f"corpus dir not found: {args.corpus}")
    tasks = [p for p in sorted(args.corpus.iterdir()) if (p / "grader.py").is_file()]
    if not tasks:
        print(f"no tasks under {args.corpus} (expected <id>/grader.py)", file=sys.stderr)
        return 1
    failed = 0
    for task in tasks:
        grader_source = (task / "grader.py").read_text()
        timeout = args.timeout
        meta = task / "meta.json"
        if meta.is_file():
            timeout = float(json.loads(meta.read_text()).get("timeout_s", timeout))
        ok, results = check_task(task, grader_source, timeout)
        failed += not ok
        detail = " ".join(f"{name}={value:.3f}" for name, value in results.items())
        print(f"{'ok' if ok else 'FAIL'} - {task.name}: {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
