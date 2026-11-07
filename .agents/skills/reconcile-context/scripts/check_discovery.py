#!/usr/bin/env python3
"""Check the integrity of the .agents/ source of truth.

Exit 0 if integrity holds, 1 if a collection is missing, a SKILL.md
entrypoint is missing, not a file, or escapes .agents/, an agent id is
duplicated or malformed, or a tree entry is orphaned. Stdlib only; safe
for hooks.
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
    and foo.md), which would silently shadow one source, or if a directory
    layout persona is missing its <name>/agent.md (the id would otherwise
    drop out of link validation while the directory still masks orphan
    detection).
    """
    if not os.path.isdir(parent):
        return []
    dir_ids: set[str] = set()
    flat_ids: set[str] = set()
    malformed_dirs: list[str] = []
    for name in os.listdir(parent):
        full = os.path.join(parent, name)
        if os.path.isdir(full):
            if os.path.isfile(os.path.join(full, "agent.md")):
                dir_ids.add(name)
            else:
                malformed_dirs.append(name)
        elif name.endswith(".md") and name != "README.md" and os.path.isfile(full):
            flat_ids.add(name[:-3])
    duplicates = dir_ids & flat_ids
    if duplicates:
        raise ValueError(
            f"DUPLICATE_ID: duplicate agent ids in {parent}: both directory "
            f"and flat-file layouts exist for {sorted(duplicates)}"
        )
    if malformed_dirs:
        raise ValueError(
            f"MISSING_AGENT_MD: agent directories in {parent} missing "
            f"agent.md: {sorted(malformed_dirs)}"
        )
    return sorted(dir_ids | flat_ids)


def _check_contained(
    path: str,
    ancestor: str,
    kind: str,
    failures: list[tuple[str, str, str, str | None]],
) -> None:
    """Require path to resolve strictly beneath ancestor.

    The ancestor is treated as a literal path (not resolved through symlinks)
    via `os.path.abspath`, while the target is followed through symlinks via
    `os.path.realpath`.  A symlinked `.agents/` cannot therefore move the
    trusted boundary outside the repository: the literal ancestor stays inside
    the repo even when the resolved target escapes.
    """
    real = os.path.realpath(path)
    lit = os.path.abspath(ancestor)
    try:
        contained = os.path.commonpath([lit, real]) == lit
    except ValueError:
        contained = False
    if not contained or real == lit:
        failures.append(("ESCAPES", kind, _rel(path), _rel(ancestor)))


def _check_regular_file(
    path: str,
    kind: str,
    failures: list[tuple[str, str, str, str | None]],
) -> None:
    """Require a source-of-truth target to resolve to a regular file."""
    if os.path.lexists(path) and not os.path.isfile(path):
        failures.append(("NOT_A_FILE", kind, _rel(path), None))


def _orphan_entries(
    tree_dir: str,
    sot_ids: set[str],
    kind: str,
    *,
    md_only: bool,
    failures: list[tuple[str, str, str, str | None]],
) -> None:
    """Fail on tree entries with no SoT peer. Skip README.md."""
    if not os.path.isdir(tree_dir):
        return
    for name in sorted(os.listdir(tree_dir)):
        if name == "README.md":
            continue
        path = os.path.join(tree_dir, name)
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
    # Missing source-of-truth collections must fail loudly rather than
    # enumerate as empty: a deleted .agents/skills/ would otherwise yield
    # no skills, no orphans, and a false OK.
    if not os.path.isdir(agents_sot):
        failures.append(("MISSING", "agents-sot", _rel(agents_sot), None))
    if not os.path.isdir(skills_sot):
        failures.append(("MISSING", "skills-sot", _rel(skills_sot), None))
    skill_ids = _sot_ids(skills_sot)
    for skill_id in skill_ids:
        # The SKILL.md entrypoint is what consumers actually load; the
        # containing directory alone can resolve while the entrypoint is
        # deleted, replaced by a directory, or symlinked outside .agents/.
        expected_skill_md = os.path.join(skills_sot, skill_id, "SKILL.md")
        _check_contained(
            expected_skill_md,
            os.path.join(ROOT, ".agents"),
            "skill-md-sot",
            failures,
        )
        if not os.path.lexists(expected_skill_md):
            failures.append(("MISSING", "skill-md-sot", _rel(expected_skill_md), None))
        else:
            _check_regular_file(expected_skill_md, "skill-md-sot", failures)
    try:
        agent_ids = _agent_sot_ids(agents_sot)
    except ValueError as exc:
        # Skill SoT / SKILL.md checks already ran; emit those before
        # returning so a malformed agent directory does not hide them.
        for code, kind, rel, expected in failures:
            if expected is None:
                print(f"{code} [{kind}] {rel}")
            else:
                print(f"{code} [{kind}] {rel} -> {expected}")
        print(f"[agent-sot] {exc}")
        print(f"\n{len(failures) + 1} source-of-truth integrity failure(s).")
        return 1
    # --- Orphan detection within the .agents trees ---
    # The id and entrypoint checks cover every loadable entry; a top-level
    # entry they cannot classify (a stray file) is dead weight no consumer
    # loads.
    expected_agent_names = set()
    for agent_id in agent_ids:
        if os.path.isdir(os.path.join(agents_sot, agent_id)):
            expected_agent_names.add(agent_id)
        else:
            expected_agent_names.add(f"{agent_id}.md")
    _orphan_entries(
        agents_sot,
        expected_agent_names,
        "agent-sot",
        md_only=False,
        failures=failures,
    )
    _orphan_entries(
        skills_sot,
        set(skill_ids),
        "skill-sot",
        md_only=False,
        failures=failures,
    )

    for code, kind, rel, expected in failures:
        if expected is None:
            print(f"{code} [{kind}] {rel}")
        else:
            print(f"{code} [{kind}] {rel} -> {expected}")

    if failures:
        print(f"\n{len(failures)} source-of-truth integrity failure(s).")
        return 1
    print("Source-of-truth integrity OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
