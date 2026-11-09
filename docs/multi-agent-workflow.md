# Multi-Agent Implementation Workflow

Use this workflow when explicitly requested for a task. It does not authorize
agent delegation or implementation for other tasks automatically.

## Roles

- **Human:** approves the initial plan and any plan escalated after two
  unsuccessful repair rounds.
- **Coordinator:** maintains task state, assigns work, saves approved plans,
  relays handoffs, and reports results. The coordinator may also prepare this
  workflow document, independently of the task's implementation approval.
- **Planner:** investigates the task, proposes the implementation plan, and
  plans repairs in response to audit findings.
- **Implementer:** changes the agreed files according to the approved plan or
  an authorized repair plan, and runs the required checks.
- **Auditor:** independently checks correctness and conformance to the plan.
  The auditor reports findings without editing the implementation.

Use separate agents for planner, implementer, and auditor. Keep the same agents
for follow-up rounds where possible so they retain task context. Implementation
and audit run sequentially; audit starts after the implementer has handed off.

## 1. Plan and Human Approval

The planner starts with a read-only investigation of the repository, applicable
instructions, current worktree, and any required external evidence. The plan
must identify:

- the problem, intended result, and current behavior;
- scope, files or modules to change, and exclusions;
- implementation steps and important compatibility constraints;
- evidence sources and any unresolved assumptions or exceptions;
- validation commands and observable acceptance criteria.

The coordinator presents the concrete plan to the human and waits for explicit
approval. Questions or requested revisions go back to the planner. Silence is
not approval. Do not start implementation or save the initial plan as a project
file before approval.

After approval, save the agreed plan as a text document in
[`docs/plans/`](plans/README.md), named for the task, such as
`docs/plans/tool-checksums.md`. The directory identifies the document as a plan;
do not add `plan` or `implementation-plan` to the filename. Give its path to both
implementer and auditor. Record the approved scope and acceptance criteria
without silently changing them during the handoff.

## 2. Implementation

The implementer receives the saved plan, ownership of the relevant files, and
the current worktree context. Preserve unrelated and pre-existing changes;
do not revert another agent's or the human's work.

Implement the plan and run the checks required by repository instructions and
the plan. Report changed files, behavior, actual check results, and limitations.
Do not claim a check passed if it was skipped or blocked. Implementation does
not imply permission to commit, push, publish, or deploy.

## 3. Independent Audit

After implementation, the auditor reviews the approved plan, the implementation
diff, relevant surrounding code, and validation evidence. Independently verify
the material claims and check for regressions, missing cases, scope drift, and
unmet acceptance criteria. Existing passing tests alone do not establish
conformance to the plan.

The audit must return one of these outcomes:

- **Pass:** acceptance criteria are satisfied and no required fixes remain.
- **Findings:** actionable problems, with file references, evidence, impact,
  and the acceptance criterion or correctness requirement they affect.
- **Blocked:** missing access, evidence, or another prerequisite prevents a
  reliable decision. This is not a pass; report what is needed to finish.

Optional suggestions should be distinguished from required fixes. A repair
round is needed only for required fixes.

## 4. Automatic Repair Rounds

The initial implementation and its audit are round zero. They do not consume
either of the two automatic repair rounds.

For required audit findings:

1. Send the auditor's findings and evidence to the planner.
2. The planner prepares a concrete repair plan tied to those findings, including
   affected files, validation, and acceptance criteria.
3. Record it as a numbered repair entry alongside the saved plan, preserving
   the original approved plan and earlier findings.
4. The planner hands the repair plan directly to the implementer, or asks the
   coordinator to perform that handoff. No additional human approval is needed
   for repairs within the approved scope during these two rounds.
5. The implementer applies the repair and reports actual validation results.
6. The auditor rechecks the findings, plan conformance, and regressions caused
   by the repair.

One repair round consists of a planner repair plan, its implementation, and the
subsequent audit. Keep a visible counter: repair round 1 or repair round 2.
New findings in the same task do not reset the counter. A blocked or incomplete
round does not allow extra attempts beyond this limit.

## 5. Escalation After Two Repair Rounds

If the audit after repair round 2 still requires fixes, stop further
implementation. The planner presents the human with:

- the remaining problems and their evidence;
- why the original implementation and two repairs did not resolve them;
- any incorrect assumptions, design constraints, or validation gaps involved;
- a revised plan, its scope and tradeoffs, and how it addresses those causes.

Wait for explicit approval before saving the revised plan as approved and
starting another implementation cycle. Approval begins a new cycle with its
own two-round limit; elapsed time or further agent messages do not.

At any stage, an essential change beyond the approved scope or an unresolved
requirement must be brought to the human before dependent implementation.
Do not use the repair allowance to bypass repository rules or tool permissions.

## 6. Completion and Record

Finish only after an audit pass and completion of required checks. The
coordinator reports the implemented result, validation, audit outcome, repair
rounds used, and any remaining optional follow-ups.

Keep the approved plan, repair entries, and audit outcomes linked from the task
record in `docs/plans/`. Preserve the history of what was approved and changed;
do not rewrite the original plan to hide deviations. No commit or publication
is implied by completing this workflow.
