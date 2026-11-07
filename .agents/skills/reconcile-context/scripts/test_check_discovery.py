#!/usr/bin/env python3
"""Regression tests for check_discovery.py (filesystem fixtures only)."""

from __future__ import annotations

import contextlib
import io
import os
import shutil
import tempfile
import unittest

import check_discovery


class CheckDiscoveryTest(unittest.TestCase):
    def run_checker(self, root: str) -> tuple[int, str]:
        old_root = check_discovery.ROOT
        output = io.StringIO()
        try:
            # Match check_discovery.ROOT (realpath): macOS /var → /private/var.
            check_discovery.ROOT = os.path.realpath(root)
            with contextlib.redirect_stdout(output):
                status = check_discovery.main()
            return status, output.getvalue()
        finally:
            check_discovery.ROOT = old_root

    def _write(self, path: str, text: str = "") -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _happy_tree(self, root: str) -> None:
        agent_md = os.path.join(root, ".agents", "agents", "example", "agent.md")
        skill_dir = os.path.join(root, ".agents", "skills", "demo")
        self._write(agent_md, "# Example\n")
        self._write(os.path.join(skill_dir, "SKILL.md"), "# Demo\n")
        self._write(os.path.join(root, "AGENTS.md"), "# Agents\n")

    def test_happy_path_exits_zero(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("Source-of-truth integrity OK.", output)

    def _flat_file_tree(self, root: str) -> None:
        """Like _happy_tree but agents are flat .md files, not directories."""
        agent_md = os.path.join(root, ".agents", "agents", "example.md")
        skill_dir = os.path.join(root, ".agents", "skills", "demo")
        self._write(agent_md, "# Example\n")
        self._write(os.path.join(skill_dir, "SKILL.md"), "# Demo\n")
        self._write(os.path.join(root, "AGENTS.md"), "# Agents\n")

    def test_flat_file_agents_exits_zero(self):
        with tempfile.TemporaryDirectory() as root:
            self._flat_file_tree(root)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("Source-of-truth integrity OK.", output)

    def test_duplicate_dir_and_flat_agent_ids(self):
        with tempfile.TemporaryDirectory() as root:
            self._flat_file_tree(root)
            # Also create the directory-based layout for the same agent id
            self._write(
                os.path.join(root, ".agents", "agents", "example", "agent.md"),
                "# Example\n",
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("DUPLICATE_ID", output)

    def test_missing_agents_sot_directory(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            # Deleting the agents source of truth must fail loudly, not
            # enumerate as empty and report an OK.
            shutil.rmtree(os.path.join(root, ".agents", "agents"))

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("MISSING [agents-sot] .agents/agents", output)

    def test_missing_skills_sot_directory(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            # Deleting the skills source of truth must fail loudly, not
            # enumerate as empty and report an OK.
            shutil.rmtree(os.path.join(root, ".agents", "skills"))

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("MISSING [skills-sot] .agents/skills", output)

    def test_skill_md_replaced_by_directory(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            # The skill directory still resolves, so only a type check catches
            # an entrypoint no consumer can read.
            skill_md = os.path.join(root, ".agents", "skills", "demo", "SKILL.md")
            os.unlink(skill_md)
            os.makedirs(skill_md)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn(
                "NOT_A_FILE [skill-md-sot] .agents/skills/demo/SKILL.md", output
            )

    def test_skill_md_symlinked_outside_agents(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            # The skill directory still resolves; the entrypoint itself
            # redirects outside .agents/ and must be caught.
            self._write(os.path.join(root, "outside", "SKILL.md"), "# Evil\n")
            skill_md = os.path.join(root, ".agents", "skills", "demo", "SKILL.md")
            os.unlink(skill_md)
            os.symlink(os.path.join("..", "..", "..", "outside", "SKILL.md"), skill_md)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("ESCAPES [skill-md-sot] .agents/skills/demo/SKILL.md", output)

    def test_skill_md_deleted(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            # The skill directory still resolves, so a deleted entrypoint must
            # fail explicitly rather than report an OK.
            skill_md = os.path.join(root, ".agents", "skills", "demo", "SKILL.md")
            os.unlink(skill_md)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("MISSING [skill-md-sot] .agents/skills/demo/SKILL.md", output)

    def test_directory_agent_missing_agent_md(self):
        """Directory persona that lost its agent.md must fail, not drop out
        of validation while the directory masks orphan detection."""
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            os.unlink(os.path.join(root, ".agents", "agents", "example", "agent.md"))

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("MISSING_AGENT_MD", output)

    def test_orphan_file_in_skills_tree(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            # A stray non-directory entry is not a skill and no consumer
            # can load it.
            self._write(os.path.join(root, ".agents", "skills", "stray.md"), "junk\n")

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("ORPHAN [skill-sot] .agents/skills/stray.md", output)

    def test_orphan_file_in_agents_tree(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            self._write(os.path.join(root, ".agents", "agents", "notes.txt"), "junk\n")

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("ORPHAN [agent-sot] .agents/agents/notes.txt", output)

    def test_readme_files_are_exempt(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            self._write(os.path.join(root, ".agents", "skills", "README.md"), "# Toc\n")
            self._write(os.path.join(root, ".agents", "agents", "README.md"), "# Toc\n")

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("Source-of-truth integrity OK.", output)


if __name__ == "__main__":
    unittest.main()
