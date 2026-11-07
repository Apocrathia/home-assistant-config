#!/usr/bin/env python3
"""Check that intra-repo markdown links and #anchors in the context surface
resolve. Exit 0 if all good, 1 if any are broken. Safe to run from a hook.

Default surface: AGENTS.md, CLAUDE.md, .agents/README.md,
.agents/**/*.md, and tracked .claude/**/*.md. Pass --all to check every
tracked markdown file in the repo instead.
"""

import html
import os
import re
import stat
import subprocess
import sys
from urllib.parse import unquote, urlsplit


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
HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.*)")
SETEXT_UNDERLINE = re.compile(r"^ {0,3}(?:=+|-+)\s*$")
_FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
_CONTAINER_MARKER = re.compile(r"^( {0,3})(?:> ?|(?:[-*+]|\d{1,9}[.)])(?=[ \t]|$))")
_LIST_START = re.compile(r"^( {0,3})([-*+]|\d{1,9}[.)])(?=[ \t]|$)")
MAX_MARKDOWN_BYTES = 1_000_000
MAX_REF_LABEL = 999


def container_content(line, pending, allow_list_interrupt=True):
    """Strip list/blockquote prefixes so fence indent is container-relative.

    List continuation keeps the pending indent across blank lines (a 4-space
    fence under a list item is still a fence). A blank unmarked line exits a
    blockquote, so the following indented line is ordinary indented code.
    Ordered lists starting at a number other than 1 cannot interrupt a
    paragraph. List-marker padding is at most four columns; extra spaces
    stay in the item content.
    """
    if isinstance(pending, tuple):
        pending_indent, pending_quote = pending
    else:
        pending_indent, pending_quote = pending, False
    raw = line.rstrip("\n")
    if not raw.strip():
        if pending_quote:
            return (0, False), raw
        return (pending_indent, False), raw
    s = raw
    indent = 0
    saw_quote = False
    saw_list = False
    while True:
        m = _CONTAINER_MARKER.match(s)
        if not m:
            break
        if ">" in m.group(0):
            saw_quote = True
            indent += m.end()
            s = s[m.end() :]
            continue
        lm = _LIST_START.match(s)
        if not lm:
            break
        num = re.match(r"(\d+)", lm.group(2))
        if not allow_list_interrupt and num and int(num.group(1)) != 1:
            break
        after = s[lm.end() :]
        pad = 0
        n = 0
        while n < len(after) and after[n] in " \t" and pad < 5:
            if after[n] == " ":
                pad += 1
                n += 1
            else:
                pad = (pad // 4 + 1) * 4
                n += 1
        if pad == 0 and after:
            break
        if pad > 4:
            n = 1
        saw_list = True
        indent += lm.end() + n
        s = after[n:]
    if indent:
        return (indent, saw_quote and not saw_list), s
    if pending_indent:
        n = 0
        cols = 0
        while cols < pending_indent and n < len(raw):
            if raw[n] == " ":
                cols += 1
                n += 1
            elif raw[n] == "\t":
                cols = (cols // 4 + 1) * 4
                n += 1
            else:
                break
        if n:
            return (pending_indent, pending_quote), raw[n:]
    if pending_quote and _is_lazy_quote_line(raw):
        return (pending_indent, True), raw
    return (0, False), raw


def _is_lazy_quote_line(content):
    if not content.strip():
        return False
    if HEADING.match(content) or SETEXT_UNDERLINE.match(content):
        return False
    if _CONTAINER_MARKER.match(content) or _FENCE.match(content):
        return False
    if is_indented_code_line(content):
        return False
    return True


def mask_code_spans(s, replace=None):
    """Drop or rewrite CommonMark code spans, including multi-backtick runs."""
    out = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] != "`":
            out.append(s[i])
            i += 1
            continue
        run = 1
        while i + run < n and s[i + run] == "`":
            run += 1
        j = i + run
        found = None
        while j < n:
            if s[j] != "`":
                j += 1
                continue
            close = 1
            while j + close < n and s[j + close] == "`":
                close += 1
            if close == run:
                found = j + close
                break
            j += close
        if found is None:
            out.append(s[i : i + run])
            i += run
            continue
        span = s[i:found]
        if replace is not None:
            out.append(replace(span))
        i = found
    return "".join(out)


def is_escaped_at(text, idx):
    bs = 0
    k = idx - 1
    while k >= 0 and text[k] == "\\":
        bs += 1
        k -= 1
    return bs % 2 == 1


_HTML_BLOCK_OPEN = re.compile(r"^ {0,3}<(script|style|pre|textarea)(?:\s|>|$)", re.I)
_HTML_CLOSE = {
    "script": re.compile(r"</script>", re.I),
    "style": re.compile(r"</style>", re.I),
    "pre": re.compile(r"</pre>", re.I),
    "textarea": re.compile(r"</textarea>", re.I),
}


_HTML_TYPE2_OPEN = re.compile(r"^ {0,3}<!--")
_HTML_TYPE3_OPEN = re.compile(r"^ {0,3}<\?")
_HTML_TYPE4_OPEN = re.compile(r"^ {0,3}<![A-Z]")
_HTML_TYPE5_OPEN = re.compile(r"^ {0,3}<!\[CDATA\[")
_HTML_TYPE6 = re.compile(
    r"^ {0,3}</?(?:address|article|aside|base|basefont|blockquote|body|"
    r"caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|"
    r"fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|"
    r"head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|"
    r"nav|noframes|ol|optgroup|option|p|param|search|section|summary|"
    r"table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:\s|/?>|$)",
    re.I,
)
_HTML_TYPE7 = re.compile(
    r"^ {0,3}(?:</[A-Za-z][A-Za-z0-9-]*\s*>|"
    r"<[A-Za-z][A-Za-z0-9-]*"
    r"(?:\s+[^\s\"'`=<>]+(?:=(?:[^\s\"'`=<>]+|\"[^\"]*\"|'[^']*'))?)*"
    r"\s*/?>)\s*$"
)
_HTML_BLOCK_END = {
    "type2": "-->",
    "type3": "?>",
    "type4": ">",
    "type5": "]]>",
}


def html_block_state(tag, content, allow_type7=True):
    """Return (new_tag, skip_line) for CommonMark HTML block types 1-7."""
    if tag in _HTML_BLOCK_END:
        if _HTML_BLOCK_END[tag] in content:
            return None, True
        return tag, True
    if tag in ("type6", "type7"):
        if not content.strip():
            return None, True
        return tag, True
    if tag:
        if _HTML_CLOSE[tag].search(content):
            return None, True
        return tag, True
    m = _HTML_BLOCK_OPEN.match(content)
    if m:
        name = m.group(1).lower()
        if _HTML_CLOSE[name].search(content):
            return None, True
        return name, True
    if _HTML_TYPE2_OPEN.match(content):
        if "-->" in content:
            return None, True
        return "type2", True
    if _HTML_TYPE3_OPEN.match(content):
        if "?>" in content:
            return None, True
        return "type3", True
    if _HTML_TYPE5_OPEN.match(content):
        if "]]>" in content:
            return None, True
        return "type5", True
    if _HTML_TYPE4_OPEN.match(content):
        if ">" in content:
            return None, True
        return "type4", True
    if _HTML_TYPE6.match(content):
        return "type6", True
    if allow_type7 and _is_type7_html(content):
        return "type7", True
    return None, False


def mask_code_spans_state(s, open_run=0):
    """Drop span bodies, including an opener that continues on the next line."""
    out = []
    i = 0
    n = len(s)
    if open_run:
        while i < n:
            if s[i] != "`":
                i += 1
                continue
            run = 1
            while i + run < n and s[i + run] == "`":
                run += 1
            if run == open_run:
                i += run
                open_run = 0
                break
            i += run
        else:
            return "", open_run
    while i < n:
        if s[i] != "`":
            out.append(s[i])
            i += 1
            continue
        run = 1
        while i + run < n and s[i + run] == "`":
            run += 1
        j = i + run
        found = None
        while j < n:
            if s[j] != "`":
                j += 1
                continue
            close = 1
            while j + close < n and s[j + close] == "`":
                close += 1
            if close == run:
                found = j + close
                break
            j += close
        if found is None:
            return "".join(out), run
        i = found
    return "".join(out), 0


def strip_balanced_links(s):
    """Replace ``[label](dest)`` / ``![alt](dest)`` with the label text."""
    out = []
    i = 0
    n = len(s)
    while i < n:
        j = s.find("[", i)
        if j < 0:
            out.append(s[i:])
            break
        if is_escaped_at(s, j):
            out.append(s[i : j + 1])
            i = j + 1
            continue
        k = j + 1
        depth = 1
        while k < n and depth:
            if is_escaped_at(s, k):
                k += 1
                continue
            if s[k] == "[":
                depth += 1
            elif s[k] == "]":
                depth -= 1
            k += 1
        if depth != 0 or k >= n or s[k] != "(":
            out.append(s[i : j + 1])
            i = j + 1
            continue
        dest_end = _dest_end(s, k + 1)
        if dest_end is None:
            out.append(s[i : j + 1])
            i = j + 1
            continue
        prefix = s[i:j]
        if prefix.endswith("!"):
            prefix = prefix[:-1]
        out.append(prefix)
        out.append(s[j + 1 : k - 1])
        i = dest_end
    return "".join(out)


def strip_ref_style_links(s, refs=None):
    """Replace defined ``[label][ref]`` / ``![alt][ref]`` with the visible label."""
    out = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] != "[" or is_escaped_at(s, i):
            out.append(s[i])
            i += 1
            continue
        is_img = i > 0 and s[i - 1] == "!" and not is_escaped_at(s, i - 1)
        label, j = _read_link_label(s, i)
        if label is None:
            out.append(s[i])
            i += 1
            continue
        if j < n and s[j] == "[":
            ref, k = _read_link_label(s, j)
            if ref is not None:
                folded = _ref_label(ref or label)
                if refs is not None and folded and folded in refs:
                    if is_img and out:
                        out.pop()
                    out.append(unescape_md_dest(label))
                    i = k
                    continue
                out.append(s[i:k])
                i = k
                continue
        out.append(s[i])
        i += 1
    return "".join(out)


