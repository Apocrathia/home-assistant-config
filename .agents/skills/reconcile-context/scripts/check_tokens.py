#!/usr/bin/env python3
"""Check `{{project_name}}` token discipline (issue #32).

The token has two roles in this package, and only one of them is renderable:

- Render positions live exclusively in skills whose frontmatter says
  `templatized: true`. A scaffold or sync renders them to the project name.
- `contribute-upstream` and `integrate-upstream` mention the token in prose
  as documentation of the convention itself. Those mentions must survive every
  render byte-identically; substituting the project name into them corrupts
  the skill (observed in six consuming repos — see issue #32).

The marker is the classifier. Nothing here greps a skill to decide whether it
is templatized; grep is the exact failure mode this check exists to end.

Modes are auto-detected. Exactly one mode runs — the rules are opposites.
`.agents/skills/` selects the consumer layout even when a top-level `skills/`
also exists: a consuming repo's own skills are not this package, and judging
them as the core would skip the rendered-token check entirely.

- **Core layout** (`skills/` exists, and `.agents/skills/` does not): the five
  known templatized skills must carry `templatized: true` and at least one
  token; the two doc skills must carry tokens and no marker; any other skill
  carrying a token or the marker fails.
- **Consumer layout** (`.agents/skills/` exists): skills marked `templatized:
  true` must be fully rendered (zero raw tokens); the two doc skills must
  keep their mentions, verified against the `token_counts` manifest recorded
  in `.agents/upstream-ref` at scaffold/sync time when present.

Exit 0 if nothing fails, 1 on failures. Hook-safe: read-only.
"""

from __future__ import annotations

import json
import os
import re
import sys

try:
    from check_frontmatter import extract_frontmatter, scan_frontmatter
except ImportError:  # deployed without the sibling script
    _FM_RE = re.compile(r"^---\n(.*?)\n---(?:\n|$)", re.S)

    def extract_frontmatter(content: str):
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        match = _FM_RE.match(content)
        if not match:
            return False, "", content
        return True, match.group(1), content[match.end() :]

    def scan_frontmatter(fm_text: str):
        values = {}
        for raw in fm_text.split("\n"):
            if raw and not raw[0].isspace() and ":" in raw:
                key, _, value = raw.partition(":")
                values[key.strip()] = value.strip()
        return values, None, []


TOKEN = "{{project_name}}"

# Versioned with this repo: the renderable set and the set that documents the
# token convention without being renderable.
TEMPLATIZED_SKILLS = {
    "find-work",
    "implement-change",
    "self-improve",
    "reconcile-context",
    "ship-work",
}
DOC_SKILLS = {"contribute-upstream", "integrate-upstream"}


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


def _marker_and_count(path: str):
    """Return (marker_present, marker_true, token_count) for one SKILL.md."""
    with open(path, encoding="utf-8-sig") as fh:
        content = fh.read()
    present, fm_text, _body = extract_frontmatter(content)
    marker_true = False
    if present:
        values, _indicator, _errors = scan_frontmatter(fm_text)
        marker_true = values.get("templatized") == "true"
    return present, marker_true, content.count(TOKEN)


def _iter_skills(skills_dir: str):
    if not os.path.isdir(skills_dir):
        return
    for name in sorted(os.listdir(skills_dir)):
        full = os.path.join(skills_dir, name)
        skill_md = os.path.join(full, "SKILL.md")
        if (
            name.startswith(".")
            or not os.path.isdir(full)
            or not os.path.isfile(skill_md)
        ):
            continue
        yield name, skill_md


