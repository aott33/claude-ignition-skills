# Reviewing 8.3 Gateway Config and Project Diffs

Applies to: Ignition 8.3.x

In 8.1, Gateway configuration lived in an internal database and never showed up in git. In 8.3 it lives on the filesystem under `data/config`, so config changes arrive as diffs and must be reviewed like code. Layout, collections and deployment modes are explained in `../../ignition-config/SKILL.md`; this file lists what a reviewer checks.

---

## 1. Where the change lands

| Path | What it is | Review question |
|---|---|---|
| `data/config/resources/core/...` | Default collection used when no mode is set | Does this change apply to every environment? |
| `data/config/resources/<mode>/...` | Deployment mode overrides (dev, staging, prod ...) | Is the override in the right mode? Does it hide a change that should be in `core`? |
| `data/config/resources/external/...` | Collection meant for VCS-placed resources; cannot be changed from the Gateway | Is the team using it as intended? |
| `data/config/resources/local`, `data/config/local` | Machine-specific data, not inherited by modes | **Should not be committed** (IA's recommended `.gitignore` excludes both) |
| `data/config/resources/core/ignition/tag-definition/...` | Tags and UDT instances as JSON, by Tag Browser path | Review like code; alarm changes need engineering review. Watch the 255-character Windows path limit |
| `data/config/resources/core/ignition/tag-type-definition/<provider>/udts.json` | UDT definitions | A change here applies to **every instance** of the UDT in every environment that inherits the collection. List the affected instances; alarm changes need engineering review |
| `data/config/resources/*/ignition/user-source/*/users.json` | Internal users and roles, with password hashes | Finding: credential material in git (hashes, not plaintext). Security review of who and which roles were added; prefer an external identity provider or keep the user source out of git |
| `data/projects/<project>/...` | Project resources (views, scripts, named queries) | Normal code review |
| `backupConfig.json` beside a `config.json` | Redundancy backup-node override | Is the backup meant to differ from the master? |

## 2. Files that should not be in git (finding: return until removed)

- **`.bin` resources:** Alarm Pipelines, Transaction Groups, Client Tags and Reports are still Java `.bin` files in 8.3. IA recommends gitignoring them because they cannot be reviewed or merged outside Ignition (only through its API). A committed `.bin` is a finding; a change to one of these resources needs evidence from the Gateway instead of a diff.
- **Caches and digests:** anything under a `.resources/` folder, whatever its extension (including `.bin` files there), and any `*.digest.json` file. These are per-system caches.
- **Runtime and security files:** `db/`, `metricsdb/`, `autobackup/`, `valueStore.idb`, `jar-cache/`, `var`, logs, `certificates/`, `keystore/`, `.container-init.conf`, `.alarms_*`, `conversion-report.txt`, `migration-log-*.md`.
- **Secrets:** any cleartext credential or secret-provider source file. This one is a **rejection**, not just a finding (see `review-checklists.md` section 2).

Compare the repo `.gitignore` against IA's recommended list in the version control guide; missing entries are a finding.

## 3. Pairing and consistency rules

- [ ] A `resource.json` change **without** the matching `view.json` change is a finding (IA team best practice). The same applies to `projects/*/com.inductiveautomation.perspective/session-props/props.json`.
- [ ] A `resource.json` `version` change with no format reason is a finding. `version` identifies the resource format (for example version 2 for named queries); do not bump it to force a recompile. Use a scan instead.
- [ ] Named queries change as a pair (SQL plus JSON) under `ignition/named-query/<name>`.
- [ ] Gateway and client event scripts are `.py` files in 8.3; review them with the Jython rules.
- [ ] Vision resources (out of scope) should use XML encoding if they must be versioned.

## 4. Alarm resource diffs (always flag for engineering review)

Flag every diff that touches:
- alarm definitions inside tag or UDT JSON (priority, setpoint, mode including the 8.3 "When True" / "When False" modes, deadband, delays, shelving, labels, notes, associated pipeline),
- alarm journal configuration (a filesystem config resource since 8.3.0; new audit profiles use lowercase table and column names),
- notification profiles,
- alarm pipelines (`.bin`, so the diff alone is not reviewable; ask for Gateway-side evidence, and use the pipeline test and alarm injection tools on a non-production Gateway),
- references to the deprecated Alarms tag folder (moved to Alarm Metrics).

List each one under **Safety Flags** in the review report. Priority changes use Ignition priorities: Diagnostic, Low, Medium, High, Critical.

## 5. IT/OT and security diffs

- [ ] New or changed database, device, OPC UA, Event Streams, HTTP or Gateway Network connections: confirm the network zones and explicit authorization.
- [ ] Secret fields use Referenced or Embedded secrets, never cleartext. For config kept in git prefer Referenced: Embedded secrets are committed as JWE ciphertext.
- [ ] API key resources and security levels changed deliberately; tokens never in the repo. See `../../ignition-security/SKILL.md`.

## 6. Deployment evidence

After merge or pull on the target Gateway, ask for:
- [ ] Config scan: `POST /data/api/v1/scan/config` or Scan File System on Platform > System > Modes (scans the whole file system).
- [ ] Project scan: `/data/api/v1/scan/projects`, Scan File System on Platform > System > Projects, or `system.project.requestScan([timeout])`.
- [ ] Gateway logs free of resource load errors after the scans.
- [ ] Read-back of the changed resource (Gateway UI or `GET` on `/data/api/v1/resources/...`).

Deployment steps: `/ignition-deploy`.

---

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide/best-practices-for-team-environments
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/gateway-folder-structure
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/resource-json-file
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/openapi
- https://www.docs.inductiveautomation.com/docs/8.3/platform/ignition-redundancy/setting-up-redundancy
- https://www.docs.inductiveautomation.com/docs/8.3/platform/sql-in-ignition/named-queries
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/secrets-management
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-project/system-project-requestScan
- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/alarm-notification
- https://www.docs.inductiveautomation.com/docs/8.3/platform/alarming/alarm-journal
