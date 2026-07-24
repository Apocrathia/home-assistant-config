#!/usr/bin/env python3
"""Regression tests for check_discovery.py (filesystem fixtures only)."""

from __future__ import annotations

import contextlib
import io
import os
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

        cursor_agents = os.path.join(root, ".cursor", "agents")
        claude_agents = os.path.join(root, ".claude", "agents")
        cursor_skills = os.path.join(root, ".cursor", "skills")
        os.makedirs(cursor_agents, exist_ok=True)
        os.makedirs(claude_agents, exist_ok=True)
        os.makedirs(cursor_skills, exist_ok=True)

        os.symlink(
            os.path.join("..", "..", ".agents", "agents", "example", "agent.md"),
            os.path.join(cursor_agents, "example.md"),
        )
        os.symlink(
            os.path.join("..", "..", ".agents", "agents", "example", "agent.md"),
            os.path.join(claude_agents, "example.md"),
        )
        os.symlink(
            os.path.join("..", "..", ".agents", "skills", "demo"),
            os.path.join(cursor_skills, "demo"),
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

    def test_missing_cursor_agent_link(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            os.unlink(os.path.join(root, ".cursor", "agents", "example.md"))

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("MISSING [agent-cursor] .cursor/agents/example.md", output)
            self.assertIn("discovery parity failure(s).", output)

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

    def test_orphan_cursor_skill(self):
        with tempfile.TemporaryDirectory() as root:
            self._happy_tree(root)
            os.symlink(
                os.path.join("..", "..", ".agents", "skills", "missing"),
                os.path.join(root, ".cursor", "skills", "ghost"),
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("ORPHAN [skill-cursor] .cursor/skills/ghost", output)

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


if __name__ == "__main__":
    unittest.main()
