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
- For Codex, choose a supported reasoning effort when spawning each subagent
  based on its assigned task. Use low for simple lookups, medium for routine
  implementation, and high for complex investigation or review. Respect explicit
  user requests for an effort level.
- For other tools, use each agent's configured effort settings.
- Give each agent a bounded task and expected output.
- Include relevant context, constraints, and completion criteria in assignments.
- Run dependent tasks in order; parallelize only independent work.
- Assign file edits to agents with distinct scopes to avoid overlapping changes.
- Verify returned work before incorporating it.
- Handle small tasks directly.

When acting as a delegated subagent, complete the assigned task directly and
return the result to the parent agent.
