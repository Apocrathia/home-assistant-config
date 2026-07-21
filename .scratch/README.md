# `.scratch/`

Local throwaway workspace for WIP scripts, YAML backups, virtualenvs, and other ephemeral files.

## Rules

- Prefer this directory over `/tmp` for anything tied to this config repo
- Contents are **not** loaded by Home Assistant
- Contents are **not** source of truth — promote finished work into `packages/`, `utilities/`, or other tracked paths
- Everything under this folder except this README is gitignored

## Agent use

Agents may create and modify files here freely without asking. Do not commit scratch contents. When work is ready to keep, move it into the appropriate tracked package or utility path and ask before editing those.
