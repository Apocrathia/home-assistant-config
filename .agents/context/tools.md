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

## Historical state (Grafana → InfluxDB)

Past entity state / change timelines / numeric sensor series live in Grafana
datasource uid `homeassistant` (InfluxQL). Do **not** use HA MCP for history.

| Need                         | Go to                                |
| ---------------------------- | ------------------------------------ |
| Query HA history via Grafana | `skills/grafana-ha-history/SKILL.md` |

## Work discovery

Local Todo (Issues / Tasks / Ideas) plus legacy shopping list. Full rules:
[`work-sources.md`](work-sources.md). Never write these files.

```bash
# Local Todo — open items (NEEDS-ACTION)
python3 <<'PY'
from pathlib import Path
import re

for list_name, path in [
    ("issues", ".storage/local_todo.issues.ics"),
    ("tasks", ".storage/local_todo.tasks.ics"),
    ("ideas", ".storage/local_todo.ideas.ics"),
]:
    p = Path(path)
    if not p.is_file():
        print(f"{list_name}: unavailable")
        continue
    text = p.read_text().replace("\r\n", "\n").replace("\r", "\n")
    for block in re.split(r"\nBEGIN:VTODO\n", text)[1:]:
        status = re.search(r"^STATUS:(.+)$", block, re.M)
        summary = re.search(r"^SUMMARY:(.+)$", block, re.M)
        uid = re.search(r"^UID:(.+)$", block, re.M)
        if not summary or not status or status.group(1).strip() != "NEEDS-ACTION":
            continue
        title = summary.group(1).replace("\\,", ",")
        print(f"{list_name}\t{title}\t{uid.group(1).strip() if uid else ''}")
PY

# Legacy shopping list — incomplete
jq -r '.[] | select(.complete == false) | "\(.name) (\(.id))"' .shopping_list.json
```

## Config / packages

| Need                     | Go to                                |
| ------------------------ | ------------------------------------ |
| Validate YAML / packages | `skills/config-validate/SKILL.md`    |
| Restructure packages     | `skills/package-organize/SKILL.md`   |
| Debug automations        | `skills/automation-debug/SKILL.md`   |
| HA history via Grafana   | `skills/grafana-ha-history/SKILL.md` |

## Agent context maintenance

| Need                               | Go to                                |
| ---------------------------------- | ------------------------------------ |
| Sync `.agents/` from prime-context | `skills/integrate-upstream/SKILL.md` |
| Fix context ↔ repo drift          | `skills/reconcile-context/SKILL.md`  |

## Git

Agents do not commit. See [`rules/operator-owned-git.md`](../rules/operator-owned-git.md).
