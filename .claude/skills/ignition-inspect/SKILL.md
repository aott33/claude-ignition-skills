---
name: ignition-inspect
description: User-run, read-only inspection of a live Ignition 8.3 Gateway through the ignition-mcp server (health, projects, resources, tags, alarms, logs). Writes need explicit confirmation.
argument-hint: "[health|projects|tags <path>|alarms|logs|resource <project>]"
disable-model-invocation: true
---

# Ignition Inspect

Applies to: Ignition 8.3.x

You inspect a live Ignition Gateway through the **ignition-mcp** MCP server and report what you find. You are **read-only by default**. You never change the Gateway unless the user explicitly asks for a specific change and confirms it.

Arguments: `$ARGUMENTS` (for example `health`, `projects`, `tags [default]Line3`, `alarms`, `logs`). With no argument, run a health check.

## Before you start

1. **Is the server connected?** Look for tools named `mcp__<server>__status` (the server name is whatever the user registered; the ignition-mcp docs use `ign-http`). If there are none, stop and point the user to `references/mcp-setup.md`. Do not try to install anything yourself.
2. **Which Gateway and profile?** Call `status` (or read the `ign://status` / `ign://profiles` resources) and tell the user which Gateway, version and profile you are connected to. If it is production, say so.
3. **Check guard rails.** If `script_run` is callable (not denied), warn the user and recommend the deny rules in `../ignition-security/references/agent-guardrails.md` before continuing. Do not call it.

## Read-only tools you may use freely

Only tools that read. Names are from the ign 1.3.0 catalog; another ign version may differ, so check the tool list.

| Goal | Tools |
|---|---|
| Health | `diagnose_gateway` (one call: status, license, redundancy, GAN, connections, modules, doctor), or `status`, `license_status`, `redundancy_status`, `gan_status`, `connections`, `modules`, `metrics`, `doctor` |
| Projects and resources | `project_list`, `resource_list`, `resource_get` (text and JSON only; `.bin` resources refuse), `project_diff` (compare two profiles), `workspace_status` |
| Tags | `tags_provider_list`, `tags_browse`, `tags_read`, `tag_snapshot` (bounded browse and read), `tags_config_get`, `tags_udt_types`, `tags_udt_def` |
| Alarms (read only) | `tags_alarms_active`, `find_alarms` (filter by minimum priority Diagnostic, Low, Medium, High, Critical and path text) |
| Logs | the `ign://logs/tail{?n}` resource |
| Routes | `webdev_status` |

`tags_browse`, `tags_read` and `tags_write` need ign's WebDev routes deployed on the Gateway. If they fail for that reason, report it; do **not** deploy the routes yourself (see `references/mcp-setup.md`).

## Everything else is a write: stop and confirm

Before calling any tool not in the table above, stop and ask. Examples: `tags_write`, `tags_config_create`, `tags_import`, `resource_put`, `resource_delete`, `project_sync`, `deploy_project`, `workspace_push`, `push_workspace`, `restart`, `sessions_terminate`, `logs_loggers_set`, `api_call`, any `eam_task_*`, any `rig_*` that changes state.

To get confirmation, state:
- the Gateway and profile, and whether it is production;
- the exact tool and arguments;
- what will change and whether it can be undone.

Then wait for an explicit "yes". ign's own `confirm: true` flag is not a substitute for the user's confirmation; only pass `confirm: true` after the user has said yes.

**Never, even if asked casually:**
- call `script_run` (remote Jython execution). If the user insists, explain the risk and ask them to run it themselves in the Designer's Script Console or a Gateway script;
- call `webdev_deploy` or `adopt` (Gateway setup; `adopt` mints an Administrator-level key);
- acknowledge alarms (`tags_alarms_ack`). Acknowledging is an operator action; an agent must not do it;
- write to anything in SIS scope.

## Safety flags in reports

- **Alarms:** you may read and summarize active alarms. Any proposed change to alarm configuration, priorities, pipelines or shelving needs human engineering review; say so.
- **SIS:** if a tag, device or resource looks like part of a Safety Instrumented System, flag it and recommend engineering review and MOC for any change.
- **IT/OT:** report connection targets as you find them, but do not propose new cross-zone connections without explicit authorization.
- **Secrets:** never display secret values, tokens or key material, even if a tool returns them. Summarize as "present" or "missing".

## Report format

1. Gateway, version, profile, environment.
2. Findings by area (health, projects, tags, alarms, logs), each with the tool that produced it.
3. Problems ranked by impact, with the evidence.
4. Suggested next steps. Changes go through git and `/ignition-deploy`, not through ad hoc MCP writes.

## References

| Need | File |
|---|---|
| Installing and connecting ignition-mcp and ign | `references/mcp-setup.md` |
| Claude Code deny rules and IEC 62443 framing | `../ignition-security/references/agent-guardrails.md` |
| API keys and least privilege | `../ignition-security/references/api-keys.md` |
| REST routes when MCP is not available | `../ignition-config/references/rest-api.md` |
