---
name: ignition-deploy
description: User-run workflow to commit Ignition 8.3 config or project changes, trigger Gateway scans, verify the result, and promote between deployment modes. Not for writing code.
argument-hint: "[config|projects|all] [promote <ModeName>]"
disable-model-invocation: true
---

# Ignition Deploy

Applies to: Ignition 8.3.x

You are running a controlled deployment of Ignition 8.3 file-based configuration and projects. You work in small, visible steps and stop for explicit user confirmation before anything that writes to a Gateway, restarts it, or changes its deployment mode.

Arguments: `$ARGUMENTS`. The first word is the scope: `config`, `projects` or `all` (default `all`). `promote <ModeName>` asks for a deployment mode promotion (step 6).

Background: `../ignition-config/SKILL.md` (collections, modes, layout) and `../ignition-security/SKILL.md` (keys, secrets). Curl commands: `references/scan-and-verify.md`.

## Non-negotiables

- **Never print, echo or log the API token.** Use it only as `$IGNITION_API_TOKEN` inside a header. Never use `curl -v` or `--trace` (they print request headers), `set -x`, `env` or `printenv`.
- **Confirm before every write or restart.** Before each step marked CONFIRM, state the Gateway URL, the environment (dev, test, prod), the exact action and its effect, then wait for a clear "yes". Silence or ambiguity is "no".
- **Do not push to a remote, pull on a Gateway host, or edit a live Gateway's files** unless the user asks for that step.
- **Stop and flag** instead of proceeding when a change touches:
  - **Alarms**: alarm pipelines, alarm journals, notification profiles, alarm configuration on tags or UDTs, interlocks. Require human engineering review; list each item.
  - **SIS**: anything in Safety Instrumented System scope. Require engineering review and **MOC** documentation.
  - **IT/OT boundary**: new or changed device connections, database connections, OPC UA connections, Gateway Network connections, remote providers, or any mode switch that repoints them. Require explicit authorization naming the network zones.
  - **Safety-critical architecture**: require MOC.

## Step 1: Preflight (read-only)

1. Check the environment variables exist without showing them:
   `test -n "$IGNITION_GATEWAY_URL" && echo "gateway url set"` and `test -n "$IGNITION_API_TOKEN" && echo "token set"`. If either is missing, ask the user to set it in their shell. Never ask them to paste the token into the chat.
2. Ask which environment the URL points at. If it is production, say so in every later confirmation.
3. Read the Gateway's current scan status (`GET /data/api/v1/scan/config` and `/scan/projects`) and note `lastScanTimestamp`. A 401 means no or bad token; a 403 means the key's security level lacks the needed Gateway permission (see `../ignition-security/references/api-keys.md`).

## Step 2: Review the change set (read-only)

1. `git status` and `git diff` (staged and unstaged) limited to the scope.
2. Classify every changed path:

| Path pattern | Meaning | Action |
|---|---|---|
| `config/resources/core/...`, `config/resources/<mode>/...` | Gateway config | Needs a config scan |
| `config/resources/external/...` | Centrally managed config | Needs a config scan |
| `config/resources/local/...`, `config/local/...` | Machine-specific | Should not be in git; stop and ask |
| `projects/...` | Project resources | Needs a project scan |
| `.../tag-definition/...` | Tags | Config scan; check for alarm properties in the diff |
| Anything `.bin` | Binary resource (Transaction Groups, Client Tags, Reports, Alarm Pipelines) | Cannot be reviewed as text; flag; alarm pipelines need engineering review |
| `config/ignition/keys/...`, certificates, keystores, `.env` | Secrets or key material | Stop. Must not be committed |

3. Check that no `resource.json` change is committed without its matching `view.json` (or `props.json`) change.
4. Scan the diff for credentials (passwords, tokens, connection strings). If any, stop.
5. If the change includes Jython or `view.json`, confirm the validation from `CLAUDE.md` (LSP, `ignition-lint`) has passed or run it.
6. Present a summary: files by category, required scans, and every Alarm / SIS / IT/OT / MOC flag.

