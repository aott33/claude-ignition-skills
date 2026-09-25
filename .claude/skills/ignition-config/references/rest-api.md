# Gateway REST API (8.3)

Applies to: Ignition 8.3.x

8.3 exposes Gateway configuration as resources through a documented HTTP API. Scripts, CI pipelines and agents can list, read, create, update and delete configuration, trigger file system scans, and more.

Labels used below:
- **[IA docs]**: stated in the IA 8.3 manual (see Sources).
- **[live 8.3.9]**: verified by this project on a live 8.3.9 Gateway (see the repository's `docs/verification.md`). Still confirm on your own Gateway's `/openapi`, since routes depend on version and installed modules.

## Documentation on the Gateway itself [IA docs]

| Format | URL |
|---|---|
| Interactive docs | `http[s]://<gateway-host>:<port>/openapi` |
| Raw OpenAPI JSON | `http[s]://<gateway-host>:<port>/openapi.json` |

The spec is generated from the running Gateway and its installed modules, so it is the authority for the exact routes, parameters and responses on that Gateway. Internal and session-dependent routes are not listed. Always check `/openapi` before scripting a route that is not in this file.

## Authentication

- Header **[IA docs]**: `X-Ignition-API-Token: <your-api-token>`. Required for all routes documented in `/openapi`.
- Keys are created on Platform > Security > API Keys; see `../../ignition-security/references/api-keys.md`.
- API keys are required for the resource-based config routes under `/data/api/v1/resources`, `/data/api/v1/sync` and `/data/api/v1/modes` **[IA docs]**.
- Token value format **[live 8.3.9]**: `<tokenName>:<secret>`, sent as `X-Ignition-API-Token: <tokenName>:<secret>`. IA's manual shows only `<your-api-token>`. A request without a token gets 401.
- Permissions **[live 8.3.9]**: access is decided by the Access, Read and Write permission settings on Security > General Settings, matched against the key's security levels. A key with only the default `Authenticated` level got 403 even on GETs on a Gateway whose permission lists did not include it. A level in Access and Read allowed GETs; POST scans also needed the level in Write.

Keep the token in an environment variable (for example `IGNITION_API_TOKEN`) and never paste it into a command line, a file in git, or a chat.

```sh
curl -sS -H "X-Ignition-API-Token: $IGNITION_API_TOKEN" \
  "https://<gateway-host>:<port>/data/api/v1/scan/config"
```

## Auditing [IA docs]

POST, PUT and DELETE requests are recorded in the audit log with the user, IP address and API key. **GET requests are not audited.** IA recommends enabling auditing at the Gateway level (Platform > Security > Audit Profiles) when using the API. IA also warns that API use can lose configuration, tags or projects, can open security holes and can degrade performance; only trusted clients should use it.

## Configuration resource routes

Organized under `/data/api/v1/resources` **[IA docs]**:

| Method and path | Purpose | Label |
|---|---|---|
| `GET /data/api/v1/resources/list/<moduleId>/<typeId>` | List all resources of a type | IA docs |
| `POST /data/api/v1/resources/<moduleId>/<typeId>` | Create a resource | IA docs |
| `DELETE /data/api/v1/resources/<moduleId>/<typeId>/<name>/<signature>` | Delete one named resource (needs its current signature) | IA docs |
| `/data/api/v1/resources/datafile/<moduleId>/<typeId>/<name>/<file>` | Update a data file of a resource (IA's themes example uses it for `index.css`). IA does not state the HTTP method; read it from `/openapi` | IA docs |
| `GET /data/api/v1/resources/names/<moduleId>/<typeId>` | Names, enabled flag and modes of each resource, for example `{"items":[{"name":"x","enabled":true,"modes":["core"]}]}` | live 8.3.9 |

Module and type IDs match the folders under `data/config/resources/<collection>/`. Examples seen on a live 8.3.9 Gateway: `ignition/database-connection`, `ignition/secret-provider`, `ignition/alarm-journal`, `ignition/api-token`, `com.inductiveautomation.historian/historian-provider`. The themes type `com.inductiveautomation.perspective/themes` is in IA's docs. Search for `/resources/` on `/openapi` for the full list.

IA's documented create body for a theme is a JSON array of objects with `name`, `collection` (for example `core`), `enabled`, `description` and `config`. Other types have their own `config` schema; read it from `/openapi`.

Mode routes are listed under `/openapi#tag/config-management` **[IA docs]**.

## Scan routes

| Method and path | Purpose | Label |
|---|---|---|
| `POST /data/api/v1/scan/config` | Scan the file system for config changes (same as Scan File System on Platform > System > Modes) | IA docs |
| `POST /data/api/v1/scan/projects` | Scan project files | IA docs (listed in the Version Control Guide) |
| `GET /data/api/v1/scan/config`, `GET /data/api/v1/scan/projects` | Scan status, for example `{"scanActive": false, "lastScanTimestamp": <ms>, "lastScanDuration": <ms>}` | live 8.3.9 |
| `GET` / `POST /data/api/v1/scan-lock/config` and `/scan-lock/projects` | Scan lock. A POST scan also releases the lock if it is held | live 8.3.9 |

Permission: POST scans need a key whose level is in the Gateway's **Write** permissions; GET status needs Access and Read **[live 8.3.9]**. IA's manual does not state the permission; confirm on your Gateway.

## Other routes seen

| Route | Purpose | Label |
|---|---|---|
| `POST /data/api/v1/encryption/encrypt` | Produce a JWE ciphertext for the File secret provider | IA docs (search "encryption" on `/openapi`) |
| `GET /data/api/v1/tags/export` | Tag export; parameters `provider`, `path`, `type`, `recursive`, `includeUdts` | live 8.3.9 |
| `GET /data/api/v1/gateway-info` | Gateway information | live 8.3.9 |
| `POST /data/api/v1/resources/com.inductiveautomation.perspective/themes/copy-base-themes` | Copy base `light` and `dark` themes into `core` for reference (token needs write permission; edits to the copies are ignored) | IA docs |

## Rules for agents

1. Read before write. Use GET routes to inspect; they are not audited, so say in your summary what you read.
2. Every POST, PUT or DELETE needs explicit user confirmation, naming the Gateway, the route and the resource.
3. Prefer a read-only key (level in Access and Read, not Write) for inspection.
4. Never print, echo or log the token. Reference it only as `$IGNITION_API_TOKEN`.
5. Changes to alarm journals, alarm pipelines or notification profiles need human engineering review. Resources that belong to a Safety Instrumented System need SIS flagging and MOC.
6. Pointing a Gateway at a different device or database crosses an IT/OT boundary; get explicit authorization.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/openapi
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/api-keys
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/secrets-management
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/creating-and-using-custom-perspective-themes
- https://www.docs.inductiveautomation.com/docs/8.3/platform/audit-log-and-profiles
