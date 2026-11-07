#!/usr/bin/env python3
"""Check the frontmatter shape of skills, rules, and agent templates.

Exit 0 if nothing fails, 1 on structural failures. Safe to run from a hook.

Default surface: skills/*/SKILL.md and .agents/skills/*/SKILL.md. Pass --all
to also check rules/*.md, .agents/rules/*.md (README.md is an index, not a
rule), templates/agents/*.tmpl, and .agents/agents/ personas.

Every skill must carry a flat YAML frontmatter block with `name` (matching
the directory) and `description`. Harnesses render `description` into flat
tables, so a literal block scalar (`|`) — which preserves internal newlines
— silently breaks them; folded (`>`) and inline scalars are fine.

Frontmatter findings warn by default so an adopting repo does not fail on
day one; pass --strict to promote them to failures. Structural failures
(skill directory without a SKILL.md, empty or unreadable file) always fail.

Parsing is a deliberate flat-mapping scan, stdlib only. Frontmatter in
this protocol is a flat `key: value` mapping, so a full YAML parser adds
nothing — and an `import yaml` has been observed to deadlock on system
Pythons with a broken user-site PyYAML, which no hook-safe script can
afford.

Checks ported from [ECC](https://github.com/affaan-m/ECC) (MIT),
`scripts/ci/validate-skills.js`.
"""

from __future__ import annotations

import os
import re
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


ROOT = os.path.realpath(_find_root(__file__))

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---(?:\n|$)", re.S)
_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
_BLOCK_IND_RE = re.compile(r"^[|>](?:[+-]?\d+|\d+[+-]?|[+-])?$")
_DQ_RE = re.compile(r'^"(?:[^"\\]|\\.)*"$')
_SQ_RE = re.compile(r"^'(?:[^']|'')*'$")


def _rel(path: str) -> str:
    return os.path.relpath(path, ROOT)


def extract_frontmatter(content: str) -> tuple[bool, str, str]:
    """Split a document into frontmatter text and body.

    Tolerant of UTF-8 BOM (via the utf-8-sig read) and CRLF. A file whose
    only `---` is the opening delimiter has no frontmatter block, same as
    a file with none — the body is then the whole file.
    """
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return False, "", content
    return True, match.group(1), content[match.end() :]


def _strip_yaml_comment(raw: str) -> str:
    """Strip a `#` comment, but only outside quoted scalars."""
    in_single = in_double = False
    i = 0
    while i < len(raw):
        ch = raw[i]
        if in_double and ch == "\\":
            i += 2
            continue
        if not in_double and ch == "'":
            if in_single and raw[i + 1 : i + 2] == "'":
                i += 1
            else:
                in_single = not in_single
            i += 1
            continue
        if not in_single and ch == '"':
            in_double = not in_double
            i += 1
            continue
        if (
            not in_single
            and not in_double
            and ch == "#"
            and (i == 0 or raw[i - 1].isspace())
        ):
            return raw[:i].strip()
        i += 1
    return raw.strip()


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def scan_frontmatter(fm_text: str):
    """Extract top-level keys and the description block-scalar indicator.

    Frontmatter here is a flat mapping: indented lines belong to nested
    structures or block scalars and never introduce top-level keys. Block
    scalars (`>` folded, `|` literal) consume every following line that is
    blank or more indented than their key. Plain values containing `: ` or
    starting with a reserved indicator (`@`, `` ` ``) are invalid YAML and
    are reported by name, since parse errors alone are not actionable.
    """
    values: dict[str, str] = {}
    syntax_errors: list[str] = []
    description_indicator = None
    block_key = None
    block_indent = 0
    block_folded = True
    block_lines: list[str] = []

    for raw in fm_text.split("\n"):
        if block_key is not None:
            stripped = raw.strip()
            indent = len(raw) - len(raw.lstrip())
            if stripped == "" or indent > block_indent:
                block_lines.append(stripped)
                continue
            values[block_key] = (
                " ".join(block_lines) if block_folded else "\n".join(block_lines)
            ).strip()
            block_key = None

        match = _KEY_RE.match(raw)
        if not match:
            # Indented lines are nested mapping entries or scalar content;
            # only a bare column-0 line makes the block a non-mapping.
            if raw and not raw[0].isspace() and not raw.startswith("#"):
                syntax_errors.append(
                    "frontmatter must be a flat mapping of 'key: value' lines"
                )
            continue
        key, raw_value = match.group(1), match.group(2)
        value = _strip_yaml_comment(raw_value)
        if _BLOCK_IND_RE.match(value):
            if key == "description":
                description_indicator = value
            block_key = key
            block_indent = len(raw) - len(raw.lstrip())
            block_folded = value[0] == ">"
            block_lines = []
            continue
        quoted = bool(_DQ_RE.match(value) or _SQ_RE.match(value))
        if not quoted and value:
            if ": " in value:
                syntax_errors.append(
                    f"{key}: unquoted value contains ': ' — quote the value"
                )
            if value[0] in "@`":
                syntax_errors.append(
                    f"{key}: unquoted value starts with reserved character "
                    f"'{value[0]}' — quote the value"
                )
        values[key] = _unquote(value)

    if block_key is not None:
        values[block_key] = (
            " ".join(block_lines) if block_folded else "\n".join(block_lines)
        ).strip()
    return values, description_indicator, syntax_errors


