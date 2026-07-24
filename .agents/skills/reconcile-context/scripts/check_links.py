#!/usr/bin/env python3
"""Check that intra-repo markdown links and #anchors in the context surface
resolve. Exit 0 if all good, 1 if any are broken. Safe to run from a hook.

Default surface: AGENTS.md, CLAUDE.md, .agents/README.md,
.agents/**/*.md, and tracked .cursor/**/*.md (hooks, README). Pass --all to check every
tracked markdown file in the repo instead.
"""

import os
import re
import stat
import subprocess
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


# Canonicalize the root so escape checks compare like with like: link and file
# paths get realpath'd below, so a symlink anywhere in the repo path (e.g. macOS
# /tmp -> /private/tmp) would otherwise make in-repo paths look like they escape.
ROOT = os.path.realpath(_find_root(__file__))
LINK = re.compile(r"\]\((\.{1,2}/[^)\s]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.*)")
MAX_MARKDOWN_BYTES = 1_000_000


def is_markdown_target(path: str) -> bool:
    """True when path (no fragment) points at a Markdown file."""
    return path.rstrip("/\\").lower().endswith(".md")


def slug(heading: str) -> str:
    """GitHub-style anchor slug. Does NOT collapse repeated hyphens."""
    s = heading.strip().lower()
    s = re.sub(r"\{#([^}]+)\}", "", s).strip()
    s = re.sub(r"[^\w\s-]", "", s)
    return s.replace(" ", "-").strip("-")


def tracked_md():
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(
            f"could not enumerate tracked files with git ls-files: {exc}"
        ) from exc
    # git ls-files reports slash-separated names on every platform; split and
    # rejoin so the paths use the OS separator. Without this, surface() matching
    # on os.sep would miss .agents/context files on Windows.
    paths = []
    for path in proc.stdout.split(b"\0"):
        if not path:
            continue
        name = path.decode("utf-8", errors="surrogateescape")
        if is_markdown_target(name):
            paths.append(os.path.join(ROOT, *name.split("/")))
    return paths


def exact_path_key(path):
    return os.path.abspath(path)


def folded_path_key(path):
    return os.path.abspath(path).casefold()


def tracked_markdown_lookup(path, exact, folded):
    return exact.get(exact_path_key(path)) or folded.get(folded_path_key(path))


def within_root(path):
    # commonpath raises ValueError when the paths share no base — e.g. they sit
    # on different Windows drives. That target is outside the repo, so treat the
    # error the same as any other escape rather than letting it crash the hook.
    try:
        return os.path.commonpath([ROOT, path]) == ROOT
    except ValueError:
        return False


def safe_markdown_path(path):
    real = os.path.realpath(path)
    if not within_root(real):
        return False, "escapes repo"
    try:
        st = os.lstat(path)
    except OSError as exc:
        return False, f"cannot stat file: {exc}"
    if stat.S_ISLNK(st.st_mode):
        return False, "symlink"
    if not stat.S_ISREG(st.st_mode):
        return False, "not a regular file"
    if st.st_size > MAX_MARKDOWN_BYTES:
        return False, f"larger than {MAX_MARKDOWN_BYTES} bytes"
    return True, ""


def read_markdown(path):
    ok, why = safe_markdown_path(path)
    if not ok:
        return None, why
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read(), ""
    except OSError as exc:
        return None, f"cannot read file: {exc}"


def anchor_map(md_files):
    m = {}
    bad = []
    for f in md_files:
        text, why = read_markdown(f)
        if text is None:
            bad.append((f, os.path.relpath(f, ROOT), why))
            continue
        anchors = set()
        for h in (HEADING.match(line) for line in text.splitlines()):
            if not h:
                continue
            heading = h.group(1)
            anchors.add(slug(heading))
            explicit = re.search(r"\{#([^}]+)\}", heading)
            if explicit:
                anchors.add(explicit.group(1))
        m[os.path.realpath(f)] = anchors
    return m, bad


