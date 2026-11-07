# Harness support matrix

Which harness loads which capability of this repo's agent tooling — with
evidence. The matrix records the claim, the ledger records the proof, and the
drift rule decides when the proof expired. Support-state records adapted from
[ECC](https://github.com/affaan-m/ECC) (MIT).

## States

| State                | Meaning                                                                         |
| -------------------- | ------------------------------------------------------------------------------- |
| `Native`             | Harness loads/runs it directly; no shim, no wiring                              |
| `Adapted`            | Thin adapter makes it work — symlink, shim, config translation                  |
| `Instruction-backed` | Files exist, but the harness exposes no runtime surface to load or enforce them |
| `None`               | Not supported; no adapter, no instruction path today                            |

## Matrix

A state is written only with evidence behind it (see ledger). `TODO` means
unproven from this repo — do not guess it.

| Capability    | prime-agent                                                                       |
| ------------- | --------------------------------------------------------------------------------- |
| Rules loading | Native — `AGENTS.md` injected as project context                                  |
| Skills        | Native — repo `.agents/skills` surface discovered as skills                       |
| Subagents     | Native — `rlm.spawn` fan-out with per-child sessions                              |
| Hooks         | None (heartbeats / goals / refinement are their own surfaces, not hooks)          |
| MCP           | Native — kernel MCP catalog + `mcp_servers` registry (HA, Grafana, …)             |
| Memories      | Native — continual harness state (memories, prompt notes, skills, subagent specs) |

This repo runs a single harness (prime-agent) — the matrix keeps the drift
discipline for its one column. The official HA MCP server exposes
entity/service control and live context but no config-check call — config
validation is the HA REST check ([`tools.md`](tools.md)), not an MCP tool.

## Verification ledger

| Harness     | Last verified | Verify                                                                                                                                |
| ----------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| prime-agent | 2026-11-07    | Live session: repo skills in the skill list, `AGENTS.md` in the system prompt, harness digest present, `mcp_servers.names()` resolves |

## Drift rule

Cells age silently. Before trusting a cell:

- `Last verified` older than **3 months** → re-verify that column before
  trusting any cell in it.
- Harness version changed since `Last verified` → re-verify runtime cells
  regardless of age.
- Capability changed (new rule, skill, agent, MCP server) → re-verify that row
  in every harness marked `Native` or `Adapted`. Symlink cells re-verify free:
  `check_discovery.py` runs on every reconcile lap.

An expired cell is not a conservative default — it is an unverified claim.
