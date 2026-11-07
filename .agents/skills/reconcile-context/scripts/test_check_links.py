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
            check_links.ROOT = os.path.realpath(root)
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

    def test_tracked_markdown_target_case_match_follows_filesystem(self):
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

            if os.path.exists(os.path.join(root, "docs", "real.md")):
                # Case-insensitive filesystem: ./docs/real.md IS
                # docs/Real.md.
                self.assertEqual(0, status, output)
                self.assertIn("All context links and anchors resolve.", output)
            else:
                # Case-sensitive filesystem: the case variant is a
                # different (here missing) file, so the link is broken.
                self.assertEqual(1, status, output)
                self.assertIn(
                    "BROKEN [missing file] AGENTS.md -> ./docs/real.md#real",
                    output,
                )

    def test_folded_match_requires_the_same_file_on_disk(self):
        """The folded fallback must reflect the real filesystem, not a
        blanket casefold: on a case-sensitive filesystem an untracked case
        variant is a different file, and a link to it is broken."""
        exact = {check_links.exact_path_key("/repo/docs/Real.md"): "/repo/docs/Real.md"}
        folded = {
            check_links.folded_path_key("/repo/docs/Real.md"): "/repo/docs/Real.md"
        }
        with mock.patch.object(
            check_links.os.path, "samefile", return_value=False
        ) as same_file:
            self.assertIsNone(
                check_links.tracked_markdown_lookup("/repo/docs/real.md", exact, folded)
            )
            same_file.assert_called_once()
        with mock.patch.object(check_links.os.path, "samefile", return_value=True):
            self.assertEqual(
                "/repo/docs/Real.md",
                check_links.tracked_markdown_lookup(
                    "/repo/docs/real.md", exact, folded
                ),
            )
        # An exact tracked-path hit never needs the folded fallback.
        self.assertEqual(
            "/repo/docs/Real.md",
            check_links.tracked_markdown_lookup("/repo/docs/Real.md", exact, folded),
        )

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
        self.assertTrue(check_links.is_markdown_target("./templates/page.md.tmpl"))
        self.assertFalse(check_links.is_markdown_target("./docs/page.txt"))
        self.assertFalse(check_links.is_markdown_target("./docs/page.md.bak"))
        self.assertFalse(check_links.is_markdown_target("./templates/mcp.json.tmpl"))

    def test_template_sibling_target_maps_md_to_tmpl(self):
        self.assertTrue(
            check_links.is_template_source("templates/context/page.md.tmpl")
        )
        self.assertFalse(check_links.is_template_source("templates/context/page.md"))
        self.assertEqual(
            "templates/context/enforcement.md.tmpl",
            check_links.template_sibling_target("templates/context/enforcement.md"),
        )
        self.assertEqual(
            "templates/context/enforcement.MD.tmpl",
            check_links.template_sibling_target("templates/context/enforcement.MD/"),
        )
        self.assertIsNone(
            check_links.template_sibling_target("templates/context/enforcement.md.tmpl")
        )
        self.assertIsNone(check_links.template_sibling_target("templates/mcp.json"))

    def test_all_scans_md_tmpl_sources(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "templates", "context"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n")
            tmpl = os.path.join(root, "templates", "context", "page.md.tmpl")
            with open(tmpl, "w", encoding="utf-8") as fh:
                fh.write("[Missing](./nope.md)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "templates/context/page.md.tmpl"],
                cwd=root,
                check=True,
            )

            status_default, output_default = self.run_checker(root)
            status_all, output_all = self.run_checker(root, "--all")

            self.assertEqual(0, status_default)
            self.assertNotIn("page.md.tmpl", output_default)
            self.assertEqual(1, status_all)
            self.assertIn(
                "BROKEN [missing file] templates/context/page.md.tmpl -> ./nope.md",
                output_all,
            )

    def test_default_surface_skips_agents_md_tmpl(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, ".agents"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n")
            tmpl = os.path.join(root, ".agents", "notes.md.tmpl")
            with open(tmpl, "w", encoding="utf-8") as fh:
                fh.write("[Missing](./nope.md)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", ".agents/notes.md.tmpl"],
                cwd=root,
                check=True,
            )

            status_default, output_default = self.run_checker(root)
            status_all, output_all = self.run_checker(root, "--all")

            self.assertEqual(0, status_default, output_default)
            self.assertNotIn("notes.md.tmpl", output_default)
            self.assertEqual(1, status_all)
            self.assertIn(
                "BROKEN [missing file] .agents/notes.md.tmpl -> ./nope.md",
                output_all,
            )

    def test_all_resolves_md_link_to_sibling_tmpl(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "templates", "context"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n")
            src = os.path.join(root, "templates", "context", "page.md.tmpl")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write("[Sibling](./enforcement.md#heading)\n")
            sibling = os.path.join(root, "templates", "context", "enforcement.md.tmpl")
            with open(sibling, "w", encoding="utf-8") as fh:
                fh.write("# Heading\n")
            subprocess.run(
                [
                    "git",
                    "add",
                    "AGENTS.md",
                    "templates/context/page.md.tmpl",
                    "templates/context/enforcement.md.tmpl",
                ],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root, "--all")

            self.assertEqual(0, status, output)
            self.assertIn("All context links and anchors resolve.", output)

    def test_all_prefers_rendered_template_over_core_file(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "templates", "context"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n## Core Only\n")
            with open(
                os.path.join(root, "templates", "AGENTS.md.tmpl"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write("# {{project_name}}\n## Routing\n")
            src = os.path.join(root, "templates", "context", "loading.md.tmpl")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(
                    "[Ok](../../AGENTS.md#routing)\n[Core](../../AGENTS.md#core-only)\n"
                )
            subprocess.run(
                [
                    "git",
                    "add",
                    "AGENTS.md",
                    "templates/AGENTS.md.tmpl",
                    "templates/context/loading.md.tmpl",
                ],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root, "--all")

            self.assertEqual(1, status, output)
            self.assertIn(
                "BROKEN [missing anchor] templates/context/loading.md.tmpl "
                "-> ../../AGENTS.md#core-only",
                output,
            )
            self.assertNotIn("#routing", output)

    def test_all_fenced_heading_in_template_is_not_an_anchor(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "templates", "context"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n")
            with open(
                os.path.join(root, "templates", "AGENTS.md.tmpl"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write("# {{project_name}}\n## Routing\n```bash\n# example\n```\n")
            src = os.path.join(root, "templates", "context", "loading.md.tmpl")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(
                    "[Ok](../../AGENTS.md#routing)\n[Fenced](../../AGENTS.md#example)\n"
                )
            subprocess.run(
                [
                    "git",
                    "add",
                    "AGENTS.md",
                    "templates/AGENTS.md.tmpl",
                    "templates/context/loading.md.tmpl",
                ],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root, "--all")

            self.assertEqual(1, status, output)
            self.assertIn(
                "BROKEN [missing anchor] templates/context/loading.md.tmpl "
                "-> ../../AGENTS.md#example",
                output,
            )
            self.assertNotIn("#routing", output)

    def test_update_fence_nested_and_tilde(self):
        fence, delim = check_links.update_fence(None, "````md")
        self.assertEqual(("`", 4), fence)
        self.assertTrue(delim)
        fence, delim = check_links.update_fence(fence, "```")
        self.assertEqual(("`", 4), fence)
        self.assertFalse(delim)
        fence, delim = check_links.update_fence(fence, "````")
        self.assertIsNone(fence)
        self.assertTrue(delim)

        fence, delim = check_links.update_fence(None, "~~~bash")
        self.assertEqual(("~", 3), fence)
        fence, delim = check_links.update_fence(fence, "```")
        self.assertEqual(("~", 3), fence)
        self.assertFalse(delim)
        fence, delim = check_links.update_fence(fence, "~~~")
        self.assertIsNone(fence)
        self.assertTrue(delim)

    def test_link_targets_skips_nested_and_tilde_fences(self):
        text = (
            "````md\n```\n[Skip](./nested.md)\n```\n````\n"
            "~~~\n[Skip](./tilde.md)\n~~~\n"
            "[Ok](./yes.md)\n"
        )
        self.assertEqual(["./yes.md"], list(check_links.link_targets(text)))

    def test_all_nested_fence_heading_is_not_an_anchor(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "templates", "context"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n")
            with open(
                os.path.join(root, "templates", "AGENTS.md.tmpl"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write(
                    "# {{project_name}}\n"
                    "## Routing\n"
                    "````md\n```\n## Inner Heading\n```\n````\n"
                )
            src = os.path.join(root, "templates", "context", "loading.md.tmpl")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(
                    "[Ok](../../AGENTS.md#routing)\n"
                    "[Fenced](../../AGENTS.md#inner-heading)\n"
                )
            subprocess.run(
                [
                    "git",
                    "add",
                    "AGENTS.md",
                    "templates/AGENTS.md.tmpl",
                    "templates/context/loading.md.tmpl",
                ],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root, "--all")

            self.assertEqual(1, status, output)
            self.assertIn(
                "BROKEN [missing anchor] templates/context/loading.md.tmpl "
                "-> ../../AGENTS.md#inner-heading",
                output,
            )
            self.assertNotIn("#routing", output)

    def test_all_missing_template_does_not_use_core_headings(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "templates", "context"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n## Core Only\n")
            src = os.path.join(root, "templates", "context", "loading.md.tmpl")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write("[Core](../../AGENTS.md#core-only)\n")
            subprocess.run(
                [
                    "git",
                    "add",
                    "AGENTS.md",
                    "templates/context/loading.md.tmpl",
                ],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root, "--all")

            self.assertEqual(1, status, output)
            self.assertIn(
                "BROKEN [missing file] templates/context/loading.md.tmpl "
                "-> ../../AGENTS.md#core-only",
                output,
            )
            self.assertNotIn("missing anchor", output)

    def test_all_resolves_template_skill_and_rule_links(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "templates", "context"), exist_ok=True)
            os.makedirs(os.path.join(root, "skills", "retrospective"), exist_ok=True)
            os.makedirs(os.path.join(root, "rules"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n")
            src = os.path.join(root, "templates", "context", "learning-loop.md.tmpl")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(
                    "[Skill](../skills/retrospective/SKILL.md)\n"
                    "[Rule](../rules/subagents.md)\n"
                )
            with open(
                os.path.join(root, "skills", "retrospective", "SKILL.md"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write("# Retrospective\n")
            with open(
                os.path.join(root, "rules", "subagents.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write("# Subagents\n")
            subprocess.run(
                [
                    "git",
                    "add",
                    "AGENTS.md",
                    "templates/context/learning-loop.md.tmpl",
                    "skills/retrospective/SKILL.md",
                    "rules/subagents.md",
                ],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root, "--all")

            self.assertEqual(0, status, output)
            self.assertIn("All context links and anchors resolve.", output)

    def test_all_resolves_copied_reference_without_tmpl(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "templates", "references"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n")
            src = os.path.join(root, "templates", "AGENTS.md.tmpl")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(
                    "[Naming](./.agents/references/agent-branch-naming.md#branch-slug-rules)\n"
                )
            copied = os.path.join(
                root, "templates", "references", "agent-branch-naming.md"
            )
            with open(copied, "w", encoding="utf-8") as fh:
                fh.write("# Agent branch naming\n## Branch slug rules\n")
            subprocess.run(
                [
                    "git",
                    "add",
                    "AGENTS.md",
                    "templates/AGENTS.md.tmpl",
                    "templates/references/agent-branch-naming.md",
                ],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root, "--all")

            self.assertEqual(0, status, output)
            self.assertIn("All context links and anchors resolve.", output)

    def test_all_resolves_template_link_to_tracked_root_readme(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "templates"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n")
            with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Pitch\n")
            src = os.path.join(root, "templates", "AGENTS.md.tmpl")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write("[Pitch](./README.md)\n[Missing](./docs/nope.md)\n")
            subprocess.run(
                [
                    "git",
                    "add",
                    "AGENTS.md",
                    "README.md",
                    "templates/AGENTS.md.tmpl",
                ],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root, "--all")

            self.assertEqual(1, status, output)
            self.assertIn(
                "BROKEN [missing file] templates/AGENTS.md.tmpl -> ./docs/nope.md",
                output,
            )
            self.assertNotIn("./README.md", output)

    def test_all_rejects_template_link_that_escapes_deployed_root(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "templates"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n")
            with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Pitch\n")
            with open(
                os.path.join(root, "templates", "AGENTS.md.tmpl"),
                "w",
                encoding="utf-8",
            ) as fh:
                fh.write("[Out](../README.md)\n")
            subprocess.run(
                [
                    "git",
                    "add",
                    "AGENTS.md",
                    "README.md",
                    "templates/AGENTS.md.tmpl",
                ],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root, "--all")

            self.assertEqual(1, status, output)
            self.assertIn(
                "BROKEN [target escapes repo] templates/AGENTS.md.tmpl -> ../README.md",
                output,
            )

    def test_template_to_deployed_maps_renamed_and_context(self):
        old_root = check_links.ROOT
        try:
            check_links.ROOT = "/repo"
            self.assertEqual(
                os.path.join("/repo", "AGENTS.md"),
                check_links.template_to_deployed(
                    os.path.join("/repo", "templates", "AGENTS.md.tmpl")
                ),
            )
            self.assertEqual(
                os.path.join("/repo", ".agents", "context", "loading.md"),
                check_links.template_to_deployed(
                    os.path.join("/repo", "templates", "context", "loading.md.tmpl")
                ),
            )
            with mock.patch("os.path.isfile", return_value=True):
                self.assertEqual(
                    os.path.join("/repo", "templates", "AGENTS.md.tmpl"),
                    check_links.deployed_to_template(
                        os.path.join("/repo", "AGENTS.md")
                    ),
                )
                self.assertEqual(
                    os.path.join("/repo", "templates", "AGENTS.md.tmpl"),
                    check_links.rendered_template_target(
                        os.path.join(
                            "/repo", "templates", "context", "loading.md.tmpl"
                        ),
                        "../../AGENTS.md",
                    ),
                )
                self.assertEqual(
                    os.path.join("/repo", "skills", "retrospective", "SKILL.md"),
                    check_links.deployed_to_template(
                        os.path.join(
                            "/repo", ".agents", "skills", "retrospective", "SKILL.md"
                        )
                    ),
                )
                self.assertEqual(
                    os.path.join("/repo", "rules", "subagents.md"),
                    check_links.deployed_to_template(
                        os.path.join("/repo", ".agents", "rules", "subagents.md")
                    ),
                )
                self.assertEqual(
                    os.path.join("/repo", "templates", "rules-README.md.tmpl"),
                    check_links.deployed_to_template(
                        os.path.join("/repo", ".agents", "rules", "README.md")
                    ),
                )
                self.assertEqual(
                    os.path.join("/repo", "skills", "retrospective", "SKILL.md"),
                    check_links.rendered_template_target(
                        os.path.join(
                            "/repo", "templates", "context", "learning-loop.md.tmpl"
                        ),
                        "../skills/retrospective/SKILL.md",
                    ),
                )
                self.assertEqual(
                    os.path.join("/repo", "rules", "subagents.md"),
                    check_links.rendered_template_target(
                        os.path.join(
                            "/repo", "templates", "context", "work-loop.md.tmpl"
                        ),
                        "../rules/subagents.md",
                    ),
                )
            with mock.patch("os.path.isfile", return_value=False):
                self.assertIsNone(
                    check_links.deployed_to_template(os.path.join("/repo", "AGENTS.md"))
                )
                self.assertIsNone(
                    check_links.deployed_to_template(
                        os.path.join(
                            "/repo", ".agents", "skills", "retrospective", "SKILL.md"
                        )
                    )
                )
                self.assertIsNone(
                    check_links.rendered_template_target(
                        os.path.join(
                            "/repo", "templates", "context", "loading.md.tmpl"
                        ),
                        "../../AGENTS.md",
                    )
                )
        finally:
            check_links.ROOT = old_root

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
                check_links.ROOT = os.path.realpath(root)
                with mock.patch.object(
                    check_links.subprocess, "run", return_value=proc
                ):
                    paths = check_links.tracked_md()
            finally:
                check_links.ROOT = old_root

            self.assertEqual(
                [os.path.join(os.path.realpath(root), "docs", "bad_\udcff.md")], paths
            )

    def test_alias_to_tracked_file_outside_surface_is_kept(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, ".agents", "context"), exist_ok=True)
            os.makedirs(os.path.join(root, "docs"), exist_ok=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n")
            with open(
                os.path.join(root, "docs", "real.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write("# Real\n")
            # Alias on the default surface (.agents/**) pointing at a tracked
            # file off the surface (docs/). It must NOT be dropped: the target
            # is never scanned on its own, so the alias is kept and reported.
            os.symlink(
                os.path.join("..", "..", "docs", "real.md"),
                os.path.join(root, ".agents", "context", "alias.md"),
            )
            subprocess.run(
                ["git", "add", "AGENTS.md", "docs/real.md", ".agents/context/alias.md"],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [symlink] .agents/context/alias.md", output)

    def test_same_document_missing_anchor_is_reported(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n[Gone](#not-a-heading)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing anchor] AGENTS.md -> #not-a-heading", output)

    def test_titled_same_document_missing_anchor_is_reported(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write('# Agents\n\n[Jump](#missing "section")\n')
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing anchor] AGENTS.md -> #missing", output)

    def test_single_quoted_title_same_document_missing_anchor_is_reported(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n[Jump](#missing 'section')\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing anchor] AGENTS.md -> #missing", output)

    def test_same_document_present_anchor_passes(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n[Here](#agents)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status)
            self.assertNotIn("BROKEN", output)
            self.assertTrue(output.rstrip().endswith("CHECK_LINKS_DONE"))

    def test_broken_run_still_prints_completion_marker(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Gone](./missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file]", output)
            self.assertTrue(output.rstrip().endswith("CHECK_LINKS_DONE"))

    def test_duplicate_heading_suffixed_anchor_passes(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n## Setup\n## Setup\n\n[Second](#setup-1)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_generated_suffix_collision_uses_setup_1_1(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Agents\n## Setup\n## Setup\n## Setup-1\n\n[Third](#setup-1-1)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_backtick_in_fence_info_is_not_an_opener(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Agents\n\n```foo`bar\n## Real Heading\n\n[Here](#real-heading)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_setext_heading_same_document_anchor_passes(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("Setup\n=====\n\n[Here](#setup)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_multiline_setext_heading_anchor_passes(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "First line\nsecond line\n---\n\n[Here](#first-line-second-line)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_untracked_agents_same_document_missing_anchor_is_reported(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Bad](#missing)\n")

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing anchor] AGENTS.md -> #missing", output)

    def test_indented_atx_heading_same_document_anchor_passes(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("   # Setup\n\n[Here](#setup)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_inline_markdown_heading_slug_is_setup(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# [Setup](./guide.md)\n\n[Jump](#setup)\n")
            with open(os.path.join(root, "guide.md"), "w", encoding="utf-8") as fh:
                fh.write("# Guide\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "guide.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_reference_link_heading_slug_is_setup(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# [Setup][guide]\n\n[Jump](#setup)\n\n[guide]: ./guide.md\n")
            with open(os.path.join(root, "guide.md"), "w", encoding="utf-8") as fh:
                fh.write("# Guide\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "guide.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_html_span_heading_slug_is_setup(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# <span>Setup</span>\n\n[Jump](#setup)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_html_entity_heading_slug_is_setup(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Setup &amp; Go\n\n[Jump](#setup--go)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_inline_code_generic_heading_slug_is_type_listt(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Type `List<T>`\n\n[Jump](#type-listt)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_list_nested_fence_blank_line_still_closes(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Agents\n\n- Example:\n    ```\n    foo\n\n    bar\n    ```\n\n"
                    "[Gone](./missing.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./missing.md", output)

    def test_list_nested_fence_skips_example_links(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Agents\n\n- Example:\n    ```\n    [x](./missing.md)\n    ```\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_list_tab_indented_fence_skips_example_links(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n- Example:\n\t```\n\t[x](./missing.md)\n\t```\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_inline_code_fragment_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\nDocument `[Jump](#missing)` syntax.\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_html_comment_heading_is_not_an_anchor(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n<!--\n# Hidden\n-->\n\n[Jump](#hidden)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing anchor] AGENTS.md -> #hidden", output)

    def test_indented_code_fragment_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n    [Jump](#missing)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_reference_style_fragment_missing_anchor_is_reported(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n[Jump][section]\n\n[section]: #missing\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing anchor] AGENTS.md -> #missing", output)

    def test_indented_paragraph_continuation_link_is_checked(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\nIntro\n    [Broken](./missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./missing.md", output)

    def test_shortcut_reference_missing_anchor_is_reported(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n[Jump]\n\n[Jump]: #missing\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing anchor] AGENTS.md -> #missing", output)

    def test_inline_code_does_not_open_html_comment(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Agents\n\nUse `<!-- drift:` here.\n\n## Ranking\n\n[Go](#ranking)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_fenced_html_comment_does_not_hide_heading(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Agents\n\n```\nrg '<!-- drift:'\n```\n\n## Ranking\n\n[Go](#ranking)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_mailto_and_tel_are_not_relative_links(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Agents\n\n[Mail](mailto:a@b.com)\n[Call](tel:+15551212)\n\n"
                    "[Ref][m]\n\n[m]: mailto:a@b.com\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_percent_encoded_path_and_fragment_resolve(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, "docs"), exist_ok=True)
            with open(
                os.path.join(root, "docs", "my file.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write("# Set Up\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Jump](./docs/my%20file.md#set%2Dup)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "docs/my file.md"],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_multibacktick_code_span_link_is_ignored(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\nShow `` `[Jump](#missing)` `` as syntax\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_indented_link_after_heading_is_code(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Heading\n    [Jump](#missing)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_gfm_footnote_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\nClaim.[^1]\n\n[^1]: Explanatory footnote text.\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_query_string_is_stripped_from_local_path(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Existing\n\n[Guide](AGENTS.md?plain=1#existing)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_balanced_paren_destination_resolves(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "foo(bar).md"), "w", encoding="utf-8") as fh:
                fh.write("# Guide\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide](foo(bar).md)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "foo(bar).md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_angle_bracket_destination_with_spaces_resolves(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "my guide.md"), "w", encoding="utf-8") as fh:
                fh.write("# Guide\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide](<my guide.md>)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "my guide.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_reference_label_whitespace_is_collapsed(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n[Jump][some   label]\n\n[some label]: #missing\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing anchor] AGENTS.md -> #missing", output)

    def test_escaped_paren_destination_resolves(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "foo(bar).md"), "w", encoding="utf-8") as fh:
                fh.write("# Guide\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide](foo\\(bar\\).md)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "foo(bar).md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_multiline_code_span_link_is_ignored(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n`before\n[Example](missing.md)\nafter`\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_heading_balanced_paren_link_slug_is_guide(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "foo(bar).md"), "w", encoding="utf-8") as fh:
                fh.write("# Dest\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# [Guide](foo(bar).md)\n\n[Jump](#guide)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "foo(bar).md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_html_script_block_link_is_ignored(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Agents\n\n<script>\n[Broken](missing.md)\n</script>\n"
                    "\n[Go](#agents)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_html_type6_div_block_link_is_ignored(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Agents\n\n<div>\n[Broken](missing.md)\n</div>\n\n[Go](#agents)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_html_type7_custom_element_block_link_is_ignored(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Agents\n\n<x-widget>\n[Broken](missing.md)\n\n[Go](#agents)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_email_autolink_heading_slug_keeps_address(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# Contact <user@example.com>\n\n[Go](#contact-userexamplecom)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_continued_reference_destination_is_checked(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide][guide]\n\n[guide]:\n  missing.md\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_angle_bracket_reference_destination_resolves(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "my guide.md"), "w", encoding="utf-8") as fh:
                fh.write("# Guide\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide][guide]\n\n[guide]: <my guide.md>\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "my guide.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_escaped_bracket_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n[literal\\](missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_unmatched_closer_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\nliteral](missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_escaped_reference_destination_resolves(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "foo(bar).md"), "w", encoding="utf-8") as fh:
                fh.write("# Guide\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide][guide]\n\n[guide]: foo\\(bar\\).md\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "foo(bar).md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_unmatched_backtick_does_not_hide_next_paragraph(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\nsee `code\n\n[Broken](missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_type7_does_not_interrupt_paragraph(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\nSee this\n<x-widget>\n[Broken](missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_incomplete_angle_destination_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n[Guide](<missing.md>\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_nested_brackets_in_label_are_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n[Guide [details]](missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_unmatched_backtick_keeps_same_line_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\nText ` literal [Broken](missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_escaped_angle_in_reference_destination(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "foo>bar.md"), "w", encoding="utf-8") as fh:
                fh.write("# Guide\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide][guide]\n\n[guide]: <foo\\>bar.md>\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "foo>bar.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_unicode_casefold_reference_is_checked(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide][STRASSE]\n\n[straße]: missing.md\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_unused_reference_definition_is_not_a_shortcut(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n[guide]: missing.md\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_nested_link_label_heading_slug_is_guide_details(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "guide.md"), "w", encoding="utf-8") as fh:
                fh.write("# Guide\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# [Guide [details]](guide.md)\n\n[Go](#guide-details)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "guide.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_comparison_text_heading_keeps_angles(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Limits: 1 < 2 > 0\n\n[Go](#limits-1--2--0)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_malformed_link_title_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Agents\n\n[Guide](missing.md trailing)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_html_attribute_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write('# Agents\n\n<span title="[Guide](missing.md)">text</span>\n')
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_quoted_html_attribute_heading_slug_is_hello_world(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    '# Hello <span title="a > b">world</span>\n\n[Go](#hello-world)\n'
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_html_entity_in_destination_resolves(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "foo&bar.md"), "w", encoding="utf-8") as fh:
                fh.write("# Guide\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide](foo&amp;bar.md)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "foo&bar.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_first_reference_definition_wins(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "existing.md"), "w", encoding="utf-8") as fh:
                fh.write("# Existing\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Guide][guide]\n\n[guide]: existing.md\n\n[guide]: missing.md\n"
                )
            subprocess.run(
                ["git", "add", "AGENTS.md", "existing.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_malformed_ref_def_suffix_is_not_a_definition(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide][guide]\n\n[guide]: missing.md trailing\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_escaped_brackets_in_ref_labels_match(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[A\\]B][]\n\n[a\\]b]: missing.md\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_padded_code_span_heading_slug_is_use_a(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Use ` a `\n\n[Go](#use-a)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_continued_ref_title_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "existing.md"), "w", encoding="utf-8") as fh:
                fh.write("# Existing\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    '[Guide][guide]\n\n[guide]: existing.md\n  "[Broken](missing.md)"\n'
                )
            subprocess.run(
                ["git", "add", "AGENTS.md", "existing.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_escaped_ref_style_heading_slug_is_ab(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# [A\\]B][guide]\n\n[Go](#ab)\n\n[guide]: https://example.com\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_unterminated_entity_in_destination_is_literal(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "foo&amp.md"), "w", encoding="utf-8") as fh:
                fh.write("# Guide\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide](foo&amp.md)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "foo&amp.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_unbalanced_ref_destination_is_not_a_definition(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide][guide]\n\n[guide]: missing(foo.md\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_footnote_body_link_is_checked(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("Claim.[^1]\n\n[^1]: [Broken](missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_angle_bracket_destination_is_not_stripped_as_html(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide](<missing.md>)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_multiline_code_span_setext_heading_slug_is_use_a_b(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("Use `a\nb`\n-----\n\n[Go](#use-a-b)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_ref_def_does_not_interrupt_a_paragraph(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("Hello\n[guide]: missing.md\n\n[Guide][guide]\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_nested_outer_link_is_not_extracted(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "existing.md"), "w", encoding="utf-8") as fh:
                fh.write("# Existing\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[outer [inner](existing.md)](missing.md)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "existing.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_angle_destination_with_inner_angle_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide](<missing<.md>)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_backslash_before_letter_is_kept_in_destination(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "foo\\q.md"), "w", encoding="utf-8") as fh:
                fh.write("# Guide\n")
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide](foo\\q.md)\n")
            subprocess.run(
                ["git", "add", "AGENTS.md", "foo\\q.md"], cwd=root, check=True
            )

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_unclosed_inline_comment_does_not_hide_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("Text <!-- [Broken](missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_blank_line_exits_blockquote_before_indented_code(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("> quote\n\n    [Broken](missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_undefined_ref_heading_slug_keeps_label_and_ref(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# [Setup][missing]\n\n[Go](#setupmissing)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_ref_def_plus_thematic_break_is_not_a_setext_heading(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[foo]: target.md\n---\n\n[Go](#foo-targetmd)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("missing anchor", output)

    def test_linked_image_keeps_outer_destination(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[![alt](./image.png)](./target.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./target.md", output)

    def test_uncontained_break_after_blockquote_is_not_setext(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("> Quote\n---\n\n[Go](#quote)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("missing anchor", output)

    def test_spaced_angle_destination_is_checked(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide]( <missing.md> )\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_multiline_reference_title_destination_is_checked(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write('[Guide][guide]\n\n[guide]: missing.md "first\nsecond"\n')
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_tab_after_list_marker_heading_anchor_passes(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("-\t# Guide\n\n[Go](#guide)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_overlong_reference_label_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            label = "x" * 1000
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(f"[{label}][{label}]\n\n[{label}]: missing.md\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_untitled_ref_def_does_not_swallow_next_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[guide]: AGENTS.md\n[Broken](missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_malformed_inline_html_does_not_hide_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("<span [Broken](missing.md)>\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_lazy_blockquote_continuation_is_not_setext(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("> Foo\nlazy\n---\n\n[Go](#lazy)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("missing anchor", output)

    def test_mismatched_ref_title_closer_does_not_hide_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[x]: AGENTS.md \"unterminated\n[bad](missing.md)'\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_tab_in_heading_slug_is_hello_world(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# Hello\tWorld\n\n[Go](#hello-world)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_unescaped_bracket_in_ref_def_is_not_a_definition(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Guide][foo\\[bar]\n\n[foo[bar]: missing.md\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_unterminated_processing_instruction_does_not_hide_link(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("Text <? [Broken](missing.md)>\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_empty_angle_ref_dest_keeps_heading_slug(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("# [Guide][x]\n\n[x]: <>\n\n[Go](#guide)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_lowercase_declaration_is_not_type4_html_block(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("<!x [Broken](missing.md)>\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_details_after_paragraph_is_type6_html_block(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("A paragraph.\n<details>\n[Broken](missing.md)\n</details>\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_multiline_ref_label_is_folded(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[foo\n bar]: missing.md\n\n[foo bar]\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_list_marker_with_five_spaces_is_indented_code(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("-     [Broken](missing.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_invalid_continued_dest_falls_through_to_paragraph(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[x]:\nordinary [Bad](missing.md) text\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("BROKEN [missing file] AGENTS.md -> missing.md", output)

    def test_ordered_list_start_not_one_does_not_interrupt_paragraph(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("para\n2. # Fake\n\n[Go](#fake)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status)
            self.assertIn("missing anchor", output)

    def test_all_mode_symlink_alias_is_scanned_as_a_link_origin(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            os.makedirs(os.path.join(root, ".agents", "context"))
            os.makedirs(os.path.join(root, "docs"))
            # The link is valid from the target's directory but broken from
            # the alias's: --all must not silently skip the alias origin.
            with open(
                os.path.join(root, "docs", "real.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write("# Real\n[Peer](peer.md)\n")
            with open(
                os.path.join(root, "docs", "peer.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write("# Peer\n")
            os.symlink(
                os.path.join("..", "..", "docs", "real.md"),
                os.path.join(root, ".agents", "context", "alias.md"),
            )
            subprocess.run(
                [
                    "git",
                    "add",
                    "docs/real.md",
                    "docs/peer.md",
                    ".agents/context/alias.md",
                ],
                cwd=root,
                check=True,
            )

            status, output = self.run_checker(root, "--all")

            self.assertEqual(1, status, output)
            self.assertIn(
                "BROKEN [missing file] .agents/context/alias.md -> peer.md",
                output,
            )
            # The target scan from docs/ stays clean; only the alias origin
            # is broken.
            self.assertEqual(1, output.count("BROKEN"))

    def test_doc_fence_does_not_close_on_container_content_line(self):
        """A ``> ``` ``-shaped line inside an ordinary fence is content:
        the fence must close on its real closer, so the heading after it
        still resolves. Closing on the container-stripped content line
        made the real closer open a new fence and hid every anchor after
        it."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Real](./doc.md#real)\n")
            with open(os.path.join(root, "doc.md"), "w", encoding="utf-8") as fh:
                fh.write("```text\n> ```\n```\n\n## Real\n")
            subprocess.run(["git", "add", "AGENTS.md", "doc.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("All context links and anchors resolve.", output)

    def test_quote_fence_bare_closer_line_reopens_through_eof(self):
        """A bare closer-shaped line inside a blockquote fence ends the
        blockquote and opens a new document-level fence that runs through
        EOF, so the heading after it does not render and a link to it is
        broken. (The consumer wave asserted the opposite outcome; the
        CommonMark reference implementations agree with this one, so the
        core keeps the reference behavior.)"""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Real](./doc.md#real)\n")
            with open(os.path.join(root, "doc.md"), "w", encoding="utf-8") as fh:
                fh.write("> ```text\n```\n> ```\n\n## Real\n")
            subprocess.run(["git", "add", "AGENTS.md", "doc.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing anchor] AGENTS.md -> ./doc.md#real", output)

    def test_blockquote_fence_closer_prefix_may_vary(self):
        """CommonMark lets the optional space after a ``>`` differ between
        the opener and closer lines; a valid ``>``` `` closer must not run
        the fence through EOF."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Real](./doc.md#real)\n")
            with open(os.path.join(root, "doc.md"), "w", encoding="utf-8") as fh:
                fh.write("> ```\n> code\n>```\n\n## Real\n")
            subprocess.run(["git", "add", "AGENTS.md", "doc.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("All context links and anchors resolve.", output)

    def test_blockquote_fence_closer_keeps_opener_quote_depth(self):
        """CommonMark strips the parent ``>`` markers first; leftover ``>``
        on a nested line is fence content, not a closer. Closing on the
        deeper ``>> ``` `` line harvested a phantom anchor from the fence
        body and hid the real anchor after the fence."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[Real](./doc.md#real)\n[Still](./doc.md#still)\n")
            with open(os.path.join(root, "doc.md"), "w", encoding="utf-8") as fh:
                fh.write("> ```\n> ## Inside\n>> ```\n> ## Still\n> ```\n\n## Real\n")
            subprocess.run(["git", "add", "AGENTS.md", "doc.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            # The real anchor after the fence resolves; the phantom inside
            # the fence body does not.
            self.assertEqual(1, status, output)
            self.assertEqual(1, output.count("BROKEN"))
            self.assertIn("BROKEN [missing anchor] AGENTS.md -> ./doc.md#still", output)
            self.assertNotIn("./doc.md#real", output)

    def test_blockquote_fence_closer_at_shallower_quote_depth(self):
        """A closer-shaped line with fewer ``>`` markers than the opener
        ends the inner blockquote. The fence must close there, so the
        heading after it resolves and a broken link after it is reported.
        A link inside the fence body stays masked."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Real](#real)\n"
                    ">>> ```\n"
                    ">>> [Ghost](./ghost.md)\n"
                    "> ```\n"
                    "\n"
                    "## Real\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertNotIn("#real", output)
            self.assertEqual(1, output.count("BROKEN"))

    def test_list_fence_closer_rejects_sibling_list_item(self):
        """After indented item content, a same-margin list marker opens a
        sibling item whose fence body must stay masked; only an indented
        continuation line may close the fence."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("- ```\n  x\n- ```\n   [Ghost](./ghost.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_list_fence_closer_rejects_quoted_sibling_list_item(self):
        """A blockquote list fence has raw margin zero on every line;
        sibling detection must measure indent and list markers after the
        ``>`` prefix or the next item's opener closes the preceding fence
        and a link in that item is falsely checked."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("> - ```\n>   x\n> - ```\n>    [Ghost](./ghost.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_quoted_list_fence_closes_on_indented_closer(self):
        """A fence opened on a blockquote list marker closes on the
        indented continuation that keeps the ``>`` markers and omits the
        list marker. The heading and link after that closer are checked;
        a link inside the fence stays masked."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Real](#real)\n"
                    "> - ```\n"
                    ">   [Ghost](./ghost.md)\n"
                    ">   ```\n"
                    "\n"
                    "## Real\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertNotIn("#real", output)
            self.assertEqual(1, output.count("BROKEN"))

    def test_quote_fence_closes_on_list_marker_that_ends_blockquote(self):
        """A list marker with no ``>`` ends the blockquote, so a fence
        opened by ``> ``` `` closes on ``- ``` ``. The heading and link
        after that line are checked; a link inside the fence stays masked."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Real](#real)\n"
                    "> ```\n"
                    "> [Ghost](./ghost.md)\n"
                    "- ```\n"
                    "\n"
                    "## Real\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertNotIn("#real", output)
            self.assertEqual(1, output.count("BROKEN"))

    def test_list_fence_closes_on_blockquote_closer(self):
        """A quote marker at document level interrupts the list item, so a
        fence opened inside the item closes on ``> ``` ``. The heading and
        link after that closer are checked; a link inside the fence stays
        masked. The reverse of the quote-fence case: quote fences close on
        list markers that end their blockquote, list fences close on quote
        markers that interrupt their item."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Real](#real)\n"
                    "- ```\n"
                    "  [Ghost](./ghost.md)\n"
                    "> ```\n"
                    "\n"
                    "## Real\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertNotIn("#real", output)
            self.assertEqual(1, output.count("BROKEN"))

    def test_list_fence_keeps_indented_blockquote_closer_as_content(self):
        """A quote marker indented to the item's content column opens a
        quote inside the item, not outside it: the closer-shaped line is
        fence content and the fence stays open. The deeper ``>`` guard
        must measure indent relative to the opener's quote level, or this
        line closes the fence and a later link is falsely checked."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("- ```\n  x\n  > ```\n  [Ghost](./ghost.md)\n\n## Real\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_quoted_list_fence_closes_on_deeper_blockquote_closer(self):
        """``> > ``` `` after ``> - ``` `` starts a quote deeper than the
        opener's level, so the list item inside the outer quote ends and
        the fence closes there. The heading and link after it are checked;
        a link inside the fence stays masked."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Real](#real)\n"
                    "> - ```\n"
                    ">   [Ghost](./ghost.md)\n"
                    "> > ```\n"
                    "\n"
                    "## Real\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertNotIn("#real", output)
            self.assertEqual(1, output.count("BROKEN"))

    def test_quoted_list_fence_closes_on_parent_blockquote_leftover(self):
        """``> ``` `` after ``> - ``` `` drops the list marker and ends the
        item. The fence closes on that parent-quote leftover, so the heading
        and link after it are checked and a link inside the item stays
        masked."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Real](#real)\n"
                    "> - ```\n"
                    ">   [Ghost](./ghost.md)\n"
                    "> ```\n"
                    "\n"
                    "## Real\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertNotIn("#real", output)
            self.assertEqual(1, output.count("BROKEN"))

    def test_list_fence_closer_requires_exact_prefix_replay(self):
        """The container closer must not skip extra spaces after the
        opener's prefix: a later list-marker line with one to three extra
        spaces is a sibling item with its own fence, and its body must stay
        masked."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("- ```\n  x\n-  ```\n   [Ghost](./ghost.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

    def test_list_fence_closes_on_exact_prefix_replay(self):
        """An exact replay of the opener's raw prefix closes the fence when
        no indented continuation line was seen, so links after it are
        checked."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("- ```\n- ```\n[Checked](./checked.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./checked.md", output)

    def test_list_continuation_fence_closes_on_sibling_marker(self):
        """A fence indented under a list item has no marker on its opener.

        A later sibling ``- ``` `` ends that item. Classifying the opener as
        a document fence kept the fence open through the heading and link
        after the sibling."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Real](#real)\n"
                    "- item\n"
                    "    ```\n"
                    "        [Ghost](./ghost.md)\n"
                    "- ```\n"
                    "\n"
                    "## Real\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertNotIn("#real", output)
            self.assertEqual(1, output.count("BROKEN"))

    def test_list_continuation_fence_closes_on_other_bullet(self):
        """The sibling that ends the item need not repeat the opener's bullet."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Real](#real)\n"
                    "- item\n"
                    "    ```\n"
                    "    [Ghost](./ghost.md)\n"
                    "* ```\n"
                    "\n"
                    "## Real\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertNotIn("#real", output)
            self.assertEqual(1, output.count("BROKEN"))

    def test_list_continuation_fence_closes_on_blockquote_interrupt(self):
        """A ``> ``` `` at column 0 ends the list item, so the continuation
        fence closes there and the heading after it stays visible."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Real](#real)\n"
                    "- item\n"
                    "    ```\n"
                    "    [Ghost](./ghost.md)\n"
                    "> ```\n"
                    "\n"
                    "## Real\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertNotIn("#real", output)
            self.assertEqual(1, output.count("BROKEN"))

    def test_quoted_list_continuation_fence_closes_on_sibling(self):
        """A quoted-list continuation still carries a ``>``, so the opener
        looks like a blockquote fence. A same-depth ``> - ``` `` ends the
        item; quote rules would treat that marker as content and hide the
        link after it."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Real](#real)\n"
                    "> - item\n"
                    ">   ```\n"
                    ">   [Ghost](./ghost.md)\n"
                    "> - ```\n"
                    "\n"
                    "## Real\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertNotIn("#real", output)
            self.assertEqual(1, output.count("BROKEN"))

    def test_quoted_list_continuation_fence_closes_on_deeper_quote(self):
        """``> > ``` `` is deeper than the list's quote and interrupts the
        item. The continuation fence must close there."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "[Real](#real)\n"
                    "> - item\n"
                    ">   ```\n"
                    ">   [Ghost](./ghost.md)\n"
                    "> > ```\n"
                    "\n"
                    "## Real\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertNotIn("#real", output)
            self.assertEqual(1, output.count("BROKEN"))

    def test_list_continuation_fence_keeps_indented_marker_as_content(self):
        """A quote or list marker at the item's content column is inside
        the fence. Closing on it would check a link that CommonMark still
        masks, and the real indented closer would open a new fence."""
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "- item\n"
                    "    ```\n"
                    "    x\n"
                    "  > ```\n"
                    "    [Ghost](./ghost.md)\n"
                    "    ```\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertEqual(1, output.count("BROKEN"))

        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "- item\n"
                    "    ```\n"
                    "    x\n"
                    "  - ```\n"
                    "    [Ghost](./ghost.md)\n"
                    "    ```\n"
                    "[Gone](./gone.md)\n"
                )
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(1, status, output)
            self.assertIn("BROKEN [missing file] AGENTS.md -> ./gone.md", output)
            self.assertNotIn("ghost.md", output)
            self.assertEqual(1, output.count("BROKEN"))

    def test_fence_container_depth_is_bounded_by_line_length(self):
        """CommonMark caps list nesting only by line length; a fixed
        container bound was a semantic limit. An unclosed fence opened
        under nine list markers masked nothing, and a broken link to its
        body passed."""
        deep = "- " * 9
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            # The link sits at the list's content indent, still inside the
            # unclosed fence body, so it must not be checked.
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write(deep + "```\n" + " " * len(deep) + "[Ghost](./ghost.md)\n")
            subprocess.run(["git", "add", "AGENTS.md"], cwd=root, check=True)

            status, output = self.run_checker(root, "--all")

            self.assertEqual(0, status, output)
            self.assertNotIn("BROKEN", output)

        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
                fh.write("[After](./doc.md#after)\n")
            with open(os.path.join(root, "doc.md"), "w", encoding="utf-8") as fh:
                fh.write(deep + "```\n## In\n" + deep + "```\n## After\n")
            subprocess.run(["git", "add", "AGENTS.md", "doc.md"], cwd=root, check=True)

            status, output = self.run_checker(root)

            self.assertEqual(0, status, output)
            self.assertIn("All context links and anchors resolve.", output)

    def test_container_prefix_scan_is_linear_at_any_depth(self):
        """The per-line container prefix scan must stay deterministic and
        linear whatever the nesting depth: an ambiguous split backtracked
        over exponentially many whitespace partitions, minutes of CPU for
        a short line in any tracked Markdown file."""
        import time

        for line in ("> " * 100 + "x", "-  " * 100 + "x"):
            with self.subTest(prefix=line[:3]):
                start = time.monotonic()
                list(check_links.link_targets(line))
                self.assertLess(time.monotonic() - start, 1.0)

    def test_link_target_extraction_is_linear_on_unmatched_brackets(self):
        """Each unclosed ``](`` candidate rescanned the whole suffix, so a
        pathological one-megabyte line pinned a CI runner for minutes.
        Extraction must finish near-linearly on bracket soup."""
        import time

        for text in ("](" * 100_000, "[](x" * 100_000):
            with self.subTest(text=text[:4]):
                start = time.monotonic()
                list(check_links.extract_link_dests(text))
                self.assertLess(time.monotonic() - start, 1.0)

    def test_link_target_extraction_is_linear_on_matched_brackets(self):
        """Each successful match must reuse position state instead of
        rescanning, so a line of many short destinations stays linear."""
        import time

        start = time.monotonic()
        dests = list(check_links.extract_link_dests("[](x)" * 100_000))
        self.assertEqual(100_000, len(dests))
        self.assertLess(time.monotonic() - start, 1.0)

    def test_unmatched_link_opener_yields_no_destination(self):
        # No closing paren, so the text is not a link destination and
        # nothing is extracted from the rest of the line.
        self.assertEqual(
            [], list(check_links.extract_link_dests(']( <a id="unclosed"></a>\n'))
        )


if __name__ == "__main__":
    unittest.main()
