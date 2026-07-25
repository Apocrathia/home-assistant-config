# Agent rules — Home Assistant Homelab

Always-on and scoped rules under `.agents/rules/`. Cursor loads via the thin
shim [`.cursor/rules/homeassistant.mdc`](../../.cursor/rules/homeassistant.mdc);
canonical detail stays here.

| Rule                                                                     | Purpose                                                                         |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| [`operator-owned-git.md`](./operator-owned-git.md)                       | Never commit/push/PR; hand off Conventional Commit messages                     |
| [`worktrees.md`](./worktrees.md)                                         | **No worktrees** — edit main checkout; override upstream `.worktrees/` ceremony |
| [`protected-paths.md`](./protected-paths.md)                             | Confirm before editing `.agents/`, HA critical paths, `.shopping_list.json`     |
| [`general.md`](./general.md)                                             | Voice and chat habits (peer, terse; see `context/voice.md`)                     |
| [`response-shape.md`](./response-shape.md)                               | Answer first; scannable replies; no process narration                           |
| [`question-format.md`](./question-format.md)                             | Context → Ask → Suggestion → Gaps                                               |
| [`clarify-dont-guess.md`](./clarify-dont-guess.md)                       | Ask on ambiguity; advice ≠ implement                                            |
| [`ground-before-asking.md`](./ground-before-asking.md)                   | Prove from disk/docs before asking                                              |
| [`ambiguity-goes-back-to-source.md`](./ambiguity-goes-back-to-source.md) | `[NEEDS CLARIFICATION]` when irreducible                                        |
| [`stop-loss.md`](./stop-loss.md)                                         | 3 failed attempts → stop and surface                                            |
| [`surgical-edits.md`](./surgical-edits.md)                               | Minimum change; touch only what the request requires                            |
| [`subagents.md`](./subagents.md)                                         | Parallel fan-out; HA project agents; no worktree gate                           |
| [`humanizer.md`](./humanizer.md)                                         | Markdown prose: strip AI writing patterns                                       |
| [`deepwiki.md`](./deepwiki.md)                                           | DeepWiki probe bank (not always-on) for repo introspection + dep vetting        |

Hard limits that these rules reinforce:
[`.agents/context/constraints.md`](../context/constraints.md).
