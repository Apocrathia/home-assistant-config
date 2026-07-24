# Tools — Home Assistant Homelab

Short map of tools agents actually use here. Not a full MCP catalog.

## Home Assistant

| Tool                                      | Use                                                                         |
| ----------------------------------------- | --------------------------------------------------------------------------- |
| Home Assistant MCP (`user-homeassistant`) | Live entity/service context; prefer `GetLiveContext` before guessing states |
| `POST /api/config/core/check_config`      | Config validation (Bearer token) — see `skills/config-validate/`            |
| Developer Tools → YAML                    | Same check from the UI                                                      |

Do not use MCP to mutate critical systems without explicit operator ask.
Discovery (`find-work`) stays read-only even when MCP is available.

## Work discovery

```bash
jq -r '.[] | select(.complete == false) | "\(.name) (\(.id))"' .shopping_list.json
```

Full rules: [`work-sources.md`](work-sources.md). Never write that file.

## Config / packages

| Need                     | Go to                              |
| ------------------------ | ---------------------------------- |
| Validate YAML / packages | `skills/config-validate/SKILL.md`  |
| Restructure packages     | `skills/package-organize/SKILL.md` |
| Debug automations        | `skills/automation-debug/SKILL.md` |

## Agent context maintenance

| Need                               | Go to                                |
| ---------------------------------- | ------------------------------------ |
| Sync `.agents/` from prime-context | `skills/integrate-upstream/SKILL.md` |
| Fix context ↔ repo drift          | `skills/reconcile-context/SKILL.md`  |

## Git

Agents do not commit. See [`rules/operator-owned-git.md`](../rules/operator-owned-git.md).
