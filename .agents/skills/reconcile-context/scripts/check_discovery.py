#!/usr/bin/env python3
"""Check Cursor/Claude discovery symlinks against the .agents/ source of truth.

Exit 0 if parity holds, 1 if any discovery path is missing, broken, wrong,
not a symlink, or orphaned. Stdlib only; safe for hooks.
"""

from __future__ import annotations

import os
import sys


def _find_root(start):
    d = os.path.dirname(os.path.abspath(start))
    while True:
        if os.path.isdir(os.path.join(d, ".git")) or os.path.exists(
            os.path.join(d, "AGENTS.md")
        ):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise SystemExit(
                "could not locate repo root (no .git or AGENTS.md found above script)"
            )
        d = parent


# Canonicalize so realpath comparisons stay consistent across macOS /tmp
# (/private/tmp) and other symlink roots.
ROOT = os.path.realpath(_find_root(__file__))


def _rel(path: str) -> str:
    return os.path.relpath(path, ROOT)


def _sot_ids(parent: str) -> list[str]:
    """Directory names under parent (skip non-dirs)."""
    if not os.path.isdir(parent):
        return []
    return sorted(
        name for name in os.listdir(parent) if os.path.isdir(os.path.join(parent, name))
    )


def _agent_sot_ids(parent: str) -> list[str]:
    """Agent ids from directories (<name>/agent.md) or flat .md files (<name>.md).

    Raises ValueError if the same id appears in both layouts (e.g. foo/agent.md
    and foo.md), which would silently shadow one source.
    """
    if not os.path.isdir(parent):
        return []
    dir_ids: set[str] = set()
    flat_ids: set[str] = set()
    for name in os.listdir(parent):
        full = os.path.join(parent, name)
        if os.path.isdir(full) and os.path.isfile(os.path.join(full, "agent.md")):
            dir_ids.add(name)
        elif name.endswith(".md") and name != "README.md" and os.path.isfile(full):
            flat_ids.add(name[:-3])
    duplicates = dir_ids & flat_ids
    if duplicates:
        raise ValueError(
            f"duplicate agent ids in {parent}: both directory and flat-file "
            f"layouts exist for {sorted(duplicates)}"
        )
    return sorted(dir_ids | flat_ids)


def _agent_expected(parent: str, agent_id: str) -> str:
    """Resolve the source-of-truth path for an agent (directory or flat file)."""
    dir_path = os.path.join(parent, agent_id, "agent.md")
    if os.path.exists(dir_path):
        return dir_path
    return os.path.join(parent, f"{agent_id}.md")


def _check_symlink(
    path: str,
    expected: str,
    kind: str,
    failures: list[tuple[str, str, str, str | None]],
) -> None:
    """Require path to be a symlink whose realpath matches expected."""
    rel = _rel(path)
    expected_rel = _rel(expected)
    if not os.path.lexists(path):
        failures.append(("MISSING", kind, rel, expected_rel))
        return
    if not os.path.islink(path):
        failures.append(("NOT_SYMLINK", kind, rel, expected_rel))
        return
    # lexists is true for dangling symlinks; exists follows and is false.
    if not os.path.exists(path):
        failures.append(("BROKEN", kind, rel, expected_rel))
        return
    if os.path.realpath(path) != os.path.realpath(expected):
        failures.append(("WRONG_TARGET", kind, rel, expected_rel))
        return


def _orphan_entries(
    discovery_dir: str,
    sot_ids: set[str],
    kind: str,
    *,
    md_only: bool,
    failures: list[tuple[str, str, str, str | None]],
) -> None:
    """Fail on discovery entries with no SoT peer. Skip README.md."""
    if not os.path.isdir(discovery_dir):
        return
    for name in sorted(os.listdir(discovery_dir)):
        if name == "README.md":
            continue
        path = os.path.join(discovery_dir, name)
        if md_only:
            if not name.endswith(".md"):
                continue
            entry_id = name[:-3]
        else:
            entry_id = name
        if entry_id not in sot_ids:
            failures.append(("ORPHAN", kind, _rel(path), None))


def main() -> int:
    failures: list[tuple[str, str, str, str | None]] = []

    agents_sot = os.path.join(ROOT, ".agents", "agents")
    skills_sot = os.path.join(ROOT, ".agents", "skills")
    try:
        agent_ids = _agent_sot_ids(agents_sot)
    except ValueError as exc:
        print(f"DUPLICATE_ID [agent-sot] {exc}")
        print("\n1 discovery parity failure(s).")
        return 1
    skill_ids = _sot_ids(skills_sot)
    agent_id_set = set(agent_ids)
    skill_id_set = set(skill_ids)

    for agent_id in agent_ids:
        expected = _agent_expected(agents_sot, agent_id)
        _check_symlink(
            os.path.join(ROOT, ".cursor", "agents", f"{agent_id}.md"),
            expected,
            "agent-cursor",
            failures,
        )
        _check_symlink(
            os.path.join(ROOT, ".claude", "agents", f"{agent_id}.md"),
            expected,
            "agent-claude",
            failures,
        )

    for skill_id in skill_ids:
        expected = os.path.join(skills_sot, skill_id)
        _check_symlink(
            os.path.join(ROOT, ".cursor", "skills", skill_id),
            expected,
            "skill-cursor",
            failures,
        )

    _check_symlink(
        os.path.join(ROOT, ".claude", "skills"),
        skills_sot,
        "skills-claude",
        failures,
    )
    _check_symlink(
        os.path.join(ROOT, "CLAUDE.md"),
        os.path.join(ROOT, "AGENTS.md"),
        "claude-md",
        failures,
    )

    _orphan_entries(
        os.path.join(ROOT, ".cursor", "agents"),
        agent_id_set,
        "agent-cursor",
        md_only=True,
        failures=failures,
    )
    _orphan_entries(
        os.path.join(ROOT, ".claude", "agents"),
        agent_id_set,
        "agent-claude",
        md_only=True,
        failures=failures,
    )
    _orphan_entries(
        os.path.join(ROOT, ".cursor", "skills"),
        skill_id_set,
        "skill-cursor",
        md_only=False,
        failures=failures,
    )

    for code, kind, rel, expected in failures:
        if expected is None:
            print(f"{code} [{kind}] {rel}")
        else:
            print(f"{code} [{kind}] {rel} -> {expected}")

    if failures:
        print(f"\n{len(failures)} discovery parity failure(s).")
        return 1
    print("Discovery parity OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
