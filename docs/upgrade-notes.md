# Ignition 8.1 to 8.3 Upgrade Notes

Working notes for moving `claude-ignition-skills` from Ignition 8.1 to Ignition 8.3.
The frozen 8.1 line lives on branch [`release/8.1`](https://github.com/aott33/claude-ignition-skills/tree/release/8.1) (commit `747250c`, intended tag `v8.1-final`).

Status: steps 1 to 3 (inventory, change map, gap analysis). No skill has been rewritten yet; skill work waits for sign-off on the gap table in section 3.

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
| A14 | `ignition-ui` | "Perspective does NOT support audio alarms" | Recheck against 8.3 Perspective |
| A15 | `ignition-dev`, `ignition-review` | Perspective-only, Vision banned | Still valid as a scope choice; Vision is not removed in 8.3 |
| A16 | `ignition-review` | Rejects `system.db.runPrepQuery` with `?` placeholders as "string-built SQL" | Not version-specific, but inaccurate: prep queries are parameterized. Flag for review |
| A17 | `docs/validation-workflow.md` | Path `com.inductiveautomation.perspective/views/<View>/view.json`, `ignition/script-python/...` | Project resource layout (check whether it changed in 8.3) |
| A18 | none | No module-development guidance | 8.3 Module SDK (JDK, Gradle plugin) is a possible new skill |

No `.proj` export guidance and no Vision-only guidance were found in the skills (Vision is only mentioned to exclude it).

---

## 2. 8.3 change map

**Source caveat.** This session's network policy blocks direct access to `docs.inductiveautomation.com`, `inductiveautomation.com` and the IA forum. Every row below was checked only through web-search summaries of those pages, not by reading the pages. Confidence column:
- **DOC**: an IA manual page summary confirms it.
- **IA**: an IA blog, webinar or release note confirms it.
- **FORUM**: only an IA forum thread supports it.
- **UNVERIFIED**: nothing confirms it yet.

Every row must be re-read against the linked page before any skill text relies on it (step 5 spot-checks).

Latest release found: **8.3.9** ([release notes](https://inductiveautomation.com/downloads/releasenotes)). 8.3.8 moved Jython from 2.7.3 to 2.7.4 ([8.3.8 notes](https://inductiveautomation.com/downloads/releasenotes/8.3.8)). The Jython 2.7 rules in `CLAUDE.md` still apply.

Link base: `https://www.docs.inductiveautomation.com/docs/8.3/`

| # | Change | Detail | Skills affected | Conf. | Source |
|---|---|---|---|---|---|
| C1 | Gateway config on the filesystem | DB connections, devices, tags, alarm pipelines and other Gateway resources are JSON files under `data/config/resources/...` (e.g. `.../core/ignition/tag-definition`), not rows in the internal SQLite DB | dev, architect, plan, review; `validation-workflow.md`, `parallel-dev.md` | DOC | [Version control guide](https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide), [Gateway folder structure](https://www.docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/gateway-folder-structure) |
| C2 | Resource collections | `core` holds what the web UI creates. `external` is for centrally managed config such as orchestrator mounts. Collections inherit from each other, and a child can override a parent's resource. Exact semantics and order of `local` and `system` are not yet confirmed | architect, dev | DOC (hierarchy) / UNVERIFIED (order) | [New in this version](https://www.docs.inductiveautomation.com/docs/8.3/new-in-this-version), [ICC 8.3 platform deep dive](https://inductiveautomation.com/resources/icc/2024/83-deep-dive-platform-updates) |
| C3 | Deployment modes | Named modes (dev/test/prod) override resource values per environment. Mode is selected at Gateway start via JVM property `ignition.config.mode` in `ignition.conf` (forum) | architect, plan, dev | DOC (feature) / FORUM (property) | [Deployment modes webinar](https://inductiveautomation.com/resources/webinar/deployment-modes-in-ignition-83-build-test-and-deploy-with-confidence), [forum](https://forum.inductiveautomation.com/t/understanding-8-3-deployment-modes/110565) |
| C4 | `.resources` digest cache | `data/config/resources/.resources` is a per-Gateway cache; do not commit it | dev (git) | DOC/IA | [Version control guide](https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide) |
| C5 | Gateway REST API + OpenAPI | Built-in REST API; spec and UI at `http://<gw>:8088/openapi`, includes module routes | new REST/MCP skill, dev | DOC | [OpenAPI](https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/openapi) |
| C6 | API keys | Created under Platform > Security > API Keys; sent as header `X-Ignition-API-Token` (exact case). Required for `/data/api/v1/resources`, `/sync`, `/modes` | new REST/MCP skill, architect (security) | DOC | [API keys](https://www.docs.inductiveautomation.com/docs/8.3/platform/security/api-keys) |
| C7 | Scan endpoints | `POST /data/api/v1/scan/config` (Gateway resources) and `POST /data/api/v1/scan/projects` (projects); scripting equivalent `system.project.requestScan()`. Required API-key permission unconfirmed (forum reports 403) | dev, ui (replace "requestScan only") | FORUM | [forum 403 thread](https://forum.inductiveautomation.com/t/403-forbidden-on-data-api-v1-scan-projects-using-ignition-8-3-api-key/116321) |
| C8 | Secrets management | Secret providers: Internal, Remote (8.3.3, via Gateway Network), File-based (8.3.5 per blog title; one snippet says 8.3.6). Embedded config secrets encrypted inline | architect, dev, review, plan | DOC/IA | [8.3.3 blog](https://inductiveautomation.com/blog/ignition-833-new-tag-event-script-x509-opc-ua-authentication-option-remote-secret-provider), [8.3.5 blog](https://inductiveautomation.com/blog/ignition-835-gds-support-filebased-secret-provider-largescale-system-improvements-more) |
| C9 | `system.secrets` (8.3.1) | `getProviders()`, `getSecrets(provider)`, `readSecretValue(provider, name)` returns `PyPlaintext` (use `with` or `.clear()`), `encrypt(...)`, `decrypt(...)` | dev, review | DOC | [system.secrets](https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets) |
| C10 | Version control guidance | Two repo patterns: curated mounting and additive. Keep secrets out of the repo. **Full recommended `.gitignore` not retrieved**; only `.resources/` confirmed | dev, `validation-workflow.md`, `parallel-dev.md` | DOC (partial) | [Version control guide](https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide), [Team best practices](https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide/best-practices-for-team-environments) |
| C11 | Historian | Historian Core module with **Core Historian** (QuestDB, no external DB) plus separate **SQL Historian** module; legacy Internal Historian (SQLite) kept. Tag Historian license replaced by Historian Core / SQL Historian licenses | architect, plan | DOC | [Core Historian](https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/tag-historian/tag-history-providers/internal-historian-questdb), [SQL Historian module](https://www.docs.inductiveautomation.com/docs/8.3/getting-started/modules-overview/core-modules/sql-historian-module) |
| C12 | Deprecated `system.tag` history functions | `queryTagHistory` → `system.historian.queryRawPoints`; `queryTagCalculations` → `system.historian.queryAggregatedPoints`; `storeTagHistory` → `system.historian.storeDataPoints`; `system.historian.browse` added. Custom aggregates only work with the legacy calls | dev, review | DOC | [system.historian](https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-historian), [deprecated system.tag](https://www.docs.inductiveautomation.com/docs/deprecated/system-functions/system-tag-deprecated) |
| C13 | Event Streams module | Sources (Tag, MQTT, Kafka, Sparkplug, event listener, HTTP) to handlers (Logger, Database, Script, Gateway Event, Gateway Message, Kafka, Tag) | architect, plan | DOC | [Event Streams](https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/event-streams) |
| C14 | Perspective: Drawing component and editor | Native SVG symbol editing in Designer; relevant to ISA-101 symbol libraries | ui | DOC | [Drawing](https://www.docs.inductiveautomation.com/docs/8.3/appendix/components/perspective-components/perspective-display-palette/perspective-drawing) |
| C15 | Perspective: Form component | Declarative inputs with validation and conditional logic | ui, dev | DOC | [Form](https://www.docs.inductiveautomation.com/docs/8.3/appendix/components/perspective-components/perspective-input-palette/perspective-form) |
| C16 | Perspective: Offline mode | Mobile app only; caches views and queues form submissions | ui, architect | DOC | [New in this version](https://www.docs.inductiveautomation.com/docs/8.3/new-in-this-version) |
| C17 | Launchers | 8.3 launchers/Workstation work with 8.1; 8.1 launchers do not work with 8.3 | plan (migration) | DOC | [8.1 to 8.3 upgrade guide](https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide) |
| C18 | Alarming | Alarm pipelines are filesystem resources; pipelines can include Event Stream blocks; endpoint to simulate alarm injection. **No ISA-18.2-specific changes (shelving, journal schema) confirmed** | architect, dev, review | IA / UNVERIFIED | [release notes](https://inductiveautomation.com/downloads/releasenotes) |
| C19 | Module SDK | JDK 17 (platform moved from Java 11 to 17); `io.ia.sdk.modl` Gradle plugin; `ExtensionPoint` API (`DeviceExtensionPoint` replaces `DriverType`/`DeviceType`); config as JSON resources; modules no longer hot start/stop | possible new module-dev skill | DOC | [SDK 8.3 upgrade guide](https://www.sdk-docs.inductiveautomation.com/docs/8.3/to-83-upgrade-guide/) |
| C20 | Maker Edition | 10,000 tags, 10 Perspective sessions; module list (incl. Event Streams) not confirmed for 8.3 | plan | DOC (limits) | [Maker Edition](https://www.docs.inductiveautomation.com/docs/8.3/other-editions/ignition-maker-edition) |
| C21 | Upgrade path | Must be on 8.1 first; back up first; Java 17 (check JDBC drivers and 3rd-party modules); Protobuf replaces Java serialization; MariaDB/MSSQL/PostgreSQL JDBC drivers become modules (Docker `GATEWAY_MODULES_ENABLED` must list them); duplicate usernames across Internal/Hybrid sources not allowed; internal audit log lost on in-place upgrade (known issue) | plan (migration epic), architect | DOC | [8.1 to 8.3 upgrade guide](https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide) |
| C22 | Redundancy | Per-resource backup overrides ("Add Backup Version") | architect | DOC | [Redundancy](https://www.docs.inductiveautomation.com/docs/8.3/platform/ignition-redundancy) |
| C23 | Project resource format | No confirmed change to `resource.json` / named query layout. Forum reports a named-query return type change in 8.3 (unread) | dev, review | UNVERIFIED / FORUM | [forum](https://forum.inductiveautomation.com/t/named-query-return-type-changed-in-8-3-regression-or-intended/116366) |

### Open verification items (need the IA docs, which are blocked here)

1. Full recommended `.gitignore` from the version control guide.
2. Semantics and precedence of the `system`, `local`, `core`, `external` collections.
3. API key permission needed for the `/scan/*` endpoints.
4. File secret provider: 8.3.5 or 8.3.6.
5. Maker Edition 8.3 module list.
6. Any ISA-18.2-relevant alarm changes (shelving, journal, notification profiles).
7. Whether Perspective built-in themes (A13) or audio support (A14) changed.

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
| Named queries and project resources (`resource.json`, scopes) | partial | WRRooney `ignition-disk`, ThoughtAgen `ignition-api` | update `ignition-dev` references after checking C23 |

#### ISA-101 (HMI)

| Capability | Me | Covered by reference | Proposed action |
|---|---|---|---|
| ISA-101 colour, hierarchy, style classes, themes | yes | WRRooney `ignition-view` (mechanics only) | update: recheck themes (A13) and audio claim (A14) for 8.3 |
| Drawing component / SVG symbol library | no | none | update `ignition-ui` (C14) |
| Form component for operator entry | no | none | update `ignition-ui` (C15) |
| Offline mode (mobile app) | no | none | update `ignition-ui`, `ignition-architect` (C16) |
| Perspective component catalogue | yes (8.1) | WRRooney `ignition-component` | update `perspective-components.md`, move to `ignition-ui/references/` |
| Perspective e2e tests (Playwright) | no | ThoughtAgen `ignition-e2e`, `init-e2e` | **install**: document ThoughtAgen plugin in README + `validation-workflow`; no new skill |

#### ISA-18.2 (alarm management)

| Capability | Me | Covered by reference | Proposed action |
|---|---|---|---|
| Priority scheme, rationalization, deadband, states | yes | none | keep; version label only |
| Alarm pipelines and journal profiles as 8.3 file resources | no | WRRooney `ignition-api`, `ignition-db` | update `ignition-architect`, `ignition-dev` (C18) |
| 8.3 alarm notification changes (Event Stream blocks, simulate injection, WhatsApp) | no | none | update `ignition-architect` after the C18 recheck. ISA-18.2 impact unconfirmed |
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
| 8.3 git workflow and `.gitignore` | partial (8.1: projects only) | agentic-ignition-stack (layout), IA version control guide | update `ignition-dev` + `validation-workflow.md` + `parallel-dev.md`; ship a sample `.gitignore` **only after** the IA list is confirmed (open item 1) |
| Deploy / scan workflow: commit, `POST /data/api/v1/scan/config` and `/scan/projects`, read back | partial (`requestScan()` only) | WRRooney `ignition-disk`; ThoughtAgen uses a third-party scan module instead | **new** A skill `ignition-deploy` (scan, verify, per-mode promotion). Native IA endpoints only |
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
| Scan mechanism | ThoughtAgen and agentic-ignition-stack use a third-party BW "project scan" module at `/data/project-scan-endpoint/scan` | 8.3 has native `/data/api/v1/scan/projects` and `/scan/config` (C7). Skills will use the native endpoints | pending doc read |
| Forcing script recompile | ThoughtAgen: bump `version` in `resource.json` | Not in IA docs we could reach; prefer a native scan | pending |
| API token header format | WRRooney: `X-Ignition-API-Token: <name>:<secret>` | IA doc confirms the header name only; value format unconfirmed | pending |
| `system.db.runPrepQuery` | our `ignition-review` rejects it as "string-built SQL" | It is parameterized; the rejection should be "prefer named queries", not "SQL injection" | fix in step 4 (needs your OK, changes review policy) |

### 3.5 Questions before step 4

1. **ISA folder layout.** The prompt says skills are organized by ISA standard. They are not: they are organized by role (dev/architect/ui/plan/review). Should I keep the role layout (my recommendation, and it keeps names stable), or restructure by ISA standard? The prompt said to ask before any restructure.
2. **Moving `docs/` into per-skill `references/`.** This is needed so a skill still works when copied alone into `~/.claude/skills/`. It moves files. OK?
3. **New skills.** Approve, drop or rename any of `ignition-config`, `ignition-security`, `ignition-deploy`, `ignition-inspect`.
4. **Install rather than build.** Testing, e2e, expressions and module development would point to ThoughtAgen and IA's skill. OK?
5. **`runPrepQuery` review rule** (3.4). Relax it to "prefer named queries"?
6. **IA docs access.** This environment's network policy blocks `docs.inductiveautomation.com`, so every C-row above rests on search summaries. For step 4 and step 5, either allow that host in the environment's network settings, or accept that rows marked FORUM/UNVERIFIED stay out of skill text.
