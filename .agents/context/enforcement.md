# Enforcement

Structural enforcement over behavioral instruction. When a failure mode can be
prevented mechanically — a hook, schema, checker, pre-commit gate — prefer that
over a rule that merely asks. An instruction in a prompt is what an injection
overrides; a mechanical check is what it cannot. When both exist, the check is
the enforcement and the rule is the explanation.

## What enforces mechanically here

| Mechanism                                                                                                                                                                       | Enforces                                                                                     | Point                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| pre-commit ([`.pre-commit-config.yaml`](../../.pre-commit-config.yaml)) — yamllint, prettier, check-json, check-symlinks, detect-private-key, whitespace/EOF fixers, commitizen | YAML/JSON validity, no leaked secrets, symlink health, commit shape                          | Operator-owned at commit; agents run the full sweep `pre-commit run --files <touched>` after any change — not just yamllint |
| HA Check Configuration — `POST /api/config/core/check_config` (Bearer token) or Developer Tools → YAML                                                                          | Whole-config validity: packages, entity refs, secrets                                        | Post-action; procedure in [`skills/config-validate/`](../skills/config-validate/SKILL.md)                                   |
| `check_links.py`                                                                                                                                                                | Every intra-repo markdown link and anchor resolves                                           | Post-action ([`skills/reconcile-context/`](../skills/reconcile-context/SKILL.md))                                           |
| `check_discovery.py`                                                                                                                                                            | Claude symlink parity with `.agents/` source of truth; no orphans; `CLAUDE.md` → `AGENTS.md` | Post-action, same skill                                                                                                     |
| `check_frontmatter.py`                                                                                                                                                          | Rules carry `alwaysApply` + description; SKILL.md carries `name` + `description`             | Post-action, same skill                                                                                                     |

The official HA MCP server exposes entity/service control and live context but
**no config-check tool** — validation is the REST check / Dev Tools YAML above,
reached via the `config-validate` skill. MCP is for live state, not enforcement.

## Hook-event vocabulary

No harness hook runtime is wired in this repo today: `.claude/` has no
`settings.json`, and prime-agent has no hook surface. The
same intents run as event → rule instead:

| Event          | Fires              | Here                                                                                                                                                                                                                                 |
| -------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `SessionStart` | session opens      | `AGENTS.md` + always-on rules load as project context; prime-agent injects the harness digest                                                                                                                                        |
| `PreToolUse`   | before a tool call | [`rules/protected-paths.md`](../rules/protected-paths.md) — confirm before `.agents/`, `.storage/`, `secrets.yaml`, `packages/system/` edits; [`rules/operator-owned-git.md`](../rules/operator-owned-git.md) — never commit/push/PR |
| `PostToolUse`  | after a tool call  | Run the reconcile checkers + `pre-commit run --files` on touched files after any change                                                                                                                                              |
| `PreCompact`   | before compaction  | [`context-management.md`](context-management.md) — Bars and decisions go to disk first                                                                                                                                               |
| `Stop`         | response ends      | Handoff summary + suggested Conventional Commit; open asks restated in bold                                                                                                                                                          |
| `SessionEnd`   | session closes     | Reports under `.scratch/`; nothing automated                                                                                                                                                                                         |

If a harness gains a hook runtime, map its events onto this vocabulary and
record the mapping here.

## Decision contract

For any future hook or checker script:

- **Exit 0** — allow; empty stdout; never echo the input payload back.
- **Exit 2** — block (pre-action events only).
- **Other non-zero** — error; logged, does not block.
- **stderr** — warning shown to model and operator.
- Fail **open** on internal error — a broken check must not wedge every call.
  The one exception: a safety check that could not read its full input fails
  **closed** and says why.
- Never echo truncated input (parses as garbage, blocks what it meant to
  allow); drain stdout before exit.

## Promotion path

Rule (behavioral) → fails 3+ times → mechanical check → failures stop. That is
how this repo got its checkers: frontmatter drift became `check_frontmatter.py`;
broken symlink parity became `check_discovery.py` in every reconcile lap. Keep
the rule when promoted — the check enforces, the rule explains. Not everything
can be structural ("answer first" stays behavioral); file writes, directory
boundaries, and output validation can and should be mechanical.
