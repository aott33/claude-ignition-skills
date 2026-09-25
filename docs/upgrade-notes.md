# Ignition 8.1 to 8.3 Upgrade Notes

Working notes for moving `claude-ignition-skills` from Ignition 8.1 to Ignition 8.3.
The frozen 8.1 line lives on branch [`release/8.1`](https://github.com/aott33/claude-ignition-skills/tree/release/8.1) (commit `747250c`, intended tag `v8.1-final`).

Status: steps 1 to 6 done. Change map verified against the IA 8.3 manual on 2026-09-25. The gap table (section 3) was approved with the role layout kept. Skills rewritten and added (section 4). Live verification is in [verification.md](verification.md). Alarm changes awaiting engineering review are in section 5.

---

## 1. Inventory (8.1 baseline)

### 1.1 How the repo is organized today

The repo is organized **by role**, not by ISA standard. There is no per-ISA folder layout: the five skills live flat under `.claude/skills/`, and every ISA standard is a cross-cutting topic inside several skills plus `docs/isa-standards.md`. The column "ISA standards touched" below records where each standard shows up.

None of the skills has a `references/` folder. Long material lives in `docs/` at the repo root and is linked with `../../../docs/...` relative paths, which break when a skill is copied on its own into `~/.claude/skills/`.

### 1.2 Skills

| Path | Name | Invocation | Description (current frontmatter) | ISA standards touched |
|---|---|---|---|---|
| `.claude/skills/ignition-dev/SKILL.md` | `ignition-dev` | auto + `/ignition-dev` | Developer mode for 8.1: Jython scripts, Perspective views, UDTs, tag configs | ISA-101, ISA-18.2, ISA-95, ISA-88 |
| `.claude/skills/ignition-architect/SKILL.md` | `ignition-architect` | auto + `/ignition-architect` | Architect mode for 8.1: Gateway architecture, UDT hierarchy, DB schema, ISA-95 model, integration | ISA-95, ISA-18.2, ISA-88, IEC 62443 |
| `.claude/skills/ignition-ui/SKILL.md` | `ignition-ui` | auto + `/ignition-ui` | Perspective UI designer for 8.1: screens, HMI layouts, faceplates, navigation | ISA-101, ISA-18.2 |
| `.claude/skills/ignition-plan/SKILL.md` | `ignition-plan` | auto + `/ignition-plan` | Planner for 8.1: PRDs, discovery, epics, sprints | ISA-95, ISA-101, ISA-18.2, ISA-88, IEC 62443 |
| `.claude/skills/ignition-review/SKILL.md` | `ignition-review` | manual only (`disable-model-invocation: true`) | Reviewer for 8.1: Jython 2.7, ISA, safety, validation evidence | ISA-18.2, ISA-101, ISA-95 |

Supporting material (not skills): `CLAUDE.md` (auto-loaded project context) and eight files in `docs/`: `jython-constraints.md`, `isa-standards.md`, `tag-structure.md`, `system-architectures.md`, `perspective-components.md`, `perspective-styles.md`, `validation-workflow.md`, `parallel-dev.md`.

### 1.3 8.1-specific assumptions

| # | Where | Assumption | Why it matters for 8.3 |
|---|---|---|---|
| A1 | every SKILL.md frontmatter and `Platform:` line, `CLAUDE.md`, `README.md` | "Ignition 8.1" hard-coded; `ignition-plan` says 8.3 "would require updated skills" | Version label and scope statement |
| A2 | `ignition-dev` (Version Control), `docs/validation-workflow.md` lines 88-205 | Tags, UDTs, images and **Gateway config live in the internal SQLite DB**; export with `system.tag.exportTags()` or the third-party ignition-git-module | 8.3 stores Gateway config on the filesystem; this guidance becomes wrong |
| A3 | `docs/validation-workflow.md`, `docs/parallel-dev.md` | Git tree shows only `projects/`; no `config/` resources, no resource collections, no deployment modes, no `.gitignore` guidance | 8.3 git workflow covers Gateway config too |
| A4 | `ignition-dev`, `ignition-ui` | `system.project.requestScan()` is the only way to make the Gateway pick up file edits | 8.3 adds REST scan endpoints for projects and config |
| A5 | `ignition-architect` Step 6, `docs/system-architectures.md` "Scan Classes" | Term "scan class" (8.1 already calls these Tag Groups; "scan class" is 7.x wording) | Terminology fix regardless of 8.3 |
| A6 | `ignition-architect` Steps 5, 8; `ignition-plan` Data Historian, Module Decisions | "Tag Historian" module writing to a SQL DB; historian config drives DB sizing | 8.3 historian changes (Core Historian, SQL historian split) |
| A7 | `ignition-architect` Step 8, `ignition-plan` | Module list without Event Streams, without the 8.3 historian options | New 8.3 modules |
| A8 | `ignition-architect` Step 9, `ignition-plan` epic ordering | "Gateway Configuration" is done by hand in the Gateway web UI, not as versioned files | 8.3 config-as-code and deployment modes change this phase |
| A9 | `ignition-plan` Licensing | 8.1 licensing statements (per-Gateway, unlimited clients/tags), no Maker Edition limits | 8.3 licensing and Maker limits need rechecking |
| A10 | all skills | Database connections, device connections and credentials never discussed; no secrets guidance | 8.3 secret providers and `system.secrets` |
| A11 | all skills | No REST API, API key, or MCP guidance | 8.3 Gateway REST API |
| A12 | `ignition-dev`, `ignition-review`, `docs/validation-workflow.md` | Validation relies on `ignition.nvim` LSP and `ignition-lint` only; no unit tests, no Perspective e2e tests | Testing gap (version-independent) |
| A13 | `ignition-ui`, `docs/perspective-styles.md` | Six built-in themes and theme-file locations as of 8.1 | Recheck against 8.3 Perspective |
| A14 | `ignition-ui` | "Perspective does NOT support audio alarms" | Wrong for 8.3: Perspective has an Audio component (section 2.7, row A14) |
| A15 | `ignition-dev`, `ignition-review` | Perspective-only, Vision banned | Still valid as a scope choice; Vision is not removed in 8.3 |
| A16 | `ignition-review` | Rejects `system.db.runPrepQuery` with `?` placeholders as "string-built SQL" | Not version-specific, but inaccurate: prep queries are parameterized. Flag for review |
| A17 | `docs/validation-workflow.md` | Path `com.inductiveautomation.perspective/views/<View>/view.json`, `ignition/script-python/...` | Project resource layout (check whether it changed in 8.3) |
| A18 | none | No module-development guidance | 8.3 Module SDK (JDK, Gradle plugin) is a possible new skill |
| A19 | `CLAUDE.md`, `ignition-dev`, `ignition-review`, `ignition-architect`, `docs/jython-constraints.md` | Every database example and review rule is built on `system.db.runNamedQuery` | Deprecated in 8.3 in favour of `system.db.execQuery` / `execUpdate` / `execScalar` (C24) |
| A20 | `ignition-dev`, `ignition-review`, `docs/tag-structure.md` | Tag history via `system.tag.queryTagHistory` style calls (implicit) | Deprecated in favour of `system.historian.*` (C12) |

No `.proj` export guidance and no Vision-only guidance were found in the skills (Vision is only mentioned to exclude it).

---

## 2. 8.3 change map

Verified on 2026-09-25 by reading the IA 8.3 user manual, the SDK docs and the release notes directly.

**Link bases:**
- `D` = `https://www.docs.inductiveautomation.com/docs/8.3/`
- `S` = `https://www.sdk-docs.inductiveautomation.com/docs/8.3/`
- `RN` = `https://inductiveautomation.com/downloads/releasenotes/`

**Status column:**
- **DOC**: confirmed in the manual or SDK docs.
- **RN**: confirmed in release notes.
- **CORR**: an earlier search-based claim that the docs corrected.
- **NF**: not found in the docs.

**Versions:**
- Latest release is **8.3.9** (August 25, 2026, per the `RN` 8.3.X index).
- Jython moved from 2.7.3 to **2.7.4** in 8.3.8 (`D` new-in-this-version). The Jython 2.7 rules in `CLAUDE.md` still apply.
- Vision is still a core module in 8.3 and gains the `system.vision` namespace.

### 2.1 Configuration, collections, deployment modes

| # | Change | Detail | Skills affected | Status | Source |
|---|---|---|---|---|---|
| C1 | Gateway config on the filesystem | "Unlike Gateway configurations in Ignition 8.1, which use an internal database, 8.3 Gateways externalize configurations into a data/config directory structure." Layout: `data/config/resources/{external,core,local,<mode>}`, `data/config/ignition`, `data/config/local`, `data/var` (transient), `data/projects`. Tags are JSON under `data/config/resources/core/ignition/tag-definition`, stored by Tag Browser path (watch the 255-character Windows path limit). The old internal DB remains after upgrade but is no longer used | dev, architect, plan, review; `validation-workflow.md`, `parallel-dev.md` | DOC | `D`tutorials/version-control-guide, `D`appendix/reference-pages/gateway-folder-structure, `D`getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide |
| C1a | **Not everything is JSON** | The version control guide recommends gitignoring **Transaction Groups, Client Tags, Reports and Alarm Pipelines**, which "are currently encoded as Java .bin files". Vision windows should be switched from binary to XML encoding | dev, architect, review | DOC | `D`tutorials/version-control-guide |
| C2 | Resource collections | Inheritance order is **system → external → core → user-created modes**. `system` is built-in and immutable but can be overridden. `external` cannot be changed from the Gateway, and is "where your VCS should place any relevant resources". `core` is the default when no mode is set. `local` holds machine-specific data that modes do not inherit; since 8.3.7 it can hold overrides, but those do not reach a backup Gateway | architect, dev | DOC | `D`platform/gateway/web-interface/platform/gateway-deployment-modes |
| C3 | Deployment modes | Created under Platform > System > Modes. Selected with `wrapper.java.additional.N=-Dignition.config.mode=<Mode>` in `ignition.conf`, then a restart. The web UI cannot switch modes, and only one mode can be active. The setting does not sync between redundant peers. No Docker env var is documented; JVM args can be passed after `--` to the image (inference, not shown for modes) | architect, plan, dev | DOC | `D`platform/gateway/web-interface/platform/gateway-deployment-modes, `D`platform/advanced-deployments/docker-image |
| C4 | `.resources` and `*.digest.json` | Per-system cache; gitignored in IA's recommended `.gitignore`. 8.3.4 added the `ignition.resources.digest.pruning` property | dev | DOC | `D`tutorials/version-control-guide, `D`new-in-this-version |
| C22 | Redundancy overrides | "Add Backup Version" per resource, stored in `backupConfig.json` next to `config.json` | architect | DOC | `D`platform/ignition-redundancy/setting-up-redundancy |

### 2.2 REST API, API keys, scans

| # | Change | Detail | Skills affected | Status | Source |
|---|---|---|---|---|---|
| C5 | REST API + OpenAPI | UI at `/openapi`, spec at `/openapi.json`. Config routes live under `/data/api/v1/resources` (e.g. `GET /data/api/v1/resources/list/<moduleId>/<typeId>`). POST, PUT and DELETE calls are audit-logged; GET calls are not | new config/deploy skills | DOC | `D`platform/gateway/openapi |
| C6 | API keys | Created under Platform > Security > API Keys; the only type is Basic Token. Header `X-Ignition-API-Token: <your-api-token>`. Default level is Authenticated; extra levels come from Security > Levels. "Require secure connections" is on by default. The key is shown once and stored hashed. Keys are required for `/data/api/v1/resources`, `/sync`, `/modes`. Keys are themselves resources and can have per-mode overrides. **The token value format (`name:secret`) is NF** | security skill | DOC / NF | `D`platform/security/api-keys |
| C7 | Scan endpoints | `POST /data/api/v1/scan/config` is documented on the deployment modes page. `/data/api/v1/scan/projects` is listed in the version control guide. After a `git pull`, scan config and projects (via UI or these endpoints). `system.project.requestScan([timeout])` still exists: projects only, blocking, Gateway and Perspective scope, default 10 s. **The permission the scan endpoints need is NF** in the manual; read it from the Gateway's `/openapi` | dev, ui, deploy skill | DOC / NF | `D`platform/gateway/web-interface/platform/gateway-deployment-modes, `D`tutorials/version-control-guide, `D`appendix/scripting-functions/system-project/system-project-requestScan |

### 2.3 Secrets

| # | Change | Detail | Skills affected | Status | Source |
|---|---|---|---|---|---|
| C8 | Secret providers | **Internal**; **Remote** (8.3.3); **File** (8.3.5; the 8.3.6 note is a repeat, since 8.3.6 was a patch release). A secret field can be None, Embedded (encrypted with Ignition's own keys, stored in `data/config/ignition/keys`) or Referenced (from a provider). The File provider reads cleartext or JWE files. JWE output comes from `system.secrets.encrypt` or `/data/api/v1/encryption/encrypt` | architect, dev, review, security skill | DOC + RN | `D`platform/security/secrets-management, `RN`8.3.3, `RN`8.3.5 |
| C9 | `system.secrets` (8.3.1; 3 functions added 8.3.8) | `encrypt(string,[charset])` / `encrypt(bytes)` returns a JWE dict. `decrypt(json)` returns PyPlaintext. `getProviders()`, `getSecrets(providerName)`, `readSecretValue(providerName, secretName)` returns PyPlaintext. Added in 8.3.8: `createEmbeddedSecretConfig(json)`, `createReferencedSecretConfig(providerName, secretName)`, `readConfiguredSecretValue(secretConfig)` | dev, review, security skill | DOC | `D`appendix/scripting-functions/system-secrets |

### 2.4 Version control

| # | Change | Detail | Skills affected | Status | Source |
|---|---|---|---|---|---|
| C10 | IA version control guide | Four layouts: (1) the whole `data/` directory in git ("subtractive"; for one or two bare-metal Gateways); (2) curated Docker mounts of `config` and `projects` ("additive"); (3) projects only; (4) several Gateways in one repo (`services/gateway-NN/` plus `shared/`). IA publishes a **recommended `.gitignore`** (below). The team best-practices subpage adds: do not commit a `resource.json` change without the matching `view.json` change | dev, `validation-workflow.md`, `parallel-dev.md` | DOC | `D`tutorials/version-control-guide, `D`tutorials/version-control-guide/best-practices-for-team-environments |

IA's recommended `.gitignore` for a repo rooted at `data/` (from the guide; reproduced here for reference, to be verified again before we ship a sample):

```
**/db/  **/metricsdb/  **/autobackup/  **/db_backup_sqlite.idb  **/valueStore.idb
**/jar-cache/  **/request  **/response  *.tmp  *.bak  **/var
*.log  **/logs
**/certificates/  **/keystore/
**/config/local  **/config/resources/local
**/.container-init.conf
**/conversion-report.txt  **.digest.json
**/projects/conversion-report.txt  **/migration-log-*.md  **/.resources/
**/.alarms_*
```

For the curated-mount layout, the guide's shorter list is `**/config/local`, `**/config/resources/local`, `**/conversion-report.txt`, `**/.resources/`.

Caution: `D`tutorials/ignition-8-deployment-best-practices still says Gateway config is in the internal SQLite DB. It is stale for 8.3 and must not be cited.

### 2.5 Scripting API changes (high impact on existing skills)

| # | Change | Detail | Skills affected | Status | Source |
|---|---|---|---|---|---|
| C12 | Historian functions deprecated | `system.tag.queryTagHistory` → `system.historian.queryRawPoints`; `queryTagCalculations` → `queryAggregatedPoints`; `storeTagHistory` → `storeDataPoints`; `browseHistoricalTags` → `system.historian.browse`; the `*Annotations` functions move to `system.historian.*`; `queryTagDensity` has no replacement. Full `system.historian` list: `browse`, `deleteAnnotations`, `queryAggregatedPoints`, `queryAnnotations`, `queryMetadata`, `queryRawPoints`, `storeAnnotations`, `storeDataPoints`, `storeMetadata`, `updateRegisteredNodePath`, `types.*` (8.3.5). Historical paths use `sys:`/`prov:` instead of `drv:`, except the SQL Historian | dev, review | DOC | `D`81to83-upgrade-guide (System Function Changes and Deprecations), `D`appendix/scripting-functions/system-historian |
| C24 | **`system.db` named-query functions deprecated** | `runNamedQuery` → **`system.db.execQuery` / `execUpdate`**. `runQuery` → `execQuery` or `runPrepQuery`. `runScalarQuery` → `execScalar` or `runScalarPrepQuery`. `runUpdateQuery` → `execUpdate` or `runPrepUpdate`. `runSFNamedQuery` → `execQuery`. `runSFUpdateQuery` → `execUpdateAsync` or `runSFPrepUpdate`. `clear*NamedQueryCache*` → `clearCache` (the function page is named `clearQueryCache`, a docs inconsistency). `execQuery(path, [parameters], [tx], [project])` "Executes a select query from a Named Query resource". Old names redirect and still work, but new code should use the replacements | **CLAUDE.md, dev, review, architect** (every example uses `runNamedQuery`) | DOC | `D`81to83-upgrade-guide, `D`appendix/scripting-functions/system-db/system-db-execQuery |
| C25 | Other deprecations | `system.net.http*` → `system.net.httpClient`. `system.dataset.toPyDataSet` has no replacement ("datasets no longer need to be manually wrapped"). `toDataSet` → `system.dataset.toDataset`. Vision-only functions move to `system.vision.*`. Expression `forceQuality` → `qualifiedValue`. New namespaces: `system.config`, `system.eventstream`, `system.secrets`, `system.historian`, `system.vision` | dev, review | DOC | `D`81to83-upgrade-guide |
| C23 | Project resource format | `resource.json` `version: 2` for named queries exposes data as attributes. Named queries live at `data/projects/<project>/ignition/named-query/<name>` as SQL plus JSON. Gateway and client event scripts migrate to `.py` files. No evidence that the named-query return type changed; the query-type split comes from `execQuery`/`execUpdate`/`execScalar` | dev, review | DOC | `D`appendix/reference-pages/resource-json-file, `D`platform/sql-in-ignition/named-queries |

### 2.6 Modules: historian, Event Streams, SDK, editions

| # | Change | Detail | Skills affected | Status | Source |
|---|---|---|---|---|---|
| C11 | Historian | The Historian Core module includes the **Core Historian** (QuestDB: partitioning, dedup, archiving, native aggregation) and the **Internal Historian (Legacy)** (SQLite). The **SQL Historian** is a separate module. "The Tag Historian license item has been replaced by the Historian Core and SQL Historian license items." | architect, plan | DOC | `D`getting-started/modules-overview/core-modules/tag-historian-module, `D`ignition-modules/tag-historian/tag-history-providers/internal-historian-questdb, `D`getting-started/modules-overview/core-modules/sql-historian-module |
| C13 | Event Streams | Stages: Source, Encoder, Filter, Transform, Buffer, Handler, Error Handler. Sources: Kafka (needs the Kafka module), HTTP (needs WebDev), Event Listener, Tag Event. Handlers: Kafka, Database, HTTP, Gateway Event, Gateway Message, Logger, Script, Tag. **CORR:** MQTT and Sparkplug are not listed as built-in sources | architect, plan | DOC | `D`ignition-modules/event-streams/types-of-sources, `D`ignition-modules/event-streams/types-of-handlers |
| C19 | Module SDK | "Ignition platform 8.3 requires a Java 17 JDK." Gradle plugin `io.ia.sdk.modl`. `DeviceExtensionPoint` replaces `DriverType`/`DeviceType`. Modules are no longer started or stopped while the Gateway runs. Config resources are JSON (`config.json`). Gateway Network objects must implement `ProtobufSerializable` | out of scope (point to IA's module-starter skill) | DOC | `S`getting-started/environment-setup/, `S`to-83-upgrade-guide/, `S`appendix/plugins |
| C20 | Maker Edition | Maximum 10 Perspective sessions and 10,000 tags. No Perspective Workstation; redundancy limited to Independent mode. Modules include Event Streams, Historian, SQL Historian, Kafka, WebDev, Reporting, SFC, SQL Bridge, Alarm Notification, Twilio and common drivers. **Vision is not included** | plan | DOC | `D`other-editions/ignition-maker-edition |

### 2.7 Perspective (ISA-101)

| # | Change | Detail | Skills affected | Status | Source |
|---|---|---|---|---|---|
| C14 | Drawing component | SVG vector graphics built in the Designer's Drawing Editor | ui | DOC | `D`appendix/components/perspective-components/perspective-display-palette/perspective-drawing |
| C15 | Form component | Container for validated input forms, with a Gateway "Form Submission" session event. The Submit button cannot be hidden | ui, dev | DOC | `D`appendix/components/perspective-components/perspective-input-palette/perspective-form |
| C16 | Offline mode | "Offline Mode only works in the Perspective App on mobile devices." | ui, architect | DOC | `D`ignition-modules/perspective/perspective-sessions/ignition-perspective-app/offline-mode |
| A13 | Themes | Unchanged set: `light`, `dark` (base, cannot be altered; use `overrides-light` / `overrides-dark`) plus `light-warm`, `light-cool`, `dark-warm`, `dark-cool`. Custom themes now live in `data/config/resources/core/com.inductiveautomation.perspective/themes/<theme>/` (`config.json`, `resource.json`, `index.css`) | ui, `perspective-styles.md` | DOC | `D`ignition-modules/perspective/styles/perspective-built-in-themes, `D`ignition-modules/perspective/styles/creating-and-using-custom-perspective-themes |
| A14 | **Audio component exists** | "An audio component, hidden by default, that Designers can use to play and pause sound clips in the browser." Our claim that "Perspective does NOT support audio alarms" is wrong. In-browser audio is still not a substitute for hardware annunciators | ui | DOC (**CORR** of our text) | `D`appendix/components/perspective-components/perspective-display-palette/perspective-audio |

### 2.8 Alarming (ISA-18.2)

All rows here are alarm-related and need human engineering review before they change skill guidance (CLAUDE.md safety rules).

| # | Change | Detail | Skills affected | Status | Source |
|---|---|---|---|---|---|
| C18a | Pipelines | Alarm pipelines are global (not project) resources and are still stored as **`.bin`** (see C1a). **CORR:** they are not plain JSON files | architect, dev, review | DOC | `D`ignition-modules/alarm-notification/alarm-notification-pipelines, `D`tutorials/version-control-guide |
| C18b | Event Stream pipeline block | Sends alarm events to an Event Stream with an Event Listener source | architect | DOC | `D`ignition-modules/alarm-notification/alarm-notification-pipelines/pipeline-blocks |
| C18c | Alarm journals | Migrated to filesystem-based config (8.3.0). New audit profiles use lowercase table and column names | architect | RN / DOC | `RN`8.3.0, `D`81to83-upgrade-guide |
| C18d | Testing notifications | Endpoints to simulate alarm injection into pipelines (8.3.0). A Gateway Test button under Services > Alarming > Notification | review, deploy skill | RN / DOC | `RN`8.3.0, `D`ignition-modules/alarm-notification |
| C18e | Notification profiles | Twilio Voice and WhatsApp (8.3.1); email consolidation (8.3.7) | architect, plan | RN | `RN`8.3.1, `RN`8.3.7 |
| C18f | Alarm config | New alarm modes "When True" / "When False". The Alarms tag folder is replaced by **Alarm Metrics** (old folder deprecated but works). Shelving bug fixes (`ShelvingAllowed` ignored; `isShelved` stuck true). Priorities unchanged (Diagnostic, Low, Medium, High, Critical) | architect, dev, review | DOC / RN | `D`81to83-upgrade-guide, `D`ignition-modules/alarm-notification |

### 2.9 Upgrade and migration (8.1 to 8.3)

| # | Change | Detail | Skills affected | Status | Source |
|---|---|---|---|---|---|
| C17 | Launchers | 8.3 launchers and Workstation work with 8.1; 8.1 ones do not work with 8.3 | plan | DOC | `D`81to83-upgrade-guide |
| C21 | Upgrade points | Upgrade to the latest 8.1 first (strong advice, not a hard block). Protobuf replaces Java serialization, so upgrade the central storage Gateway first (8.3 cannot store to 8.1 remotely). MariaDB/MSSQL/PostgreSQL JDBC drivers are now modules, so add them to `GATEWAY_MODULES_ENABLED` in containers. Duplicate usernames in Internal/Hybrid sources are not allowed. No module hot swapping. Require Two-Way Authentication defaults to true. Anonymous OPC UA users lose write/call. 8.1 Gateway permissions are not carried over. Identity Provider JSON exports cannot be imported. Store-and-Forward quarantine exports are now JSON. The EAM Agent Recovery task is removed. Serial Support is bundled into the platform and Web Browser into Vision. **CORR:** audit log loss was a bug fixed in 8.3.0, not a standing limitation. **CORR:** Java 17 is stated in the SDK docs, not the upgrade guide | plan (migration epic), architect | DOC / RN | `D`81to83-upgrade-guide, `RN`8.3.0 |

### 2.10 Not in the docs, resolved on a live 8.3.9 Gateway

See [verification.md](verification.md) for details.

1. **API token value format:** `<tokenName>:<secret>`.
2. **Scan permission:** scan `POST`s need a key level in the Gateway's **Write** permission. GETs, including scan status, need Access + Read.
3. **Deployment mode in Docker:** `-Dignition.config.mode=<Mode>` after `--` in the container command works, and it is not written to `ignition.conf`.
4. `system.historian.queryValues` is mentioned on one page but has no reference page. Still unverified; do not use it.
5. **IA docs discrepancy:** the API Keys page says `/data/api/v1/modes`. The live route is `/data/api/v1/mode` (singular).

---

## 3. Gap analysis

### 3.1 References studied

| Repo | Licence | What it is | How we use it |
|---|---|---|---|
| [WRRooney/ignition-skills](https://github.com/WRRooney/ignition-skills) | Apache-2.0 | 11 action skills for 8.3 driven by its `ign` CLI (`ignition-gen-sdk`): tags/UDTs, views, providers, DB connections, raw API, disk inspection, manifests, guard-rail hook, multi-host installer | Coverage and structure ideas (short SKILL.md + on-demand `references/`, "when NOT to use" in descriptions, a local-override skill, write-guard hook). No text adapted |
| [TheThoughtagen/ignition-ide-plugins](https://github.com/TheThoughtagen/ignition-ide-plugins) | MIT | Claude Code plugin: 4 auto-invoked knowledge skills (`system.*` API, expressions, Jython testing, Playwright e2e) and 4 user-invoked action skills (lint, init-testing, init-e2e, test), plus lint/test hooks | Knowledge/action split; testing and lint are best installed from here, not rebuilt. No text adapted |
| [inductiveautomation/ignition-module-starter](https://github.com/inductiveautomation/ignition-module-starter) | **no licence file** (all rights reserved) | IA's own 8.3 module-dev skill: 5 phases + optional signing, `references/{concepts,prerequisites,scaffold-and-build,signing,resources}.md`, JDK 17, `io.ia.sdk.modl` | House-style idea only (phased workflow, confirm every real action, references per phase). Nothing copied |
| [TheThoughtagen/agentic-ignition-stack](https://github.com/TheThoughtagen/agentic-ignition-stack) | Apache-2.0 | Docker Compose 8.3 dev stack (tested on `8.3.9`), bind-mounts `config/resources/core` and `projects`, bootstraps an API token, lint + Jython + Playwright test script | Step 5 test harness |
| [WhiskeyHouse/ignition-mcp](https://github.com/WhiskeyHouse/ignition-mcp) | GPL-3.0 | MCP proxy over the `ign` CLI (91 tools). Has `script_run` with **no server-side switch** to disable it | Step 5 live inspection, installed separately and never vendored. `script_run` must be denied in Claude Code permissions (`permissions.deny`) and its WebDev routes not deployed |

### 3.2 Gap table

Coverage: **yes** / **partial** / **no** (for this repo today, 8.1 line).
Proposed action: **update** (rewrite existing skill or doc) / **new** (new skill) / **install** (point to an external tool; we do not write it) / **out of scope**.
Skill type in the proposal: **K** = auto-invoked knowledge, **A** = user-invoked action (`disable-model-invocation: true`).

#### ISA-95 (equipment model, tags, UDTs, data)

| Capability | Me | Covered by reference | Proposed action |
|---|---|---|---|
| ISA-95 hierarchy, tag folders, DB master-data model | yes | none at this depth | update: version label only (`ignition-architect`, `tag-structure.md`) |
| UDT definitions and instances **as 8.3 files** (`tag-type-definition/.../udts.json`, `tag-definition`) | no (8.1 says SQLite + `exportTags`) | WRRooney `ignition-tag`, `ignition-disk` | update `ignition-dev` + new `references/config-resources.md` (layout verified against IA docs) |
| Tag Groups (replace "scan class" wording) | partial (wrong term) | WRRooney `ignition-tag` | update `ignition-architect`, `system-architectures.md` |
| Historian: Core Historian (QuestDB) vs SQL Historian vs legacy; licence change | no | none | update `ignition-architect`, `ignition-plan` (C11) |
| `system.historian.*` replacing deprecated `system.tag` history calls | no | ThoughtAgen `ignition-api` (partial, version not stated) | update `ignition-dev`, `ignition-review` (reject deprecated calls in new code) |
| Event Streams (Kafka/MQTT/HTTP to DB/tag/script) | no | none | update `ignition-architect` integration section (C13) |
| DB connections as config resources; JWE passwords cannot be hand-written | no | WRRooney `ignition-db` | fold into the new config-as-code knowledge skill |
| Named queries and project resources (`resource.json`, scopes) | partial | WRRooney `ignition-disk`, ThoughtAgen `ignition-api` | update `ignition-dev` references (C23) |
| **Named-query call API: `runNamedQuery` → `execQuery`/`execUpdate`/`execScalar`** | no (all examples use the deprecated call) | none | **update `CLAUDE.md`, `ignition-dev`, `ignition-review`, `ignition-architect`, `jython-constraints.md`** (C24). Highest-impact change |

#### ISA-101 (HMI)

| Capability | Me | Covered by reference | Proposed action |
|---|---|---|---|
| ISA-101 colour, hierarchy, style classes, themes | yes | WRRooney `ignition-view` (mechanics only) | update: theme set unchanged, but custom-theme path moves to `data/config/resources/core/...` (A13); remove the "no audio" claim (A14) |
| Drawing component / SVG symbol library | no | none | update `ignition-ui` (C14) |
| Form component for operator entry | no | none | update `ignition-ui` (C15) |
| Offline mode (mobile app) | no | none | update `ignition-ui`, `ignition-architect` (C16) |
| Perspective component catalogue | yes (8.1) | WRRooney `ignition-component` | update `perspective-components.md`, move to `ignition-ui/references/` |
| Perspective e2e tests (Playwright) | no | ThoughtAgen `ignition-e2e`, `init-e2e` | **install**: document ThoughtAgen plugin in README + `validation-workflow`; no new skill |

#### ISA-18.2 (alarm management)

| Capability | Me | Covered by reference | Proposed action |
|---|---|---|---|
| Priority scheme, rationalization, deadband, states | yes | none | keep; version label only |
| Alarm journals as 8.3 file resources; alarm pipelines still `.bin` (not diffable, IA recommends gitignoring) | no | WRRooney `ignition-api`, `ignition-db` | update `ignition-architect`, `ignition-dev`, `ignition-review` (C18a, C18c, C1a) |
| 8.3 alarm changes: Event Stream block, simulate injection, Twilio Voice/WhatsApp, email consolidation, When True/When False modes, Alarm Metrics folder, shelving fixes | no | none | update `ignition-architect`, `ignition-review` (C18b to C18f). Priorities unchanged. Flag for engineering review |
| Safety flag on alarm priority/interlock changes | yes | none | keep; extend to "alarm resource files in a git diff" for review |

#### ISA-88 (batch)

| Capability | Me | Covered by reference | Proposed action |
|---|---|---|---|
| Procedural/physical model, phase state machine | yes | none | keep; version label only. No 8.3 impact found |

#### IEC 62443 (security, zones, credentials)

| Capability | Me | Covered by reference | Proposed action |
|---|---|---|---|
| Zones/conduits, IT/OT boundary, SIS flagging | yes | none | keep |
| Secrets: providers (Internal/Remote/File), `system.secrets` (8.3.1) | no | none | **new** K skill `ignition-security` (secrets, API keys, least privilege) + update `ignition-dev`/`ignition-review` (no plaintext credentials in scripts or committed config) |
| API keys: creation, `X-Ignition-API-Token`, scoping, never in command args or git | no | WRRooney `ignition-setup` hard rules | in `ignition-security` |
| Guard rails for agent writes to a live Gateway (deny direct writes to `config/resources/**`, `projects/**` on a shared gateway) | no | WRRooney `ignition-guardrails` | **new**: example `settings.json` deny list + hook in `ignition-security/references/`, written in our own words |
| MCP-connected gateway inspection (read-only) | no | WhiskeyHouse ignition-mcp | **new** A skill `ignition-inspect`: install + configure ignition-mcp, deny `script_run`, read-only verbs only by default |

#### Cross-cutting: platform engineering (8.3)

| Capability | Me | Covered by reference | Proposed action |
|---|---|---|---|
| 8.3 config-as-code: `data/config`, resource collections, deployment modes, redundancy overrides | no | WRRooney `ignition-disk` (partial) | **new** K skill `ignition-config` (collections, modes, file layout, what to commit) |
| 8.3 git workflow and `.gitignore` | partial (8.1: projects only) | agentic-ignition-stack (layout), IA version control guide | update `ignition-dev` + `validation-workflow.md` + `parallel-dev.md`; ship IA's four layouts and a sample `.gitignore` based on IA's list (C10) |
| Deploy / scan workflow: commit, `POST /data/api/v1/scan/config` and `/scan/projects`, read back | partial (`requestScan()` only, which covers projects not config) | WRRooney `ignition-disk`; ThoughtAgen uses a third-party scan module instead | **new** A skill `ignition-deploy` (scan, verify, per-mode promotion). Native IA endpoints only (C7) |
| REST API + OpenAPI discovery | no | WRRooney `ignition-api` | in `ignition-config/references/rest-api.md` (K), used by `ignition-deploy` and `ignition-inspect` |
| `system.*` API reference | partial (examples only) | ThoughtAgen `ignition-api` (239 functions) | out of scope for a full catalogue; add `ignition-dev/references/changed-in-8.3.md` (historian, secrets, deprecated calls). Point to ThoughtAgen or the IA docs for the full list |
| Expression language reference | partial | ThoughtAgen `ignition-expressions` | install (ThoughtAgen); keep our ISA-101 binding patterns |
| Jython unit tests | no | ThoughtAgen `ignition-testing`, `init-testing` | install; update `validation-workflow.md` to add a test stage |
| Linting (`ignition-lint`) | yes (8.1 CLI usage) | ThoughtAgen `ignition-lint` (profiles, `ignition-lint-toolkit`) | update `validation-workflow.md` to current package/profiles after verifying |
| LSP (`ignition.nvim`) | yes | ThoughtAgen `ignition-lsp` (nvim/VS Code/Zed) | update: add the multi-editor option |
| Module development (JDK 17, `io.ia.sdk.modl`) | no | IA `ignition-module-starter` | **out of scope / install**: point to IA's skill in README. Do not write our own |
| 8.1 to 8.3 migration planning | no | none | update `ignition-plan` (migration epic, C17, C21) |
| Licensing / Maker Edition limits | partial (8.1) | none | update `ignition-plan` (C11, C20) |
| Skill packaging: `references/`, `Applies to:` line, install to `~/.claude/skills/` | no (docs/ at root, `../../../` links) | all references | update every skill (step 4) |

### 3.3 Proposed skill set after 8.3 (for approval)

| Skill | Type | Status |
|---|---|---|
| `ignition-dev` | K + `/` | rewrite in place |
| `ignition-architect` | K + `/` | rewrite in place |
| `ignition-ui` | K + `/` | rewrite in place |
| `ignition-plan` | K + `/` | rewrite in place |
| `ignition-review` | A | rewrite in place |
| `ignition-config` | K | **new**: 8.3 config-as-code, collections, deployment modes, REST API reference |
| `ignition-security` | K | **new**: secrets, API keys, guard rails, IEC 62443 |
| `ignition-deploy` | A | **new**: commit, scan, verify, promote between modes |
| `ignition-inspect` | A | **new**: read-only gateway inspection over ignition-mcp |

Testing, expressions, lint and module development are handled by pointing to the ThoughtAgen plugin and IA's module-starter skill, not by writing new skills.

### 3.4 Disagreements and cautions found in references

| Topic | Reference says | IA / our position | Status |
|---|---|---|---|
| `print` in Jython | ThoughtAgen `ignition-api` treats `print x` as a lint error and prefers `print(...)` | Jython 2.7 `print` is a statement; `print('a', 'b')` prints a tuple unless `from __future__ import print_function`. Our CLAUDE.md is correct. Production code should use `system.util.getLogger` anyway | keep ours |
| Scan mechanism | ThoughtAgen and agentic-ignition-stack use a third-party BW "project scan" module at `/data/project-scan-endpoint/scan` | IA documents native `/data/api/v1/scan/config` and `/scan/projects` (C7). Skills will use the native endpoints | resolved: use native |
| Forcing script recompile | ThoughtAgen: bump `version` in `resource.json` | Not in the IA docs; in IA's docs `version` identifies the resource format (e.g. named queries v2). Use a native scan | resolved: do not bump `version` |
| API token header format | WRRooney: `X-Ignition-API-Token: <name>:<secret>` | IA doc confirms the header name; value shown only as `<your-api-token>` | check live in step 5 |
| `system.db.runPrepQuery` | our `ignition-review` rejects it as "string-built SQL" | It is parameterized, and IA's 8.3 upgrade guide lists `runPrepQuery` as a replacement for `runQuery`. The rule should be "prefer named queries via `execQuery`" and "reject string-formatted SQL" | fix in step 4 (needs your OK, changes review policy) |
| Deployment best-practices page | n/a | `D`tutorials/ignition-8-deployment-best-practices still says Gateway config is in the internal SQLite DB | stale IA page; the version control guide and folder structure reference win |

### 3.5 Questions before step 4

1. **ISA folder layout.** The prompt says skills are organized by ISA standard. They are not: they are organized by role (dev/architect/ui/plan/review). Should I keep the role layout (my recommendation, and it keeps names stable), or restructure by ISA standard? The prompt said to ask before any restructure.
2. **Moving `docs/` into per-skill `references/`.** This is needed so a skill still works when copied alone into `~/.claude/skills/`. It moves files. OK?
3. **New skills.** Approve, drop or rename any of `ignition-config`, `ignition-security`, `ignition-deploy`, `ignition-inspect`.
4. **Install rather than build.** Testing, e2e, expressions and module development would point to ThoughtAgen and IA's skill. OK?
5. **`runPrepQuery` review rule** (3.4). Relax it to "prefer named queries"?
6. **`runNamedQuery` in `CLAUDE.md`.** It is deprecated in 8.3 (C24). I plan to switch `CLAUDE.md` and every skill to `system.db.execQuery` / `execUpdate` / `execScalar`. Old code that uses `runNamedQuery` would get a review finding ("deprecated, migrate") rather than a rejection. OK?
7. **Alarm changes** (section 2.8). Per `CLAUDE.md`, alarm guidance changes need engineering review. Who should review the ISA-18.2 text before merge?

---

## 4. What changed in step 4

Decisions approved:
- Keep the role layout.
- Move `docs/` into per-skill `references/`.
- Add `ignition-config`, `ignition-security`, `ignition-deploy` and `ignition-inspect`.
- Point to external tools for tests, expressions and module development.
- Database rule, in the owner's words: "Prefer `system.db.execQuery` with Named Queries for the best security and maintainability. Use `system.db.runPrepQuery` when you need to construct queries dynamically in script that can't be defined ahead of time."

| Skill | Type | Change |
|---|---|---|
| `ignition-dev` | role | Rewritten. New `references/changed-in-8.3.md` (`system.db`, `system.historian`, `system.secrets` signatures). Validation, parallel-dev and Jython references rewritten for 8.3 |
| `ignition-architect` | role | Rewritten: config-as-code step, Tag Groups, historian choice, Event Streams, secrets, alarm architecture, 8.3 module table. References rewritten; the alarm JSON was corrected and verified live |
| `ignition-ui` | role | Rewritten: Drawing, Form, Audio, Offline mode, 8.3 themes, project vs config scans. Several wrong 8.1-era component property names fixed |
| `ignition-plan` | role | Rewritten: 8.3 modules and licensing, Maker limits, deployment modes in FAT/SAT. New `prd-template.md` and `migration-8.1-to-8.3.md` |
| `ignition-review` | action | Rewritten: DB verdict table, deprecated APIs, secrets, 8.3 config diffs. New `review-checklists.md` and `config-diff-review.md` |
| `ignition-config` | knowledge (new) | Collections and modes, file layout, version control, `gitignore.sample`, REST API |
| `ignition-security` | knowledge (new) | Secrets, API keys, agent guard rails, example Claude Code settings |
| `ignition-deploy` | action (new) | Commit, scan, verify, promote between modes |
| `ignition-inspect` | action (new) | Read-only Gateway inspection over ignition-mcp |

Also changed:
- `CLAUDE.md` rewritten for 8.3.
- README rewritten, with install instructions.
- Added `THIRD_PARTY_NOTICES.md` (no adapted material).
- Added the CI check (`scripts/check_skills.py`, `.github/workflows/check-skills.yml`).

## 5. Alarm-related changes for engineering review

Per `CLAUDE.md`, the repo owner reviews every alarm-related change before merge. Grouped by file:

| File | Change |
|---|---|
| `CLAUDE.md` | The alarm flag now also covers alarm pipeline and journal changes |
| `ignition-dev/SKILL.md` | ISA-18.2 bullet: numbered priorities 1 to 4 replaced by Ignition's names (Diagnostic, Low, Medium, High, Critical). **Removed the list of alarm states** (Active, Acknowledged, Cleared, Suppressed). Added the Alarm Metrics folder (replaces the deprecated Alarms folder). Alarm Pipelines listed as `.bin` resources to gitignore |
| `ignition-dev/references/*` | Alarm Metrics row. Setpoint writes affecting alarms or interlocks need review. Alarm pipelines have a single owner and are `.bin` |
| `ignition-architect/SKILL.md` | Step 8 rewritten:<br>- five Ignition priorities and how the rationalized scheme maps to them<br>- pipelines are global `.bin` resources, documented rather than diffed<br>- Event Stream pipeline block<br>- alarm journals are file-based config<br>- notification profiles (Twilio SMS, Voice, WhatsApp)<br>- Alarm Metrics<br>- notify from each spoke<br>- review / MOC banner<br><br>Also: the module table adds Alarm Notification and Twilio; the implementation sequence adds journals and pipelines |
| `ignition-architect/references/tag-structure.md` | UDT alarm JSON corrected:<br>- `alarms` list<br>- priority names instead of numbers (the old 1 = Critical mapping was wrong)<br>- `ackMode` changed from Auto to **Manual**<br>- `mode: AboveValue`, `deadbandMode`<br>- WhenTrue / WhenFalse modes<br>- `shelvingAllowed` and Alarm Metrics notes<br><br>Verified to import on 8.3.9 |
| `ignition-architect/references/system-architectures.md` | New Alarm Architecture section. Hub-and-Spoke: "spoke alarms route through hub" replaced with IA's advice to notify at each spoke. Event Streams alarm block |
| `ignition-architect/references/isa-standards.md` | Priority table in Ignition names with Diagnostic added. Blinking reserved for **Critical**. `shelvingAllowed`, WhenTrue / WhenFalse and Alarm Metrics notes. The "about 6 alarms/hour/operator" figure is kept as an ISA-18.2 figure, not an IA one |
| `ignition-ui/SKILL.md` and references | Red and amber mapped to Critical/High and Medium/Low. Blinking only for unacknowledged Critical. **Removed "Perspective does NOT support audio alarms"**: the Audio component exists, but hardware annunciators remain required and browser audio is not a substitute. Offline sessions must not carry alarm response |
| `ignition-plan/SKILL.md` and references | Alarm philosophy discovery (priority mapping, Twilio channels, named reviewer). Journal and pipeline epic flagged. FAT/SAT alarm path test with engineering sign-off. Migration: VOIP call-script locale collisions, Alarms folder to Alarm Metrics |
| `ignition-review/*` | The alarm flag list now covers priority, setpoint, deadband, delay, mode, shelving and ack changes; alarm properties in tag/UDT JSON; journals; notification profiles; `.bin` pipelines. Deprecated Alarms folder is a finding. Audio proposed as an annunciator is flagged |
| `ignition-security/*`, `ignition-inspect/*` | Agents must never acknowledge alarms: `tags_alarms_ack` is denied, and alarm reads are allowed |
| `ignition-deploy/*`, `ignition-config/*` | Stop and flag any alarm pipeline, journal, notification or tag/UDT alarm change. `.bin` pipelines cannot be reviewed as text |