def feed_html_comment(in_comment, content):
    """Strip HTML comments. Return ``(still_in_comment, visible_text)``.

    Inline code is masked first so `` `<!--` `` does not open a comment.
    """
    held = []

    def _hold(span):
        held.append(span)
        return f"\x00C{len(held) - 1}\x00"

    s = mask_code_spans(content, _hold)
    out = []
    if in_comment:
        end = s.find("-->")
        if end < 0:
            return True, ""
        s = s[end + 3 :]
        in_comment = False
    while True:
        start = s.find("<!--")
        if start < 0:
            out.append(s)
            visible = "".join(out)
            break
        out.append(s[:start])
        s = s[start + 4 :]
        end = s.find("-->")
        if end < 0:
            out.append("<!--")
            out.append(s)
            visible = "".join(out)
            for i, val in enumerate(held):
                visible = visible.replace(f"\x00C{i}\x00", val)
            return False, visible
        s = s[end + 3 :]
    for i, val in enumerate(held):
        visible = visible.replace(f"\x00C{i}\x00", val)
    return False, visible


def is_indented_code_line(content):
    if content.startswith("\t"):
        return True
    n = 0
    while n < len(content) and content[n] == " ":
        n += 1
    return n >= 4


def update_fence(fence, line, allow_close=True):
    """Advance CommonMark fence state. Return ``(new_fence, is_delimiter)``.

    *fence* is ``None`` or ``(char, min_len)``. A closing fence must use the
    same character, be at least as long as the opener, and have no info
    string. Nested ````` inside a ```` fence stays content.

    When a fence is open and the line is closer-shaped, *allow_close*
    decides whether it closes. Callers that know the raw container prefix
    pass False for lines CommonMark treats as fence content (a
    ``> ``` ``-shaped line inside a document fence, a deeper quote run
    inside a blockquote fence, a sibling list marker under a list fence).
    """
    m = _FENCE.match(line.rstrip("\n"))
    if not m:
        return fence, False
    mark, rest = m.group(2), m.group(3)
    ch, n = mark[0], len(mark)
    if fence is None:
        if ch == "`" and "`" in rest:
            return fence, False
        return (ch, n), True
    if ch == fence[0] and n >= fence[1] and rest.strip() == "":
        if not allow_close:
            return fence, False
        return None, True
    return fence, False


_LIST_MARKER = re.compile(r"(?:[*+-]|\d{1,9}[.)])[ \t]+")


def _container_scan(line):
    """Parse a raw line's leading container prefix: ``>`` blockquote
    markers and list markers at any depth, each behind up to three indent
    characters, with one optional space swallowed after a ``>``.

    Deterministic and linear: the space after a ``>`` is consumed in one
    place only, and depth is bounded by line length, not a fixed count.
    Returns ``(quote_depth, list_depth, fence_offset)``.
    """
    quote = lists = 0
    pos = 0
    n = len(line)
    while True:
        start = pos
        while pos < n and line[pos] in " \t" and pos - start < 3:
            pos += 1
        if pos < n and line[pos] == ">":
            quote += 1
            pos += 1
            if pos < n and line[pos] in " \t":
                pos += 1
            continue
        marker = _LIST_MARKER.match(line, pos)
        if marker is None:
            break
        lists += 1
        pos = marker.end()
    return quote, lists, pos


def _after_quotes(line):
    """Offset past leading ``>`` markers and the optional space after each.

    Indent not followed by ``>`` stays in place so sibling-fence detection
    measures a container-relative margin: raw ``lstrip`` margin is always
    zero on a ``>``-prefixed line, which hid indented continuation and made
    the marker check read the quote character instead of the list marker.
    """
    pos = 0
    n = len(line)
    while True:
        start = pos
        look = pos
        while look < n and line[look] in " \t" and look - start < 3:
            look += 1
        if look < n and line[look] == ">":
            pos = look + 1
            if pos < n and line[pos] in " \t":
                pos += 1
            continue
        return pos


def _content_margin(line):
    """Indent after quote prefixes, and the offset where that indent starts."""
    at = _after_quotes(line)
    rest = line[at:]
    return at, len(rest) - len(rest.lstrip())


def _quote_marker_indent(line, depth):
    """Raw indent before the ``(depth + 1)``-th ``>`` marker, or None.

    Walks with the same rules as ``_container_scan``: up to three indent
    characters before a marker, one optional space after it. Returns the
    indent measured from after the *depth*-th marker, or ``None`` when
    the line has no deeper quote marker.
    """
    pos = 0
    n = len(line)
    for _ in range(depth):
        start = pos
        while pos < n and line[pos] in " \t" and pos - start < 3:
            pos += 1
        if pos >= n or line[pos] != ">":
            return None
        pos += 1
        if pos < n and line[pos] in " \t":
            pos += 1
    start = pos
    look = pos
    while look < n and line[look] in " \t" and look - start < 3:
        look += 1
    if look >= n or line[look] != ">":
        return None
    return look - pos


def _pending_parts(pending):
    """``(indent, quote_only)`` from ``container_content`` state."""
    if isinstance(pending, tuple):
        return pending[0], bool(pending[1])
    return pending or 0, False


