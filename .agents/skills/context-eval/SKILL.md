---
name: context-eval
description: >-
  Measure whether the .agents/ context changes agent outcomes on a project's
  own tasks: author a small corpus of fixture tasks with hidden deterministic
  graders, validate the graders against reference, naive, and decoy overlays,
  run context-on vs baseline arms, and report paired scores with token cost.
  Use when asked whether the context is worth its tokens, before shipping a
  context revision, or to build an agent task corpus.
disable-model-invocation: true
---

# Context eval

Benchmark methodology adapted from [ECC](https://github.com/affaan-m/ECC) (MIT):
`docker/context-profiles/` (corpus, grader contract) and
`docker/gateguard-effectiveness/` (arms, paired stats).

Link and discovery checks certify that the context surface resolves. They say
nothing about outcomes: whether the context changes what an agent delivers on
this repo's real work. This skill is the outcome check — a small corpus of
the project's own tasks, hidden deterministic graders, and paired arms
answering: **is the context worth its tokens?** Same task, same model, same
repeats, context-on vs context-off: if the score does not move, the context
is not earning its keep; if it moves and doubles the tokens, it is a
different product, not a free win.

## Corpus format

One corpus directory, one subdirectory per task (suggested: `evals/tasks/`):

```
evals/tasks/<id>/
  files/          fixture: a miniature of the real repo (few files, docs, a test)
  query.md        the ask, in the user's plain voice
  grader.py       hidden grader — see the contract below
  meta.json       optional: {"category": "...", "timeout_s": 60}
  reference/      correct solution, overlaid on files/ — must score 1.0
  naive/          plausible-but-wrong overlay — must score < 1.0
  decoy-*/       right shape, wrong content — must score < 1.0
```

- `files/` is small, self-contained, and production-shaped: docs, a
  changelog, a test — everything the agent needs and never a benchmark item.
- `query.md` reads the way a real user writes: no context-engine vocabulary,
  no hints about which rule or skill applies. A query that names the mechanism
  measures prompt-following, not context.
- Overlays are grader tests, never agent inputs. `reference` proves the grader
  can pass; `naive` and `decoy-*` prove it can fail.

## Grader contract

- Runs **after the agent exits**, read-only, from a file the agent never saw.
  The runner copies it into the workspace, runs it, deletes it — a grader
  that lingers teaches the next agent to game it.
- Prints **one sentinel line** to stdout and **always exits 0**:

  ```
  EVAL_SCORE {"score": 0.8, "passed": 4, "total": 5}
  ```

  The score carries the verdict; the exit code carries nothing. A nonzero
  exit or a missing sentinel is a grader that died — a zero, never a silent
  pass. A crashed grader's remaining checks stay unscored but count in the
  total.

- **Partial credit.** Four of five vulnerabilities closed is 0.8 of the task,
  not a binary fail. Report mean score and pass rate (score = 1.0) separately.
- **Probe behavior, not strings.** Import the module and call it with boundary
  values, run the tests, hit the endpoint. A grader that greps a source file
  passes a decoy with the right shape and wrong content. Traps that beat
  plausible work: red herrings, exact boundary values, encoded exploit
  variants so partial fixes score partially.

A complete grader is ~20 lines (fixture: a fee function with a half-cent
rounding trap):

```python
import importlib.util, json, sys
from pathlib import Path

checks = []
def record(name, ok): checks.append((name, bool(ok)))

# Denominator is this list, not how far record() got. A crash leaves the
# rest unscored, and they still count.
probes = [
    ('base-rate-exact', 100_00, 300),
    ('half-cent-rounds-up', 150, 5),  # float path gives 4
    ('tiny-order-rounds-up', 17, 1),  # floor gives 0
    ('zero-order', 0, 0),
]

if Path('src/fee.py').is_file():
    spec = importlib.util.spec_from_file_location('fee', 'src/fee.py')
    fee = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(fee)
        for name, cents, want in probes:
            record(name, fee.fee(cents) == want)
    except Exception:
        pass  # a crash leaves the rest unscored, still in total
ok = sum(1 for _, passed in checks if passed)
score = ok / len(probes) if probes else 0
print(f'EVAL_SCORE {json.dumps({"score": score, "passed": ok, "total": len(probes)})}')
sys.exit(0)
```

## Validate the graders before billing anything

Every grader must be proven able to fail before any agent run. The gate:

```bash
python3 .agents/skills/context-eval/scripts/verify_checks.py evals/tasks
```

It stages each task in a throwaway workspace and requires `reference` to
score exactly 1.0, and the bare fixture, `naive`, and every `decoy-*` to
score below 1.0. Any miss exits 1 — the rationale is this package's own rule
for script gates: "Each check has been verified to fail when its condition
is broken. A check that only ever passes is worse than none" — the
core's own rule for script gates. The gate catches the
two quiet failures of hand-built evals: grader rot (the fixture drifted until
it passes) and grader blindness (string matching that decoys sail through).

## Arms

| Arm                       | Context in the workspace                               | Answers                                  |
| ------------------------- | ------------------------------------------------------ | ---------------------------------------- |
| `on`                      | current `AGENTS.md` + `.agents/`                       | does the context change outcomes         |
| `off`                     | none                                                   | the raw harness floor                    |
| `prev`                    | `AGENTS.md` + `.agents/` at the previous commit        | what the latest change added             |
| `placebo` (optional)      | plausible but irrelevant context                       | is it the content, or any added file     |
| `minus-target` (optional) | current tree minus the piece the change claims to help | is the claimed mechanism the working one |

Materialize `prev` from git objects — `git archive <prev-sha> AGENTS.md
.agents | tar -x -C <workspace>`. Context arrives
the way it does in production: discovered from the workspace, never pasted
into the prompt. Pin the plan before spending money — model, repeats, both
context SHAs, corpus path, date — in a `run.json` beside the corpus;
comparisons are within-run only, and a changed plan makes old rows history,
not a baseline.

## Run and record

Per trial (task × arm × repeat):

1. Fresh temp workspace; copy `files/` in; lay the arm's context on top.
2. Launch the agent harness with `query.md` verbatim, cwd in the workspace,
   same model and flags in every arm. Record usage — input and output
   tokens, calls, wall time — if the CLI emits it; report-only if not.
3. After exit, run the grader from outside the agent's session: copy it in,
   run, parse the sentinel, delete it.
4. Append one row: `{"task", "arm", "repeat", "score", "tokens_in", "tokens_out", "seconds"}`.

## Report honestly

- **Pair by task and repeat.** Compare arms only within one run.
- **Wilson 95% interval** on every rate, with p̂ = k/n and z = 1.96:
  `center = (p̂ + z²/2n)/(1 + z²/n)`, `radius = z·sqrt(p̂(1−p̂)/n + z²/4n²)/(1 + z²/n)`.
- **Small-n honesty.** Three tasks is a probe, not a census. Below ~20 pairs
  the counts are descriptive; say so. Show the discordant pairs so a reader
  sees the texture, not just means.
- **Publish nulls.** "No arm moved on 4 tasks × 3 repeats" is a result. A
  corpus that never produces a null is suspicious.
- **Cost next to outcome.** Every table carries tokens and seconds next to
  score. A pass-rate win that doubles tokens is a pricing decision.

## Grow a corpus from real work

3-5 tasks, each from something that actually happened in this repo:

1. Mine closed PRs, [`retrospective`](../retrospective/SKILL.md) findings,
   and post-mortems: a real bug with a plausible wrong first fix, a real
   feature slice, a real hardening pass.
2. Shrink each into a fixture with one clear correct outcome and a
   deterministic check. Keep the wrong-but-plausible first fix — that is the
   `naive` overlay.
3. Author `reference` from the fix that actually landed.
4. Pass the gate. When every arm scores 1.0 the task saturated and stopped
   measuring — sharpen it, but version the corpus dir instead of editing
   mid-comparison.
5. Rerun when the context changes materially — an
   [`integrate-upstream`](../integrate-upstream/SKILL.md) sync, a new rule —
   and the eval turns "trust the diff" into "measure the diff".

## Anti-patterns

- Billing agent runs before the grader gate passes.
- LLM judges or rubric scoring. Correctness must be decidable.
- Chasing pass rates while ignoring token and latency drift.
- Editing the corpus mid-run, or comparing across runs.
