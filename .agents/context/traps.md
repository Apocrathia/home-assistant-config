# Traps — Home Assistant Homelab

## Known Pitfalls and Gotchas

### Configuration Traps

1. **`.storage/` files are runtime state** — Never edit these directly. They are managed by Home Assistant's UI and integrations. Editing them can corrupt your integration registry, device registry, or entity registry.

2. **YAML indentation kills** — Home Assistant uses YAML. 2-space indentation is the standard. Mixed tabs/spaces will cause silent failures or startup errors. Always validate with `POST /api/config/core/check_config` (or Developer Tools → YAML) before reload/restart.

3. **`secrets.yaml` not loaded by default** — Make sure `configuration.yaml` includes `!include secrets.yaml` or uses `!secret` references. Hardcoded credentials will be committed to git.

4. **Package includes are alphabetical** — `!include_dir_list` and `!include_dir_merge_list` process files in alphabetical order. This matters for automations that depend on entities defined in other packages.

5. **Entity ID collisions** — Two entities with the same ID across different packages will conflict. Use area prefixes (`light_kitchen_...`, `light_living_room_...`) to avoid this.

6. **Duplicate package filenames collide** — `!include_dir_named` keys each package by its bare filename, recursively and ignoring the subfolder. Two files with the same name in different folders (e.g., `integrations/appletv.yaml` and `areas/master_bedroom/appletv.yaml`) resolve to the same package key, and one silently clobbers the other. Package filenames must be unique across the entire `packages/` tree — disambiguate with a prefix (e.g., `master_bedroom_appletv.yaml`).

### Automation Traps

7. **Use current automation YAML keys** — Prefer `triggers:`, `conditions:`, `actions:`. Trigger list items use `trigger:` (not `platform:`). Action list items use `action:` (not `service:`). Nested condition type keys stay singular (`condition: state`). Blind find-replace of `platform:` will smash light/sensor groups — only rewrite trigger platforms.

8. **Trigger ordering matters** — Automations evaluate triggers in order. A `state` trigger might fire before a `time_pattern` trigger depending on when Home Assistant started. Use `initial_state: false` for time-based automations during development.

9. **`homeassistant.start` fires once** — Don't rely on `homeassistant.start` for daily recurring behavior. Use `time_pattern` or `schedule` integrations for recurring tasks.

10. **Template triggers evaluate on any state change** — A template trigger with `{{ states.sensor.temperature.state | int > 75 }}` will fire on ANY entity change, not just temperature changes. Scope it with `entity_id` triggers when possible.

11. **Delay in actions vs conditions** — `delay:` only works in actions, not conditions. You can't use `delay` to wait for a condition to become true in a single condition block.

12. **Variables scope** — `variables:` in an automation are scoped to that automation's actions. They can't be shared across automations. Use `input_boolean`, `input_number`, or `rest_command` for cross-automation state.

### Integration Traps

13. **API rate limits** — Many integrations (Ecobee, Spotify, etc.) have rate limits. Don't poll more frequently than the integration's recommended interval. Use push/webhook notifications when available.

14. **Z-Wave network congestion** — The "fuckload more traffic" scripts (light_transition, colorloop) are intentionally heavy on the Z-Wave network. Don't run multiple simultaneously on large networks.

15. **ESPHome OTA conflicts** — Multiple ESPHome devices on the same WiFi network can cause OTA conflicts. Stagger firmware updates and avoid simultaneous OTA flashes.

16. **Zone boundaries** — Zone-based automations (geofencing) can have 100-300m radius variance. Don't use zones for precise boundary detection. Use Bluetooth trackers or presence sensors for indoor precision.

### System Traps

17. **Database bloat** — Every sensor logged to `home-assistant_v2.db` adds size. Be selective with `recorder:` exclude/include filters. Not everything needs to be historical.

18. **Backup before bulk operations** — Scripts like `utilities/bulk_remove_devices.py` can have wide impact. Always backup before running bulk operations.

19. **Custom component updates** — Custom components in `custom_components/` don't auto-update. They require manual updates and may break on Home Assistant upgrades. Test in a dev environment first.

### Agent-Specific Traps

20. **Don't confuse `.agents/` with `packages/`** — `.agents/` contains AI agent context. `packages/` contains Home Assistant configuration. They serve completely different purposes.

21. **`.scratch/` is not config** — Throwaways and WIP live there (see `.scratch/README.md`). Home Assistant does not load it. Do not treat scratch files as source of truth or commit them; promote finished work into tracked paths.

22. **Skills are playbooks, not code** — `.agents/skills/*/SKILL.md` files are procedural instructions for agents. They are not Home Assistant automations or scripts.

23. **The context pattern is lazy-loading** — Context modules should only be loaded when needed. Don't assume all modules are relevant to every task.

24. **`.shopping_list.json` is not writable** — It is Home Assistant runtime state (to-dos), used only as a **read-only** work source. Never mark items complete, add/remove entries, or "tidy" the JSON. Completion happens in HA. See [`work-sources.md`](work-sources.md).

25. **Do not follow upstream `ship-work` commit instructions** — Shared prime-context skills may say to commit, push, or open PRs. Here that is wrong. Git is operator-owned ([`rules/operator-owned-git.md`](../rules/operator-owned-git.md)): validate, suggest a Conventional Commit message, hand off. Same override applies to `clock-out` / `self-improve` shipping steps.