def _continuation_column(raw_line, pending):
    """Content column when *raw_line* continues a list item, else None.

    *pending* is the container state from the previous line. A fence under
    a list item is indented to that item's content column and usually has
    no list marker of its own. The returned column is relative to the
    line's blockquote prefix, which is the same measure ``_fence_closer_ok``
    uses for a marker-line list fence.
    """
    indent, quote_only = _pending_parts(pending)
    if quote_only or indent <= 0:
        return None
    qpos = _after_quotes(raw_line)
    rel = indent - qpos
    if rel <= 0:
        return None
    cols = 0
    for ch in raw_line[qpos:]:
        if ch == " ":
            cols += 1
        elif ch == "\t":
            cols = (cols // 4 + 1) * 4
        else:
            break
        if cols >= rel:
            return rel
    return None


def _rel_marker_column(line):
    """Indent of the first list marker after quote prefixes, or None."""
    pos = _after_quotes(line)
    n = len(line)
    look = pos
    while look < n and line[look] in " \t" and look - pos < 3:
        look += 1
    if look < n and _LIST_MARKER.match(line, look):
        return look - pos
    return None


def _fence_context(raw_line, pending=0):
    """Opener context for a fence: kind, quote depth, prefix, margin.

    Returns ``[kind, quote_depth, prefix, margin, saw_indented]`` where
    kind is ``"doc"``, ``"quote"``, or ``"container"`` (list markers).
    *prefix* is the raw container prefix up to the fence run, *margin* the
    content indent measured after quote prefixes, and *saw_indented* a
    mutable flag set once a body line is indented past the opener margin.

    A fence opened by indent under a list item has no marker on the opener
    line. It is still a container fence: *prefix* is empty and *margin* is
    the item's content column, so a later sibling or interrupt closer is
    not judged with document or quote rules.
    """
    quote, lists, at = _container_scan(raw_line)
    if lists:
        _, margin = _content_margin(raw_line)
        # Keep the opener's quote depth. An indented continuation closer
        # repeats those ``>`` markers and omits the list marker, so a
        # container fence cannot match it on the raw prefix alone.
        return ["container", quote, raw_line[:at], margin, False]
    column = _continuation_column(raw_line, pending)
    if column is not None:
        return ["container", quote, "", column, False]
    if quote:
        return ["quote", quote, "", 0, False]
    return ["doc", 0, "", 0, False]


def _continuation_fence_closer_ok(raw_line, ctx):
    """Closer rules for a fence opened on a list-item continuation line.

    ``ctx[3]`` is the item's content column relative to ``ctx[1]`` quote
    markers. A list or blockquote marker before that column ends the item,
    so a closer-shaped line there closes the fence. A marker at the column
    is inside the item and stays fence content. An indented closer, a
    parent-blockquote leftover, and a shallower quote run close too.
    """
    quote, lists, _at = _container_scan(raw_line)
    column = ctx[3]
    if quote > ctx[1]:
        indent = _quote_marker_indent(raw_line, ctx[1])
        return indent is not None and indent < column
    if lists:
        if quote < ctx[1]:
            return True
        marker_col = _rel_marker_column(raw_line)
        return marker_col is not None and marker_col < column
    return True


def _fence_closer_ok(raw_line, fence, ctx):
    """True when a closer-shaped raw line may close the open fence.

    The closer's container prefix must match the opener's kind: a
    document-level fence closes only at document level; a blockquote fence
    closes at the opener's quote depth or any shallower depth (the optional
    space after ``>`` may vary per line). A shallower ``>`` run ends the
    inner blockquote, so the leftover closer still closes the fence; a
    deeper run is content left after CommonMark strips the parent markers.
    A list fence closes on an exact replay of the opener's raw prefix,
    at document level, on an indented continuation that keeps the
    opener's blockquote markers and omits the list marker, on a
    parent-blockquote leftover that ends the list item, or on a deeper
    quote marker that interrupts the item. A sibling
    list marker after indented continuation opens a sibling item instead.
    A continuation fence (empty prefix) uses the item content column
    instead of that prefix replay.
    """
    quote, lists, at = _container_scan(raw_line)
    kind = ctx[0]
    if kind == "doc":
        return quote == 0 and lists == 0
    if kind == "quote":
        # Fewer ``>`` markers than the opener end the inner blockquote,
        # including a raw line with none. A closer-shaped line at that
        # depth still closes the fence; a deeper run is fence content.
        # A list marker still inside that quote is content. A list marker
        # outside it (shallower depth, including none) ends the quote, so
        # the fence closes there too.
        if lists and quote >= ctx[1]:
            return False
        return quote <= ctx[1]
    if not ctx[2]:
        return _continuation_fence_closer_ok(raw_line, ctx)
    if quote == 0 and lists == 0:
        return True
    if lists and raw_line.startswith(ctx[2]):
        run_ch, run_len = fence[0], fence[1]
        body = raw_line[len(ctx[2]) :]
        if not re.match(rf"{re.escape(run_ch)}{{{run_len},}}[ \t]*$", body):
            return False
        content_at, margin = _content_margin(raw_line)
        if (
            ctx[4]
            and margin <= ctx[3]
            and _LIST_MARKER.match(raw_line, content_at + margin)
        ):
            return False
        return True
    # Quoted-list continuation, or the parent blockquote left once the
    # list item ends. The usual closer keeps the opener's ``>`` markers
    # and reaches the fence by indent, so it has no list marker to replay;
    # at most three spaces past the item's content column still count.
    # A smaller margin is not inside the item: the ``>`` run is a leftover
    # of the parent quote and the closer-shaped remainder closes the fence.
    # A shallower ``>`` run ends the inner blockquote the same way.
    if not lists and quote and quote <= ctx[1]:
        if quote < ctx[1]:
            return True
        _, margin = _content_margin(raw_line)
        column = len(ctx[2]) - _after_quotes(ctx[2])
        if margin <= column + 3:
            return True
    # A deeper ``>`` run than the opener's quote depth interrupts the list
    # item: CommonMark starts a nested blockquote there, and the item (and
    # the fence inside it) ends. That holds only while the marker sits at
    # the opener's own quote level — indented to the item's content column
    # it opens a quote inside the item, where the fence reads it as
    # content. This is the reverse of the quote-fence case above: a quote
    # fence closes on a list marker that ends its blockquote, and a list
    # fence closes on a quote marker that ends its item.
    if not lists and quote > ctx[1]:
        indent = _quote_marker_indent(raw_line, ctx[1])
        column = len(ctx[2]) - _after_quotes(ctx[2])
        if indent is not None and indent < column:
            return True
    return False


def is_markdown_target(path: str) -> bool:
    """True when path (no fragment) points at a Markdown file.

    Includes ``*.md.tmpl`` so ``--all`` scans scaffold templates the same way
    it scans the rendered ``.md`` consumers get.
    """
    p = path.rstrip("/\\").lower()
    return p.endswith(".md") or p.endswith(".md.tmpl")


def is_template_source(path: str) -> bool:
    """True when *path* is a scaffold ``*.md.tmpl`` source."""
    return path.rstrip("/\\").lower().endswith(".md.tmpl")


def template_sibling_target(path: str):
    """Map a rendered ``*.md`` path to its sibling ``*.md.tmpl``, or None.

    Templates keep the consumer-facing ``./enforcement.md`` link text; the
    scaffold tree stores the sibling as ``enforcement.md.tmpl``.
    """
    p = path.rstrip("/\\")
    lower = p.lower()
    if lower.endswith(".md.tmpl"):
        return None
    if lower.endswith(".md"):
        return p + ".tmpl"
    return None


_RENAMED_TEMPLATE = {
    "AGENTS.md": "AGENTS.md",
    "agents-README.md": ".agents/README.md",
    "rules-README.md": ".agents/rules/README.md",
    "memories-README.md": ".agents/memories/README.md",
    "scratch-README.md": ".scratch/README.md",
}

_TEMPLATE_FOR_DEPLOYED = {
    "AGENTS.md": "templates/AGENTS.md.tmpl",
    ".agents/README.md": "templates/agents-README.md.tmpl",
    ".agents/rules/README.md": "templates/rules-README.md.tmpl",
    ".agents/memories/README.md": "templates/memories-README.md.tmpl",
    ".scratch/README.md": "templates/scratch-README.md.tmpl",
}


def _posix_rel(path):
    rel = os.path.relpath(path, ROOT) if os.path.isabs(path) else path
    return rel.replace(os.sep, "/")


def template_to_deployed(path):
    """Consumer path a ``templates/*.tmpl`` source renders to, or None."""
    rel = _posix_rel(path)
    if not rel.startswith("templates/"):
        return None
    rest = rel[len("templates/") :]
    if rest.endswith(".tmpl"):
        rest = rest[:-5]
    deployed = _RENAMED_TEMPLATE.get(rest, ".agents/" + rest)
    return os.path.join(ROOT, *deployed.split("/"))


def deployed_to_template(path):
    """Scaffold source that *path* deploys from in a consumer, or None."""
    rel = _posix_rel(path)
    mapped = _TEMPLATE_FOR_DEPLOYED.get(rel)
    if mapped:
        cand = os.path.join(ROOT, *mapped.split("/"))
        return cand if os.path.isfile(cand) else None
    for prefix, dest_dir, suffix in (
        (".agents/context/", "templates/context", ".tmpl"),
        (".agents/agents/", "templates/agents", ".tmpl"),
        (".agents/references/", "templates/references", ".tmpl"),
        # Skills and rules are copied as-is from the core trees.
        (".agents/skills/", "skills", ""),
        (".agents/rules/", "rules", ""),
    ):
        if rel.startswith(prefix):
            rest = rel[len(prefix) :]
            if suffix:
                tmpl = os.path.join(ROOT, dest_dir, rest + suffix)
                direct = os.path.join(ROOT, dest_dir, rest)
                if os.path.isfile(tmpl):
                    return tmpl
                if os.path.isfile(direct):
                    return direct
                return None
            cand = os.path.join(ROOT, dest_dir, rest)
            return cand if os.path.isfile(cand) else None
    return None


def rendered_template_target(source, link_path):
    """Prefer the scaffold template a consumer-layout link actually hits.

    ``templates/context/loading.md.tmpl`` -> ``../../AGENTS.md`` lexically
    lands on this repo's core ``AGENTS.md``. Consumers get
    ``templates/AGENTS.md.tmpl`` at that location, so resolve there first.
    """
    deployed_src = template_to_deployed(source)
    if deployed_src is None:
        return None
    deployed = os.path.normpath(os.path.join(os.path.dirname(deployed_src), link_path))
    return deployed_to_template(deployed)


def strip_inline_html(s):
    """Drop HTML tags, keeping quoted attribute text from cutting the tag short."""
    out = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] != "<":
            out.append(s[i])
            i += 1
            continue
        j = i
        while j > 0 and s[j - 1].isspace():
            j -= 1
        if j >= 2 and s[j - 2 : j] == "](" and not is_escaped_at(s, j - 2):
            out.append(s[i])
            i += 1
            continue
        end = _inline_html_end(s, i)
        if end is None:
            out.append(s[i])
            i += 1
            continue
        i = end
    return "".join(out)