def surface(check_all, md_files):
    if check_all:
        return md_files
    files = [
        os.path.join(ROOT, "AGENTS.md"),
        os.path.join(ROOT, "CLAUDE.md"),
    ]
    files += [
        f
        for f in md_files
        if os.path.relpath(f, ROOT).split(os.sep, 1)[0]
        in {".agents", ".cursor", ".claude"}
    ]
    return [f for f in files if os.path.lexists(f)]


def tracked_lookup(md_files):
    exact = {exact_path_key(path): path for path in md_files}
    folded = {folded_path_key(path): path for path in md_files}
    return exact, folded


def link_targets(text):
    """Yield relative link targets, skipping fenced code blocks."""
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for target in LINK.findall(line):
            yield target


def main():
    check_all = "--all" in sys.argv[1:]
    md_files = tracked_md()
    tracked_markdown, folded_tracked_markdown = tracked_lookup(md_files)
    anchors, read_bad = anchor_map(md_files)
    # anchor_map drops files it can't read from the anchor index but records why
    # in read_bad. Key those reasons by realpath so the link loop below can blame
    # the real cause (e.g. "cannot read file") instead of a bogus "missing anchor"
    # when a link points at a tracked-but-unreadable Markdown file.
    read_failures = {os.path.realpath(f): why for f, _, why in read_bad}
    surface_files = surface(check_all, md_files)
    # anchor_map records read failures for every tracked file because the anchor
    # index has to cover any link target. A read failure only fails the run if
    # that file is on the surface, which is every tracked file under --all but
    # just AGENTS.md/CLAUDE.md/.agents in default mode. Otherwise a symlink or
    # unreadable Markdown under docs/ that nothing links to would break the
    # default hook.
    surface_set = set(surface_files)
    bad = [entry for entry in read_bad if entry[0] in surface_set]
    already_bad = {f for f, _, _ in bad}
    for f in surface_files:
        base = os.path.dirname(f)
        text, why = read_markdown(f)
        if text is None:
            if f not in already_bad:
                bad.append((f, os.path.relpath(f, ROOT), why))
            continue
        for target in link_targets(text):
            path, _, anc = target.partition("#")
            joined = os.path.join(base, path)
            linked = os.path.normpath(joined)
            # realpath the raw join, not the normpath'd path: normpath collapses
            # `link/..` lexically, dropping a symlink component before the OS gets
            # to resolve it. A link like ./link/../x.md (link -> /outside) would
            # then look in-repo even though it escapes. Resolve from the raw path
            # so the escape check sees where the symlinks actually point; the
            # normpath'd `linked` is still what the tracked-file lookup keys on.
            rp = os.path.realpath(joined)
            if not within_root(rp):
                bad.append((f, target, "target escapes repo"))
            elif is_markdown_target(path):
                tracked = tracked_markdown_lookup(
                    linked,
                    tracked_markdown,
                    folded_tracked_markdown,
                )
                if tracked is None:
                    bad.append((f, target, "missing file"))
                    continue
                ok, why = safe_markdown_path(tracked)
                if not ok:
                    bad.append((f, target, why))
                    continue
                anchor_key = os.path.realpath(tracked)
                if anchor_key not in anchors:
                    # safe_markdown_path only stats; a file can pass that yet still
                    # fail to read (e.g. no read permission). Report the real
                    # reason for both plain and #fragment links instead of letting
                    # plain links pass silently or fragment links say "missing
                    # anchor".
                    bad.append(
                        (f, target, read_failures.get(anchor_key, "cannot read file"))
                    )
                elif anc and anc not in anchors[anchor_key]:
                    bad.append((f, target, "missing anchor"))
            elif not os.path.exists(rp):
                bad.append((f, target, "missing file"))
    for f, target, why in bad:
        print(f"BROKEN [{why}] {os.path.relpath(f, ROOT)} -> {target}")
    if bad:
        print(f"\n{len(bad)} broken link(s).")
        return 1
    print("All context links and anchors resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
