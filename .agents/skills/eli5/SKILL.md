---
name: eli5
description: >-
  Decompose a thing and explain it in plain language. Use when the operator
  says eli5, explain simply, plain language, or word soup; when handed a PR,
  diff, doc, webpage, question, or dense agent output; or when another skill
  invokes this by name for a plain-language pass.
disable-model-invocation: true
---

# Eli5

Decompose a thing and explain it in plain language for a competent non-expert,
claims preserved. Read-only by default: do not edit the source artifact unless
the operator explicitly asks to replace it.

## Boundary

- Not the default house voice. Invoke by `/eli5` or by name from another skill.
- Do not start this because a reply looks confusing.
- Do not file issues, edit the source, or open PRs as part of this skill.

## Steps

1. **Identify** the artifact: PR / diff, file, URL, question, or pasted output.
   If more than one is in play and it matters which, ask. Otherwise pick the
   obvious one and say so. Done when the source is named.
2. **Decompose** into parts or claims. Short list. Done when a reader can see
   the structure without reading the source.
3. **Explain** the whole in plain language. Explain the parts only if the whole
   is not enough. Done when someone who does not live in this codebase could
   repeat the point.
4. **Check** every simplified claim against the source. Drop or rewrite anything
   the analogy inverted. Run a humanizer quick pass so the explanation is not
   itself slop. Done when you would defend each sentence from the original.
5. **Return** the explanation to the operator or parent. Lead with the
   explanation, not a preamble about explaining. Done when the return section
   below is satisfied.

## Callers

Other skills may invoke `/eli5` when handing off dense output. They name it in
their procedure. This skill does not auto-discover work.

## Do not

- Kindergarten voice, forced analogies, or "imagine a castle" framing
- Change `writing-style` or add always-on guidance to `general.md`
- Write `references/` for a catalog of analogies (YAGNI)
- Create `README.md`, `CHANGELOG.md`, or other non-agent files in the skill
  folder

## Return

The explanation. If a claim could not be simplified without lying, say so in
one sentence and keep the precise wording. Do not return a process narrative.

Tone, length, and whether to use an analogy are up to you, as long as steps 3
and 4 hold.