def _inline_html_end(s, i):
    """Index after a valid CommonMark inline HTML construct, or None."""
    n = len(s)
    if i >= n or s[i] != "<" or i + 1 >= n:
        return None
    nxt = s[i + 1]
    if nxt == "/":
        j = i + 2
        if j >= n or not s[j].isalpha():
            return None
        j += 1
        while j < n and (s[j].isalnum() or s[j] == "-"):
            j += 1
        while j < n and s[j].isspace():
            j += 1
        if j < n and s[j] == ">":
            return j + 1
        return None
    if nxt.isalpha():
        j = i + 2
        while j < n and (s[j].isalnum() or s[j] == "-"):
            j += 1
        while True:
            while j < n and s[j].isspace():
                j += 1
            if j < n and s[j] == "/":
                j += 1
                while j < n and s[j].isspace():
                    j += 1
                if j < n and s[j] == ">":
                    return j + 1
                return None
            if j < n and s[j] == ">":
                return j + 1
            if j >= n or not (s[j].isalpha() or s[j] in "_:"):
                return None
            j += 1
            while j < n and (s[j].isalnum() or s[j] in "_.:-"):
                j += 1
            k = j
            while k < n and s[k].isspace():
                k += 1
            if k < n and s[k] == "=":
                k += 1
                while k < n and s[k].isspace():
                    k += 1
                if k >= n:
                    return None
                if s[k] in "\"'":
                    q = s[k]
                    k += 1
                    while k < n and s[k] != q:
                        k += 1
                    if k >= n:
                        return None
                    j = k + 1
                else:
                    if s[k].isspace() or s[k] in "\"'=<>`":
                        return None
                    k += 1
                    while k < n and not s[k].isspace() and s[k] not in "\"'=<>`":
                        k += 1
                    j = k
        return None
    if nxt == "?":
        j = i + 2
        while j + 1 < n:
            if s[j] == "?" and s[j + 1] == ">":
                return j + 2
            j += 1
        return None
    if nxt == "!":
        if s.startswith("<!--", i):
            end = s.find("-->", i + 4)
            return None if end < 0 else end + 3
        if s.startswith("<![CDATA[", i):
            end = s.find("]]>", i + 9)
            return None if end < 0 else end + 3
        if i + 2 >= n or not s[i + 2].isascii() or not s[i + 2].isupper():
            return None
        j = i + 3
        while j < n:
            if s[j] == ">":
                return j + 1
            j += 1
        return None
    return None


def _is_type7_html(content):
    s = content or ""
    i = 0
    while i < 3 and i < len(s) and s[i] == " ":
        i += 1
    if i >= len(s) or s[i] != "<":
        return False
    end = _inline_html_end(s, i)
    return end is not None and not s[end:].strip()


def slug(heading: str, refs=None) -> str:
    """GitHub-style anchor slug. Does NOT collapse repeated hyphens.

    GitHub slugs the rendered heading, so ``# [Setup](./guide.md)`` and
    ``# [Setup][guide]`` are ``setup``, not ``setupguidemd``. Inline HTML
    is stripped, but angle brackets inside backticks or GFM autolinks stay
    (``# Type `List<T>` `` is ``type-listt``).
    """
    s = heading
    s = re.sub(r"\{#([^}]+)\}", "", s)
    s = strip_balanced_links(s)
    s = strip_ref_style_links(s, refs)
    held = []

    def _hold(span):
        held.append(span)
        return f"\x00P{len(held) - 1}\x00"

    s = mask_code_spans(s, _hold)

    def _hold_autolink(m):
        held.append(m.group(0))
        return f"\x00P{len(held) - 1}\x00"

    s = re.sub(
        r"<(?:[a-zA-Z][a-zA-Z0-9+.-]{1,31}:[^<>\s]+|[^<>\s]+@[^<>\s]+)>",
        _hold_autolink,
        s,
    )
    s = strip_inline_html(s)
    s = unescape_md_entities(s)
    for i, val in enumerate(held):
        if val.startswith("`"):
            n = 0
            while n < len(val) and val[n] == "`":
                n += 1
            inner = val[n:-n] if n and val.endswith("`" * n) else val[1:-1]
            inner = inner.replace("\n", " ")
            if inner.startswith(" ") and inner.endswith(" ") and inner.strip():
                inner = inner[1:-1]
        elif val[:1] in "`<":
            inner = val[1:-1]
        else:
            inner = val
        s = s.replace(f"\x00P{i}\x00", inner)
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s", " ", s)
    return s.replace(" ", "-").strip("-")


