# Questions — Home Assistant Homelab

## Clarification Protocol

### When to Ask

Ask questions when:

- The task could go multiple ways and the user hasn't specified a preference
- A configuration change could have significant side effects
- The requested entity/area doesn't exist and you need to know how to create it
- The user's request conflicts with existing constraints or patterns
- You need access to information you don't have (API keys, device models, etc.)

### When NOT to Ask

Don't ask when:

- The answer is obvious from context (e.g., they say "add a light to kitchen" — use `packages/areas/kitchen.yaml`)
- There's a clear convention already established
- You can infer the answer from existing patterns
- The risk is low and reversible

### Question Format

Keep questions short and specific. Offer options when possible:

**Good:**

```
Your office doesn't have a ceiling light entity yet. Should I create:
1. `light_office_ceiling` — standard on/off
2. `light_office_ceiling` — dimmable
3. `light_office_ceiling` — color temperature
```

**Bad:**

```
What kind of light would you like me to create for the office and what should I name it and do you want it to be dimmable or have color capabilities?
```

### Escalation

If the user says "you decide" or gives no preference:

1. Pick the most conservative option
2. Note that you chose the default
3. Offer to adjust

### Context-Seeking Priority

Ask about these first when missing:

1. **Target file** — Which package file should changes go in? (areas/, functions/, integrations/, routines/)
2. **Scope** — Single entity or multiple?
3. **Impact** — Is this critical path or dev/experimental?
4. **Preferences** — Any specific behavior beyond the basic request?

Vague shopping-list titles (see [`work-sources.md`](work-sources.md)) need
scoping/`alignment` before implementation — ask rather than invent intent.
