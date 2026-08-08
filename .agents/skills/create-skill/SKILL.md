---
name: create-skill
description: >-
  Create a new skill under .agents/skills/. Use when the user says create skill,
  new skill, add a skill, or when a repeated multi-step procedure should become
  a reusable, invocable workflow instead of being re-explained each session.
disable-model-invocation: true
---

# Create skill

Create a procedural skill in `.agents/skills/<name>/SKILL.md` so the parent can
invoke a repeatable workflow by name (`/name`) instead of re-deriving the steps
each session.

Before writing, skim existing Homelab skills and (when available) upstream
`/Users/ianyoung/Projects/prime-context/templates/context/skill-authoring.md.tmpl`
— conciseness, progressive disclosure, invocation choice, information
hierarchy, imperative voice.

## When to create a skill

| Signal                                                        | Action                         |
| ------------------------------------------------------------- | ------------------------------ |
| A multi-step procedure runs 3+ sessions, same steps each time | Create a skill                 |
| The parent re-derives the same workflow from scratch each lap | Create a skill                 |
| Another skill needs to call this procedure by name            | Create a skill (model-invoked) |

**Do not create a skill when:**

- The procedure is one or two steps. Put it in a rule or context module.
- The task is a single role's charter (what it does, not how to do it). That is
  a **persona**, not a skill. Use [`create-agent`](../create-agent/SKILL.md).
- The workflow is project-specific and unlikely to recur. Keep it in chat or a
  plan file.

## Procedure

1. **Name the skill.** Use a verb phrase or noun describing the workflow:
   `find-work`, `review-loop`, `ship-work`. Check `.agents/skills/` for
   collisions.

2. **Create the directory:**

   ```
   .agents/skills/<name>/SKILL.md
   ```

   Optionally add `references/` for long reference material or `scripts/` for
   executable checks. Do not add `README.md`, `CHANGELOG.md`, or other
   non-agent files.

3. **Write the frontmatter:**

   ```yaml
   ---
   name: <skill-name>
   description: >-
     <what it does; include trigger phrases the agent or operator matches on.
     This is the only trigger surface — do not duplicate it in the body.>
   disable-model-invocation: true
   ---
   ```

   Set `disable-model-invocation: true` when only the operator should invoke
   the skill by name. Omit it when the agent should discover the skill
   autonomously from the description, or when another skill needs to call it.
   Each model-invoked description sits in the context window every turn, so
   prefer user-invocation when only the operator needs to reach the skill.

4. **Write the body.** Structure:

   - **Opening** — one or two sentences: what the skill does and its boundary
     (read-only, creates worktree, etc.).
   - **Steps** — ordered, numbered. Each step ends on a completion criterion the
     agent can check (done vs not-done).
   - **Reference** — non-ordered material (tables, pattern catalogs) the agent
     consults during a step. Keep this in the skill or move to `references/` if
     it is long.
   - **Return** — what the skill hands back to the parent or operator.

5. **Keep SKILL.md lean.** Move long catalogs and examples to `references/`
   and load them only when the step needs them. The skill body is the
   procedure; the references are the library.

6. **Update routing.** If the skill should be discoverable via `AGENTS.md`,
   add a routing table row in `AGENTS.md` pointing at the skill.

7. **Validate.** Run `check_links.py` if the skill contains links:

   ```bash
   python3 .agents/skills/reconcile-context/scripts/check_links.py
   ```

8. **Hand off.** Do not commit or push
   ([`operator-owned-git.md`](../../rules/operator-owned-git.md)).

## Return to parent

Lead with the skill name and one-sentence description. Then:

- **File** — path created
- **Routing** — whether `AGENTS.md` was updated (and the row added)
- **Next** — suggest a first invocation to test the skill; operator commits
