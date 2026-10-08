## Delegation

When acting as the primary agent, use subagents when independent work can run
in parallel and delegation would materially improve speed or quality.

- Use `fast` for focused exploration and straightforward independent tasks.
- Use `worker` for bounded implementation, bug fixes, and tests.
- Use `reviewer` for complex correctness and security reviews.
- Use each agent's configured model and effort settings.
- Give each agent a bounded task and expected output.
- Assign file edits to agents with distinct scopes to avoid overlapping changes.
- Verify returned work before incorporating it.
- Handle small tasks directly.

When acting as a delegated subagent, complete the assigned task directly and
return the result to the parent agent.