def add_github_anchor(anchors, heading, refs=None):
    """Record a heading slug plus GitHub's duplicate suffixes (``-1``, ``-2``)."""
    base = slug(heading, refs)
    if base:
        cand = base
        i = 1
        while cand in anchors:
            cand = f"{base}-{i}"
            i += 1
        anchors.add(cand)
    explicit = re.search(r"\{#([^}]+)\}", heading)
    if explicit:
        anchors.add(explicit.group(1))


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
    hit = exact.get(exact_path_key(path))
    if hit is not None:
        return hit
    candidate = folded.get(folded_path_key(path))
    # A case-folded match is only real when the filesystem itself folds
    # case: the link path and the tracked file must denote the same file
    # on disk. On a case-sensitive filesystem an untracked case variant is
    # a different file (or missing), and the link is broken.
    if candidate is not None:
        try:
            if os.path.samefile(path, candidate):
                return candidate
        except OSError:
            return None
    return None


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
        refs = _collect_ref_map(text)
        fence = None
        fence_ctx = None
        para = []
        pending = 0
        in_comment = False
        html_tag = None
        span_run = 0
        after_para = False
        for line in text.splitlines():
            prev = pending
            pending, content = container_content(
                line, pending, allow_list_interrupt=not after_para
            )
            prev_indent = prev[0] if isinstance(prev, tuple) else prev
            new_indent = pending[0] if isinstance(pending, tuple) else pending
            if prev_indent and not new_indent:
                para = []
                after_para = False
            opened = fence is None
            if fence is not None and fence_ctx is not None:
                if _content_margin(line)[1] > fence_ctx[3]:
                    fence_ctx[4] = True
            fence, delim = update_fence(
                fence,
                content,
                allow_close=(
                    True if fence is None else _fence_closer_ok(line, fence, fence_ctx)
                ),
            )
            if opened and fence is not None:
                fence_ctx = _fence_context(line, prev)
            elif fence is None:
                fence_ctx = None
            if delim or fence is not None:
                para = []
                span_run = 0
                after_para = False
                continue
            html_tag, skip_html = html_block_state(
                html_tag, content, allow_type7=not any(p.strip() for p in para)
            )
            if skip_html:
                para = []
                after_para = False
                continue
            if span_run and (
                not content.strip()
                or HEADING.match(content)
                or SETEXT_UNDERLINE.match(content)
            ):
                span_run = 0
            if span_run:
                _, span_run = mask_code_spans_state(content, span_run)
                para.append(content)
                continue
            _, span_run = mask_code_spans_state(content, 0)
            in_comment, content = feed_html_comment(in_comment, content)
            if is_indented_code_line(content):
                para = []
                after_para = False
                continue
            if not after_para and _parse_ref_def(content) is not None:
                para = []
                after_para = False
                continue
            h = HEADING.match(content)
            if h:
                add_github_anchor(anchors, h.group(1), refs)
                para = []
                after_para = False
                continue
            if (
                para
                and SETEXT_UNDERLINE.match(content)
                and any(p.strip() for p in para)
                and not para[0].lstrip().startswith("#")
            ):
                add_github_anchor(
                    anchors,
                    " ".join(p.strip() for p in para if p.strip()),
                    refs,
                )
                para = []
                after_para = False
                continue
            if not content.strip():
                para = []
                after_para = False
                continue
            para.append(content)
            after_para = True
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
        in {".agents", ".claude"}
    ]
    return [f for f in files if os.path.lexists(f) and not is_template_source(f)]


def drop_internal_symlinks(surface_files, md_files):
    """Drop surface files that are symlinks to another tracked Markdown file.

    Harness discovery paths are symlinks into `.agents/` (CLAUDE.md -> AGENTS.md,
    .claude/agents/ -> .agents/agents/). safe_markdown_path refuses to read
    through any symlink, so scanning these reports the file as broken against
    itself. The target is tracked and scanned on its own, so skipping the link
    is lossless — provided the target is also on the surface.  When a symlink
    target is tracked but NOT on the surface (e.g. a `.agents/` alias pointing
    at a `docs/` file in default mode), the alias is kept so the link is still
    validated.  A broken symlink (realpath resolves to a nonexistent target) is
    never dropped: its target is not a tracked file, so it stays on the surface
    and is reported as broken.
    """
    # Only independently tracked non-symlink files count as targets: a
    # tracked symlink's realpath would otherwise put its (possibly untracked)
    # target into the set, letting an alias to an unvalidated file vanish.
    tracked = {os.path.realpath(f) for f in md_files if not os.path.islink(f)}
    # Like `tracked`, the surface set must exclude symlinks: an alias's
    # realpath would otherwise put its target into the set via the alias
    # itself, so the guard below could never preserve the alias and the
    # target would never be scanned.
    surface_real = {os.path.realpath(f) for f in surface_files if not os.path.islink(f)}
    kept = []
    for f in surface_files:
        try:
            is_link = stat.S_ISLNK(os.lstat(f).st_mode)
        except OSError:
            kept.append(f)
            continue
        real = os.path.realpath(f)
        if is_link and within_root(real) and real in tracked and os.path.exists(real):
            if real not in surface_real:
                # Target is tracked but not on this surface — keep the alias
                # so it gets validated on its own terms.
                kept.append(f)
                continue
            continue  # drop the alias — the target is on the surface and will be scanned
        kept.append(f)
    return kept


def tracked_lookup(md_files):
    exact = {exact_path_key(path): path for path in md_files}
    folded = {folded_path_key(path): path for path in md_files}
    return exact, folded


def _unescaped_find(s, ch, start=0):
    i = start
    n = len(s)
    while i < n:
        if s[i] == "\\" and i + 1 < n:
            i += 2
            continue
        if s[i] == ch:
            return i
        i += 1
    return -1


def _valid_angle_inner(inner):
    i = 0
    n = len(inner)
    while i < n:
        if inner[i] == "\\" and i + 1 < n:
            i += 2
            continue
        if inner[i] in "<\n":
            return False
        i += 1
    return True


def _take_ref_dest(rest):
    rest = rest or ""
    if rest.startswith("<"):
        end = _unescaped_find(rest, ">", 1)
        if end < 1:
            return None, rest
        inner = rest[1:end]
        if not _valid_angle_inner(inner):
            return None, rest
        return unescape_md_dest(inner), rest[end + 1 :]
    i = 0
    n = len(rest)
    while i < n and not rest[i].isspace():
        if rest[i] == "\\" and i + 1 < n:
            i += 2
            continue
        i += 1
    if i == 0:
        return None, rest
    dest_raw = rest[:i]
    if not _balanced_parens(dest_raw):
        return None, rest
    return unescape_md_dest(dest_raw), rest[i:]


def _balanced_parens(s):
    depth = 0
    i = 0
    n = len(s)
    while i < n:
        if s[i] == "\\" and i + 1 < n:
            i += 2
            continue
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0


def _complete_ref_title(rest):
    rest = (rest or "").strip()
    if not rest:
        return True
    if rest[0] not in "\"'(":
        return False
    closer = ")" if rest[0] == "(" else rest[0]
    end = _unescaped_find(rest, closer, 1)
    if end < 0:
        return True
    return rest[end + 1 :].strip() == ""


