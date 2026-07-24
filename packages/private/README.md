# `packages/private/`

Local-only Home Assistant packages. Loaded by `!include_dir_named packages`
like every other package file; **not** committed to git.

## Rules

- Put personal / sensitive routines and entities here (health, habits, private reminders)
- Filename stem is still the package id (e.g. `habits.yaml` → package `habits`)
- Everything under this folder except this README is gitignored
- Prefer this over commenting out stubs in tracked `packages/routines/` files

## Agent use

Agents may create and edit files here when the operator asks for private config.
Do not commit private package contents. Do not copy private entity details into
tracked docs or public packages.
