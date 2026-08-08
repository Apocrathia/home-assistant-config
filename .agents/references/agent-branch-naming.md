# Agent branch naming

Optional guidance when the **operator** asks for a branch name. Agents do not
create branches, worktrees, or commits unless explicitly asked
([`operator-owned-git.md`](../rules/operator-owned-git.md),
[`worktrees.md`](../rules/worktrees.md)).

## Format

```text
<type>/<kebab-slug>
```

- **type:** `feat` | `fix` | `docs` | `chore` | `refactor` | `test` | `ci`
- **slug:** 2–4 words, kebab-case, names the **change**

Examples: `feat/primary-suite-rename`, `docs/issue-ledger`,
`fix/closet-motion-timeout`.

## Derive from issue/plan (suggestions only)

| Work                             | Suggested branch                                               |
| -------------------------------- | -------------------------------------------------------------- |
| Plan for `docs/issues/<slug>.md` | `docs/<short-slug>-plan`                                       |
| New `docs/issues/<slug>.md`      | `docs/<short-slug>-issue`                                      |
| Implement plan checkbox          | `feat` / `fix` / `chore` + change slug from the checkbox title |

## Forbidden patterns (if operator uses automation)

| Pattern              | Why                    |
| -------------------- | ---------------------- |
| `*self-improve-lap*` | Opaque automation stub |
| No `/` in name       | Not house format       |
| `wip/*`              | Status prefix          |

Do **not** validate "must be in `.worktrees/`" — that rule does not apply here.
