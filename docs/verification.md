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

An independent agent picked five claims per skill (its own choice, weighted toward claims that would cause harm if wrong) and checked them against the IA 8.3 manual. Claims already verified live were skipped.

| Skill | Checked | Correct | Wrong / unsupported | Fixed |
|---|---|---|---|---|
| `ignition-config` | 5 | 4 | API key "required for all routes" (IA: "most") | Yes |
| `ignition-security` | 5 | 5 | Same wording in `api-keys.md` (found while checking config) | Yes |
| `ignition-dev` | 5 | 5 | none | - |
| `ignition-architect` | 5 | 4 | "Core Historian does not use Store and Forward" (IA: it does when writes are pending); "own WAL" unsupported | Yes |
| `ignition-ui` | 5 | 5 | none | - |
| `ignition-plan` | 5 | 5 | none | - |

Claims checked included:
- mode selection and scans
- the 8.3.7 `local` overrides
- `requestScan` defaults
- secret provider versions and `system.secrets` signatures
- API key defaults
- the Jython 2.7.4 update
- `execUpdate` / `runPrepQuery` / `queryAggregatedPoints` signatures, including parameters removed in 8.3.9
- failover time
- Event Streams sources and handlers
- the two-way auth default
- style class ordering and built-in themes
- query binding return formats
- the Form submit button and Offline mode
- Edge storage limits, the 20 MB upload limit, the duplicate-username migration behaviour and audit table names

Caveat added: anonymous access to Ignition's OPC UA server is off by default. IA's own manual contradicts itself on whether Offline mode queues form submissions; the skills make no claim either way.

## Summary

| Area | Result |
|---|---|
| `/ignition-deploy` end to end (UDT + ISA-18.2 alarm, commit, scan, read back, mode promotion) | PASS after fixes |
| `/ignition-inspect` over MCP with a read-only key, `script_run` not deployed | PASS after fixes |
| `/ignition-review` blind run | PASS; 7 skill gaps fixed |
| Knowledge spot checks | 28 of 30 correct; 2 wrong and 1 unsupported, all fixed |
| Open questions from the change map | All resolved live except `system.historian.queryValues` (left out of the skills) |


## Second verification: home-ignition Docker stack (2026-09-25)

