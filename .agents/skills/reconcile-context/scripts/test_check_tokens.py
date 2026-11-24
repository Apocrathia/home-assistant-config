#!/usr/bin/env python3
"""Tests for check_tokens.py (filesystem fixtures only, no git)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_tokens

TOKEN = "{{project_name}}"


def skill_md(
    name: str, marker: bool, tokens: int, description_token: bool = False
) -> str:
    fm = f"""---
name: {name}
"""
    if marker:
        fm += "templatized: true\n"
    if description_token:
        fm += "description: >-\n  The skill that works on " + TOKEN + ".\n"
    else:
        fm += "description: >-\n  A folded description that renders as one line.\n"
    fm += "---\n\n# " + name + "\n\nBody text.\n"
    body_tokens = tokens - (1 if description_token else 0)
    assert body_tokens >= 0
    for i in range(body_tokens):
        fm += f"\nPosition {i} on {TOKEN} here.\n"
    return fm


class CheckTokensTest(unittest.TestCase):
    def run_checker(self, root: str) -> tuple[int, str]:
        old_root = check_tokens.ROOT
        old_argv = sys.argv
        output = io.StringIO()
        try:
            check_tokens.ROOT = os.path.realpath(root)
            sys.argv = ["check_tokens.py"]
            with contextlib.redirect_stdout(output):
                status = check_tokens.main()
            return status, output.getvalue()
        finally:
            check_tokens.ROOT = old_root
            sys.argv = old_argv

    def _write(self, path: str, text: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _skill(
        self,
        root: str,
        name: str,
        marker: bool,
        tokens: int,
        description_token: bool = False,
    ) -> None:
        self._write(
            os.path.join(root, "skills", name, "SKILL.md"),
            skill_md(name, marker, tokens, description_token),
        )

    def _consumer_skill(
        self,
        root: str,
        name: str,
        marker: bool,
        tokens: int,
        description_token: bool = False,
    ) -> None:
        self._write(
            os.path.join(root, ".agents", "skills", name, "SKILL.md"),
            skill_md(name, marker, tokens, description_token),
        )

    def _upstream_ref(self, root: str, token_counts: dict | None) -> None:
        obj = {"sha": "0" * 40, "synced_at": "2026-11-03T00:00:00Z"}
        if token_counts is not None:
            obj["token_counts"] = token_counts
        self._write(
            os.path.join(root, ".agents", "upstream-ref"),
            json.dumps(obj, indent=2) + "\n",
        )

    # ---- core layout ----

    def _happy_core(self, root: str) -> None:
        for name in (
            "find-work",
            "implement-change",
            "ship-work",
            "self-improve",
            "reconcile-context",
        ):
            self._skill(root, name, marker=True, tokens=1, description_token=True)
        self._skill(root, "contribute-upstream", marker=False, tokens=2)
        self._skill(root, "integrate-upstream", marker=False, tokens=1)
        self._skill(root, "alignment", marker=False, tokens=0)

    def test_core_happy_exit_zero(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_core(root)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("Token discipline holds in core layout.", output)
            self.assertTrue(output.rstrip().endswith("CHECK_TOKENS_DONE"))

    def test_core_templatized_skill_missing_marker_fails(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_core(root)
            self._skill(
                root, "find-work", marker=False, tokens=1, description_token=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("find-work", output)
            self.assertIn("does not say `templatized: true`", output)

    def test_core_doc_skill_rendered_fails(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_core(root)
            self._skill(root, "contribute-upstream", marker=False, tokens=0)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("lost its {{project_name}} documentation mentions", output)

    def test_core_doc_skill_with_marker_fails(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_core(root)
            self._skill(root, "integrate-upstream", marker=True, tokens=1)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("must stay byte-identical", output)

    def test_core_unmarked_skill_with_token_fails(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_core(root)
            self._skill(root, "retrospective", marker=False, tokens=1)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("without the templatized marker", output)

    def test_core_marker_without_token_fails(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_core(root)
            self._skill(root, "find-work", marker=True, tokens=0)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("carries the marker but contains no", output)

    # ---- consumer layout ----

    def _happy_consumer(self, root: str, manifest: dict | None) -> None:
        self._consumer_skill(root, "find-work", marker=True, tokens=0)
        self._consumer_skill(root, "contribute-upstream", marker=False, tokens=12)
        self._consumer_skill(root, "integrate-upstream", marker=False, tokens=8)
        self._consumer_skill(root, "alignment", marker=False, tokens=0)
        self._upstream_ref(root, manifest)

    def test_consumer_happy_exit_zero(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_consumer(
                root,
                {"contribute-upstream": 12, "integrate-upstream": 8},
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("Token discipline holds in consumer layout.", output)

    def test_consumer_rendered_doc_skill_fails_against_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_consumer(
                root,
                {"contribute-upstream": 12, "integrate-upstream": 8},
            )
            self._consumer_skill(root, "contribute-upstream", marker=False, tokens=0)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn(
                "holds 0 {{project_name}} but upstream-ref records 12", output
            )
            self.assertIn("issue #32", output)

    def test_consumer_unrendered_templatized_fails(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_consumer(
                root,
                {"contribute-upstream": 12, "integrate-upstream": 8},
            )
            self._consumer_skill(
                root, "find-work", marker=True, tokens=1, description_token=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("finish the render before shipping the scaffold", output)

    def test_consumer_unmarked_token_bearer_fails(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_consumer(
                root,
                {"contribute-upstream": 12, "integrate-upstream": 8},
            )
            self._consumer_skill(root, "retrospective", marker=False, tokens=1)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("is not marked templatized but holds 1 raw", output)

    def test_consumer_missing_manifest_reports(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_consumer(root, None)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("records no `token_counts`", output)

    def test_consumer_empty_token_counts_rejects_substituted_doc_skills(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_consumer(root, {})
            self._consumer_skill(root, "contribute-upstream", marker=False, tokens=0)
            self._consumer_skill(root, "integrate-upstream", marker=False, tokens=0)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn(
                ".agents/skills/contribute-upstream/SKILL.md lost its "
                "{{project_name}} documentation mentions",
                output,
            )
            self.assertIn(
                ".agents/skills/integrate-upstream/SKILL.md lost its "
                "{{project_name}} documentation mentions",
                output,
            )
            self.assertIn("records no `token_counts`", output)

    def test_consumer_empty_token_counts_with_mentions_reports_gap(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_consumer(root, {})

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("records no `token_counts`", output)
            self.assertNotIn("substituted", output)
            self.assertNotIn("lost its", output)
            self.assertEqual(output.count("FAIL"), 1)

    def test_consumer_partial_token_counts_checks_unrecorded_skill(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_consumer(root, {"contribute-upstream": 12})
            self._consumer_skill(root, "integrate-upstream", marker=False, tokens=0)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertNotIn("contribute-upstream/SKILL.md holds", output)
            self.assertIn(
                ".agents/skills/integrate-upstream/SKILL.md lost its "
                "{{project_name}} documentation mentions",
                output,
            )
            self.assertIn("records no `token_counts`", output)

    def test_consumer_partial_token_counts_still_compares_recorded_skill(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_consumer(root, {"contribute-upstream": 12})
            self._consumer_skill(root, "contribute-upstream", marker=False, tokens=0)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn(
                "holds 0 {{project_name}} but upstream-ref records 12", output
            )
            self.assertIn("records no `token_counts`", output)
            self.assertNotIn("integrate-upstream/SKILL.md lost", output)

    def test_consumer_bare_sha_pin_reports_manifest_missing(self):
        with tempfile.TemporaryDirectory() as root:
            self._consumer_skill(root, "find-work", marker=True, tokens=0)
            self._consumer_skill(root, "contribute-upstream", marker=False, tokens=12)
            self._write(os.path.join(root, ".agents", "upstream-ref"), "0" * 40 + "\n")

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("records no `token_counts`", output)
            # doc-skill token counts cannot be judged; only the manifest finding fires
            self.assertEqual(output.count("FAIL"), 1)

    def test_top_level_skills_do_not_select_core_mode(self):
        """A consumer skills/ tree must not hide .agents/skills/ (issue #32)."""
        with tempfile.TemporaryDirectory() as root:
            self._happy_consumer(
                root,
                {"contribute-upstream": 12, "integrate-upstream": 8},
            )
            # Own skill: a token here fails core rules and must be ignored.
            self._skill(root, "charts", marker=False, tokens=1)
            self._consumer_skill(
                root, "find-work", marker=True, tokens=1, description_token=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("consumer layout", output)
            self.assertIn("finish the render before shipping the scaffold", output)
            self.assertNotIn("without the templatized marker", output)
            self.assertNotIn("core layout", output)

    def test_both_layouts_present_healthy_consumer_ignores_own_skills(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_consumer(
                root,
                {"contribute-upstream": 12, "integrate-upstream": 8},
            )
            self._skill(root, "charts", marker=False, tokens=1)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("Token discipline holds in consumer layout.", output)
            self.assertNotIn("FAIL", output)

    def test_no_layout_skips(self):
        with tempfile.TemporaryDirectory() as root:
            self._write(os.path.join(root, "AGENTS.md"), "# not a layout\n")

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("No skills/ or .agents/skills/ layout found", output)


if __name__ == "__main__":
    unittest.main()
