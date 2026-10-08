# coding-agent-setup

Personal subagent definitions and delegation rules for Codex, Claude Code,
OpenCode v2, and Grok Build. Codex and OpenCode get five roles; Claude Code and
Grok Build get three.
Each role has a configured model and effort level.
The delegation rules apply across projects on the machine where you install them.

## Models and roles

| Tool | `fast` | `worker` | `reviewer` | `explorer` | `default` | `explore` | `general` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Codex | `gpt-6-luna`, Medium | `gpt-6.1-sol`, Medium | `gpt-6-astra`, Medium | `gpt-6-luna`, High | `gpt-6.1-sol`, Medium | N/A | N/A |
| Claude Code | Haiku 5.5, medium | Sonnet 5.5, medium | Opus 5.5, medium | N/A | N/A | N/A | N/A |
| OpenCode | `opencode-go/muse-spark-1.3-contributor`, high | `opencode-go/deepseek-v4.1-flash`, max | `opencode-go/glm-5.3`, max | N/A | N/A | `opencode-go/muse-spark-1.3-contributor`, medium | `opencode-go/deepseek-v4.1-flash`, max |
| Grok Build | Grok 4.7, low | Grok 4.7, medium | Grok 4.7, high | N/A | N/A | N/A | N/A |

- `fast` performs simple lookups, targeted searches, and mechanical checks.
- `worker` implements defined changes within clear file ownership and verifies the affected behavior.
- `reviewer` independently assesses correctness, regressions, security issues, and missing validation with read-only tools.
- `explore` is OpenCode's built-in exploration subagent.
- `general` is OpenCode's built-in general-purpose subagent.

N/A means this setup does not provide that role for the tool.

The shared policy routes deeper investigation to Codex `explorer`, OpenCode
`explore`, or Claude Code's built-in `Explore` when available. Mixed work goes
to Codex `default`, OpenCode `general`, or Claude Code's built-in
`general-purpose` when available. These Claude built-ins keep their own model
settings; this setup configures only Claude's three custom roles.
For tools without a matching specialist, the primary agent handles the work or
splits it into scoped assignments for available agents.

Codex uses these descriptions and routing distinctions:

| Agent | Description | Route here to |
| --- | --- | --- |
| `fast` | Performs simple lookups, targeted searches, and mechanical checks with concise results. | Find a symbol or check a fact. |
| `explorer` | Investigates codebase behavior across files, traces execution paths, and returns evidence without editing code. | Explain how a flow works or where behavior originates. |
| `worker` | Implements assigned changes within clear file ownership and verifies the affected behavior. | Implement a defined change. |
| `reviewer` | Independently reviews changes for correctness, regressions, security issues, and missing validation. | Assess the resulting change. |
| `default` | Handles general tasks that do not fit a specialist role, including mixed investigation and implementation. | Handle work that spans responsibilities without a clear specialist. |

The primary agent delegates when independent work can run in parallel and doing
so would improve speed or quality. It handles small tasks directly. The shared
policy is in [delegation.md](delegation.md).

These definitions configure subagents. Select your daily main model separately
in the tool's model selector or settings. The installer does not set the main
model, main effort, or default primary agent. The Codex `default` definition is
a subagent role.

