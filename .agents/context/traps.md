# Traps — Home Assistant Homelab

## Known Pitfalls and Gotchas

### Configuration Traps

1. **`.storage/` files are runtime state** — Never edit these directly. They are managed by Home Assistant's UI and integrations. Editing them can corrupt your integration registry, device registry, or entity registry.

2. **YAML indentation kills** — Home Assistant uses YAML. 2-space indentation is the standard. Mixed tabs/spaces will cause silent failures or startup errors. Always validate with `ha config check`.

3. **`secrets.yaml` not loaded by default** — Make sure `configuration.yaml` includes `!include secrets.yaml` or uses `!secret` references. Hardcoded credentials will be committed to git.

4. **Package includes are alphabetical** — `!include_dir_list` and `!include_dir_merge_list` process files in alphabetical order. This matters for automations that depend on entities defined in other packages.

5. **Entity ID collisions** — Two entities with the same ID across different packages will conflict. Use area prefixes (`light_kitchen_...`, `light_living_room_...`) to avoid this.

### Automation Traps

6. **Trigger ordering matters** — Automations evaluate triggers in order. A `state` trigger might fire before a `time_pattern` trigger depending on when Home Assistant started. Use `initial_state: false` for time-based automations during development.

7. **`homeassistant.start` fires once** — Don't rely on `homeassistant.start` for daily recurring behavior. Use `time_pattern` or `schedule` integrations for recurring tasks.

8. **Template triggers evaluate on any state change** — A template trigger with `{{ states.sensor.temperature.state | int > 75 }}` will fire on ANY entity change, not just temperature changes. Scope it with `entity_id` triggers when possible.

9. **Delay in actions vs conditions** — `delay:` only works in actions, not conditions. You can't use `delay` to wait for a condition to become true in a single condition block.

10. **Variables scope** — `variables:` in an automation are scoped to that automation's actions. They can't be shared across automations. Use `input_boolean`, `input_number`, or `rest_command` for cross-automation state.

### Integration Traps

11. **API rate limits** — Many integrations (Ecobee, Spotify, etc.) have rate limits. Don't poll more frequently than the integration's recommended interval. Use push/webhook notifications when available.

12. **Z-Wave network congestion** — The "fuckload more traffic" scripts (light_transition, colorloop) are intentionally heavy on the Z-Wave network. Don't run multiple simultaneously on large networks.

13. **ESPHome OTA conflicts** — Multiple ESPHome devices on the same WiFi network can cause OTA conflicts. Stagger firmware updates and avoid simultaneous OTA flashes.

14. **Zone boundaries** — Zone-based automations (geofencing) can have 100-300m radius variance. Don't use zones for precise boundary detection. Use Bluetooth trackers or presence sensors for indoor precision.

### System Traps

15. **Database bloat** — Every sensor logged to `home-assistant_v2.db` adds size. Be selective with `recorder:` exclude/include filters. Not everything needs to be historical.

16. **Backup before bulk operations** — Scripts like `utilities/bulk_remove_devices.py` can have wide impact. Always backup before running bulk operations.

17. **Custom component updates** — Custom components in `custom_components/` don't auto-update. They require manual updates and may break on Home Assistant upgrades. Test in a dev environment first.

### Agent-Specific Traps

18. **Don't confuse `.agents/` with `packages/`** — `.agents/` contains AI agent context. `packages/` contains Home Assistant configuration. They serve completely different purposes.

19. **`.scratch/` is not config** — Throwaways and WIP live there (see `.scratch/README.md`). Home Assistant does not load it. Do not treat scratch files as source of truth or commit them; promote finished work into tracked paths.

20. **Skills are playbooks, not code** — `.agents/skills/*/SKILL.md` files are procedural instructions for agents. They are not Home Assistant automations or scripts.

21. **The context pattern is lazy-loading** — Context modules should only be loaded when needed. Don't assume all modules are relevant to every task.