While building the [home-ignition](https://github.com/aott33/home-ignition) Compose stack, a second live run on the same image (`inductiveautomation/ignition:8.3.9`, trial) confirmed or found the following. All of it is now in the skills.

| Finding | Where it went |
|---|---|
| `IGNITION_UID`/`IGNITION_GID` only work when the container starts as root (`user: "0:0"`); otherwise it runs as uid 2003 | `ignition-config/references/docker.md` |
| An empty licence `_FILE` crashes the Gateway (NPE in `EnvironmentVariable.resolveEnvVarFile`), in any edition | `docker.md` |
| A pre-filled `external` folder needs `config-mode.json` (`"parent": "system"`), or the Gateway faults ("exists but is not empty") | `docker.md`, `collections-and-modes.md` |
| Mounting a collection `:ro` makes the entrypoint's `chown` fail and the container restart-loop | `docker.md` |
| A partially committed `core` breaks default resources; keep `core` per Gateway, version `external` + mode folders (**superseded** by the third verification: commit `core` minus per-Gateway resources) | `docker.md`, `version-control.md` |
| First boot rewrites the active mode's `security-properties` | `docker.md`, `api-keys.md` |
| `core` overrides `external`, so singleton settings that must win go in the mode folder | `collections-and-modes.md` |
| API keys cannot hold role levels ("cannot be granted via config"); custom `Authenticated/ApiKeys/*` levels work; keys in `local` work | `ignition-security/references/api-keys.md` |
| Default permissions on a fresh Gateway: Access open, Read and Write `Authenticated/Roles/Administrator` | `api-keys.md` |
| Tested nginx layout: only Perspective exposed; `/app`, `/openapi*`, `/data/api/`, `/system/webdev/`, `/system/eventstream/`, `/StatusPing`, `/Start` denied | `ignition-security/references/reverse-proxy.md` |
| HiveMQ CE Docker image removes allow-all unless `HIVEMQ_ALLOW_ALL_CLIENTS=true`; broker RBAC blocked Ignition from publishing device commands | `ignition-architect/references/system-architectures.md` |

The home stack's own smoke test (`scripts/test-stack.sh`, 30 checks) passed from a clean clone.

## Third verification: home-ignition UDTs and a committed `core` (2026-09-26)

Epic 5 of home-ignition (UDTs, history, alarms, a simulated MQTT Engine provider) on `inductiveautomation/ignition:8.3.9` (trial). Every result was checked from a fresh clone, in the `dev` and `prod` deployment modes. Values, alarms and history were read through a temporary tag-change script on the local test Gateway, because REST has no tag-value read.

| Finding | Where it went |
|---|---|
| **Correction:** v8.3.9-1 said to keep `core` out of git. IA's Deployment Modes page and both Version Control Guide examples treat `core` as the committed, shared base. Committing it (whole `config/resources` mount) booted with 0 errors in both modes, provided 8 per-Gateway resources are gitignored | `ignition-config/references/docker.md`, `version-control.md`, `collections-and-modes.md`, `gitignore.sample`, `ignition-config/SKILL.md`, `ignition-architect` |
| Committing `gateway-network-queue-settings`, `gateway-network-proxy-rules` or `quickstart` causes `PushConflictException: CREATE conflict` on every start; committing `com.inductiveautomation.opcua/one-time` stops the OPC UA module creating its user source and connection | `docker.md` rule 4, `config-diff-review.md` |
| The Gateway regenerates an empty `tag-type-definition/<provider>` in `core` on every start, which hides UDT definitions placed in `external` | `docker.md` rule 6, `tag-structure.md` |
| Memory-tag values (including UDT instance overrides) reach the JSON only with the provider's Value Persistence = `Configuration`; otherwise they stay in `valueStore.idb` | `docker.md` rule 9, `rest-api.md`, `tag-structure.md` |
| With `core` in the working tree, `docker compose down -v` does not reset config; `git clean -fdX config/resources` is needed, or first boot conflicts and adds a `temp_0` identity provider | `docker.md` rule 10 |
| A fresh Gateway has no historian provider; creating `CoreHistorian` over REST (body recorded) | `rest-api.md`, `docker.md` rule 11 |
| Tag import needs `Content-Type: application/octet-stream` and writes to `core`; no REST route reads tag values or active alarms | `rest-api.md` |
| UDT inheritance (`typeId`), reference members via a parameter, expression-bound setpoints and delays, parameter-bound priority, instance overrides with `tagType`, `.Timestamp` for last-seen | `ignition-architect/references/tag-structure.md` |
| HiveMQ File RBAC: key device publish rights to `${{username}}`; a `${{clientid}}` rule allowed publishing under another device's prefix | `system-architectures.md` |

The home stack's `scripts/test-stack.sh` passed in both modes. It now also fails if a tracked config file contains a password or an Embedded secret.

## Fourth verification: home-ignition epic 7 Perspective HMI (2026-09-26)

Epic 7 of home-ignition built a Perspective HMI on the same 8.3.9 image (trial, `dev` mode):
- custom themes, style classes and an Advanced Stylesheet;
- a custom icon library;
- page-config with shared docks;
- symbol and page views.

How the findings were sourced:
- An independent verifier rendered every route in headless Chromium at 390x844 and 1440x900 (768x1024 for spot checks), in the day and night themes, including a leak alarm, acknowledge and clear scenario. It read the served CSS and computed styles, and fixed what it found.
- Facts read from the 8.3.9 Perspective module (Java classes, bundled JSON schemas, client JavaScript and CSS) are labelled "observed in the 8.3.9 module/client" in the skills, because they are not a documented API.
- Build-agent claims that were neither verified live nor visible in the working project were left out.

| Finding | Where it went |
|---|---|
| A style class inside a folder that is itself a style class is silently skipped, with no log line. The nav highlight and secondary icon colour never rendered until the parents became leaves (`.../menu`, `.../primary`) | `ignition-ui/references/perspective-styles.md`, `ignition-ui/SKILL.md` |
| Style class on-disk format (`style.json` = `base` + `variants` with `pseudo`, `media`, `animation`); grouping folders need no `resource.json`; the module's `style-class-schema.json` is a different layout | `perspective-styles.md` |
| Served style-class CSS: Advanced Stylesheet first, then classes sorted by their CSS text (name order, animated classes last); `.psc-` prefix with `/` escaped; keyframes `psc-<path>-anim` | `perspective-styles.md` |
| Only the 68 `StyleAttribute` keys reach the CSS (no `gap`, `display`, `width`, `height`, `min-*`); `fontVariant: tabular-nums` works | `perspective-styles.md`, `ignition-ui/SKILL.md` |
| An animated variant writes no `style` block; animation defaults (direction `alternate`); an animation beats inline colours | `perspective-styles.md`, `perspective-components.md` |
| Alphabetical class order makes state classes lose; a doubled selector in the Advanced Stylesheet makes them win | `perspective-styles.md` |
| Themes: imports flattened, comments stripped, served uncompressed and uncached at `/data/perspective/themes/<theme>.css`; hand-written `resource.json` accepted; animating `@property` values on `:root` recalculates style every frame | `perspective-styles.md` |
| Base-theme chrome (tooltip, pager, filter pills) keeps base greys unless the theme maps all `--neutral-*` values; Noto Sans ships only 400/500/700, so 600 renders as 700; font resource type | `perspective-styles.md` |
| Session theme from `session-props/props.json`; `?theme=` through `page.props.urlParams` and an `onChange` script (a page startup event cannot read it) | `perspective-styles.md` |
| Alarm Status Table: `rowStyles` entries with only `classes` still get the schema's default colours inline (a solid blue bar for Cleared-Unacked); set explicit `var(--...)` colours on every entry of all four states. Flagged as an alarm presentation change for engineering review | `ignition-ui/references/perspective-components.md` |
| Table body cells have zero padding; `props.cells.style` padding lines them up with the headers. Label ellipsis clipped text at 390px | `perspective-components.md`, `validation-workflow.md` |
| Component ids and full schemas come from `ia.components.json` in `Perspective-module.modl`; Flex Container has no `gap`; Flex Repeater, Label, Linear Scale, page-config and dock keys, client action types, view JSON keys, binding and transform ids | `perspective-components.md`, `validation-workflow.md` |
| Alarm Metrics bindings on UDT instances; `[System]Gateway/Alarming/*` counts as triggers; `EventData.getTimestamp()` is already epoch ms (`.getTime()` raised an error that a broad `except` hid) | `perspective-components.md` |
| Icon library resource format, sprite rules, colouring through CSS `color`, missing icon = page error, sessionStorage quota, SVG masks under `display:none` | new `ignition-ui/references/icon-libraries.md` |
| Headless render check: anonymous client URL, what to check (page errors, DOM error placeholders, quality overlays, bad values, served CSS and computed styles, clipping), screenshots; trial status route | `ignition-dev/references/validation-workflow.md` Stage 4b |
| Offline Jython check with `jython-standalone` 2.7.4; `lib2to3` accepted f-strings and annotations, so it is not a Jython check | `validation-workflow.md` Stage 1, `ignition-dev/SKILL.md` |

The `ignition-ui` alarm rules (ISA-101 colours, blink only for unacknowledged Critical, engineering review for alarm presentation) are unchanged.

Not added, for lack of evidence:
- The claim that neither a Gateway restart nor the REST API resets an expired trial. The 8.3.9 `/openapi` lists only `GET /data/api/v1/trial`, but ign's own documentation describes a POST-based reset of an expired trial, and neither was tested here.
- A build-agent claim that alarm table schema defaults "only arrive if the Designer wrote them". The live render contradicted it.
- Linear Scale default pixel size.

## Fifth verification: home-ignition trends, third-party modules, network and UPS monitoring (2026-09-26)

home-ignition PRs 6 and 7 on the same 8.3.9 image (trial, `dev` mode):
- trends on Embr Charts, Embr Periscope toasts and repeaters, baked into a derived Gateway image;
- Telegraf and NUT monitoring with five new UDTs.

How the findings were sourced:
- Every alarm scenario was driven through the dev simulation and read back from the Gateway with a temporary diagnostic tag.
- Pages were rendered headless at 390 px and 1440 px.
- The fresh-clone boot was repeated with the derived image.
- Telegraf was tested end to end through HiveMQ against a lab NUT dummy UPS and a net-snmp SNMPv3 agent. **Not tested:** real network devices, a real UPS, and a Maker Gateway.

| Finding | Where it went |
|---|---|
| Third-party modules in a derived image: `ADD --checksum`, `ACCEPT_MODULE_LICENSES` / `ACCEPT_MODULE_CERTS` or first boot stalls in commissioning, module health over REST, no UI uninstall | `ignition-config/references/docker.md` |
| Maker only runs modules whose hook returns `isMakerEditionCompatible() == true`; `freeModule` is licensing only (from module source; verify on Maker) | `docker.md` |
| Power Chart with the Core Historian failed on 8.3.9 (QuestDB `UnsupportedOperationException`); Time Series Chart tick format must be Auto or d3 | `ignition-ui/references/perspective-components.md` |
| Tag History binding: dynamic paths through a custom `pens` array; `valueFormat: document` feeds Chart.js directly | `perspective-components.md` |
| Embr Charts and Periscope usage; `runJavaScriptAsync` only with fixed code and data arguments | `perspective-components.md` |
| `onChange` scripts: nested `currentValue` entries are qualified values; read `self.custom.*` | `perspective-components.md` |
| `json.dumps` data embedded in generated Jython breaks on `true`/`false`; embed a string and `system.util.jsonDecode` it | `ignition-dev/references/jython-constraints.md` |
| UDT parameters in expressions are references (`{P}`, not `'{P}'`); no `dateParse` (use `toDate`); `fromMillis(null)` warns on every evaluation (guard with `if(isNull(..), null, ..)`); `dateDiff(null, ..)` gives bad quality and no alarm | `ignition-architect/references/tag-structure.md` |
| Staleness from a payload poll time; device alarms only on fresh data, one "monitoring stopped" alarm on staleness | `tag-structure.md` |
| Telegraf to MQTT pattern for network and UPS monitoring; strict env handling skips TOML keys; read-only at every hop | `ignition-architect/references/system-architectures.md` |
| Tag export can be empty right after a config scan; diagnostic tag for reading values on a local test Gateway | `ignition-dev/references/validation-workflow.md` |

Not added, for lack of evidence:
- Whether the Mustry Designer Dark Mode and Perspective Components modules load on Maker. Their hooks do not override `isMakerEditionCompatible()`, so they probably will not, but this was not tested.
- Real-device SNMP details: CBS220 `ifName` format, OPNsense SNMPv3 UI behaviour.
