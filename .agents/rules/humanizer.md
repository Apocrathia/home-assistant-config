---
globs: '**/*.md'
alwaysApply: false
description: Remove AI writing patterns from markdown
---

# Humanizer (markdown)

Applies when creating or editing markdown. Chat replies use the shorter checklist
in [`general.md`](./general.md).

Before handing off prose, run a humanizer pass using the patterns in
[blader/humanizer](https://github.com/blader/humanizer). Use it early, not as
final polish. Also match [`.agents/context/voice.md`](../context/voice.md).

Do not commit docs yourself ([`operator-owned-git.md`](./operator-owned-git.md)).

## Quick pass

Cut: em/en dashes, rule-of-three padding, "-ing" tails, copula avoidance ("serves as"), promotional adjectives, signposting, inflated significance, inline-header bullets, title-case headings, engagement bait.

## Full pattern catalog

The upstream skill detects 33 patterns across four categories, each with
before/after examples:

- **Content patterns** — significance inflation, notability name-dropping,
  superficial -ing analyses, promotional language, vague attributions,
  formulaic challenges.
- **Language patterns** — AI vocabulary, copula avoidance, negative
  parallelisms, rule of three, synonym cycling, false ranges, passive voice.
- **Style patterns** — em/en dashes, sentence uniformity, announcement
  paragraphs, inline-header bullets, title-case headings.
- **Engagement patterns** — engagement bait, signposting, inflated
  significance.

The upstream skill also runs a two-pass rewrite (draft, audit, final) and
supports **voice calibration**: provide a writing sample and it matches your
sentence rhythm and quirks instead of producing generic "clean" output.

Full pattern list, rationale, and voice calibration:
[github.com/blader/humanizer](https://github.com/blader/humanizer). Based on
Wikipedia's
["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
guide, maintained by WikiProject AI Cleanup.
