# API Keys

Applies to: Ignition 8.3.x

API keys let scripts, pipelines and tools call the Gateway's HTTP API without an interactive login. IA warns that a key can reach routes that modify configuration, tags and projects, so issue keys only to trusted users and systems.

Labels: **[IA docs]** from the IA 8.3 manual; **[live 8.3.9]** verified by this project on a live 8.3.9 Gateway (see the repository's `docs/verification.md`).

## Creating a key [IA docs]

You need write permission as defined on the Gateway's Security > General Settings page.

1. Platform > Security > API Keys > **Create API Key +**.
2. Type: **Basic Token** (the only type). Next.
3. Name and optional description. **Require secure connections** is enabled by default; leave it on and call the Gateway over HTTPS.
4. Security levels: **Authenticated** is selected by default and cannot be removed. Add levels created on Security > Levels to grant specific access.
5. Create. The key is displayed **once**. Copy it straight into a password manager or vault, then confirm "I have stored my API Key". It cannot be retrieved later; the Gateway stores only a hash.

Manage keys from the three-dots menu: Edit, Rename, Duplicate, Disable (temporary revoke), Create Override / Move Definition, Delete (immediate, permanent revoke).

## Keys are resources [IA docs]

A key is a named Gateway resource. It can be overridden or moved per deployment mode, so a Dev key and a Prod key can differ under the same name. On a live 8.3.9 Gateway, keys appear as the `ignition/api-token` resource type (`GET /data/api/v1/resources/names/ignition/api-token`) **[live 8.3.9]**. Treat the key resource folder as sensitive even though it holds a hash.

## Using a key

- Header **[IA docs]**: `X-Ignition-API-Token: <your-api-token>`.
- Value format **[live 8.3.9]**: `<tokenName>:<secret>`.
- Required for all routes documented on the Gateway's `/openapi`, including `/data/api/v1/resources`, `/data/api/v1/sync`, `/data/api/v1/modes` **[IA docs]** (on a live 8.3.9 Gateway the deployment mode route is `/data/api/v1/mode`, singular; `/modes` returns 404).

## Permissions and least privilege

Security > General Settings has **Gateway Access Permissions**, **Gateway Read Permissions** and **Gateway Write Permissions**. Each lists security levels and whether a caller must match at least one or all of them. Write permission also grants Read, and Read also grants Access **[IA docs]**.

What an API key can do depends on its security levels matched against those lists **[live 8.3.9]**:

| Key purpose | Security level placement | Result seen on 8.3.9 |
|---|---|---|
| Default key, only `Authenticated`, on a Gateway whose permission lists do not include it | Not in any list | 403 on every route, even GET |
| Read-only inspection | Level in Access and Read, **not** Write | GETs return 200; POST scans return 403 |
| Deploy (scans, resource writes) | Level in Access, Read and Write | POST scans return 200 |

Recipes:
- Create one level per purpose, for example `apiReader` and `apiDeployer`, on Security > Levels.
- Give inspection tools and AI agents a key with the reader level only.
- Give the deploy pipeline its own key with the deployer level, used only from CI or by a human running `/ignition-deploy`.
- One key per tool or pipeline, so you can disable one without breaking others and so audit entries identify the caller.
- Enable Gateway auditing: POST, PUT and DELETE calls are logged with user, IP address and key; GETs are not **[IA docs]**.
- Rotate by creating a new key, switching the consumer, then deleting the old key.

Changing Security > General Settings permissions affects every user and key on the Gateway. Propose the change and let a human make it.

## Storing and passing the token

- Keep the token in an environment variable, for example `IGNITION_API_TOKEN`, loaded from a password manager, a CI secret, or a git-ignored `.env` file.
- Do **not** put the token on a command line as a literal. Command lines can show up in shell history, process lists and CI logs. Reference the variable instead: `-H "X-Ignition-API-Token: $IGNITION_API_TOKEN"`.
- Do **not** commit it, paste it into chat, write it to a Gateway tag, or log it. Do not run `env`, `printenv` or `set -x` in a shell or CI step that holds it.
- IA's team guidance: store secrets in environment variables rather than hardcode them, keep local env files out of git, and use a secret scanner.
- If a token leaks, disable or delete the key on the Gateway at once and issue a new one.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/api-keys
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/openapi
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/gateway-general-security-settings
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/identity-provider-authentication-strategy/security-levels
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide/best-practices-for-team-environments