def _title_pending_state(after):
    rest = (after or "").strip()
    if not rest:
        return "start"
    if rest[0] not in "\"'(":
        return False
    closer = ")" if rest[0] == "(" else rest[0]
    if _unescaped_find(rest, closer, 1) < 0:
        return closer
    return False


def _title_line_consumed(content, pending):
    rest = (content or "").strip()
    if pending == "start":
        if not rest or rest[0] not in "\"'(":
            return False, False
        closer = ")" if rest[0] == "(" else rest[0]
        end = _unescaped_find(rest, closer, 1)
        if end < 0:
            return closer, True
        if rest[end + 1 :].strip():
            return False, False
        return False, True
    if pending in "\"')":
        if not rest:
            return False, False
        end = _unescaped_find(rest, pending, 0)
        if end >= 0 and rest[end + 1 :].strip() == "":
            return False, True
        return False, False
    return False, False


def _open_ref_label(content):
    s = content or ""
    i = 0
    while i < 3 and i < len(s) and s[i] == " ":
        i += 1
    if i >= len(s) or s[i] != "[":
        return None
    i += 1
    start = i
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            i += 2
            continue
        if s[i] == "[":
            return None
        if s[i] == "]":
            return None
        i += 1
    raw = s[start:]
    if not raw or len(raw) > MAX_REF_LABEL:
        return None
    return raw


def _finish_ref_label(pending_raw, content):
    s = (pending_raw or "") + " " + (content or "").lstrip()
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            i += 2
            continue
        if s[i] == "[":
            return None
        if s[i] == "]":
            break
        i += 1
    else:
        if len(s) > MAX_REF_LABEL:
            return None
        return ("open", s)
    raw = s[:i]
    if not raw or len(raw) > MAX_REF_LABEL:
        return None
    i += 1
    if i >= len(s) or s[i] != ":":
        return None
    rest = s[i + 1 :].lstrip()
    if not rest:
        return ("def", _ref_label(raw), None)
    dest, after = _take_ref_dest(rest)
    if dest is None or not _complete_ref_title(after):
        return None
    return ("def", _ref_label(raw), dest)


def _parse_ref_def(content):
    s = content or ""
    i = 0
    while i < 3 and i < len(s) and s[i] == " ":
        i += 1
    if i >= len(s) or s[i] != "[":
        return None
    i += 1
    start = i
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            i += 2
            continue
        if s[i] == "[":
            return None
        if s[i] == "]":
            break
        i += 1
    else:
        return None
    raw = s[start:i]
    if not raw or len(raw) > MAX_REF_LABEL:
        return None
    if unescape_md_dest(raw).lstrip().startswith("^"):
        return None
    label = _ref_label(raw)
    i += 1
    if i >= len(s) or s[i] != ":":
        return None
    rest = s[i + 1 :].lstrip()
    if not rest:
        return label, None
    dest, after = _take_ref_dest(rest)
    if dest is None:
        return None
    if not _complete_ref_title(after):
        return None
    return label, dest


def _ref_dest(rest):
    dest, after = _take_ref_dest((rest or "").strip())
    if dest is None or not _complete_ref_title(after):
        return None
    return dest


def _iter_ref_uses(text):
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "[" or is_escaped_at(text, i):
            i += 1
            continue
        label, j = _read_link_label(text, i)
        if label is None:
            i += 1
            continue
        if j < n and text[j] == "(":
            i = j + 1
            continue
        if j < n and text[j] == "[":
            ref, k = _read_link_label(text, j)
            if ref is None:
                i = j + 1
                continue
            folded = _ref_label(ref or label)
            if folded:
                yield folded
            i = k
            continue
        folded = _ref_label(label)
        if folded:
            yield folded
        i = j


def _read_link_label(text, start):
    i = start + 1
    n = len(text)
    while i < n:
        if i - (start + 1) > MAX_REF_LABEL:
            return None, start
        if text[i] == "\\" and i + 1 < n:
            i += 2
            continue
        if text[i] == "[":
            return None, start
        if text[i] == "]":
            raw = text[start + 1 : i]
            if len(raw) > MAX_REF_LABEL:
                return None, start
            return raw, i + 1
        i += 1
    return None, start


def _usable_ref_dest(dest):
    if not dest:
        return False
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", dest):
        return False
    if dest.startswith("/"):
        return False
    return True


def _is_paragraph_text(content, *, allow_ref_def=True):
    if not content.strip():
        return False
    if HEADING.match(content):
        return False
    if SETEXT_UNDERLINE.match(content):
        return False
    if allow_ref_def and _parse_ref_def(content) is not None:
        return False
    return True


def _ref_label(label):
    label = unescape_md_dest(label or "").strip()
    if not label or label.startswith("^"):
        return ""
    return re.sub(r"\s+", " ", label).casefold()


def _dest_end(s, k):
    """Return the index after a destination that starts at ``k``, or None."""
    n = len(s)
    if k < n and s[k] == "<":
        p = k + 1
        while p < n:
            if s[p] == "\\" and p + 1 < n:
                p += 2
                continue
            if s[p] in "<\n":
                return None
            if s[p] == ">":
                q = p + 1
                while q < n and s[q].isspace():
                    q += 1
                if q < n and s[q] in "\"'(":
                    quote = ")" if s[q] == "(" else s[q]
                    q += 1
                    while q < n:
                        if s[q] == "\\" and q + 1 < n:
                            q += 2
                            continue
                        if s[q] == quote:
                            q += 1
                            break
                        q += 1
                    while q < n and s[q].isspace():
                        q += 1
                if q < n and s[q] == ")":
                    return q + 1
                return None
            p += 1
        return None
    depth = 1
    p = k
    dest_end = None
    quote = ""
    while p < n and depth:
        ch = s[p]
        if ch == "\\" and p + 1 < n:
            p += 2
            continue
        if quote:
            if ch == quote:
                quote = ""
            p += 1
            continue
        if dest_end is not None and ch in "\"'(":
            quote = ")" if ch == "(" else ch
            p += 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return p + 1
        elif ch.isspace() and dest_end is None:
            dest_end = p
        p += 1
    return None


_MD_ENTITY = re.compile(r"&(?:#x[0-9a-fA-F]+|#\d+|[A-Za-z][A-Za-z0-9]+);")


def unescape_md_entities(s):
    return _MD_ENTITY.sub(lambda m: html.unescape(m.group(0)), s)


_MD_ESCAPABLE = frozenset('!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\x27')


def unescape_md_dest(s):
    out = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt in _MD_ESCAPABLE:
                out.append(nxt)
                i += 2
                continue
            out.append("\\")
            i += 1
            continue
        out.append(s[i])
        i += 1
    return unescape_md_entities("".join(out))


def _keep_image_openers(text, opens):
    kept = []
    for o in opens:
        if o > 0 and text[o - 1] == "!" and not is_escaped_at(text, o - 1):
            kept.append(o)
    return kept


def _is_ref_title_line(content, pending="start"):
    _, consumed = _title_line_consumed(content, pending)
    return consumed


def _ref_def_after_colon(content):
    s = content or ""
    i = 0
    while i < 3 and i < len(s) and s[i] == " ":
        i += 1
    if i >= len(s) or s[i] != "[":
        return ""
    i += 1
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            i += 2
            continue
        if s[i] == "]":
            break
        i += 1
    else:
        return ""
    i += 1
    if i >= len(s) or s[i] != ":":
        return ""
    return s[i + 1 :].lstrip()


def _line_title_pending_after_dest(content):
    dest, after = _take_ref_dest((content or "").strip())
    return dest is not None and _title_pending_state(after)


