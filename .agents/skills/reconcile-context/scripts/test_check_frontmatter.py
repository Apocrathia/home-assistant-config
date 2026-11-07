#!/usr/bin/env python3
"""Tests for check_frontmatter.py (filesystem fixtures only, no git)."""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest

import check_frontmatter


GOOD_SKILL = """---
name: demo
description: >-
  A folded description that renders as one logical line in flat tables.
disable-model-invocation: true
---

# Demo

Body text.
"""

LITERAL_SKILL = """---
name: demo
description: |-
  A literal block scalar that keeps internal newlines.
---

# Demo

Body text.
"""


class CheckFrontmatterTest(unittest.TestCase):
    def run_checker(self, root: str, *args: str) -> tuple[int, str]:
        old_root = check_frontmatter.ROOT
        old_argv = sys.argv
        output = io.StringIO()
        try:
            # Match check_frontmatter.ROOT (realpath): macOS /var -> /private/var.
            check_frontmatter.ROOT = os.path.realpath(root)
            sys.argv = ["check_frontmatter.py", *args]
            with contextlib.redirect_stdout(output):
                status = check_frontmatter.main()
            return status, output.getvalue()
        finally:
            check_frontmatter.ROOT = old_root
            sys.argv = old_argv

    def _write(self, path: str, text: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _skill(self, root: str, name: str = "demo", text: str = GOOD_SKILL) -> str:
        path = os.path.join(root, "skills", name, "SKILL.md")
        self._write(path, text)
        return path

    def test_happy_skill_exit_zero(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(root)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("Validated 1 file(s)", output)
            self.assertNotIn("WARN", output)
            self.assertNotIn("FAIL", output)
            self.assertTrue(output.rstrip().endswith("CHECK_FRONTMATTER_DONE"))

    def test_folded_description_passes_strict(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(root)

            status, output = self.run_checker(root, "--strict")

            self.assertEqual(0, status, output)
            self.assertNotIn("WARN", output)

    def test_literal_block_description_warns_by_default(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(root, text=LITERAL_SKILL)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("WARN [literal-description] skills/demo/SKILL.md", output)
            self.assertIn("literal block scalar '|-'", output)
            self.assertIn("(1 warning)", output)

    def test_literal_block_description_fails_under_strict(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(root, text=LITERAL_SKILL)

            status, output = self.run_checker(root, "--strict")

            self.assertEqual(1, status)
            self.assertIn("FAIL [literal-description] skills/demo/SKILL.md", output)
            self.assertIn("1 frontmatter failure(s).", output)
            self.assertTrue(output.rstrip().endswith("CHECK_FRONTMATTER_DONE"))

    def test_name_mismatch_with_directory_warns(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(root, text=GOOD_SKILL.replace("name: demo", "name: other"))

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("WARN [name-mismatch] skills/demo/SKILL.md", output)
            self.assertIn("does not match directory 'demo'", output)

            status, output = self.run_checker(root, "--strict")

            self.assertEqual(1, status, output)
            self.assertIn("FAIL [name-mismatch]", output)

    def test_quoted_name_matches_directory(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(root, text=GOOD_SKILL.replace("name: demo", 'name: "demo"'))

            status, output = self.run_checker(root, "--strict")

            self.assertEqual(0, status, output)

    def test_missing_name_and_description(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(root, text="---\nlicense: MIT\n---\n\n# Demo\n")

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("WARN [missing-name]", output)
            self.assertIn("WARN [missing-description]", output)

    def test_no_frontmatter_block_warns(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(root, text="# Demo\n\nNo frontmatter.\n")

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("WARN [no-frontmatter] skills/demo/SKILL.md", output)

    def test_missing_skill_md_fails_without_strict(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "skills", "demo"))

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("FAIL [missing-skill-md] skills/demo", output)
            self.assertIn("1 frontmatter failure(s).", output)

    def test_empty_skill_md_fails_without_strict(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(root, text="")

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("FAIL [empty-file] skills/demo/SKILL.md", output)

    def test_empty_body_warns(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(
                root,
                text=("---\nname: demo\ndescription: >-\n  Folded.\n---\n"),
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("WARN [empty-body] skills/demo/SKILL.md", output)

    def test_unquoted_colon_in_value_is_invalid_yaml(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(
                root,
                text=(
                    "---\n"
                    "name: demo\n"
                    "description: Use when asked: sync\n"
                    "---\n\n# Demo\n"
                ),
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("WARN [invalid-yaml] skills/demo/SKILL.md", output)
            self.assertIn("unquoted value contains ': '", output)

            status, output = self.run_checker(root, "--strict")

            self.assertEqual(1, status, output)

    def test_quoted_description_with_colon_passes(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(
                root,
                text=(
                    "---\n"
                    "name: demo\n"
                    "description: 'Shape output: lead with the next action'\n"
                    "---\n\n# Demo\n"
                ),
            )

            status, output = self.run_checker(root, "--strict")

            self.assertEqual(0, status, output)

    def test_nested_mapping_is_not_a_flat_mapping_error(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(
                root,
                text=(
                    "---\n"
                    "name: demo\n"
                    "description: >-\n"
                    "  Folded.\n"
                    "metadata:\n"
                    '  tags: "demo"\n'
                    "  category: productivity\n"
                    "---\n\n# Demo\n"
                ),
            )

            status, output = self.run_checker(root, "--strict")

            self.assertEqual(0, status, output)

    def test_bare_top_level_line_is_invalid(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(
                root,
                text=(
                    "---\n"
                    "name: demo\n"
                    "not a key value line\n"
                    "description: Inline.\n"
                    "---\n\n# Demo\n"
                ),
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("WARN [invalid-yaml]", output)
            self.assertIn("flat mapping", output)

    def test_rules_checked_only_under_all(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(root)
            self._write(
                os.path.join(root, "rules", "general.md"),
                "---\nalwaysApply: true\ndescription: Voice\n---\n\n# General\n",
            )

            status, output = self.run_checker(root)
            self.assertEqual(0, status, output)
            self.assertIn("Validated 1 file(s)", output)

            status, output = self.run_checker(root, "--all")
            self.assertEqual(0, status, output)
            self.assertIn("Validated 2 file(s)", output)

            self._write(
                os.path.join(root, "rules", "broken.md"),
                "---\nalwaysApply: true\n---\n\n# Broken\n",
            )
            status, output = self.run_checker(root, "--all")
            self.assertEqual(0, status, output)
            self.assertIn("WARN [missing-description] rules/broken.md", output)

    def test_agent_templates_checked_under_all(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(root)
            self._write(
                os.path.join(root, "templates", "agents", "verifier.md.tmpl"),
                (
                    "---\n"
                    "name: verifier\n"
                    "description: >-\n"
                    "  Judge the artifact.\n"
                    "---\n\nYou are the verifier.\n"
                ),
            )

            status, output = self.run_checker(root)
            self.assertIn("Validated 1 file(s)", output)

            status, output = self.run_checker(root, "--all")
            self.assertEqual(0, status, output)
            self.assertIn("Validated 2 file(s)", output)

            self._write(
                os.path.join(root, "templates", "agents", "broken.md.tmpl"),
                "---\ndescription: Has one.\n---\nBody.\n",
            )
            status, output = self.run_checker(root, "--all")
            self.assertEqual(0, status, output)
            self.assertIn("WARN [missing-name] templates/agents/broken.md.tmpl", output)

    def test_consumer_layouts_checked(self):
        with tempfile.TemporaryDirectory() as root:
            self._write(
                os.path.join(root, ".agents", "skills", "demo", "SKILL.md"),
                GOOD_SKILL,
            )
            self._write(
                os.path.join(root, ".agents", "rules", "general.md"),
                "---\nalwaysApply: true\ndescription: Voice\n---\n\n# General\n",
            )
            self._write(
                os.path.join(root, ".agents", "agents", "qux", "agent.md"),
                "---\nname: qux\ndescription: Persona.\n---\n\nPersona body.\n",
            )

            status, output = self.run_checker(root)
            self.assertEqual(0, status, output)
            self.assertIn("Validated 1 file(s)", output)

            status, output = self.run_checker(root, "--all")
            self.assertEqual(0, status, output)
            self.assertIn("Validated 3 file(s)", output)

    def test_rules_readme_is_skipped(self):
        with tempfile.TemporaryDirectory() as root:
            self._skill(root)
            self._write(
                os.path.join(root, ".agents", "rules", "README.md"),
                "# Rules index, no frontmatter.\n",
            )

            status, output = self.run_checker(root, "--all")

            self.assertEqual(0, status, output)
            self.assertNotIn("README.md", output)

    def test_nothing_to_check_skips(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "docs"))

            status, output = self.run_checker(root, "--all")

            self.assertEqual(0, status, output)
            self.assertIn("No skill, rule, or agent files found", output)


if __name__ == "__main__":
    unittest.main()
