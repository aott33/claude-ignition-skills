# Setting Up ignition-mcp for Read-Only Inspection

Applies to: Ignition 8.3.x

This page describes, in our own words, how to install and connect the third-party **ignition-mcp** server so `/ignition-inspect` can read a Gateway. It reflects ignition-mcp 1.1.0 and ign 1.3.0; check both projects' current documentation before installing.

## What it is

- **ignition-mcp** (https://github.com/WhiskeyHouse/ignition-mcp) is an MCP server that sits in front of `ign mcp serve`. It forwards every `ign` tool unchanged and adds a few composite tools (for example `diagnose_gateway`, `tag_snapshot`, `find_alarms`), `ign://` resources and runbook prompts. It never talks to a Gateway directly; `ign` does.
- **ign** is the command-line tool that actually calls the Gateway. It holds the Gateway URL and credentials in named profiles.
- **Licence:** ignition-mcp is **GPL-3.0**. Install it separately. Do not copy its code into this repository or into your project.

## Install

Requirements from ignition-mcp's docs: `ign` 1.3.0 or newer on `PATH` with a working profile, Python 3.11+, and `uv`.

### 1. Install `ign`

ignition-mcp's README links to `github.com/WhiskeyHouse/ignition-cli`, but that repository is not publicly reachable. The `ign` tool is published on crates.io as **`ignition-cli`** (repository listed as `github.com/TheThoughtagen/ignition-cli`). With a Rust toolchain installed:

```sh
cargo install ignition-cli
ign --version
```

**Do not `pip install ignition-cli`.** The PyPI package with that name is an unrelated project.

### 2. Create a read-only API key on the Gateway

Do this yourself on the Gateway web page (Platform > Security > API Keys); see `../../ignition-security/references/api-keys.md`. Give the key a security level that appears in the Gateway's Access and Read permissions but **not** in Write permissions. Copy the key once into your password manager.

`ign adopt` can set a Gateway up automatically, but according to the ign 1.3.0 tool catalog it mints an **Administrator-level** API key and can deploy ign's WebDev routes. For read-only inspection, prefer a manually created read-only key.

### 3. Configure an `ign` profile

Use `ign profile --help` (and `ign profile add --help`) to create a profile pointing at the Gateway URL. Then provide the credential. ign resolves it in this order:

1. `IGNITION_TOKEN_<PROFILE>` (for example `IGNITION_TOKEN_UAT` for a profile named `uat`)
2. the profile's own `token_env` variable
3. `IGNITION_TOKEN`
4. the OS keyring
5. `IGNITION_USER` plus `IGNITION_PASSWORD`

Recommendation: use the per-profile variable (`IGNITION_TOKEN_<PROFILE>`) holding the read-only key. A bare `IGNITION_TOKEN` applies to **every** profile and overrides keyring credentials, which can silently point a "read-only" session at a more powerful key. Set the variable from a password manager or with `read -rs`, never as a literal on the command line or in a committed file.

Check the profile works before going further:

```sh
ign --profile uat status
ign --profile uat doctor
```

### 4. Install and run ignition-mcp

```sh
git clone https://github.com/WhiskeyHouse/ignition-mcp.git
cd ignition-mcp
uv sync
uv run ign-mcp --profile uat
```

This serves Streamable HTTP at `http://127.0.0.1:8765/mcp`. Startup fails if `ign` is missing or older than 1.3.0.

Settings (flag wins over environment variable):

| Env var | Flag | Default |
|---|---|---|
| `IGN_BIN` | `--ign-bin` | `ign` |
| `IGNITION_PROFILE` | `--profile` | ign's active profile |
| `IGN_MCP_HOST` | `--host` | `127.0.0.1` |
| `IGN_MCP_PORT` | `--port` | `8765` |

**Keep the loopback bind.** The HTTP server has **no client authentication**: anything that can reach the port can run every tool the profile's key allows. `127.0.0.1` is the default, but `--host` / `IGN_MCP_HOST` can change it, so do not set them to a routable address. Exposing it on a network would also create an unauthorized path across an IT/OT boundary.

A stdio mode (`uv run ign-mcp --profile uat --stdio`) is available for clients that start the server as a subprocess; it opens no port at all.

### 5. Connect Claude Code

With the HTTP server running:

```sh
claude mcp add --transport http ign-http http://127.0.0.1:8765/mcp
```

Or add an entry to the project's `.mcp.json`:

```json
{
  "mcpServers": {
    "ign-http": { "type": "http", "url": "http://127.0.0.1:8765/mcp" }
  }
}
```

The key (`ign-http` here) becomes the `<server>` part of every tool name, for example `mcp__ign-http__status`. If you choose a different name, adjust the permission rules to match.

### 6. Apply the guard rails

Add the deny, ask and allow rules from `../../ignition-security/references/claude-settings.example.json` (explained in `../../ignition-security/references/agent-guardrails.md`), adjusted for your server name. At minimum deny:

- `mcp__<server>__script_run`: ign's tool that executes Jython on the Gateway. ignition-mcp forwards it and has **no setting to disable it**, so the Claude Code deny rule is the control.
- `mcp__<server>__webdev_deploy` and `mcp__<server>__adopt`.
- `mcp__<server>__tags_alarms_ack`.

## About the WebDev routes

ign's tag verbs (`tags_browse`, `tags_read`, `tags_write`) and `script_run` rely on a WebDev route bundle that ign deploys into a dedicated project on the Gateway (`ign webdev deploy`, or `ign adopt --project ...`). Trade-off:

- **Shared or production Gateway: do not deploy the routes.** Without them, `script_run` and tag writes through ign have nothing to call. You lose ign's live tag browse and read; use `diagnose_gateway`, project and resource reads, alarms, logs, and the REST tag export (`../../ignition-config/references/rest-api.md`) instead.
- **Personal dev Gateway:** deploying them is a local decision. If you do, the Claude Code deny rule on `script_run` is what keeps the agent from executing code.

Deploying the routes is a Gateway change: a human does it, deliberately, never the agent.

## Verify the setup

In Claude Code, run `/ignition-inspect health`. The agent should report the Gateway identity and a health verdict, and should report `script_run` as denied.

## Sources

- https://github.com/WhiskeyHouse/ignition-mcp (README, `docs/installation.md`, `docs/configuration.md`, `docs/reference.md`, `docs/troubleshooting.md`; GPL-3.0)
- https://crates.io/crates/ignition-cli (the `ign` tool)
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/api-keys
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/gateway-general-security-settings
- https://code.claude.com/docs/en/permissions