def _ref_def_title_pending(content):
    rest = _ref_def_after_colon(content)
    if not rest:
        return False
    dest, after = _take_ref_dest(rest)
    return dest is not None and _title_pending_state(after)


def _unreachable_closes(text):
    """For each offset, True when a bare-paren destination scan from there
    can never reach its closing paren.

    Each unclosed ``](`` candidate rescans the suffix once, which is
    quadratic on pathological input (``[](x`` soup pins a CI runner for
    minutes on a one-megabyte file). A right-to-left suffix minimum of the
    paren balance answers "can this scan ever close" in linear total
    time. The answer is exact only for suffixes without quote or backslash
    characters (a quoted or escaped ``)`` is invisible to the balance but
    visible to the real scan), so those positions keep the slow path.
    """
    n = len(text)
    out = bytearray(n + 1)
    out[n] = 1
    minbal = 0
    plain = True
    for k in range(n - 1, -1, -1):
        ch = text[k]
        if ch in "\"'\\":
            plain = False
        if ch == "(":
            minbal = min(minbal + 1, 0)
        elif ch == ")":
            minbal -= 1
        out[k] = 1 if (plain and minbal >= 0) else 0
    return out


def extract_link_dests(text):
    """Yield inline-link destinations, including <> and balanced parentheses."""
    i = 0
    n = len(text)
    opens = []
    unreachable = None
    while i < n:
        if text[i] == "\\" and i + 1 < n:
            i += 2
            continue
        if text[i] == "[":
            opens.append(i)
            i += 1
            continue
        if text[i] == "]" and i + 1 < n and text[i + 1] == "(" and opens:
            opener = opens.pop()
            k = i + 2
            while k < n and text[k].isspace():
                k += 1
        elif text[i] == "]":
            if opens:
                opens.pop()
            i += 1
            continue
        else:
            i += 1
            continue
        # dest starts at k after a matched ]( and optional whitespace
        if k < n and text[k] == "<":
            end = _dest_end(text, k)
            if end is None:
                i = k
                continue
            p = k + 1
            while p < end:
                if text[p] == "\\" and p + 1 < n:
                    p += 2
                    continue
                if text[p] == ">":
                    yield unescape_md_dest(text[k + 1 : p])
                    if not (
                        opener > 0
                        and text[opener - 1] == "!"
                        and not is_escaped_at(text, opener - 1)
                    ):
                        opens[:] = _keep_image_openers(text, opens)
                    break
                p += 1
            i = end
            continue
        if unreachable is None:
            unreachable = _unreachable_closes(text)
        if unreachable[k]:
            i = k
            continue
        depth = 1
        p = k
        dest_end = None
        quote = ""
        while p < n and depth:
            ch = text[p]
            if ch == "\\" and p + 1 < n:
                p += 2
                continue
            if quote:
                if ch == quote:
                    quote = ""
                p += 1
                continue
            if dest_end is not None and ch in "\"'(":
                quote = ")" if ch == "(" else ch
                p += 1
                continue
            if dest_end is not None and not ch.isspace() and ch != ")":
                depth = -1
                break
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
            elif ch.isspace() and dest_end is None:
                dest_end = p
            p += 1
        if depth != 0:
            i = k
            continue
        yield unescape_md_dest(text[k : dest_end if dest_end is not None else p])
        if not (
            opener > 0
            and text[opener - 1] == "!"
            and not is_escaped_at(text, opener - 1)
        ):
            opens[:] = _keep_image_openers(text, opens)
        i = p + 1


def _collect_ref_map(text):
    refs = {}
    fence = None
    fence_ctx = None
    pending = 0
    in_comment = False
    after_para = False
    html_tag = None
    span_run = 0
    pending_ref = None
    pending_title = False
    pending_label = None
    for line in text.splitlines():
        prev_pending = pending
        pending, content = container_content(
            line, pending, allow_list_interrupt=not after_para
        )
        opened = fence is None
        if fence is not None and fence_ctx is not None:
            if _content_margin(line)[1] > fence_ctx[3]:
                fence_ctx[4] = True
        fence, delim = update_fence(
            fence,
            content,
            allow_close=(
                True if fence is None else _fence_closer_ok(line, fence, fence_ctx)
            ),
        )
        if opened and fence is not None:
            fence_ctx = _fence_context(line, prev_pending)
        elif fence is None:
            fence_ctx = None
        if delim or fence is not None:
            if not content.strip():
                after_para = False
            span_run = 0
            pending_ref = None
            pending_title = False
            pending_label = None
            continue
        html_tag, skip_html = html_block_state(
            html_tag, content, allow_type7=not after_para
        )
        if skip_html:
            after_para = False
            pending_ref = None
            pending_title = False
            pending_label = None
            if not content.strip():
                span_run = 0
            continue
        if span_run and not _is_paragraph_text(content):
            span_run = 0
        if not content.strip():
            span_run = 0
            after_para = False
            pending_ref = None
            pending_title = False
            pending_label = None
            continue
        content, span_run = mask_code_spans_state(content, span_run)
        in_comment, content = feed_html_comment(in_comment, content)
        skip_indent = is_indented_code_line(content) and not after_para
        if skip_indent:
            pending_ref = None
            pending_title = False
            pending_label = None
            continue
        if pending_title:
            pending_title, consumed = _title_line_consumed(content, pending_title)
            if consumed:
                after_para = False
                continue
        if pending_ref:
            dest = _ref_dest(content)
            if dest is not None:
                if pending_ref not in refs:
                    refs[pending_ref] = dest
                pending_title = _line_title_pending_after_dest(content)
                pending_ref = None
                after_para = False
                continue
            pending_ref = None
        if pending_label is not None:
            finished = _finish_ref_label(pending_label, content)
            if finished is None:
                pending_label = None
            elif finished[0] == "open":
                pending_label = finished[1]
                after_para = False
                continue
            else:
                label, dest = finished[1], finished[2]
                if label and dest is not None and label not in refs:
                    refs[label] = dest
                elif label and dest is None and label not in refs:
                    pending_ref = label
                pending_label = None
                after_para = False
                continue
        if not after_para:
            opened = _open_ref_label(content)
            if opened:
                pending_label = opened
                after_para = False
                continue
            parsed = _parse_ref_def(content)
            if parsed:
                label, dest = parsed
                if label and dest is not None and label not in refs:
                    refs[label] = dest
                    pending_title = _ref_def_title_pending(content)
                elif label and dest is None and label not in refs:
                    pending_ref = label
        after_para = _is_paragraph_text(content, allow_ref_def=not after_para)
    return refs


