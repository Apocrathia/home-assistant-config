#!/usr/bin/env python3
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import check_links


class CheckLinksTest(unittest.TestCase):
    def run_checker(self, root, *args):
        old_root = check_links.ROOT
        old_argv = sys.argv
        output = io.StringIO()
        try:
            check_links.ROOT = root
            sys.argv = ["check_links.py", *args]
            with contextlib.redirect_stdout(output):
                status = check_links.main()
            return status, output.getvalue()
        finally:
            check_links.ROOT = old_root
            sys.argv = old_argv

    def test_untracked_markdown_target_with_existing_anchor_is_missing_file(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Target](./untracked.md#present-heading)\n")
            with open(os.path.join(root, "untracked.md"), "w", encoding="utf-8") as fh:
                fh.write("# Present Heading\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn(
                "BROKEN [missing file] AGENTS.md -> ./untracked.md#present-heading",
                output,
            )
            self.assertNotIn("missing anchor", output)

    def test_tracked_symlink_to_untracked_markdown_is_missing_file(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Direct](./untracked.md)\n")
            with open(os.path.join(root, "untracked.md"), "w", encoding="utf-8") as fh:
                fh.write("# Present\n")
            os.symlink("untracked.md", os.path.join(root, "alias.md"))
            subprocess.run(
                ["git", "add", "AGENTS.md", "alias.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./untracked.md", output)

    def test_no_anchor_tracked_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "docs"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Alias](./docs/alias.md)\n")
            with open(
                os.path.join(root, "docs", "real.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write("# Real\n")
            os.symlink("real.md", os.path.join(root, "docs", "alias.md"))
            subprocess.run(
                ["git", "add", "AGENTS.md", "docs/alias.md", "docs/real.md"],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [symlink] AGENTS.md -> ./docs/alias.md", output)

    def test_anchor_through_tracked_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "docs"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Alias](./docs/alias.md#real)\n")
            with open(
                os.path.join(root, "docs", "real.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write("# Real\n")
            os.symlink("real.md", os.path.join(root, "docs", "alias.md"))
            subprocess.run(
                ["git", "add", "AGENTS.md", "docs/alias.md", "docs/real.md"],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [symlink] AGENTS.md -> ./docs/alias.md#real", output)

    def test_tracked_markdown_target_allows_case_insensitive_path_match(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "docs"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Real](./docs/real.md#real)\n")
            with open(
                os.path.join(root, "docs", "Real.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write("# Real\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "docs/Real.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("All context links and anchors resolve.", output)

    def test_anchor_link_to_oversized_tracked_target_reports_read_failure(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "docs"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Huge](./docs/huge.md#heading)\n")
            with open(os.path.join(root, "docs", "huge.md"), "wb") as fh:
                fh.write(b"# Heading\n")
                fh.write(b"x" * (check_links.MAX_MARKDOWN_BYTES + 1))
            subprocess.run(
                ["git", "add", "AGENTS.md", "docs/huge.md"],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [larger than", output)
            self.assertIn("AGENTS.md -> ./docs/huge.md#heading", output)
            self.assertNotIn("missing anchor", output)

    def test_broken_context_symlink_is_reported_in_default_mode(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, ".agents", "context"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n")
            os.symlink("missing.md", os.path.join(root, ".agents", "context", "old.md"))
            subprocess.run(
                ["git", "add", "AGENTS.md", ".agents/context/old.md"],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [symlink] .agents/context/old.md", output)

    def test_broken_skill_link_is_reported_in_default_mode(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            skill_dir = os.path.join(root, ".agents", "skills", "example")
            os.makedirs(skill_dir, exist_ok=True)
            with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as fh:
                fh.write("[Missing](./missing.md)\n")
            subprocess.run(
                ["git", "add", ".agents/skills/example/SKILL.md"],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn(
                "BROKEN [missing file] .agents/skills/example/SKILL.md -> ./missing.md",
                output,
            )

    def test_agents_directory_above_root_does_not_expand_default_surface(self):
        with tempfile.TemporaryDirectory() as parent:
            root = os.path.join(parent, ".agents", "repo")
            docs_dir = os.path.join(root, "docs")
            os.makedirs(docs_dir)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(docs_dir, "page.md"), "w", encoding="utf-8") as fh:
                fh.write("[Missing](./missing.md)\n")
            subprocess.run(["git", "add", "docs/page.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)

    def test_markdown_suffix_case_insensitive_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "docs"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Alias](./docs/alias.MD)\n")
            with open(
                os.path.join(root, "docs", "real.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write("# Real\n")
            os.symlink("real.md", os.path.join(root, "docs", "alias.MD"))
            subprocess.run(
                ["git", "add", "AGENTS.md", "docs/alias.MD", "docs/real.md"],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [symlink] AGENTS.md -> ./docs/alias.MD", output)

    def test_markdown_trailing_slash_runs_validation(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "docs"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Alias](./docs/alias.md/)\n")
            with open(
                os.path.join(root, "docs", "real.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write("# Real\n")
            os.symlink("real.md", os.path.join(root, "docs", "alias.md"))
            subprocess.run(
                ["git", "add", "AGENTS.md", "docs/alias.md", "docs/real.md"],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [symlink] AGENTS.md -> ./docs/alias.md/", output)

    def test_unlinked_symlink_alias_does_not_shadow_context_anchor(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, ".agents", "context"), exist_ok=True)
            os.makedirs(os.path.join(root, "docs"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Page](./.agents/context/page.md#heading)\n")
            with open(
                os.path.join(root, ".agents", "context", "page.md"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write("# Heading\n")
            os.symlink(
                os.path.join("..", ".agents", "context", "page.md"),
                os.path.join(root, "docs", "alias.md"),
            )
            subprocess.run(
                ["git", "add", "AGENTS.md", ".agents/context/page.md", "docs/alias.md"],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("All context links and anchors resolve.", output)

    def test_untracked_markdown_with_uppercase_extension_is_missing_file(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Target](./untracked.MD#present-heading)\n")
            with open(os.path.join(root, "untracked.MD"), "w", encoding="utf-8") as fh:
                fh.write("# Present Heading\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn(
                "BROKEN [missing file] AGENTS.md -> ./untracked.MD#present-heading",
                output,
            )
            self.assertNotIn("missing anchor", output)

    def test_untracked_markdown_with_trailing_slash_is_missing_file(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Target](./untracked.md/#present-heading)\n")
            with open(os.path.join(root, "untracked.md"), "w", encoding="utf-8") as fh:
                fh.write("# Present Heading\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn(
                "BROKEN [missing file] AGENTS.md -> ./untracked.md/#present-heading",
                output,
            )
            self.assertNotIn("missing anchor", output)

    def test_is_markdown_target_accepts_case_and_trailing_slash(self):
        self.assertTrue(check_links.is_markdown_target("./docs/page.MD"))
        self.assertTrue(check_links.is_markdown_target("./docs/page.md/"))
        self.assertFalse(check_links.is_markdown_target("./docs/page.txt"))
        self.assertFalse(check_links.is_markdown_target("./docs/page.md.bak"))

    def test_unreadable_tracked_target_reports_read_failure_not_missing_anchor(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Frag](./docs/secret.md#heading)\n[Plain](./docs/secret.md)\n"
                )
            os.makedirs(os.path.join(root, "docs"), exist_ok=True)
            secret = os.path.join(root, "docs", "secret.md")
            with open(secret, "w", encoding="utf-8") as fh:
                fh.write("# Heading\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "docs/secret.md"],
                cwd=root,
                check=True,
            )

            # safe_markdown_path only stats, so the target passes that gate; the
            # failure has to surface when anchor_map tries to actually read it.
            real_open = open
            secret_real = os.path.realpath(secret)

            def fake_open(file, *args, **kwargs):
                if (
                    isinstance(file, (str, bytes, os.PathLike))
                    and os.path.realpath(file) == secret_real
                ):
                    raise PermissionError(13, "Permission denied")
                return real_open(file, *args, **kwargs)

            with mock.patch("builtins.open", side_effect=fake_open):
                status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("cannot read file", output)
            self.assertIn("AGENTS.md -> ./docs/secret.md#heading", output)
            self.assertIn("AGENTS.md -> ./docs/secret.md\n", output)
            self.assertNotIn("missing anchor", output)

    def test_symlink_then_dotdot_link_target_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "repo")
            outside = os.path.join(tmp, "outside")
            os.makedirs(root)
            os.makedirs(outside)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            # A symlinked dir pointing outside the repo. Walking through it and
            # back up with `..` lands outside, but lexical normpath would collapse
            # `link/..` to nothing and hide the escape.
            os.symlink(outside, os.path.join(root, "link"))
            with open(os.path.join(root, "escape.md"), "w", encoding="utf-8") as fh:
                fh.write("# Escape\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Escape](./link/../escape.md)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "escape.md"],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(os.path.realpath(root))

            self.assertEqual(1, status)
            self.assertIn(
                "BROKEN [target escapes repo] AGENTS.md -> ./link/../escape.md",
                output,
            )

    def test_tracked_md_preserves_non_utf8_filenames(self):
        with tempfile.TemporaryDirectory() as root:
            old_root = check_links.ROOT
            proc = subprocess.CompletedProcess(
                ["git", "ls-files", "-z"],
                0,
                stdout=b"docs/bad_\xff.md\0docs/ignored_\xff.txt\0",
                stderr=b"",
            )
            try:
                check_links.ROOT = root
                with mock.patch.object(
                    check_links.subprocess, "run", return_value=proc
                ):
                    paths = check_links.tracked_md()
            finally:
                check_links.ROOT = old_root

            self.assertEqual([os.path.join(root, "docs", "bad_\udcff.md")], paths)


if __name__ == "__main__":
    unittest.main()
