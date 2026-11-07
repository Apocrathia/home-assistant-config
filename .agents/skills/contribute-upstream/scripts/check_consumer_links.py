#!/usr/bin/env python3
"""Consumer-layout markdown link checks for contribute-upstream step 10.

filter-layout: drop check_links.py BROKEN lines that are only layout noise
when the target exists in the deployed consumer tree.
scan-deployed: remap copied sources through the consumer layout and fail
on new missing files or anchors versus $BASE.

Both modes share one heading_anchors implementation so fragment checks
agree (reference definitions clear paragraph state in both).
"""

import html
import os
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.*)")
FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
CONTAINER = re.compile(r"^( {0,3})(?:> ?|(?:[-*+]|\d{1,9}[.)])(?=[ \t]|$))")
LIST_START = re.compile(r"^( {0,3})([-*+]|\d{1,9}[.)])(?=[ \t]|$)")
SETEXT_UNDERLINE = re.compile(r"^ {0,3}(?:=+|-+)\s*$")
HTML_BLOCK_OPEN = re.compile(r"^ {0,3}<(script|style|pre|textarea)(?:\s|>|$)", re.I)
HTML_CLOSE = {
    "script": re.compile(r"</script>", re.I),
    "style": re.compile(r"</style>", re.I),
    "pre": re.compile(r"</pre>", re.I),
    "textarea": re.compile(r"</textarea>", re.I),
}
HTML_TYPE2_OPEN = re.compile(r"^ {0,3}<!--")
HTML_TYPE3_OPEN = re.compile(r"^ {0,3}<\?")
HTML_TYPE4_OPEN = re.compile(r"^ {0,3}<![A-Z]")
HTML_TYPE5_OPEN = re.compile(r"^ {0,3}<!\[CDATA\[")
HTML_TYPE6 = re.compile(
    r"^ {0,3}</?(?:address|article|aside|base|basefont|blockquote|body|"
    r"caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|"
    r"fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|"
    r"head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|"
    r"nav|noframes|ol|optgroup|option|p|param|search|section|summary|"
    r"table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:\s|/?>|$)",
    re.I,
)
HTML_TYPE7 = re.compile(
    r"^ {0,3}(?:</[A-Za-z][A-Za-z0-9-]*\s*>|"
    r"<[A-Za-z][A-Za-z0-9-]*"
    r"(?:\s+[^\s\"`\x27=<>]+(?:=(?:[^\s\"`\x27=<>]+|\"[^\"]*\"|\x27[^\x27]*\x27))?)*"
    r"\s*/?>)\s*$"
)
HTML_BLOCK_END = {
    "type2": "-->",
    "type3": "?>",
    "type4": ">",
    "type5": "]]>",
}


def html_block_state(tag, content, allow_type7=True):
    if tag in HTML_BLOCK_END:
        if HTML_BLOCK_END[tag] in content:
            return None, True
        return tag, True
    if tag in ("type6", "type7"):
        if not content.strip():
            return None, True
        return tag, True
    if tag:
        if HTML_CLOSE[tag].search(content):
            return None, True
        return tag, True
    m = HTML_BLOCK_OPEN.match(content)
    if m:
        name = m.group(1).lower()
        if HTML_CLOSE[name].search(content):
            return None, True
        return name, True
    if HTML_TYPE2_OPEN.match(content):
        if "-->" in content:
            return None, True
        return "type2", True
    if HTML_TYPE3_OPEN.match(content):
        if "?>" in content:
            return None, True
        return "type3", True
    if HTML_TYPE5_OPEN.match(content):
        if "]]>" in content:
            return None, True
        return "type5", True
    if HTML_TYPE4_OPEN.match(content):
        if ">" in content:
            return None, True
        return "type4", True
    if HTML_TYPE6.match(content):
        return "type6", True
    if allow_type7 and is_type7_html(content):
        return "type7", True
    return None, False


def content_line(line, pending, allow_list_interrupt=True):
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
        m = CONTAINER.match(s)
        if not m:
            break
        if ">" in m.group(0):
            saw_quote = True
            indent += m.end()
            s = s[m.end() :]
            continue
        lm = LIST_START.match(s)
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
    if pending_quote and is_lazy_quote_line(raw):
        return (pending_indent, True), raw
    return (0, False), raw


def is_lazy_quote_line(content):
    if not content.strip():
        return False
    if HEADING.match(content) or SETEXT_UNDERLINE.match(content):
        return False
    if CONTAINER.match(content) or FENCE.match(content):
        return False
    if indented_code(content):
        return False
    return True


