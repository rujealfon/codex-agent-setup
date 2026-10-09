## Delegation

When acting as the primary agent, use subagents when independent work can run
in parallel and delegation would materially improve speed or quality.

- Use `fast` for simple lookups, targeted searches, and mechanical checks.
- Use `worker` to implement a defined change within clear file ownership and
  verify the affected behavior.
- Use `reviewer` for independent assessment of correctness, regressions,
  security issues, and missing validation.
- For investigation across files without code edits, use Codex `explorer`,
  OpenCode `explore`, or Claude Code `Explore` when available.
- For mixed investigation and implementation without a clear specialist, use
  Codex `default`, OpenCode `general`, or Claude Code `general-purpose` when
  available. Otherwise, handle the task as the primary agent or split it into
  clearly scoped assignments for the available roles.
- Use each agent's configured model.
- For Codex and Claude Code, choose a supported reasoning effort when spawning each subagent
  based on its assigned task. Use low for simple lookups, medium for routine
  implementation, and high for complex investigation or review. Respect explicit
  user requests for an effort level.
- In Codex, follow the spawn tool's context and effort constraints. When an effort
  override requires a fresh context, supply a self-contained assignment with the
  necessary project instructions and evidence.
- In Claude Code, pass the chosen effort through the Agent tool's per-invocation
  effort parameter for non-fork subagents. This requires v2.1.292 or later. If the
  parameter is unavailable, use the session default and report that limitation.
  Respect the `CLAUDE_CODE_EFFORT_LEVEL` environment override when set.
- For OpenCode and Grok Build, use each agent's configured effort settings.
- In Codex and Claude Code, keep orchestration in the primary agent.
- In Claude Code, use the built-in
  `Plan` agent for research during plan mode and `Explore` for codebase tracing;
  include relevant project constraints because these built-ins skip CLAUDE.md.
- For Codex and Claude assignments, include the objective, relevant context, file ownership
  or read-only scope, acceptance criteria, and expected evidence. Give reviewers
  the diff, baseline, requirements, and available test results.
- Start Codex and Claude workers after their required investigation or decisions are ready.
  Run independent work concurrently and integrate it before reviewing the combined
  change. Use independent review for meaningful changes; handle trivial edits directly.
- If a Codex or Claude subagent reports missing context or a scope dependency, resolve it
  in the primary agent and resume with the additional context. Verify review
  findings, fix confirmed defects, and rerun the checks affected by each fix.
- Give each agent a bounded task and expected output.
- Include relevant context, constraints, and completion criteria in assignments.
- Run dependent tasks in order; parallelize only independent work.
- Assign file edits to agents with distinct scopes to avoid overlapping changes.
- Verify returned work before incorporating it.
- Handle small tasks directly.

When acting as a delegated subagent, complete the assigned task directly and
return the result to the parent agent.
