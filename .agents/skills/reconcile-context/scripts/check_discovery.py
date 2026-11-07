#!/usr/bin/env python3
"""Check Claude Code discovery symlinks against the .agents/ source of truth.

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


def _agent_expected(parent: str, agent_id: str) -> str:
    """Resolve the source-of-truth path for an agent (directory or flat file)."""
    dir_path = os.path.join(parent, agent_id, "agent.md")
    if os.path.exists(dir_path):
        return dir_path
    return os.path.join(parent, f"{agent_id}.md")


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
    # Missing source-of-truth collections must fail loudly rather than
    # enumerate as empty: a deleted .agents/skills/ would otherwise yield
    # no skills, no orphans, and a false parity OK.
    if not os.path.isdir(agents_sot):
        failures.append(("MISSING", "agents-sot", _rel(agents_sot), None))
    if not os.path.isdir(skills_sot):
        failures.append(("MISSING", "skills-sot", _rel(skills_sot), None))
    skill_ids = _sot_ids(skills_sot)
    for skill_id in skill_ids:
        # The SKILL.md entrypoint is what Claude Code actually loads; the
        # containing directory alone can resolve while the entrypoint is
        # deleted, replaced by a directory, or symlinked outside .agents/.
        # A deleted entrypoint must fail explicitly: the discovery symlinks
        # point at the directory, so nothing else catches the absence.
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
        print(f"\n{len(failures) + 1} discovery parity failure(s).")
        return 1
    agent_id_set = set(agent_ids)

    # --- Agent discovery ---
    # Two valid layouts:
    #   1. Directory-level symlink: .claude/agents -> ../.agents/agents
    #   2. Per-file symlinks: .claude/agents/<id>.md -> ../../.agents/agents/<id>.md
    for harness in ("claude",):
        disc_dir = os.path.join(ROOT, f".{harness}", "agents")
        if os.path.islink(disc_dir):
            if not os.path.exists(disc_dir):
                failures.append(
                    ("BROKEN", f"agents-{harness}", _rel(disc_dir), _rel(agents_sot))
                )
                continue
            if os.path.realpath(disc_dir) == os.path.realpath(agents_sot):
                continue  # directory-level symlink is sufficient
            failures.append(
                ("WRONG_TARGET", f"agents-{harness}", _rel(disc_dir), _rel(agents_sot))
            )
            continue
        if not os.path.isdir(disc_dir):
            failures.append(
                ("MISSING", f"agents-{harness}", _rel(disc_dir), _rel(agents_sot))
            )
            continue
        # Per-file layout: check each agent file.
        for agent_id in agent_ids:
            expected = _agent_expected(agents_sot, agent_id)
            _check_symlink(
                os.path.join(disc_dir, f"{agent_id}.md"),
                expected,
                f"agent-{harness}",
                failures,
            )

    # --- Skill discovery ---
    # Claude: .claude/skills -> ../.agents/skills (directory-level symlink).
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

    # --- Orphan detection ---
    # A directory-level symlink mirrors the SoT exactly, so only real
    # directories can hold orphans.
    for harness in ("claude",):
        disc_dir = os.path.join(ROOT, f".{harness}", "agents")
        if os.path.islink(disc_dir):
            continue
        _orphan_entries(
            disc_dir,
            agent_id_set,
            f"agent-{harness}",
            md_only=True,
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
