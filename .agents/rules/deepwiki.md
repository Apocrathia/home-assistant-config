---
description: DeepWiki MCP probe bank for adversarial repo introspection and dependency vetting
alwaysApply: false
---

# DeepWiki probes

DeepWiki (`user-deepwiki` MCP) serves AI-generated documentation and Q&A for
public GitHub repositories. Here it is a **recon tool**, not a deploy gate: use
it to see what an outsider learns from this config and to vet the upstreams of
any dependency the config trusts. Primary consumer is
[`security-analyst`](../agents/security-analyst/agent.md); any skill probing an
external repo may cite this file instead of freelancing its own questions.

## Tools

- `read_wiki_structure` — topic list for a repo
- `read_wiki_contents` — full generated docs for a repo
- `ask_question` — targeted questions (accepts several repos at once)

All take `repoName` in `owner/repo` form (e.g. `Apocrathia/home-assistant-config`,
`esphome/esphome`, `home-assistant/core`).

## Scope and limits

- DeepWiki only sees what is **pushed and indexed** on GitHub. `secrets.yaml`
  values, `packages/private/`, `.storage/`, and gitignored files are invisible.
  Good for leak checks (if DeepWiki can read it, so can a stranger); useless as
  a complete inventory. Cross-check against the working tree.
- If a repo is not indexed, `ask_question` may hallucinate or refuse. Confirm the
  repo resolves before trusting answers.
- Read-only. Never treat a DeepWiki answer as ground truth for a live entity —
  confirm state via the Home Assistant MCP (`GetLiveContext`).

## Probe bank — this repo (leak / exposure lens)

Run against `Apocrathia/home-assistant-config`. The question is always "what does
a stranger reading this repo learn about the house and how to abuse it?"

- "What does this repository reveal about when the home is occupied or empty
  (presence, away mode, vacation mode, occupancy simulation)?"
- "What physical access controls (locks, garage, doors, alarm, cameras) are
  automated here, and what would disarm or bypass them?"
- "Are any secrets, tokens, API keys, internal hostnames, IPs, or external URLs
  exposed in tracked files rather than referenced via `!secret`?"
- "What external services and integrations does this config connect to, and what
  network surface do they imply?"
- "What daily routines or schedules are documented that would tell an observer
  the occupants' patterns?"

## Probe bank — dependencies (supply-chain lens)

Run against each `custom_components/*`, HACS integration, or ESPHome library the
config trusts (`ask_question` on the dependency's own `owner/repo`).

**Privacy / telemetry**

- "Does this project phone home, send telemetry, or transmit usage data?"
- "Does it contact external services on startup or in the background, and to
  where?"
- "Are analytics, tracking, or data collection enabled by default?"

**Security**

- "Does it store credentials in plaintext or use weak encryption?"
- "Are there known CVEs, security advisories, or unsafe default configurations?"
- "Does it require privileged access, run as root, or request broad HA
  permissions / long-lived tokens?"
- "Are there hardcoded secrets, default passwords, or insecure defaults?"

**General fuckery**

- "Does it have an opaque or auto-updating code path (pulls remote code, eval,
  dynamic imports) after install?"
- "Are there features that silently modify data, overwrite config, or carry
  destructive defaults?"
- "Does it introduce vendor lock-in, forced account creation, or license traps?"

Probe **before** trusting a new dependency. Anything that smells off gets flagged
to the operator with the DeepWiki source cited, not silently accepted.

## Citing

When a finding rests on DeepWiki, cite it: "Per DeepWiki for `owner/repo`, …".
Separate what DeepWiki claims from what you confirmed against the working tree or
live HA.