def inline_html_end(s, i):
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
                if s[k] in '"\x27':
                    q = s[k]
                    k += 1
                    while k < n and s[k] != q:
                        k += 1
                    if k >= n:
                        return None
                    j = k + 1
                else:
                    if s[k].isspace() or s[k] in '"\x27=<>`':
                        return None
                    k += 1
                    while k < n and not s[k].isspace() and s[k] not in '"\x27=<>`':
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


def is_type7_html(content):
    s = content or ""
    i = 0
    while i < 3 and i < len(s) and s[i] == " ":
        i += 1
    if i >= len(s) or s[i] != "<":
        return False
    end = inline_html_end(s, i)
    return end is not None and not s[end:].strip()


def mask_code_spans(s, replace=None):
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


def mask_code_spans_state(s, open_run=0):
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


def feed_comment(in_comment, content):
    held = []

    def _hold(span):
        held.append(span)
        return "@@C%d@@" % (len(held) - 1)

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
                visible = visible.replace("@@C%d@@" % i, val)
            return False, visible
        s = s[end + 3 :]
    for i, val in enumerate(held):
        visible = visible.replace("@@C%d@@" % i, val)
    return False, visible


def indented_code(content):
    if content.startswith("\t"):
        return True
    n = 0
    while n < len(content) and content[n] == " ":
        n += 1
    return n >= 4


def tick_fence(fence, line):
    m = FENCE.match(line.rstrip("\n"))
    if not m:
        return fence, False
    mark, rest = m.group(2), m.group(3)
    ch, n = mark[0], len(mark)
    if fence is None:
        if ch == "`" and "`" in rest:
            return fence, False
        return (ch, n), True
    if ch == fence[0] and n >= fence[1] and rest.strip() == "":
        return None, True
    return fence, False


TEMPLATE_FOR_DEPLOYED = {
    ".agents/README.md": "templates/agents-README.md.tmpl",
    ".agents/rules/README.md": "templates/rules-README.md.tmpl",
    ".agents/memories/README.md": "templates/memories-README.md.tmpl",
    "AGENTS.md": "templates/AGENTS.md.tmpl",
    ".scratch/README.md": "templates/scratch-README.md.tmpl",
}


def under_root(path, root):
    if not root:
        return False
    real_root = os.path.realpath(root)
    real_path = os.path.realpath(path)
    return real_path == real_root or real_path.startswith(real_root + os.sep)


def consumer_src(path):
    if path.startswith("templates/"):
        rest = path[len("templates/") :]
        if rest.endswith(".tmpl"):
            rest = rest[:-5]
        renamed = {
            "AGENTS.md": "AGENTS.md",
            "agents-README.md": ".agents/README.md",
            "rules-README.md": ".agents/rules/README.md",
            "memories-README.md": ".agents/memories/README.md",
            "scratch-README.md": ".scratch/README.md",
        }
        return renamed.get(rest, os.path.join(".agents", rest))
    if path.startswith(".agents/") or os.path.dirname(path) == "":
        return path
    return os.path.join(".agents", path)