def _check_file(
    path: str,
    kind: str,
    expected_name: str | None,
    report,
) -> bool:
    """Run the frontmatter checks on one file. Returns True if it was read."""
    rel = _rel(path)
    try:
        with open(path, encoding="utf-8-sig") as fh:
            content = fh.read()
    except (OSError, UnicodeDecodeError) as err:
        report(True, "unreadable", rel, str(err).splitlines()[0])
        return False
    if not content.strip():
        report(True, "empty-file", rel, "file is empty")
        return True

    present, fm_text, body = extract_frontmatter(content)
    if not present:
        report(False, "no-frontmatter", rel, "no frontmatter block found")
        return True

    values, indicator, syntax_errors = scan_frontmatter(fm_text)
    for err in syntax_errors:
        report(False, "invalid-yaml", rel, err)

    if kind in ("skill", "agent"):
        if "name" not in values:
            report(
                False, "missing-name", rel, "frontmatter missing required field: name"
            )
        elif not values["name"].strip():
            report(False, "empty-name", rel, "frontmatter 'name' is empty")
        elif kind == "skill" and expected_name and values["name"] != expected_name:
            report(
                False,
                "name-mismatch",
                rel,
                f"frontmatter name '{values['name']}' does not match "
                f"directory '{expected_name}'",
            )

    if "description" not in values:
        report(
            False,
            "missing-description",
            rel,
            "frontmatter missing required field: description",
        )
    elif not values["description"].strip():
        report(False, "empty-description", rel, "frontmatter 'description' is empty")
    if indicator and indicator.startswith("|"):
        report(
            False,
            "literal-description",
            rel,
            f"description uses literal block scalar '{indicator}', which preserves "
            "internal newlines; use an inline string or folded '>' scalar instead",
        )

    if not body.strip():
        report(False, "empty-body", rel, "body is empty after frontmatter")
    return True


def _iter_files(check_all: bool, report):
    """Yield (path, kind, expected_name) plus structural failures.

    Both the core layout (skills/, rules/, templates/agents/) and the
    scaffolded consumer layout (.agents/skills/, .agents/rules/,
    .agents/agents/) are scanned, whichever exist. Realpath dedupe keeps
    a symlinked collection from being reported twice.
    """
    seen: set[str] = set()
    files = []
    for skills_dir in (
        os.path.join(ROOT, "skills"),
        os.path.join(ROOT, ".agents", "skills"),
    ):
        if not os.path.isdir(skills_dir):
            continue
        for name in sorted(os.listdir(skills_dir)):
            full = os.path.join(skills_dir, name)
            if name.startswith(".") or not os.path.isdir(full):
                continue
            skill_md = os.path.join(full, "SKILL.md")
            if not os.path.isfile(skill_md):
                report(
                    True,
                    "missing-skill-md",
                    _rel(full),
                    "no SKILL.md in skill directory",
                )
                continue
            real = os.path.realpath(skill_md)
            if real in seen:
                continue
            seen.add(real)
            files.append((skill_md, "skill", name))

    if check_all:
        for base in ("rules", os.path.join(".agents", "rules")):
            rules_dir = os.path.join(ROOT, base)
            if not os.path.isdir(rules_dir):
                continue
            for name in sorted(os.listdir(rules_dir)):
                if not name.endswith(".md") or name == "README.md":
                    continue
                path = os.path.join(rules_dir, name)
                real = os.path.realpath(path)
                if real in seen or not os.path.isfile(path):
                    continue
                seen.add(real)
                files.append((path, "rule", None))

        for base in (
            os.path.join("templates", "agents"),
            os.path.join(".agents", "agents"),
        ):
            agents_dir = os.path.join(ROOT, base)
            if not os.path.isdir(agents_dir):
                continue
            for name in sorted(os.listdir(agents_dir)):
                full = os.path.join(agents_dir, name)
                if name == "README.md" or name.startswith("."):
                    continue
                if os.path.isdir(full):
                    path = os.path.join(full, "agent.md")
                elif name.endswith((".md.tmpl", ".md")):
                    path = full
                else:
                    continue
                real = os.path.realpath(path)
                if real in seen or not os.path.isfile(path):
                    continue
                seen.add(real)
                files.append((path, "agent", None))

    yield from files


def main() -> int:
    args = sys.argv[1:]
    check_all = "--all" in args
    strict = "--strict" in args

    results: list[tuple[bool, str, str, str]] = []

    def report(is_failure: bool, code: str, rel: str, detail: str):
        results.append((is_failure, code, rel, detail))

    checked = 0
    for path, kind, expected_name in _iter_files(check_all, report):
        if _check_file(path, kind, expected_name, report):
            checked += 1

    findings = [r for r in results if not r[0]]
    failures = [r for r in results if r[0]]
    bad = failures + findings if strict else failures

    for is_failure, code, rel, detail in results:
        level = "FAIL" if (is_failure or strict) else "WARN"
        print(f"{level} [{code}] {rel} - {detail}")

    if bad:
        print(f"\n{len(bad)} frontmatter failure(s).")
        print("CHECK_FRONTMATTER_DONE")
        return 1
    if checked == 0:
        print("No skill, rule, or agent files found, skipping.")
        print("CHECK_FRONTMATTER_DONE")
        return 0
    message = f"Validated {checked} file(s)"
    if findings:
        plural = "s" if len(findings) != 1 else ""
        message += f" ({len(findings)} warning{plural})"
    print(message)
    print("CHECK_FRONTMATTER_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
