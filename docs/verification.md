# Verification against a live Ignition 8.3 Gateway

Date: 2026-09-25. Step 5 of the 8.3 upgrade: run each action skill end to end against a real 8.3 Gateway, and spot-check knowledge skills against the IA 8.3 manual.

## Test environment

| Item | Value |
|---|---|
| Gateway | `inductiveautomation/ignition:8.3.9` (b2026082511), Standard edition, **Trial** licence, JVM 17.0.19 |
| Harness | [TheThoughtagen/agentic-ignition-stack](https://github.com/TheThoughtagen/agentic-ignition-stack) at `d71ae41`, Docker Compose, bound to `127.0.0.1:8088` only |
| Harness changes | `AUTO_INSTALL_MODULES=false` (no third-party BW scan module or Git module; only IA's native scan endpoints were tested); random local admin password; `-Dignition.config.mode=Dev` added to the command for the mode test |
| MCP | [WhiskeyHouse/ignition-mcp](https://github.com/WhiskeyHouse/ignition-mcp) at `30af56a` over stdio, with `ign` 1.3.0 (crates.io `ignition-cli`) |
| MCP credential | A **read-only** API key: its security level is in the Gateway's Access and Read permissions but not Write |
| Script execution | Not enabled: ign's WebDev routes (including `scriptExec`) were never deployed |

Harness fixes needed (not skill issues): the bootstrap script needs `uuidgen` (missing on the test host), and the bind-mounted `gateway/` and `projects/` folders had to be owned by uid 2003 or the Gateway faulted with `unable to create resource dir: .../data/projects/.resources`.

## Action skills

### `/ignition-deploy` - PASS (after fixes)

Task: create a tag provider and a UDT with an ISA-18.2 alarm, commit, change the alarm in git, scan, read back, then promote between deployment modes.

| Step | Result |
|---|---|
| Tag provider `default` written as `config/resources/core/ignition/tag-provider/default/{config,resource}.json`, then `POST /data/api/v1/scan/config` | PASS: provider live, listed by `GET /data/api/v1/resources/names/ignition/tag-provider` with `"modes":["core"]` |
| UDT `Compressor` with `HighTemp` alarm (JSON exactly as in `ignition-architect/references/tag-structure.md`) and instance `Refrigeration/Compressor1`, via `POST /data/api/v1/tags/import` | PASS: 4 imported, 0 failures; export matched the skill's JSON field for field |
| Files on disk | UDT definitions in `tag-type-definition/default/udts.json`, instances in `tag-definition/default/Refrigeration/udts.json`, each with `unary-resource.json` (**added to the skills**) |
| Commit the `data/` folder with `ignition-config/references/gitignore.sample` | PASS with a finding (see "Credential material" below) |
| Edit `deadband` 2.0 to 1.5 in `udts.json`, commit, `POST /scan/config`, `GET /data/api/v1/tags/export` | PASS: read 2.0 before the scan and 1.5 after; `GET /scan/config` showed a new `lastScanTimestamp` |
| Step 6B: create mode `Dev` with `POST /data/api/v1/mode`, add an override (`deadband` 1.0) under `config/resources/Dev/...`, scan | PASS: Gateway in `core` still read 1.5 |
| Step 6A: add `-Dignition.config.mode=Dev` after `--` in the container command, recreate | PASS: `gateway-info` reported `"deploymentMode":"Dev"`, tag export read 1.0, `ignition.conf` untouched |

Fixes made to the skills from this run:
- The scan endpoints are both `POST` (plus `GET` for status); the skills had hedged on `/scan/projects`.
- Added the UDT file layout.
- Documented the Docker way to select a mode, the `gateway-info` check, and `POST /data/api/v1/mode`.

### `/ignition-inspect` - PASS (after fixes)

Task: inspect the Gateway read-only over MCP and read back the UDT from the deploy test.

| Check | Result |
|---|---|
| Install | ignition-mcp's README links its `ign` dependency to `github.com/WhiskeyHouse/ignition-cli`, which is **404**. `ign` is on crates.io as `ignition-cli` (MIT, repository TheThoughtagen/ignition-cli); `cargo install ignition-cli` worked. The PyPI package of the same name is **unrelated**. Documented in the skill |
| `status` | PASS: Gateway name, 8.3.9, Trial, RUNNING |
| `tags_provider_list` | PASS: `System`, `default` |
| UDT read back | `tags_udt_def` / `tags_export` need ign's WebDev routes, which we do not deploy. Read back instead with `api_call GET /data/api/v1/tags/export`: PASS, `deadband` 1.5 and `priority` High, matching git |
| Write attempt with the read-only key (`api_call POST /data/api/v1/scan/config`) | Refused by the Gateway with **403**, as intended |
| `script_run` | One call made to confirm it is refused: `script_exec_not_configured` (route never deployed). PASS |
| Permission rules | All 45 tool names in `ignition-security/references/claude-settings.example.json` exist on the live server (97 tools). 20 write-capable or data-exporting tools were unlisted; they are now in `deny` (for example `backup_download`, which exports a `.gwbk` holding the Gateway's secrets) or `ask` |

### `/ignition-review` - PASS (after fixes)

Task: a separate agent ran the skill blind (no answer key) on a planted gateway timer script and config diff.

The planted script contained:
- an f-string;
- SQL with a formatted value and a concatenated table name passed to `runPrepQuery`;
- `runNamedQuery`, `queryTagHistory` and `httpGet`;
- a hardcoded API token in a URL.

The planted config diff contained:
- a UDT alarm priority change High → Low;
- a `users.json` change;
- a committed `.resources/.../digest.bin`;
- a `resource.json` change without its `view.json`;
- no validation evidence.

| Expected | Caught |
|---|---|
| f-string, SQL values in text, hardcoded token: hard rejections | Yes (all three) |
| `runNamedQuery`, `queryTagHistory`, `httpGet`: "deprecated - migrate" | Yes |
| `.resources` digest, `resource.json` without `view.json` | Yes |
| Alarm High → Low flagged for engineering review / MOC | Yes |
| Missing LSP, lint, scan, Designer evidence | Yes |
| Decision RETURN | Yes |

The agent listed seven gaps in the skill, all fixed:
1. `tag-type-definition` (UDT definitions) is now a review row, with the note that a change there reaches every instance.
2. `users.json` is now a security finding.
3. Anything under `.resources/`, whatever its extension, is now a cache.
4. The output format now allows N/A and has a "Deprecated APIs" section.
5. Leaked credentials: rotate them, purge them from git history, and never put tokens in URLs.
6. Added Gateway timer script checks.
7. Added validation stages for Gateway-only scripts.

## API key and permission findings (live)

| Finding | Detail |
|---|---|
| Token format | `X-Ignition-API-Token: <tokenName>:<secret>` |
| No token | 401 |
| Permissions | A key's security levels are matched against the Gateway's **Access / Read / Write** permissions (Security > General Settings). With only `Authenticated`: 403 on everything, even `GET /data/api/v1/gateway-info`. With a level in Access + Read: GETs 200, scan `POST`s 403. With a level in Write: scan `POST`s 200 |
| Scan status | `GET /data/api/v1/scan/config` and `/scan/projects` return `{"scanActive", "lastScanTimestamp", "lastScanDuration"}` |
| Mode route | `/data/api/v1/mode` (singular). IA's API Keys page says `/data/api/v1/modes`, which returns 404 on 8.3.9 |

## Credential material in git (live)

We committed a live Gateway's whole `data/` folder using IA's recommended `.gitignore`. Databases, logs, certificates, keystores, `.resources` and `local` folders were excluded correctly (870 files tracked). Still tracked:

- `ignition/user-source/*/users.json` - internal users with password hashes
- `ignition/api-token/*/config.json` - API key hashes
- `ignition/opc-connection/Ignition OPC UA Server/config.json` - Embedded secrets as JWE (`ciphertext`, `encrypted_key`)

IA's list also does not exclude `data/config/ignition/keys/` (Secrets Management keys). That folder was absent on this default Gateway, so the risk could not be observed directly. Changes made:
- `gitignore.sample` now adds the keys folder as a clearly marked local addition and lists the credential-bearing files.
- `ignition-config/references/version-control.md` and `ignition-security/SKILL.md` explain the finding and recommend Referenced secrets for config kept in git.

## Knowledge skill spot checks

See the table appended below (five claims per skill, checked against the IA 8.3 manual).