## Step 3: Commit (CONFIRM)

Propose the branch and commit message. On confirmation, stage only the reviewed paths and commit. Do not push unless asked.

## Step 4: Get the files onto the Gateway (CONFIRM, user-driven)

How files reach the Gateway depends on the repository layout (`../ignition-config/references/version-control.md`):

- **Full data directory**: someone runs `git pull` inside the Gateway's `data` folder.
- **Curated mounts / multi-Gateway**: the container's bind-mounted folders are updated (pull on the host, or a GitOps controller syncs them).
- **Other**: follow the team's documented mechanism.

Ask the user which applies and who performs it. On a container with bind mounts, files must be owned by the Gateway's user (on a live 8.3.9 official image this was uid 2003) or the Gateway faults when it creates resource folders. Alternatively run the Gateway as the repo owner with `IGNITION_UID`/`IGNITION_GID`, which needs the container to start as root; see `../ignition-config/references/docker.md`.

## Step 5: Scan and verify (CONFIRM before each POST)

1. CONFIRM, then `POST /data/api/v1/scan/config` when config changed.
2. CONFIRM, then `POST /data/api/v1/scan/projects` when projects changed. Run config first, then projects, so projects see new connections.
3. Poll `GET /data/api/v1/scan/config` (and `/scan/projects`) until `scanActive` is false and `lastScanTimestamp` is newer than the preflight value.
4. Verify each changed resource type:
   - `GET /data/api/v1/resources/names/<moduleId>/<typeId>`: the resource exists, `enabled` is as expected, and `modes` lists the intended collection.
   - Tags: `GET /data/api/v1/tags/export` for the changed path and compare with the committed JSON.
   - Projects: read the project files back and check the project on the Gateway's Projects page or in the Designer.
5. Check logs for errors since the scan: Gateway web page Diagnostics > Logs, `docker logs` for containers (the image logs to stdout), or the wrapper log in the install's `logs` folder.
6. Report what was verified, what could not be verified, and any errors. For views and scripts, remind the user that Designer verification with live tags is still required.

## Step 6: Promote between deployment modes (only with `promote`)

Explain the two different things "promote" can mean and ask which one the user wants:

**A. Switch the Gateway's active mode (restart).** The mode is set only in `data/ignition.conf` by `wrapper.java.additional.N=-Dignition.config.mode=<ModeName>` with the next free `N`. The Gateway web page cannot change it. Changing it needs a Gateway restart, and on a redundant pair the setting does not sync: both nodes need the same value and both need a restart. This changes which devices and databases the Gateway talks to. It is an **IT/OT boundary** change and a restart of a running control system: CONFIRM with the environment named, get explicit authorization, and let the user (or their change process) perform the restart. On a container, the same JVM argument can go after `--` in the container command instead (verified on 8.3.9; it is not written to `ignition.conf`, so record it in the Compose file under version control). After restart, check `GET /data/api/v1/gateway-info` returns the expected `deploymentMode` (or Platform > System > Modes) and repeat the Step 5 checks.

**B. Move configuration into a mode's collection (no restart).** Create or move overrides into `config/resources/<ModeName>/` so a Gateway running that mode picks them up. IA prefers doing this on the Gateway web page (Create Override, Move Definition) or through the REST API; editing mode folders by hand is IA's last resort. If done through files and git, it follows Steps 2 to 5 (config scan).

Promotion between separate Gateways (Dev Gateway to Prod Gateway) is a git merge to the target's branch or folder, then Steps 3 to 5 against the target Gateway with that Gateway's own key.

## Finish

Summarize: commit hash, scans run with timestamps, verification results, flags raised (Alarm, SIS, IT/OT, MOC) and items left for human review. Do not include any token or secret in the summary.
