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

        claude_agents = os.path.join(root, ".claude", "agents")
        os.makedirs(claude_agents, exist_ok=True)

        os.symlink(
            os.path.join("..", "..", ".agents", "agents", "example", "agent.md"),
            os.path.join(claude_agents, "example.md"),
        )
        os.symlink(
            os.path.join("..", ".agents", "skills"),
            os.path.join(root, ".claude", "skills"),
        )
        os.symlink("AGENTS.md", os.path.join(root, "CLAUDE.md"))

    def test_happy_path_exits_zero(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("Discovery parity OK.", output)

    def test_claude_md_regular_file_is_not_symlink(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            claude = os.path.join(root, "CLAUDE.md")
            os.unlink(claude)
            with open(claude, "w", encoding="utf-8") as fh:
                fh.write("# Agents\n")

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("NOT_SYMLINK [claude-md] CLAUDE.md", output)

    def test_wrong_target_claude_agent(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            wrong = os.path.join(root, ".agents", "skills", "demo", "SKILL.md")
            link = os.path.join(root, ".claude", "agents", "example.md")
            os.unlink(link)
            os.symlink(
                os.path.join("..", "..", ".agents", "skills", "demo", "SKILL.md"),
                link,
            )
            self.assertTrue(os.path.exists(wrong))

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn(
                "WRONG_TARGET [agent-claude] .claude/agents/example.md"
                " -> .agents/agents/example/agent.md",
                output,
            )

    def _flat_file_tree(self, root: str) -> None:
        """Like _happy_tree but agents are flat .md files, not directories."""
        agent_md = os.path.join(root, ".agents", "agents", "example.md")
        skill_dir = os.path.join(root, ".agents", "skills", "demo")
        self._write(agent_md, "# Example\n")
        self._write(os.path.join(skill_dir, "SKILL.md"), "# Demo\n")
        self._write(os.path.join(root, "AGENTS.md"), "# Agents\n")

        claude_agents = os.path.join(root, ".claude", "agents")
        os.makedirs(claude_agents, exist_ok=True)

        os.symlink(
            os.path.join("..", "..", ".agents", "agents", "example.md"),
            os.path.join(claude_agents, "example.md"),
        )
        os.symlink(
            os.path.join("..", ".agents", "skills"),
            os.path.join(root, ".claude", "skills"),
        )
        os.symlink("AGENTS.md", os.path.join(root, "CLAUDE.md"))

    def test_flat_file_agents_exits_zero(self):
        with tempfile.TemporaryDirectory() as root:
            self._flat_file_tree(root)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("Discovery parity OK.", output)

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
            # Deleting the agents source of truth (with its discovery mirrors)
            # must fail loudly, not enumerate as empty and report parity OK.
            shutil.rmtree(os.path.join(root, ".agents", "agents"))
            shutil.rmtree(os.path.join(root, ".claude", "agents"))

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("MISSING [agents-sot] .agents/agents", output)

    def test_missing_skills_sot_directory(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            # Deleting the skills source of truth (with its discovery mirrors)
            # must fail loudly, not enumerate as empty and report parity OK.
            shutil.rmtree(os.path.join(root, ".agents", "skills"))
            os.unlink(os.path.join(root, ".claude", "skills"))

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("MISSING [skills-sot] .agents/skills", output)

    def test_skill_md_replaced_by_directory(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            # The discovery links still resolve to the skill directory, so only
            # a type check catches an entrypoint no harness can read.
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
            # Claude still resolves the skill directory; the entrypoint
            # itself redirects outside .agents/ and must be caught.
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
            # The discovery links point at the skill directory, so a deleted
            # entrypoint must fail explicitly rather than report parity OK.
            skill_md = os.path.join(root, ".agents", "skills", "demo", "SKILL.md")
            os.unlink(skill_md)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("MISSING [skill-md-sot] .agents/skills/demo/SKILL.md", output)

    def test_directory_level_agent_symlinks(self):
        """Repo layout where .claude/agents is a directory-level symlink
        onto the source of truth."""
        with tempfile.TemporaryDirectory() as root:
            agent_md = os.path.join(root, ".agents", "agents", "example", "agent.md")
            skill_dir = os.path.join(root, ".agents", "skills", "demo")
            self._write(agent_md, "# Example\n")
            self._write(os.path.join(skill_dir, "SKILL.md"), "# Demo\n")
            self._write(os.path.join(root, "AGENTS.md"), "# Agents\n")
            os.symlink("AGENTS.md", os.path.join(root, "CLAUDE.md"))

            os.makedirs(os.path.join(root, ".claude"), exist_ok=True)
            os.symlink(
                os.path.join("..", ".agents", "agents"),
                os.path.join(root, ".claude", "agents"),
            )
            os.symlink(
                os.path.join("..", ".agents", "skills"),
                os.path.join(root, ".claude", "skills"),
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("Discovery parity OK.", output)

    def test_flat_agent_files_with_dir_symlink(self):
        """Flat .md agent files under .agents/agents/ with directory-level
        discovery symlinks."""
        with tempfile.TemporaryDirectory() as root:
            agent_md = os.path.join(root, ".agents", "agents", "project-manager.md")
            skill_dir = os.path.join(root, ".agents", "skills", "demo")
            self._write(agent_md, "# PM\n")
            self._write(os.path.join(skill_dir, "SKILL.md"), "# Demo\n")
            self._write(os.path.join(root, "AGENTS.md"), "# Agents\n")
            os.symlink("AGENTS.md", os.path.join(root, "CLAUDE.md"))

            os.makedirs(os.path.join(root, ".claude"), exist_ok=True)
            os.symlink(
                os.path.join("..", ".agents", "agents"),
                os.path.join(root, ".claude", "agents"),
            )
            os.symlink(
                os.path.join("..", ".agents", "skills"),
                os.path.join(root, ".claude", "skills"),
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("Discovery parity OK.", output)

    def test_wrong_target_agent_directory_symlinks(self):
        """A directory-level symlink pointing anywhere other than the
        source of truth must fail."""
        for harness in ("claude",):
            with self.subTest(harness=harness), tempfile.TemporaryDirectory() as root:
                self._happy_tree(root)
                agents = os.path.join(root, f".{harness}", "agents")
                os.unlink(os.path.join(agents, "example.md"))
                os.rmdir(agents)
                os.symlink(os.path.join("..", ".agents", "skills"), agents)

                status, output = self.run_checker(root)

                self.assertEqual(1, status)
                self.assertIn(
                    f"WRONG_TARGET [agents-{harness}] .{harness}/agents"
                    " -> .agents/agents",
                    output,
                )

    def test_directory_agent_missing_agent_md(self):
        """Directory persona that lost its agent.md must fail, not drop out
        of validation while the directory masks orphan detection."""
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            os.unlink(os.path.join(root, ".agents", "agents", "example", "agent.md"))

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("MISSING_AGENT_MD", output)


if __name__ == "__main__":
    unittest.main()
