# Working with AI coding agents

This repository is prepared for agent-assisted development. You do not need to understand the entire Python codebase before asking an agent to explain it or work on a focused task. The instruction files give the agent the project purpose, architecture, safety rules, development workflow, and current project memory.

**Recommended approach: clone the repository and open its root folder in your coding agent.** Do not just paste individual Python files into a chat: the agent needs the surrounding tests, configuration template, documentation, and instruction files.

### 1. Open the repository in your agent

~~~bash
git clone https://github.com/mudassir-93/OCI-Always-Free-VM.git
cd OCI-Always-Free-VM
~~~

Then open this folder in the tool you want to use. Examples:

| Agent / tool | How to start | Instruction file |
|---|---|---|
| OpenAI Codex (CLI or IDE) | Open the repository root, start Codex, then give it the task | `AGENTS.md` |
| Claude Code | Run `claude` from the repository root | `CLAUDE.md`, then `AGENTS.md` |
| Gemini CLI | Run `gemini` from the repository root | `GEMINI.md`, then `AGENTS.md` |
| Google Antigravity | Open the repository folder and start an agent session | Point the agent to `GEMINI.md`, `AGENTS.md`, and project memory if it does not load them automatically |
| VS Code GitHub Copilot | Open the repository folder, open Copilot Chat, and use Agent mode | `.github/copilot-instructions.md` and `AGENTS.md` |
| Cursor or another agentic IDE | Open the repository root and start its agent | Give it `AGENTS.md` and the project memory file |

Agent instruction-file support can vary by product, version, and IDE configuration. If the agent does not automatically load its instruction file, explicitly ask it to read the files listed above. Do not assume that every tool automatically reads every file.

### 2. Give the agent the project context

The agent should read these files in this order:

1. `AGENTS.md` — mandatory project rules, safety boundaries, coding standards, and workflow.
2. `docs/agents/PROJECT_MEMORY.md` — durable architecture, decisions, and project context.
3. `README.md` — operator-facing setup and behavior.
4. `docs/agents/WORKLOG.md` — completed milestones, known limitations, and handoff notes.
5. Relevant source code and tests for the task.

The reusable prompt is in [reusable start prompt](START_PROMPT.md). Copy it into any agent when you want a full project briefing. It tells the agent to inspect the repository first, explain its understanding, plan the work, preserve the safety model, test changes, update documentation, and report the result.

### 3. Start a task — copy one of these prompts

**First session: understand the project (no code changes)**

~~~text
Read AGENTS.md, docs/agents/PROJECT_MEMORY.md, README.md, and docs/agents/WORKLOG.md.
Do not edit files yet. Explain in simple language:
1. What this project does and who it is for.
2. How the Python application, config, OCI SDK, state, and systemd service fit together.
3. What each CLI command does.
4. How the three-part creation safety guard works.
5. Which parts are implemented, tested, and still limited.
6. How I should request the next change safely.
Do not connect to OCI or run live cloud commands.
~~~

**Implement a feature or fix**

~~~text
Read the repository instructions and project memory first. Inspect git status, current branch, source code, and related tests. Explain the issue and propose a short plan before editing. Implement only this task: [DESCRIBE THE CHANGE]. Add or update offline tests, run the required checks, review the diff for secrets and safety regressions, update the worklog and relevant documentation, and report exactly what changed and what remains. Do not run live OCI operations or touch a production server.
~~~

**Ask for a code review only**

~~~text
Read AGENTS.md and docs/agents/PROJECT_MEMORY.md. Review the current branch for bugs, security problems, unsafe defaults, missing tests, and documentation mismatches. Do not modify files. Prioritize findings by severity and include file paths and line numbers. Do not run live OCI operations.
~~~

**Continue work from a previous agent session**

~~~text
Read AGENTS.md, docs/agents/PROJECT_MEMORY.md, and the latest entries in docs/agents/WORKLOG.md. Inspect git status and the current branch. Summarize the last completed milestone, current state, and next safe task. Do not repeat completed work or touch live OCI resources.
~~~

### 4. Tool-specific shortcuts

- **Claude Code:** from the repository root run `claude`. The repository includes a custom `/work` command in `.claude/commands/work.md`. In Claude Code, enter `/work`, then describe the task in your next message. If the command is not listed, ask Claude Code to read `AGENTS.md` and `docs/agents/START_PROMPT.md` directly.
- **Codex:** open the repository root in Codex. It should use `AGENTS.md` as repository guidance; if it has not loaded the file, explicitly ask it to read it before acting.
- **Gemini CLI:** run `gemini` from the root. If your environment does not automatically import `GEMINI.md`, ask it to open that file and the shared instructions.
- **Antigravity:** open this folder as the workspace. At the beginning of the agent conversation, paste the reusable start prompt or explicitly name the instruction and memory files.
- **GitHub Copilot:** open the folder in VS Code, start Copilot Chat in Agent mode, and ask it to read the repository instructions before making changes.

### 5. Do you need to install the application to work on the code?

Not always.

- For explanation, planning, documentation, and code review, the agent can inspect the repository without OCI credentials or a running VM.
- For Python tests, install the project dependencies. The simplest local setup is:

~~~bash
./oci-free setup
./oci-free test
~~~

- `./oci-free setup` creates a local virtual environment and creates `config.json` from the generic example only if it does not already exist. It preserves an existing config file.
- Do not add your real `config.json`, OCI SDK profile, private keys, or tokens to Git.
- You do not need to run `./oci-free audit` or connect to an OCI tenancy for ordinary development tasks.

### 6. Safe development workflow

For each task, ask the agent to:

1. Inspect the current branch and `git status`; preserve any unrelated local changes.
2. Explain the proposed change and identify cloud, billing, security, or data-loss risks.
3. Make a focused change on a separate Git branch.
4. Add or update offline tests.
5. Run:

~~~bash
python -m py_compile oci_free_watch.py
bash -n oci-free
python -m unittest discover -s tests -v
~~~

6. Review the final diff for credentials, personal identifiers, account-specific OCIDs, unsafe defaults, and weakened guardrails.
7. Update the README, project memory, and worklog when relevant.
8. Report changed files, commands and test results, limitations, and any manual operator action.

**Important:** Agent-ready does not mean permission to operate your cloud account. Agents must not run live OCI audits, enable a creation-capable service, submit an instance launch, change IAM/network/billing settings, or modify a production VPS unless you explicitly authorize that exact operation. The three-part creation guard must never be weakened or bypassed.

### Agent instruction files at a glance

| File | Purpose |
|---|---|
| `AGENTS.md` | Shared rules for Codex and other coding agents |
| `CLAUDE.md` | Claude Code entry point |
| `GEMINI.md` | Gemini-family entry point |
| `.github/copilot-instructions.md` | GitHub Copilot repository instructions |
| `docs/agents/PROJECT_MEMORY.md` | Durable technical memory; not personal account data |
| `docs/agents/START_PROMPT.md` | Copy/paste universal agent briefing |
| `docs/agents/WORKLOG.md` | Milestones, test evidence, and agent handoffs |
| `.claude/commands/work.md` | Optional Claude Code `/work` shortcut |