def link_targets(text):
    """Yield relative link targets, skipping fenced and indented code."""
    refs = _collect_ref_map(text)
    lines = text.splitlines()
    fence = None
    fence_ctx = None
    pending = 0
    in_comment = False
    after_para = False
    html_tag = None
    para_parts = []
    pending_ref_emit = False
    pending_title = False

    def emit_from(masked):
        masked = strip_inline_html(masked)
        for target in extract_link_dests(masked):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("/"):
                continue
            yield target
        for label in _iter_ref_uses(masked):
            dest = refs.get(label)
            if _usable_ref_dest(dest):
                yield dest

    def flush_para():
        if not para_parts:
            return
        masked = mask_code_spans("\n".join(para_parts))
        para_parts.clear()
        yield from emit_from(masked)

    pending_label = None
    for line in lines:
        prev_pending = pending
        pending, content = container_content(
            line, pending, allow_list_interrupt=not after_para
        )
        opened = fence is None
        if fence is not None and fence_ctx is not None:
            if _content_margin(line)[1] > fence_ctx[3]:
                fence_ctx[4] = True
        fence, delim = update_fence(
            fence,
            content,
            allow_close=(
                True if fence is None else _fence_closer_ok(line, fence, fence_ctx)
            ),
        )
        if opened and fence is not None:
            fence_ctx = _fence_context(line, prev_pending)
        elif fence is None:
            fence_ctx = None
        if delim or fence is not None:
            yield from flush_para()
            pending_ref_emit = False
            pending_title = False
            pending_label = None
            if not content.strip():
                after_para = False
            continue
        html_tag, skip_html = html_block_state(
            html_tag, content, allow_type7=not after_para
        )
        if skip_html:
            yield from flush_para()
            pending_ref_emit = False
            pending_title = False
            pending_label = None
            after_para = False
            continue
        in_comment, content = feed_html_comment(in_comment, content)
        skip_indent = is_indented_code_line(content) and not after_para
        if skip_indent:
            yield from flush_para()
            pending_ref_emit = False
            pending_title = False
            pending_label = None
            if not content.strip():
                after_para = False
            continue
        if not content.strip():
            yield from flush_para()
            pending_ref_emit = False
            pending_title = False
            pending_label = None
            after_para = False
            continue
        if pending_title:
            pending_title, consumed = _title_line_consumed(content, pending_title)
            if consumed:
                after_para = False
                continue
        if pending_ref_emit:
            dest = _ref_dest(content)
            if dest is not None:
                pending_title = _line_title_pending_after_dest(content)
                pending_ref_emit = False
                after_para = False
                continue
            pending_ref_emit = False
        if pending_label is not None:
            finished = _finish_ref_label(pending_label, content)
            if finished is None:
                pending_label = None
            elif finished[0] == "open":
                pending_label = finished[1]
                after_para = False
                continue
            else:
                _label, dest = finished[1], finished[2]
                if dest is not None:
                    pending_title = False
                elif _label:
                    pending_ref_emit = True
                pending_label = None
                after_para = False
                continue
        if not after_para:
            opened = _open_ref_label(content)
            if opened:
                yield from flush_para()
                pending_label = opened
                after_para = False
                continue
        if after_para and _parse_ref_def(content) is not None:
            para_parts.append(content)
            after_para = True
            continue
        if not _is_paragraph_text(content):
            yield from flush_para()
            parsed = _parse_ref_def(content)
            if parsed is None:
                yield from emit_from(mask_code_spans(content))
            else:
                label, dest = parsed
                if dest is not None:
                    pending_title = _ref_def_title_pending(content)
                elif label:
                    pending_ref_emit = True
            after_para = False
            continue
        para_parts.append(content)
        after_para = True
    yield from flush_para()


def main():
    check_all = "--all" in sys.argv[1:]
    md_files = tracked_md()
    tracked_markdown, folded_tracked_markdown = tracked_lookup(md_files)
    surface_files_early = drop_internal_symlinks(surface(check_all, md_files), md_files)
    # Default mode puts AGENTS.md / CLAUDE.md on the surface even when they
    # are still untracked. Index those too so same-doc #fragments are checked.
    seen = {os.path.realpath(f) for f in md_files}
    anchor_files = list(md_files)
    for f in surface_files_early:
        real = os.path.realpath(f)
        if real in seen:
            continue
        if os.path.isfile(f) and not os.path.islink(f):
            anchor_files.append(f)
            seen.add(real)
    anchors, read_bad = anchor_map(anchor_files)
    # anchor_map drops files it can't read from the anchor index but records why
    # in read_bad. Key those reasons by realpath so the link loop below can blame
    # the real cause (e.g. "cannot read file") instead of a bogus "missing anchor"
    # when a link points at a tracked-but-unreadable Markdown file.
    read_failures = {os.path.realpath(f): why for f, _, why in read_bad}
    surface_files = surface_files_early
    # anchor_map records read failures for every tracked file because the anchor
    # index has to cover any link target. A read failure only fails the run if
    # that file is on the surface, which is every tracked file under --all but
    # just AGENTS.md/CLAUDE.md/.agents in default mode. Otherwise a symlink or
    # unreadable Markdown under docs/ that nothing links to would break the
    # default hook.
    surface_set = set(surface_files)
    bad = [entry for entry in read_bad if entry[0] in surface_set]
    already_bad = {f for f, _, _ in bad}
    origins = []
    for f in surface_files:
        text, why = read_markdown(f)
        if text is None:
            if f not in already_bad:
                bad.append((f, os.path.relpath(f, ROOT), why))
            continue
        origins.append((f, text))
    # In --all mode, a tracked symlink whose target is also on the surface
    # was deduplicated off the surface (the target is scanned on its own),
    # but the alias is still a link origin: the same content read from the
    # alias's directory resolves relative links differently. Scan each such
    # alias with the alias path as the relative-link base. An unreadable
    # target was already reported above through its surface entry.
    if check_all:
        surface_real = {
            os.path.realpath(f) for f in surface_files if not os.path.islink(f)
        }
        for f in md_files:
            if not os.path.islink(f):
                continue
            real = os.path.realpath(f)
            if real not in surface_real:
                continue
            text, _why = read_markdown(real)
            if text is not None:
                origins.append((f, text))
    for f, text in origins:
        base = os.path.dirname(f)
        for target in link_targets(text):
            parts = urlsplit(target)
            path = unquote(parts.path)
            anc = unquote(parts.fragment)
            if not path:
                anchor_key = os.path.realpath(f)
                if anc:
                    if anchor_key not in anchors:
                        bad.append(
                            (
                                f,
                                target,
                                read_failures.get(anchor_key, "missing anchor"),
                            )
                        )
                    elif anc not in anchors[anchor_key]:
                        bad.append((f, target, "missing anchor"))
                continue
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
                tracked = None
                # Template sources: map to the scaffolded consumer path
                # before the lexical core lookup. A core file at the same
                # relative path (AGENTS.md) is not what consumers get.
                if is_template_source(f):
                    rendered = rendered_template_target(f, path)
                    if rendered is not None:
                        tracked = tracked_markdown_lookup(
                            rendered,
                            tracked_markdown,
                            folded_tracked_markdown,
                        )
                    if tracked is None:
                        # Renamed consumer paths (AGENTS.md →
                        # templates/AGENTS.md.tmpl) must not fall through
                        # to the core file when the scaffold source is
                        # missing or untracked.
                        deployed_src = template_to_deployed(f)
                        if deployed_src is not None:
                            deployed = os.path.normpath(
                                os.path.join(os.path.dirname(deployed_src), path)
                            )
                            if not within_root(os.path.abspath(deployed)):
                                bad.append((f, target, "target escapes repo"))
                                continue
                            rel = _posix_rel(deployed)
                            if _TEMPLATE_FOR_DEPLOYED.get(rel):
                                bad.append((f, target, "missing file"))
                                continue
                            # Consumer-owned root/docs paths have no
                            # scaffold mapping. Resolve the deployed
                            # file (README.md), not templates/README.md.
                            if not rel.startswith(".agents/"):
                                tracked = tracked_markdown_lookup(
                                    deployed,
                                    tracked_markdown,
                                    folded_tracked_markdown,
                                )
                if tracked is None:
                    tracked = tracked_markdown_lookup(
                        linked,
                        tracked_markdown,
                        folded_tracked_markdown,
                    )
                if tracked is None and is_template_source(f):
                    sibling = template_sibling_target(linked)
                    if sibling is not None:
                        tracked = tracked_markdown_lookup(
                            sibling,
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
        print("CHECK_LINKS_DONE")
        return 1
    print("All context links and anchors resolve.")
    print("CHECK_LINKS_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
