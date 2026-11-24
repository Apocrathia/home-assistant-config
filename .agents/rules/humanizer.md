---
description: Remove signs of AI-generated writing from text.
globs: **/*.md
alwaysApply: true
---

# Humanizer

Rewrite AI-sounding text so it reads like the writer wrote it. Change wording,
not meaning: every fact, link, command, and code block survives. If a writing
sample of the author exists, read it first; the sample overrides every pattern
below, including the dash rule.

Decomposed from
[blader/humanizer](https://github.com/blader/humanizer) v4.0.0 (commit
a48c60c2, fetched 2026-11-19). Re-sync from upstream when it drifts. Tone lives in
[`.agents/context/voice.md`](../context/voice.md); reply shape in
[`response-shape.md`](./response-shape.md).

## How to work

1. Scan for the patterns below.
2. Rewrite the flagged text; do not delete content. Cover everything the
   original covers.
3. Read the result once more and cut what still sounds generated.

Return the rewrite plus a short list of tells that survived the first pass.

## A. Staging instead of stating

1. Not X but Y: "not just X, but Y", "it's not X, it's Y", "X rather than Y",
   or the contrast split across two sentences. State the thing directly.
2. One-line closers and dramatic fragments: "That is the real win.", "Read
   that again.", a sentence that restates the paragraph above it. Delete.
3. Sayings that sound deep: "at its core", "the real question is", "the heart
   of the matter", "X is the Y of Z". Say the plain thing.
4. Staged run-up: "Let's dive in", "here's what you need to know", "Here's the
   thing", any throat-clearing before the point. Start at the point.
5. Arguing with no one: "This isn't about X", "Some might say... but", "To be
   clear", "Don't get me wrong". Drop the strawman; keep the claim.

## B. Rhythm by rule

6. Forced triads: ideas arrive in threes to sound complete. Use the number the
   meaning has.
7. Repeated sentence openings: several sentences starting with the same
   subject. Merge or vary.
8. Dashes as the universal connector: no em or en dashes in the final rewrite
   unless the author's sample uses them. Period, comma, colon, or parentheses
   instead.
9. Stacked qualifiers: "to be fair", "could potentially", "might arguably".
   One qualifier at most; commit to the claim.
10. Hyphenated pairs everywhere: keep the hyphen only before a noun ("a
    well-known tool", but "the tool is well known").
11. Passive voice and missing subjects: name the actor when it clarifies.

## C. Inflation and borrowed authority

12. Overused AI words: actually, additionally, crucial, deep dive, delve,
    enhance, garner, highlight (verb), intricate, key (adjective), robust,
    seamless, leverage, unlock. Use the plain word.
13. Inflated significance: "stands as a testament", "pivotal moment", "plays a
    key role", "underscores its importance", "evolving landscape". State the
    fact.
14. Vague connection: "associated with", "linked to", "tied to" without saying
    how. Say the relation.
15. Shallow -ing phrases: "highlighting", "ensuring", "showcasing",
    "reflecting" bolted onto a fact. Cut the tail.
16. Sales language: rich, profound, groundbreaking, renowned, nestled,
    breathtaking, diverse array. Describe plainly.
17. Borrowed authority: "experts argue", "industry reports", a list of outlets
    without context. Name a specific source or drop the claim.
18. Avoiding is, are, and has: "serves as", "stands as", "boasts", "features".
    Use the simple verb.

## D. Formatting by rule

19. Bold as decoration: bold without a reason, or a vertical list where every
    item carries a bold label and a colon. Remove the bold; keep the content.
20. Decorative headings: title case on every main word, emojis or arrows as
    decoration, horizontal rules between every section. Follow the document's
    existing heading style.
21. Curly quotation marks where the format uses straight quotes. Weak signal
    alone; fix with the rest.

## E. Leftovers from the chat and the draft

22. Chatbot residue: "I hope this helps", "Great question!", "let me know".
    Delete.
23. Knowledge-limit disclaimers: "as of my last update", "based on available
    information". State what is known or mark the gap once.
24. A heading repeated in the first sentence below it. Delete the sentence.
25. Writing about the document instead of its subject: "was added to replace",
    "generated from", legends describing layout. Write about the subject.

## F. Writing for the wrong reader

26. Re-explaining what the reader knows: restating the problem, walking
    through the diagnosis, proving the plan with numbers the reader already
    has. Answer first; trim the run-up.

## When not to act

Leave the text alone when it is quoted material, code, or the author's own
informal voice (chat logs, commit messages, notes). Informal human writing is
not slop; over-editing it is the failure mode, not the fix. A pattern list is
a detector, not a law: if the meaning reads clean and the voice is the
author's, ship it.