def git_type(rev, path):
    r = subprocess.run(
        ["git", "cat-file", "-t", f"{rev}:{path}"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def path_isfile(path, rev=None):
    if rev:
        return git_type(rev, path) == "blob"
    return os.path.isfile(path)


def path_isdir(path, rev=None):
    if rev:
        return git_type(rev, path) == "tree"
    return os.path.isdir(path)


def file_text(path, rev=None):
    # Absolute paths are CONSUMER_ROOT targets (live disk). git show
    # cannot read them at rev and would invent a missing-anchor miss.
    if rev and not os.path.isabs(path):
        r = subprocess.run(
            ["git", "show", f"{rev}:{path}"],
            capture_output=True,
            text=True,
        )
        return r.stdout if r.returncode == 0 else None
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return None


def deployed_source(deployed, rev=None):
    """Resolve a deployed path to the file or directory a consumer gets.

    When *rev* is set, look up core templates/files in that revision so a
    baseline comparison does not read HEAD targets. Consumer-owned paths
    still resolve against CONSUMER_ROOT on the live disk.
    """
    if deployed.startswith(".agents/.agents/"):
        return None
    mapped = TEMPLATE_FOR_DEPLOYED.get(deployed)
    if mapped and path_isfile(mapped, rev):
        return mapped
    for prefix, tmpl_dir in (
        (".agents/context/", "templates/context"),
        (".agents/agents/", "templates/agents"),
        (".agents/references/", "templates/references"),
    ):
        if deployed.startswith(prefix):
            rest = deployed[len(prefix) :]
            for cand in (
                os.path.join(tmpl_dir, rest + ".tmpl"),
                os.path.join(tmpl_dir, rest),
            ):
                if path_isfile(cand, rev) or path_isdir(cand, rev):
                    return cand
    # Do not treat the core .agents/ tree as deployed. Core-only
    # docs (contributing.md, scaffold-guide.md, ...) live there without
    # matching templates and are not copied into consumers.
    # Scaffolded roots (AGENTS.md) already returned a template. Other
    # root/docs paths are consumer-owned; check CONSUMER_ROOT before
    # core files that collide on basename (README.md#usage).
    consumer = os.environ.get("CONSUMER_ROOT", "")
    if consumer and not deployed.startswith(".agents/"):
        owned = os.path.normpath(os.path.join(consumer, deployed))
        if not under_root(owned, consumer):
            return None
        if os.path.isfile(owned) or os.path.isdir(owned):
            return owned
        return None
    if not deployed.startswith(".agents/") and (
        path_isfile(deployed, rev) or path_isdir(deployed, rev)
    ):
        return deployed
    rest = deployed[len(".agents/") :] if deployed.startswith(".agents/") else deployed
    if rest.startswith(".agents/"):
        return None
    for cand in (
        rest,
        os.path.join("templates", rest),
        os.path.join("templates", rest + ".tmpl"),
    ):
        if path_isfile(cand, rev) or path_isdir(cand, rev):
            return cand
    consumer = os.environ.get("CONSUMER_ROOT", "")
    if consumer:
        cand = os.path.normpath(os.path.join(consumer, deployed))
        if under_root(cand, consumer) and (os.path.isfile(cand) or os.path.isdir(cand)):
            return cand
    return None


def deployed_file(path):
    # Prefer the template that renders the consumer file. Do not bind
    # .agents/README.md to the repo-root README.md (same basename, wrong
    # headings), and do not treat the core .agents/ tree as deployed.
    if path.startswith(".agents/.agents/"):
        return None
    mapped = TEMPLATE_FOR_DEPLOYED.get(path)
    if mapped and os.path.isfile(mapped):
        return mapped
    for prefix, tmpl_dir in (
        (".agents/context/", "templates/context"),
        (".agents/agents/", "templates/agents"),
        (".agents/references/", "templates/references"),
    ):
        if path.startswith(prefix):
            rest = path[len(prefix) :]
            for cand in (
                os.path.join(tmpl_dir, rest + ".tmpl"),
                os.path.join(tmpl_dir, rest),
            ):
                if os.path.isfile(cand) or os.path.isdir(cand):
                    return cand
    consumer = os.environ.get("CONSUMER_ROOT", "")
    # Scaffolded roots (AGENTS.md) already bound to a template. Other
    # root/docs paths are consumer-owned; do not prefer the core copy.
    if consumer and not path.startswith(".agents/"):
        owned = os.path.normpath(os.path.join(consumer, path))
        if not under_root(owned, consumer):
            return None
        if os.path.isfile(owned) or os.path.isdir(owned):
            return owned
        return None
    if not path.startswith(".agents/") and (
        os.path.isfile(path) or os.path.isdir(path)
    ):
        return path
    if path.startswith(".agents/"):
        rest = path[len(".agents/") :]
        if rest.startswith(".agents/"):
            return None
        for cand in (
            rest,
            os.path.join("templates", rest),
            os.path.join("templates", rest + ".tmpl"),
        ):
            if os.path.isfile(cand) or os.path.isdir(cand):
                return cand
    if consumer:
        cand = os.path.normpath(os.path.join(consumer, path))
        if under_root(cand, consumer) and (os.path.isfile(cand) or os.path.isdir(cand)):
            return cand
    return None


def deployed_exists(path):
    return deployed_file(path) is not None


def add_anchor(anchors, heading, refs=None):
    s = re.sub(r"\{#([^}]+)\}", "", heading)
    out = []
    i = 0
    n = len(s)
    while i < n:
        j = s.find("[", i)
        if j < 0:
            out.append(s[i:])
            break
        k = j + 1
        depth = 1
        while k < n and depth:
            if s[k] == "\\" and k + 1 < n:
                k += 2
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
        depth = 1
        p = k + 1
        if p < n and s[p] == "<":
            gt = s.find(">", p)
            p = n if gt < 0 else gt + 1
            while p < n and s[p] != ")":
                p += 1
            p = p + 1 if p < n else n
        else:
            while p < n and depth:
                if s[p] == "\\" and p + 1 < n:
                    p += 2
                    continue
                if s[p] == "(":
                    depth += 1
                elif s[p] == ")":
                    depth -= 1
                p += 1
        prefix = s[i:j]
        if prefix.endswith("!"):
            prefix = prefix[:-1]
        out.append(prefix)
        out.append(s[j + 1 : k - 1])
        i = p
    s = "".join(out)
    rebuilt = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] != "[":
            rebuilt.append(s[i])
            i += 1
            continue
        bs = 0
        k = i - 1
        while k >= 0 and s[k] == "\\":
            bs += 1
            k -= 1
        if bs % 2 == 1:
            rebuilt.append(s[i])
            i += 1
            continue
        j = i + 1
        while j < n:
            if s[j] == "\\" and j + 1 < n:
                j += 2
                continue
            if s[j] == "]":
                break
            j += 1
        else:
            rebuilt.append(s[i])
            i += 1
            continue
        label = s[i + 1 : j]
        j += 1
        if j < n and s[j] == "[":
            r = j + 1
            while r < n:
                if s[r] == "\\" and r + 1 < n:
                    r += 2
                    continue
                if s[r] == "]":
                    break
                r += 1
            else:
                rebuilt.append(s[i])
                i += 1
                continue
            if i > 0 and s[i - 1] == "!" and rebuilt:
                rebuilt.pop()
            ref_raw = s[j + 1 : r]
            folded = ref_label(ref_raw or label)
            un = []
            p = 0
            while p < len(label):
                if label[p] == "\\" and p + 1 < len(label):
                    un.append(label[p + 1])
                    p += 2
                    continue
                un.append(label[p])
                p += 1
            rebuilt.append("".join(un))
            if refs is None or not folded or folded not in refs:
                unref = []
                p = 0
                while p < len(ref_raw):
                    if ref_raw[p] == "\\" and p + 1 < len(ref_raw):
                        unref.append(ref_raw[p + 1])
                        p += 2
                        continue
                    unref.append(ref_raw[p])
                    p += 1
                rebuilt.append("".join(unref))
            i = r + 1
            continue
        rebuilt.append(s[i])
        i += 1
    s = "".join(rebuilt)
    held = []

    def _hold(span):
        held.append(span)
        return "@@H%d@@" % (len(held) - 1)

    s = mask_code_spans(s, _hold)

    def _hold_auto(m):
        held.append(m.group(0))
        return "@@H%d@@" % (len(held) - 1)

    s = re.sub(
        r"<(?:[a-zA-Z][a-zA-Z0-9+.-]{1,31}:[^<>\s]+|[^<>\s]+@[^<>\s]+)>",
        _hold_auto,
        s,
    )
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
        if j >= 2 and s[j - 2 : j] == "](":
            bs = 0
            k = j - 3
            while k >= 0 and s[k] == "\\":
                bs += 1
                k -= 1
            if bs % 2 == 0:
                out.append(s[i])
                i += 1
                continue
        end = inline_html_end(s, i)
        if end is None:
            out.append(s[i])
            i += 1
            continue
        i = end
    s = "".join(out)
    s = re.sub(
        r"&(?:#x[0-9a-fA-F]+|#\d+|[A-Za-z][A-Za-z0-9]+);",
        lambda m: html.unescape(m.group(0)),
        s,
    )
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
        s = s.replace("@@H%d@@" % i, inner)
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s", " ", s)
    s = s.replace(" ", "-").strip("-")
    if s:
        cand = s
        i = 1
        while cand in anchors:
            cand = f"{s}-{i}"
            i += 1
        anchors.add(cand)
    explicit = re.search(r"\{#([^}]+)\}", heading)
    if explicit:
        anchors.add(explicit.group(1))


def heading_anchors(path, rev=None):
    text = file_text(path, rev)
    if text is None:
        return set()
    refs = collect_ref_map(text)
    anchors = set()
    fence = None
    para = []
    pending = 0
    in_comment = False
    html_tag = None
    span_run = 0
    after_para = False
    for line in text.splitlines():
        prev = pending
        pending, content = content_line(
            line, pending, allow_list_interrupt=not after_para
        )
        prev_indent = prev[0] if isinstance(prev, tuple) else prev
        new_indent = pending[0] if isinstance(pending, tuple) else pending
        if prev_indent and not new_indent:
            para = []
            after_para = False
        fence, delim = tick_fence(fence, content)
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
        in_comment, content = feed_comment(in_comment, content)
        if indented_code(content) and not after_para:
            para = []
            after_para = False
            continue
        if not after_para and parse_ref_def(content) is not None:
            para = []
            after_para = False
            continue
        h = HEADING.match(content)
        if h:
            add_anchor(anchors, h.group(1), refs)
            para = []
            after_para = False
            continue
        if (
            para
            and SETEXT_UNDERLINE.match(content)
            and any(p.strip() for p in para)
            and not para[0].lstrip().startswith("#")
        ):
            add_anchor(anchors, " ".join(p.strip() for p in para if p.strip()), refs)
            para = []
            after_para = False
            continue
        if not content.strip():
            para = []
            after_para = False
            continue
        para.append(content)
        after_para = True
    return anchors


def usable_ref(dest):
    if not dest:
        return False
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", dest):
        return False
    if dest.startswith("/"):
        return False
    return True


def is_paragraph(content, allow_ref_def=True):
    if not content.strip():
        return False
    if HEADING.match(content):
        return False
    if SETEXT_UNDERLINE.match(content):
        return False
    if allow_ref_def and parse_ref_def(content) is not None:
        return False
    return True


def is_escaped_at(text, idx):
    bs = 0
    k = idx - 1
    while k >= 0 and text[k] == "\\":
        bs += 1
        k -= 1
    return bs % 2 == 1


def unescaped_find(s, ch, start=0):
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


def take_ref_dest(rest):
    rest = rest or ""
    if rest.startswith("<"):
        end = unescaped_find(rest, ">", 1)
        if end < 1:
            return None, rest
        inner = rest[1:end]
        p = 0
        while p < len(inner):
            if inner[p] == "\\" and p + 1 < len(inner):
                p += 2
                continue
            if inner[p] in "<\n":
                return None, rest
            p += 1
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
    depth = 0
    p = 0
    while p < len(dest_raw):
        if dest_raw[p] == "\\" and p + 1 < len(dest_raw):
            p += 2
            continue
        if dest_raw[p] == "(":
            depth += 1
        elif dest_raw[p] == ")":
            depth -= 1
            if depth < 0:
                return None, rest
        p += 1
    if depth != 0:
        return None, rest
    return unescape_md_dest(dest_raw), rest[i:]


def complete_ref_title(rest):
    rest = (rest or "").strip()
    if not rest:
        return True
    if rest[0] not in '"\x27(':
        return False
    closer = ")" if rest[0] == "(" else rest[0]
    end = unescaped_find(rest, closer, 1)
    if end < 0:
        return True
    return rest[end + 1 :].strip() == ""


def title_pending_state(after):
    rest = (after or "").strip()
    if not rest:
        return "start"
    if rest[0] not in '"\x27(':
        return False
    closer = ")" if rest[0] == "(" else rest[0]
    if unescaped_find(rest, closer, 1) < 0:
        return closer
    return False


def title_line_consumed(content, pending):
    rest = (content or "").strip()
    if pending == "start":
        if not rest or rest[0] not in '"\x27(':
            return False, False
        closer = ")" if rest[0] == "(" else rest[0]
        end = unescaped_find(rest, closer, 1)
        if end < 0:
            return closer, True
        if rest[end + 1 :].strip():
            return False, False
        return False, True
    if pending in '"\x27)':
        if not rest:
            return False, False
        end = unescaped_find(rest, pending, 0)
        if end >= 0 and rest[end + 1 :].strip() == "":
            return False, True
        return False, False
    return False, False


def parse_ref_def(content):
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
    if not raw or len(raw) > 999:
        return None
    if unescape_md_dest(raw).lstrip().startswith("^"):
        return None
    label = ref_label(raw)
    i += 1
    if i >= len(s) or s[i] != ":":
        return None
    rest = s[i + 1 :].lstrip()
    if not rest:
        return label, None
    dest, after = take_ref_dest(rest)
    if dest is None:
        return None
    if not complete_ref_title(after):
        return None
    return label, dest


def open_ref_label(content):
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
    if not raw or len(raw) > 999:
        return None
    return raw


def finish_ref_label(pending_raw, content):
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
        if len(s) > 999:
            return None
        return ("open", s)
    raw = s[:i]
    if not raw or len(raw) > 999:
        return None
    i += 1
    if i >= len(s) or s[i] != ":":
        return None
    rest = s[i + 1 :].lstrip()
    if not rest:
        return ("def", ref_label(raw), None)
    dest, after = take_ref_dest(rest)
    if dest is None or not complete_ref_title(after):
        return None
    return ("def", ref_label(raw), dest)


def ref_label(label):
    label = unescape_md_dest(label or "").strip()
    if not label or label.startswith("^"):
        return ""
    return re.sub(r"\s+", " ", label).casefold()


def ref_dest(rest):
    dest, after = take_ref_dest((rest or "").strip())
    if dest is None or not complete_ref_title(after):
        return None
    return dest


def read_link_label(text, start):
    i = start + 1
    n = len(text)
    while i < n:
        if i - (start + 1) > 999:
            return None, start
        if text[i] == "\\" and i + 1 < n:
            i += 2
            continue
        if text[i] == "[":
            return None, start
        if text[i] == "]":
            raw = text[start + 1 : i]
            if len(raw) > 999:
                return None, start
            return raw, i + 1
        i += 1
    return None, start


def iter_ref_uses(text):
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "[" or is_escaped_at(text, i):
            i += 1
            continue
        label, j = read_link_label(text, i)
        if label is None:
            i += 1
            continue
        if j < n and text[j] == "(":
            i = j + 1
            continue
        if j < n and text[j] == "[":
            ref, k = read_link_label(text, j)
            if ref is None:
                i = j + 1
                continue
            folded = ref_label(ref or label)
            if folded:
                yield folded
            i = k
            continue
        folded = ref_label(label)
        if folded:
            yield folded
        i = j


MD_ESCAPABLE = set('!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\x27')


def unescape_md_dest(s):
    out = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt in MD_ESCAPABLE:
                out.append(nxt)
                i += 2
                continue
            out.append("\\")
            i += 1
            continue
        out.append(s[i])
        i += 1
    return re.sub(
        r"&(?:#x[0-9a-fA-F]+|#\d+|[A-Za-z][A-Za-z0-9]+);",
        lambda m: html.unescape(m.group(0)),
        "".join(out),
    )


def is_ref_title_line(content, pending="start"):
    _, consumed = title_line_consumed(content, pending)
    return consumed


def ref_def_after_colon(content):
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


def line_title_pending_after_dest(content):
    dest, after = take_ref_dest((content or "").strip())
    return dest is not None and title_pending_state(after)


def ref_def_title_pending(content):
    rest = ref_def_after_colon(content)
    if not rest:
        return False
    dest, after = take_ref_dest(rest)
    return dest is not None and title_pending_state(after)


def extract_link_dests(text):
    i = 0
    n = len(text)
    opens = []
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
        if k < n and text[k] == "<":
            p = k + 1
            while p < n:
                if text[p] == "\\" and p + 1 < n:
                    p += 2
                    continue
                if text[p] in "<\n":
                    i = k
                    break
                if text[p] == ">":
                    q = p + 1
                    while q < n and text[q].isspace():
                        q += 1
                    if q < n and text[q] in '"\x27(':
                        quote = ")" if text[q] == "(" else text[q]
                        q += 1
                        while q < n:
                            if text[q] == "\\" and q + 1 < n:
                                q += 2
                                continue
                            if text[q] == quote:
                                q += 1
                                break
                            q += 1
                        while q < n and text[q].isspace():
                            q += 1
                    if q < n and text[q] == ")":
                        yield unescape_md_dest(text[k + 1 : p])
                        if not (
                            opener > 0
                            and text[opener - 1] == "!"
                            and not is_escaped_at(text, opener - 1)
                        ):
                            opens[:] = [
                                o
                                for o in opens
                                if o > 0
                                and text[o - 1] == "!"
                                and not is_escaped_at(text, o - 1)
                            ]
                        i = q + 1
                    else:
                        i = k
                    break
                p += 1
            else:
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
            if dest_end is not None and ch in '"\x27(':
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
            opens[:] = [
                o
                for o in opens
                if o > 0 and text[o - 1] == "!" and not is_escaped_at(text, o - 1)
            ]
        i = p + 1


def collect_ref_map(text):
    refs = {}
    fence = None
    pending = 0
    in_comment = False
    after_para = False
    html_tag = None
    span_run = 0
    pending_ref = None
    pending_title = False
    pending_label = None
    for line in text.splitlines():
        pending, content = content_line(
            line, pending, allow_list_interrupt=not after_para
        )
        fence, delim = tick_fence(fence, content)
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
        if span_run and not is_paragraph(content):
            span_run = 0
        if not content.strip():
            span_run = 0
            after_para = False
            pending_ref = None
            pending_title = False
            pending_label = None
            continue
        content, span_run = mask_code_spans_state(content, span_run)
        in_comment, content = feed_comment(in_comment, content)
        skip_indent = indented_code(content) and not after_para
        if skip_indent:
            pending_ref = None
            pending_title = False
            pending_label = None
            continue
        if pending_title:
            pending_title, consumed = title_line_consumed(content, pending_title)
            if consumed:
                after_para = False
                continue
        if pending_ref:
            dest = ref_dest(content)
            if dest is not None:
                if pending_ref not in refs:
                    refs[pending_ref] = dest
                pending_title = line_title_pending_after_dest(content)
                pending_ref = None
                after_para = False
                continue
            pending_ref = None
        if pending_label is not None:
            finished = finish_ref_label(pending_label, content)
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
            opened = open_ref_label(content)
            if opened:
                pending_label = opened
                after_para = False
                continue
            parsed = parse_ref_def(content)
            if parsed:
                label, dest = parsed
                if label and dest is not None and label not in refs:
                    refs[label] = dest
                    pending_title = ref_def_title_pending(content)
                elif label and dest is None and label not in refs:
                    pending_ref = label
        after_para = is_paragraph(content, allow_ref_def=not after_para)
    return refs


def link_targets(text):
    refs = collect_ref_map(text)
    lines = text.splitlines()
    fence = None
    pending = 0
    in_comment = False
    after_para = False
    html_tag = None
    para_parts = []
    pending_ref_emit = False
    pending_title = False

    def emit_from(masked):
        i = 0
        n = len(masked)
        out = []
        while i < n:
            if masked[i] != "<":
                out.append(masked[i])
                i += 1
                continue
            j = i
            while j > 0 and masked[j - 1].isspace():
                j -= 1
            if (
                j >= 2
                and masked[j - 2 : j] == "]("
                and not is_escaped_at(masked, j - 2)
            ):
                out.append(masked[i])
                i += 1
                continue
            end = inline_html_end(masked, i)
            if end is None:
                out.append(masked[i])
                i += 1
                continue
            i = end
        masked = "".join(out)
        for target in extract_link_dests(masked):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("/"):
                continue
            yield target
        for label in iter_ref_uses(masked):
            dest = refs.get(label)
            if usable_ref(dest):
                yield dest

    def flush_para():
        if not para_parts:
            return
        masked = mask_code_spans("\n".join(para_parts))
        para_parts.clear()
        yield from emit_from(masked)

    pending_label = None
    for line in lines:
        pending, content = content_line(
            line, pending, allow_list_interrupt=not after_para
        )
        fence, delim = tick_fence(fence, content)
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
        in_comment, content = feed_comment(in_comment, content)
        skip_indent = indented_code(content) and not after_para
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
            pending_title, consumed = title_line_consumed(content, pending_title)
            if consumed:
                after_para = False
                continue
        if pending_ref_emit:
            dest = ref_dest(content)
            if dest is not None:
                pending_title = line_title_pending_after_dest(content)
                pending_ref_emit = False
                after_para = False
                continue
            pending_ref_emit = False
        if pending_label is not None:
            finished = finish_ref_label(pending_label, content)
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
            opened = open_ref_label(content)
            if opened:
                yield from flush_para()
                pending_label = opened
                after_para = False
                continue
        if after_para and parse_ref_def(content) is not None:
            para_parts.append(content)
            after_para = True
            continue
        if not is_paragraph(content):
            yield from flush_para()
            parsed = parse_ref_def(content)
            if parsed is None:
                yield from emit_from(mask_code_spans(content))
            else:
                label, dest = parsed
                if dest is not None:
                    pending_title = ref_def_title_pending(content)
                elif label:
                    pending_ref_emit = True
            after_para = False
            continue
        para_parts.append(content)
        after_para = True
    yield from flush_para()


def collect_bad(src, text, rev=None):
    found = []
    deployed_src = consumer_src(src)
    for target in link_targets(text):
        parts = urlsplit(target)
        path, fragment = unquote(parts.path), unquote(parts.fragment)
        if not path:
            resolved = deployed_source(deployed_src, rev=rev)
            if resolved is None:
                found.append(
                    f"BROKEN [missing file] {src} (deployed {deployed_src}) -> {target}"
                )
            elif fragment and fragment not in heading_anchors(resolved, rev=rev):
                found.append(
                    f"BROKEN [missing anchor] {src} (deployed {deployed_src}) -> {target}"
                )
            continue
        deployed = os.path.normpath(os.path.join(os.path.dirname(deployed_src), path))
        resolved = deployed_source(deployed, rev=rev)
        if resolved is None:
            found.append(
                f"BROKEN [missing file] {src} (deployed {deployed_src}) -> {target}"
            )
            continue
        if fragment and fragment not in heading_anchors(resolved, rev=rev):
            found.append(
                f"BROKEN [missing anchor] {src} (deployed {deployed_src}) -> {target}"
            )
    return found


def is_copied_source(path):
    # Consumers receive rules/, skills/, and rendered templates.
    # Core-only docs (.agents/context/, root AGENTS.md, README.md)
    # stay in this repo and must not be remapped through consumer_src.
    return path.startswith(("rules/", "skills/", "templates/"))


def scan_sources(extras):
    listed = subprocess.run(
        ["git", "ls-files", "-z", "*.md", "*.md.tmpl"],
        capture_output=True,
    )
    if listed.returncode != 0:
        print("git ls-files failed", file=sys.stderr)
        sys.exit(1)
    listed_names = [
        n.decode("utf-8", "surrogateescape") for n in listed.stdout.split(b"\0") if n
    ]
    names = [n for n in listed_names if is_copied_source(n)]
    seen = set(names)
    for extra in extras:
        if extra == "--" or extra in seen or not is_copied_source(extra):
            continue
        names.append(extra)
        seen.add(extra)
    if not listed_names and not names:
        print("no markdown sources to scan", file=sys.stderr)
        sys.exit(1)
    return names


def filter_layout():
    for raw in sys.stdin:
        line = raw.rstrip("\n")
        if not line.startswith("BROKEN "):
            if line:
                print(line)
            continue
        try:
            head, rest = line.split("] ", 1)
            why = head[len("BROKEN [") :]
            src, target = rest.split(" -> ", 1)
        except (IndexError, ValueError):
            print(line)
            continue
        parts = urlsplit(target)
        target_path, fragment = unquote(parts.path), unquote(parts.fragment)
        if not target_path:
            print(line)
            continue
        deployed = os.path.normpath(
            os.path.join(os.path.dirname(consumer_src(src)), target_path)
        )
        # Layout-only noise: missing-file and escapes-repo when the same
        # target exists in the deployed consumer layout (rules/ ->
        # .agents/rules/, so ../../AGENTS.md is valid there). Keep genuine
        # escapes that land outside the repo, and every other why.
        layout_only = why in ("missing file", "escapes repo", "target escapes repo")
        try:
            deployed_real = os.path.realpath(deployed)
            repo_real = os.path.realpath(".")
            in_repo = os.path.commonpath([repo_real, deployed_real]) == repo_real
        except ValueError:
            in_repo = False
        if not layout_only or not in_repo or not deployed_exists(deployed):
            print(line)
            continue
        src_file = deployed_file(deployed)
        if fragment and (not src_file or fragment not in heading_anchors(src_file)):
            print(line)


def scan_deployed(extras):
    base = os.environ.get("BASE", "")
    if not base:
        print(
            "BASE is unset — cannot compare deployed failures to baseline",
            file=sys.stderr,
        )
        sys.exit(1)
    bad = []
    base_bad = set()
    for src in scan_sources(extras):
        try:
            text = open(src, encoding="utf-8").read()
        except OSError as exc:
            print(f"cannot read {src}: {exc}", file=sys.stderr)
            sys.exit(1)
        bad.extend(collect_bad(src, text))
        shown = subprocess.run(
            ["git", "show", f"{base}:{src}"],
            capture_output=True,
            text=True,
        )
        if shown.returncode == 0:
            base_bad.update(collect_bad(src, shown.stdout, rev=base))
    new_bad = [line for line in bad if line not in base_bad]
    if new_bad:
        print("\n".join(new_bad), file=sys.stderr)
        sys.exit(1)


def main(argv):
    if len(argv) < 2 or argv[1] not in ("filter-layout", "scan-deployed"):
        print(
            "usage: check_consumer_links.py filter-layout | scan-deployed [path ...]",
            file=sys.stderr,
        )
        sys.exit(2)
    if argv[1] == "filter-layout":
        filter_layout()
        return
    scan_deployed(argv[2:])


if __name__ == "__main__":
    main(sys.argv)
