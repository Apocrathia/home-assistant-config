---
name: create-agent
description: >-
  Create a new agent persona under .agents/agents/. Use when the user says
  create agent, new agent, add a persona, or when a recurring delegation pattern
  needs its own subagent charter.
disable-model-invocation: true
---

# Create agent

Create a sub-agent persona in `.agents/agents/` so the parent can delegate a
recurring role by name (`/name`) instead of hand-writing cold-start prompts each
time.

Before writing, skim existing personas under `.agents/agents/` and, when the
core checkout is available (ask the operator), the core's
`templates/context/agent-personas.md.tmpl` plus `templates/agents/*.tmpl`;
format, when to create vs reuse, return structure.

## When to create a persona

| Signal                                                                     | Action           |
| -------------------------------------------------------------------------- | ---------------- |
| You delegate the same role 3+ times with similar prompts                   | Create a persona |
| A role needs project-specific context the parent cannot cold-start quickly | Create a persona |
| The `subagents` rule table has no row for a task type                      | Create a persona |

**Do not create a persona when:**

- A one-off delegation (unique task, unlikely to recur). Write a cold-start
  prompt instead.
- An existing persona covers the role with minor wording differences. Extend
  the existing one.
- The task is procedural (multi-step workflow). That is a **skill**, not a
  persona. Use [`create-skill`](../create-skill/SKILL.md) instead.

## Procedure

1. **Personas vs skills.** Decide the surface first:

   |         | Persona                                      | Skill                                         |
   | ------- | -------------------------------------------- | --------------------------------------------- |
   | What    | A role charter: who, what, boundaries        | A procedure: steps to follow, in order        |
   | Runs in | A sub-agent (own context window)             | The parent agent (or a delegated sub-agent)   |
   | Invoked | `/name` by the parent or operator            | `/name` by the operator or model-invoked      |
   | Returns | Evidence and findings to the parent          | A completed workflow (report, issue, handoff) |
   | Lives   | `.agents/agents/<name>/agent.md` (preferred) | `.agents/skills/<name>/SKILL.md`              |

   If the need is "who" (a role with judgment and boundaries), write a persona.
   If the need is "how" (an ordered procedure), write a skill.

2. **Name the persona.** Use a role noun, not a verb phrase: `debugger`, not
   `debug-issues`. One word when possible. Check `.agents/agents/` **and**
   `.agents/skills/`; both surface as `/<name>`.

3. **Preflight the protected paths.** A persona writes steering surfaces:
   `.agents/agents/<name>/agent.md`, the `subagents.md` routing row, and the
   `AGENTS.md` agents table. Name the exact paths and wait for operator
   confirmation unless an approved plan already lists them
   ([`protected-paths.md`](../../rules/protected-paths.md)).

4. **Write the frontmatter:**

   ```yaml
   ---
   name: <persona-name>
   description: >-
     <what it does; include trigger phrases the parent matches on>
   model: inherit # or "fast" for cheap read-only scouts
   readonly: true # if the persona should not edit files
   ---
   ```

   Folded (`>-`) or quoted scalars only: a `: ` inside an unquoted plain
   scalar breaks the frontmatter YAML and the persona.

5. **Write the body.** Structure every persona the same way, sections in
   order:

   ```markdown
   ## Identity

   <1-3 sentences of role assumption: who this agent IS. No "you are an AI
   assistant"; direct role framing.>

   ## Purpose

   <What the persona is for, when to invoke it.>

   ## Context to load

   <Which .agents/context/ modules, skills, or docs to read first. Links only,
   never copy. Optional; omit if truly self-contained.>

   ## Method

   <How the persona works, as direct commands.>

   ## Boundaries

   <What the persona does not do (edit files, run state-changing commands,
   etc.).>

   ## Return to parent

   <Structured return format. Lead with 1-3 sentences answering the question,
   then evidence.>

   ## Continuous Improvement

   <Link the work loop ([`retrospective`](../../skills/retrospective/SKILL.md)
   and `.agents/context/development-loop.md`) and name the persona's own
   improvement targets: when the same friction recurs, propose the
   check/skill/rule update instead of working around it.>
   ```

6. **Keep it under 60 lines.** A persona is a charter, not a manual. If it
   grows past 60 lines, the role is too broad; split into two personas or
   move reference content to a linked doc.

7. **Update the routing table.** Add the persona to the `subagents` rule
   (`.agents/rules/subagents.md`) project agents table — and to the
   `AGENTS.md` agents table, which is the router surface:

   ```markdown
   | `/<persona-name>` | <when to delegate to it> |
   ```

8. **Validate.**

   ```bash
   python3 .agents/skills/reconcile-context/scripts/check_frontmatter.py --all
   python3 .agents/skills/reconcile-context/scripts/check_links.py
   ```

   `check_links.py` walks tracked files only — a brand-new persona is
   invisible until tracked, so eyeball its links and note the file for the
   operator (`git add -N` makes it visible; agents never stage).

## Template

Homelab layout is **directory SoT**: `.agents/agents/<name>/agent.md`. Use
existing Homelab personas as
format references. Upstream seeds (when the core checkout is present, under `templates/agents/`):

```
templates/agents/implementer.md.tmpl
templates/agents/verifier.md.tmpl
templates/agents/reviewer.md.tmpl
templates/agents/context-steward.md.tmpl
```

Update [`.agents/rules/subagents.md`](../../rules/subagents.md) when adding a
persona. Do not commit — hand off per
[`operator-owned-git.md`](../../rules/operator-owned-git.md).

## Return to parent

Lead with the persona name and one-sentence description. Then:

- **File**: path created
- **Routing**: confirm the `subagents` rule was updated
- **Next**: suggest the first delegation to test the persona