Claude uses explicit `claude-haiku-5-5`, `claude-sonnet-5-5`, and
`claude-opus-5-5` model IDs. OpenCode uses the `opencode-go` provider and encodes
effort as a model variant, such as `#medium`, `#high`, or `#max`. Access to these
models and variants depends on your account and provider. Check that they are available
before using the agents. [Claude models](https://platform.claude.com/docs/en/models/overview),
[OpenAI models](https://developers.openai.com/api/docs/models), and
[OpenCode model variants](https://opencode.ai/v2/docs/models#variants).

Grok Build uses `grok-4.7` for all three native agents, with low effort for
`fast`, medium for `worker`, and high for `reviewer`. The reviewer sets `capabilityMode: read-only`, which excludes file
edits and shell execution. These fields follow the
[Grok agent schema](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-agent/src/config.rs).

## Global instructions and installation paths

`~` means your home directory. These paths are personal configuration and apply
across projects; they are separate from instruction files inside a repository.

| Tool | Global instruction file | Where this setup installs the delegation policy | Agent definitions |
| --- | --- | --- | --- |
| Codex | `~/.codex/AGENTS.md` | `~/.codex/AGENTS.md` | `~/.codex/agents/*.toml` |
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/rules/delegation.md` | `~/.claude/agents/*.md` |
| OpenCode v2 | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/agents/*.md`, `~/.config/opencode/opencode.jsonc` |
| Grok Build | `~/.grok/AGENTS.md` or `~/.grok/rules/*.md` | `~/.grok/rules/delegation.md` | `~/.grok/agents/*.md` |

Claude Code supports `~/.claude/CLAUDE.md` as global personal instructions.
It also loads global rules from `~/.claude/rules/`. This setup uses the separate
`delegation.md` rule so you can keep other personal instructions in `CLAUDE.md`.
An empty global `CLAUDE.md` is fine: the delegation rule still loads. There is no
need to duplicate the policy in both files. [Claude global instructions](https://code.claude.com/docs/en/memory#choose-where-to-put-claudemd-files)
and [global rules](https://code.claude.com/docs/en/memory#user-level-rules).

OpenCode's `fast`, `worker`, and `reviewer` definitions live in
`~/.config/opencode/agents/*.md`. Its `explore` and `general` model overrides
live in `~/.config/opencode/opencode.jsonc`.

For project-specific instructions, put `AGENTS.md` or `CLAUDE.md` inside the
repository. Claude Code v2.1.277 and later can load project `AGENTS.md`, with
loading determined by its Project instructions setting and existing project
`CLAUDE.md` files. To share a project `AGENTS.md` through `CLAUDE.md`, add this
line to the project's `CLAUDE.md`:

```markdown
@AGENTS.md
```

That import is a Claude-specific feature. OpenCode v2 reads `AGENTS.md` directly
and does not use `CLAUDE.md` as a fallback. [Claude project instruction loading](https://code.claude.com/docs/en/memory#agentsmd)
and [OpenCode v2 instructions](https://opencode.ai/v2/docs/instructions).

Grok Build loads global rules from `~/.grok/rules/` and project `AGENTS.md`
files. This setup installs native Grok agents and a separate delegation rule;
it does not change `~/.grok/config.toml` or your main model. Project agents under
`.grok/agents/` can override the global agents with the same names. Grok can
also load Claude instruction files and rules through its compatibility settings.
Use `grok inspect --json` to inspect discovered configuration and `/config-agents`
to check the available agents. See
[Grok instructions](https://docs.x.ai/build/features/project-rules) and
[Grok subagents](https://docs.x.ai/build/features/subagents).

## Install or upgrade

Install the tools you intend to use and have Python 3 available. The installer
uses only Python's standard library and installs configuration for all four
tools. It does not install the tools or configure credentials.

From the cloned `coding-agent-setup` directory, preview a fresh installation:

```sh
python3 install-agents.py --dry-run
```

Install the files:

```sh
python3 install-agents.py
```

To upgrade an earlier version of this setup, preview and then apply the update:

```sh
python3 install-agents.py --update --dry-run
python3 install-agents.py --update
```

The installer checks all destinations before writing. Identical files stay as
they are. With `--update`, it replaces only files that match recorded earlier
versions in [previous-install-hashes.json](previous-install-hashes.json) and saves
a backup beside each changed file as `<filename>.bak-<UTC timestamp>`. Customized
instructions or agents cause it to stop before changing any files. `--update`
does not force replacement of unrecognized files.

If you have existing personal instructions, review the reported conflict and
merge the delegation policy into the appropriate instruction file manually.
Keep your existing instructions. The installer does not perform this merge.

If your customized `~/.config/opencode/opencode.jsonc` uses plain JSON and
already contains all the specified `explore` and `general` agent fields, the
installer preserves the entire file and continues. Extra settings, agents,
and agent fields stay intact. Uninstall still preserves this customized file.
Otherwise, it reports a conflict before changing any files. Merge the entries
under `agents` from [opencode/opencode.jsonc](opencode/opencode.jsonc) manually.
Configs with JSONC comments or trailing commas still require manual review.

Start fresh tool sessions after installing. To preview installation under another
home directory, use `--target-home /path/to/home --dry-run`. This option is also
useful for testing the installer without changing your personal configuration.

## Uninstall

Preview which installed files would be removed:

```sh
python3 install-agents.py --uninstall --dry-run
```

Remove the recognized agent definitions and delegation rules:

```sh
python3 install-agents.py --uninstall
```

Uninstall checks the same nineteen destinations as installation. It removes files
that match the current definitions or recorded earlier versions of this setup.
Customized files, empty personal instruction files, symlinks, and directories
are preserved and reported for manual review. Recognized files are still removed
when other files need manual review; the command exits with status `1` if any
destination was preserved. Missing files are harmless, so you can rerun it.

Customized app settings, credentials, other agents, and upgrade backups stay in place.
The setup-owned OpenCode `opencode.jsonc` is removed when its contents match
the current setup or a recorded earlier version.
Backups are not restored automatically. To recover an earlier instruction file,
review its `.bak-<UTC timestamp>` copy and restore or merge it manually. Start
fresh tool sessions after uninstalling.

Use `--target-home /path/to/home` to uninstall from another home directory.
`--uninstall` and `--update` cannot be combined.

## Repository files

```text
coding-agent-setup/
├── codex/
├── claude/
├── opencode/
├── grok/
├── delegation.md
├── install-agents.py
├── install-claude-opencode.py
├── previous-install-hashes.json
├── tests/
├── README.md
└── LICENSE
```

| Path | Purpose |
| --- | --- |
| `codex/*.toml` | Codex agent definitions |
| `claude/*.md` | Claude Code agent definitions |
| `opencode/*.md` | OpenCode v2 agent definitions |
| `opencode/opencode.jsonc` | OpenCode v2 built-in `explore` and `general` model overrides |
| `grok/*.md` | Grok Build agent definitions |
| `delegation.md` | Shared delegation policy copied to each tool's global instruction location |
| `install-agents.py` | Combined installer and uninstaller for all four tools |
| `install-claude-opencode.py` | Compatibility entry point that calls the combined installer |
| `previous-install-hashes.json` | Fingerprints of recognized earlier configurations for safe upgrades |
| `tests/test_uninstall.py` | Tests removal and preservation behavior in temporary home directories |

The installer resolves source files relative to its own location, so the clone
can live anywhere. Repository files are the editable source; installed copies
are the configuration each tool reads.

Configuration syntax and installer behavior have been checked locally. Live
delegation and access to every configured model have not been verified.
Grok Build 1.0.46 discovers the native agents and delegation rule in a temporary
home directory with `grok inspect --json`.

Run the tests with Python's standard library:

```sh
python3 -B -m unittest discover -s tests -v
```

Agent format references: [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[Claude subagents](https://code.claude.com/docs/en/sub-agents), and
[OpenCode v2 agents](https://opencode.ai/v2/docs/agents). Grok Build references:
[subagents](https://docs.x.ai/build/features/subagents) and
[agent definitions](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-agent/README.md).

## License

[MIT](LICENSE), copyright 2026 Ruje Alfon.