def check_core(skills_dir: str, report):
    for name, skill_md in _iter_skills(skills_dir):
        _present, marker, count = _marker_and_count(skill_md)
        if name in TEMPLATIZED_SKILLS:
            if not marker:
                report(
                    f"skills/{name}/SKILL.md is one of the five templatized "
                    "skills but its frontmatter does not say `templatized: true`"
                )
            if count == 0:
                report(
                    f"skills/{name}/SKILL.md carries the marker but contains no "
                    f"{TOKEN} render positions"
                )
        elif name in DOC_SKILLS:
            if marker:
                report(
                    f"skills/{name}/SKILL.md documents the token convention and "
                    "must stay byte-identical; it must not carry "
                    "`templatized: true`"
                )
            if count == 0:
                report(
                    f"skills/{name}/SKILL.md lost its {TOKEN} documentation "
                    "mentions — restore them"
                )
        else:
            if marker:
                report(
                    f"skills/{name}/SKILL.md is not in the templatized set but "
                    "carries `templatized: true`; extend TEMPLATIZED_SKILLS in "
                    "check_tokens.py in the same change"
                )
            if count:
                report(
                    f"skills/{name}/SKILL.md contains {count} {TOKEN} without "
                    "the templatized marker — mark it or remove the token"
                )


def _load_manifest(ref_path: str):
    """Return token_counts from upstream-ref; tolerate JSON or a bare sha."""
    try:
        with open(ref_path, encoding="utf-8-sig") as fh:
            raw = fh.read().strip()
    except OSError:
        return None
    if raw.startswith("{"):
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return obj.get("token_counts") if isinstance(obj, dict) else None
    return None  # bare sha pin, or unreadable — no manifest recorded


def check_consumer(skills_dir: str, ref_path: str, report):
    manifest = _load_manifest(ref_path)
    for name, skill_md in _iter_skills(skills_dir):
        _present, marker, count = _marker_and_count(skill_md)
        rel = os.path.relpath(skill_md, ROOT)
        if marker:
            if count:
                report(
                    f"{rel} is marked templatized but still holds {count} raw "
                    f"{TOKEN} — finish the render before shipping the scaffold"
                )
            continue
        if name in DOC_SKILLS:
            expected = manifest.get(name) if isinstance(manifest, dict) else None
            if expected is None:
                # No count recorded for this skill (missing pin, {}, or a
                # dict that omits the key). Presence is the weak check: a
                # substituted copy holds zero tokens.
                if count == 0:
                    report(
                        f"{rel} lost its {TOKEN} documentation mentions — restore them"
                    )
                continue
            if count != expected:
                report(
                    f"{rel} holds {count} {TOKEN} but upstream-ref records "
                    f"{expected} — the mentions were substituted (issue #32); "
                    "restore the file byte-identical to the pinned core"
                )
            continue
        if count:
            report(
                f"{rel} is not marked templatized but holds {count} raw "
                f"{TOKEN} — either render it, mark it, or restore the "
                "byte-identical core copy"
            )
    # {} and a dict missing a doc-skill key are not a manifest. Only an
    # entry per doc skill makes the recorded counts authoritative.
    if not isinstance(manifest, dict) or any(
        manifest.get(name) is None for name in DOC_SKILLS
    ):
        report(
            ".agents/upstream-ref records no `token_counts` — re-run scaffold "
            "step 10 or an integrate-upstream sync pin write so rendered-token "
            "drift can be detected"
        )


def main() -> int:
    core_dir = os.path.join(ROOT, "skills")
    consumer_dir = os.path.join(ROOT, ".agents", "skills")
    ref_path = os.path.join(ROOT, ".agents", "upstream-ref")

    findings: list[str] = []

    # Consumer layout wins when both trees exist. A consuming repo installs
    # this package under .agents/skills/ and may also have a top-level skills/
    # for its own use; that directory is not the core, and core rules would
    # ignore rendered-token drift in .agents/skills/ and upstream-ref.
    if os.path.isdir(consumer_dir):
        mode = "consumer"
        check_consumer(consumer_dir, ref_path, findings.append)
    elif os.path.isdir(core_dir):
        mode = "core"
        check_core(core_dir, findings.append)
    else:
        print("No skills/ or .agents/skills/ layout found, skipping.")
        print("CHECK_TOKENS_DONE")
        return 0

    for finding in findings:
        print(f"FAIL [tokens] {finding}")
    if findings:
        print(f"\n{len(findings)} token-discipline failure(s) in {mode} layout.")
        print("CHECK_TOKENS_DONE")
        return 1
    print(f"Token discipline holds in {mode} layout.")
    print("CHECK_TOKENS_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
