---
name: ignition-security
description: Ignition 8.3 secrets, secret providers, API keys and agent guard rails (IEC 62443). Use whenever credentials, tokens, keys or AI tool access to a Gateway come up.
user-invocable: false
---

# Ignition 8.3 Security: Secrets, API Keys, Agent Guard Rails

Applies to: Ignition 8.3.x

Background knowledge that applies whenever a task involves a password, token, key, certificate, API access, or an AI agent working against a Gateway.

## Hard rules

1. **No credentials in code or git.** Never put a password, API token, connection string with a password, or private key in a Jython script, named query, view, tag, `.env` committed to git, or any file under version control. Use a secret field (Embedded or Referenced) or `system.secrets.*`.
2. **Never print a secret.** Do not echo, log, return to a Perspective session, or write to a tag or component any secret value or API token. Refer to tokens only by their environment variable name, for example `$IGNITION_API_TOKEN`.
3. **Clear plaintext.** `system.secrets.readSecretValue`, `readConfiguredSecretValue` and `decrypt` return a `PyPlaintext`. Use it in a `with ... as` block, or call `clear()` when done.
4. **Least privilege for API keys.** One key per tool or pipeline, with only the security levels it needs. Read-only inspection keys must not have Write permission.
5. **Agents do not get production write access by default.** Deny file edits on a shared Gateway's live `data/config/resources/**` and `data/projects/**`, deny remote script execution tools, and deny reading secret files. See `references/agent-guardrails.md` and `references/claude-settings.example.json`.
6. **Keep keys and key material out of backups you share and out of git**: `data/config/ignition/keys/` (`root.json`, `kek.json`), certificates, keystores. IA's recommended `.gitignore` does not exclude the keys folder, user-source `users.json` (password hashes), API key hashes, or Embedded secrets inside resource files; on a live 8.3.9 Gateway all of these were committed with IA's list. Use Referenced secrets for config that lives in git (details: [../ignition-config/references/version-control.md](../ignition-config/references/version-control.md)).

## Secrets at a glance

| Field option | Meaning |
|---|---|
| None | No secret. Greyed out when the field requires one |
| Embedded | Value entered once, encrypted with Ignition's keys, never shown again |
| Referenced | Points at a secret in a **secret provider** by provider name and secret name |

| Provider | Since | What it does |
|---|---|---|
| Internal | 8.3.0 | Secrets stored encrypted as files on the Gateway, managed on the Manage Secrets panel |
| Remote | 8.3.3 | Reads secrets from a provider on another Gateway over the Gateway Network. Access is denied until allowed in the Security Zone policy |
| File | 8.3.5 | Reads a secret from a file on disk, cleartext or JWE ciphertext (good for Kubernetes-mounted secrets) |

Scripting: `system.secrets.*` arrived in 8.3.1; `createEmbeddedSecretConfig`, `createReferencedSecretConfig` and `readConfiguredSecretValue` arrived in 8.3.8. Exact signatures, `PyPlaintext` handling, JWE creation and the Secrets Management key system: `references/secrets.md`.

The default encryption key is the same on every Ignition install. Recommend opting in to a customized Root Key and Encryption Key Set for any production Gateway, and warn that the environment password must then be kept safe; without it nothing decrypts.

## API keys at a glance

Created on Platform > Security > API Keys. The key is shown **once**; the Gateway stores only a hash. Default level is `Authenticated` (cannot be removed); "Require secure connections" is on by default. Keys are resources, so they can be overridden per deployment mode. Header: `X-Ignition-API-Token`. Details and least-privilege recipes: `references/api-keys.md`.

## IEC 62443 framing for agent tooling

Treat an AI agent, its MCP servers and its API keys as a separate actor inside the OT security model:

| IEC 62443 foundational requirement | What it means here |
|---|---|
| FR1 Identification and authentication | A dedicated API key per agent or tool; never a shared human login |
| FR2 Use control | Key security levels limited to what the task needs; Claude Code deny rules on write tools |
| FR3 System integrity | Changes go through git review and a native scan, not ad hoc edits on a live Gateway |
| FR4 Data confidentiality | Secrets in providers, tokens in environment variables, never in prompts, logs or commits |
| FR5 Restricted data flow | MCP servers bound to loopback; no new connection across zones without authorization |
| FR6 Timely response to events | Gateway auditing enabled so API writes are recorded with user, IP and key |
| FR7 Resource availability | No bulk or looping API calls against production; prefer a dev Gateway |

## Safety

- **IT/OT boundaries:** do not create a Remote secret provider, Gateway Network connection, API client or MCP bridge across network zones without explicit authorization.
- **SIS:** credentials or keys that reach Safety Instrumented System equipment need SIS flagging, engineering review and MOC.
- **Alarms:** anything that changes alarm notification credentials, profiles or pipelines needs human engineering review.

## Where to look

| Need | File |
|---|---|
| Secret providers, `system.secrets` signatures, `PyPlaintext`, JWE | `references/secrets.md` |
| Creating and handling API keys | `references/api-keys.md` |
| Claude Code guard rails for Gateways | `references/agent-guardrails.md` |
| Example Claude Code settings | `references/claude-settings.example.json` |
| REST API routes and permissions | `../ignition-config/references/rest-api.md` |
