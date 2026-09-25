# Guard Rails for AI Agents Working on Ignition

Applies to: Ignition 8.3.x

An AI coding agent such as Claude Code can edit files, run shell commands and call MCP tools. Pointed at an Ignition Gateway, that means it can change live control-system configuration. These guard rails keep the agent useful for development while keeping it away from production writes, secrets and remote code execution.

## Principles

1. **Develop against a dev Gateway or a git working copy, not a shared live Gateway.** Changes reach shared Gateways through git review, then `/ignition-deploy` run by a human.
2. **Read-only by default.** Inspection uses a read-only API key (security level in Gateway Access and Read permissions, not Write) and read-only MCP tools. See `api-keys.md`.
3. **No remote code execution.** Tools that run arbitrary Jython on the Gateway are denied outright.
4. **No secrets in the agent's context.** The agent cannot read `.env`, secret folders or Ignition key files, and never prints tokens.
5. **A human confirms every write**, naming the Gateway, the target and the effect. Alarm, interlock and SIS-related changes also need human engineering review and, where safety architecture changes, MOC.
6. **Loopback only for local bridges.** An MCP server with no client authentication must stay bound to `127.0.0.1`.

These map to the IEC 62443 foundational requirements summarized in `../SKILL.md`.

## Claude Code permission rules in brief

Claude Code reads permission rules from `permissions.allow`, `permissions.ask` and `permissions.deny` in its settings files (for example a project's `.claude/settings.json`, or `.claude/settings.local.json` for rules that should stay on one machine). Deny rules win over ask and allow rules.

### File rules

- Use `Edit(...)` rules to block changes. Claude Code checks file writes against `Edit` and `Read` path rules only; a path rule written for `Write` is accepted but never consulted. An `Edit` deny covers the built-in editing tools.
- A `Read(...)` deny also blocks Edit and Write on the same path.
- Paths use gitignore-style patterns with four anchors:
  - `//path` is absolute from the filesystem root.
  - `~/path` is relative to the home directory.
  - `/path` is relative to the settings file's location (the project root for project settings), **not** the filesystem root.
  - `path` or `./path` is relative to the current directory. A bare filename such as `.env` matches at any depth.
- On Windows, paths are normalized to POSIX form: `C:\Program Files\...` is written `//c/Program Files/...`.
- Limits: Read and Edit rules apply to Claude's file tools, to file commands Claude Code recognizes in Bash (such as `cat`, `sed`, `tee`) and to redirections. They do **not** stop an arbitrary program (for example a Python script) that opens files itself. For a hard boundary, enable Claude Code's sandbox or rely on operating system permissions.

### MCP tool rules

MCP tools are named `mcp__<server>__<tool>`:

- `<server>` is the name the user gave the server, from the key in `.mcp.json` or the name passed to `claude mcp add`. It is **not** fixed by the tool. The ignition-mcp README registers it as `ign-http`, so its script tool becomes `mcp__ign-http__script_run`. If the user named the server `ignition`, the rule must say `mcp__ignition__script_run`. Check the user's `.mcp.json` (or `claude mcp list`) before writing rules.
- `mcp__<server>` or `mcp__<server>__*` matches every tool from that server.
- Rules for MCP tools cannot match parameters: Claude Code skips an `mcp__` rule that has parentheses.
- Tools not listed in allow still prompt in the default permission mode. Do not run an agent against a Gateway with permission prompts disabled.

## The example settings file

`claude-settings.example.json` (next to this file) is a starting point for a developer machine that can reach a shared Gateway. Copy what applies into your settings and adapt it. What it does:

| Rule group | Purpose |
|---|---|
| `Edit` deny on `.../data/config/resources/**`, `.../data/projects/**`, `.../data/ignition.conf` | Stops the agent editing a live Gateway install in place. Paths shown are IA's default Linux (`/usr/local/bin/ignition`) and Windows (`C:\Program Files\Inductive Automation\Ignition`) install folders; change them to yours, and add the host side of any Docker bind mount of a shared Gateway. **Only add these when the machine hosts or mounts a shared Gateway**; on a git working copy you want the agent to edit files |
| `Read` deny on `**/config/ignition/keys/**`, `secrets/**`, `.env`, `.env.*` | Keeps Secrets Management key files, secret folders and env files out of the agent's context |
| `Bash` deny on `printenv`, `env` | Stops casual dumping of environment variables that may hold `IGNITION_API_TOKEN`. Not a hard boundary |
| MCP deny: `script_run` | ignition-mcp forwards ign's `script_run`, which executes Jython on the Gateway. The server has no switch to turn it off, so deny it here |
| MCP deny: `webdev_deploy`, `adopt` | `webdev_deploy` installs ign's WebDev route bundle that `script_run` (and tag read, browse and write) use. `adopt` mints an Administrator-level API key and can deploy those routes. Both are Gateway setup steps for a human, not an agent |
| MCP deny: `tags_alarms_ack` | Acknowledging alarms is an operator action. ign does not guard it with a confirmation. An agent must never acknowledge alarms |
| MCP deny: `backup_restore`, `rig_restore`, `rig_reset` | Whole-Gateway or whole-rig replacement |
| MCP deny: `backup_download`, `session_login`, `eam_task_new`, `eam_task_delete`, `rig_trial_reset` | A `.gwbk` backup contains the Gateway's config, including embedded secrets, so downloading one is a credential export. `session_login` returns a live session cookie. EAM tasks act on other Gateways. Trial reset changes licensing state |
| MCP ask: `tags_provider_create/delete`, `project_new/copy/rename/set`, `rig_up/down`, `testing_run`, `diagnostics_bundle_*`, `logs_download`, `workspace_checkout`, `wait_restart` | Create or change Gateway state, run code (tests), or copy Gateway data to disk |
| MCP ask: writes such as `tags_write`, `resource_put`, `project_sync`, `restart`, `api_call` | Each write prompts, even when ign has its own `confirm` flag. `api_call` can send any HTTP method, so it prompts too |
| MCP allow: read-only verbs | Status, diagnostics, project and resource listing, tag and alarm reads run without prompts |

Tool names come from the ign 1.3.0 catalog. Every name in the example was checked against the 97 tools a live ignition-mcp (ign 1.3.0) server listed, and every write-capable or data-exporting tool is in `deny` or `ask`. Another ign version can add or rename tools: ask the client to list tools and re-check the rules after every upgrade. Anything new and unlisted will prompt in the default mode, which is the safe failure.

**Alarm-related note:** the example denies alarm acknowledgement and allows reading active alarms. Changing either choice is an alarm-handling decision and needs human engineering review.

## Other guard rails

- **Separate keys:** the agent's MCP profile uses a read-only key. The deploy key lives only with the human or CI.
- **Audit:** enable Gateway auditing so that any POST, PUT or DELETE made with a key is recorded with the user, IP and key. GETs are not audited, so ask the agent to summarize what it read.
- **Network zones:** do not expose an MCP bridge, a Gateway API or a Remote secret provider across an IT/OT boundary without explicit authorization.
- **SIS:** never let an agent write to anything in Safety Instrumented System scope. Flag it, require engineering review and MOC.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/api-keys
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/openapi
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/secrets-management
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://code.claude.com/docs/en/permissions (Claude Code permission rule syntax)
- https://github.com/WhiskeyHouse/ignition-mcp (README and docs: tool catalog, `ign-http` server name, loopback default)
