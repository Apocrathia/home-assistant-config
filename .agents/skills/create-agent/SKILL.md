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

Before writing, skim existing personas under `.agents/agents/` and (when
available) the upstream seed
`/Users/ianyoung/Projects/prime-context/templates/context/agent-personas.md.tmpl`
plus `templates/agents/*.tmpl` — format, when to create vs reuse, return
structure.

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

1. **Name the persona.** Use a role noun, not a verb phrase: `debugger`, not
   `debug-issues`. One word when possible. Check `.agents/agents/` for name
   collisions.

2. **Write the frontmatter:**

   ```yaml
   ---
   name: <persona-name>
   description: <what it does; include trigger phrases the parent matches on>
   model: inherit # or "fast" for cheap read-only scouts
   readonly: true # if the persona should not edit files
   ---
   ```

3. **Write the body.** Structure every persona the same way:

   - **Opening line** — one sentence: what the persona is and does.
   - **Context to load** — which `.agents/context/` modules, skills, or docs to
     read before working. Link, do not copy.
   - **Method / focus areas** — what the persona does, as direct commands.
   - **Repo notes** (optional) — project-specific gotchas, toolchain details,
     naming conventions.
   - **Boundaries** — what the persona does not do (edit files, run state-
     changing commands, etc.).
   - **Return to parent** — the structured return format. Lead with 1-3 sentences
     answering the question. Then evidence, not narration.

4. **Keep it under 60 lines.** A persona is a charter, not a manual. If it grows
   past 60 lines, the role is too broad — split into two personas or move
   reference content to a linked doc.

5. **Update the routing table.** Add the persona to the `subagents` rule
   (`.agents/rules/subagents.md`) project agents table:

   ```markdown
   | `/<persona-name>` | <when to delegate to it> |
   ```

6. **Validate.** Run `check_links.py` on the new file if it contains links:
   ```bash
   python3 .agents/skills/reconcile-context/scripts/check_links.py
   ```

## Template

Homelab layout is **directory SoT**: `.agents/agents/<name>/agent.md` (Cursor
mirrors under `.cursor/agents/<name>.md`). Use existing Homelab personas as
format references. Upstream seeds (when the prime-context checkout is present):

```
/Users/ianyoung/Projects/prime-context/templates/agents/implementer.md.tmpl
/Users/ianyoung/Projects/prime-context/templates/agents/verifier.md.tmpl
/Users/ianyoung/Projects/prime-context/templates/agents/reviewer.md.tmpl
/Users/ianyoung/Projects/prime-context/templates/agents/context-steward.md.tmpl
```

Update [`.agents/rules/subagents.md`](../../rules/subagents.md) when adding a
persona. Do not commit — hand off per
[`operator-owned-git.md`](../../rules/operator-owned-git.md).

## Return to parent

Lead with the persona name and one-sentence description. Then:

- **File** — path created
- **Routing** — confirm the `subagents` rule was updated
- **Next** — suggest the first delegation to test the persona
