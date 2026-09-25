# Migration Epic: Ignition 8.1 to 8.3

Applies to: Ignition 8.3.x

Use this as the backlog for any project that upgrades existing 8.1 Gateways. Each item is a story or task. Items marked **(alarm)** touch alarming and need human engineering review; items marked **(security)** go through the security owner.

Read IA's 8.1 to 8.3 Upgrade Guide in full before sizing this epic; this list is a planning aid, not a replacement for it.

---

## Phase 0: Readiness and inventory

| # | Story | Acceptance |
|---|---|---|
| M0.1 | Confirm every license is 8.3-ready (contact IA sales if not). Note the license item changes: Tag Historian is replaced by **Historian Core** and **SQL Historian**; Serial Support is bundled into the platform; the Web Browser module is bundled into Vision; JDBC drivers appear as modules with a "Free" license | License check recorded per Gateway |
| M0.2 | Inventory Gateways, versions, modules and roles (central storage, spokes, Edge, EAM controller/agents, redundant pairs) | Inventory table in the PRD |
| M0.3 | Check every **third-party module** for a stated 8.3-compatible release | Compatibility evidence or replacement plan per module |
| M0.4 | Upgrade every Gateway to the **latest 8.1** first (IA strongly advises it; not a hard block) | All Gateways on latest 8.1 |
| M0.5 | Take a **Gateway backup** of every Gateway | Backups stored and restore-tested |
| M0.6 | Plan to upgrade dev/test before production, on hardware similar to production | Dev/test upgrade in the schedule ahead of prod |
| M0.7 | Prefer the installer (in-place) or Gateway backup restore. Avoid fresh install plus project/tag imports: imports skip the upgrade check and tags may break on name changes | Method chosen and justified |

## Phase 1: Clean up on 8.1 before upgrading

| # | Story | Acceptance |
|---|---|---|
| M1.1 | Remove **duplicate usernames** in Internal and AD/Internal Hybrid user sources (Manage Users page). 8.3 does not allow them; since 8.3.4 the migration skips and logs such sources instead of breaking them | Zero duplicates per user source |
| M1.2 **(security)** | Document every **Identity Provider** setting: 8.1 IdP JSON exports cannot be imported into 8.3, so IdPs are re-created | IdP settings captured for rebuild |
| M1.3 | Resolve **Store and Forward quarantine** on 8.1. 8.3 quarantine exports are JSON, and 8.1 XML exports cannot be imported. Leftover data remains an HSQL file to be moved to `data/local/store-forward/quarantined-databases/` | Quarantine empty or exported and accounted for |
| M1.4 | Audit **tag path lengths**: 8.3 stores tag JSON by Tag Browser path under `data/config/resources/core/ignition/tag-definition`, and Windows limits paths to 255 characters | Long paths listed and shortened, or Gateway moved to a short install path |
| M1.5 **(security)** | Record **Gateway permissions and roles**: 8.1 Gateway permissions are not carried over and must be reassigned; some setting names changed | Permission matrix ready for re-entry |
| M1.6 | Replace any use of the **EAM Agent Recovery** task (removed in 8.3) in runbooks with other agent tasks. The EAM Remote Upgrade task cannot take agents from 8.1 to 8.3 on Apple M-series Macs; upgrade those in place | Runbooks updated |
| M1.7 **(alarm)** | Check **VOIP call scripts** for locales that collapse to the same language tag (for example `nn_NO_NY` and `nn_NO` both become `nn-NO`); one of a colliding pair fails to migrate | Colliding call scripts merged or renamed |
| M1.8 | Inventory Gateway and client event scripts; they migrate to `.py` files and some may be renamed to meet naming rules, which can break references | Script list with owners |

## Phase 2: Upgrade order

| # | Story | Acceptance |
|---|---|---|
| M2.1 | **Upgrade the central storage Gateway first.** 8.3 uses Protobuf instead of Java serialization and cannot store data to an 8.1 Gateway (Edge Sync Services, remote history providers, remote alarm journals, remote audit profiles) | Central Gateway on 8.3 and verified before any remote or Edge Gateway |
| M2.2 | Then upgrade remote and Edge Gateways that store to it | Store and Forward drained, no quarantine growth |
| M2.3 | Keep **Allow Java Serialization** enabled while any 8.1 Gateway remains on the Gateway Network (8.3 enables it automatically on upgrade or restore) | Setting reviewed; removal planned for when the last 8.1 Gateway is gone |
| M2.4 | **Redundant pairs:** follow IA's "Upgrading a Redundant Pair" procedure. If the backup is a new install, set its Require Two-Way Authentication to match the master | Pair reconnected and synced |
| M2.5 | Roll out **8.3 launchers and Perspective Workstation** first: 8.3 launchers work with 8.1 Gateways, 8.1 launchers do not work with 8.3 | Every client machine on 8.3 launchers before cut-over |
| M2.6 | Schedule restarts for module work: **module hot swapping is gone**, installing or upgrading a module needs a Gateway restart | Maintenance windows booked |
| M2.7 | **Containers:** add the MariaDB, MSSQL and PostgreSQL **JDBC driver modules** to `GATEWAY_MODULES_ENABLED` by their new module identifiers | DB connections Valid after start-up |
| M2.8 | Confirm browsers meet the 8.3 Perspective minimum versions | Browser check signed off |

## Phase 3: Post-upgrade configuration

| # | Story | Acceptance |
|---|---|---|
| M3.1 **(security)** | **Gateway Network:** Require Two-Way Authentication defaults to true on new installs. Approve certificates on the Outgoing Connections page and connections on the Incoming Connections page, on both ends | All connections Running |
| M3.2 **(security)** | Re-assign **Gateway permissions** (M1.5). Service security now lives in Security Zones (Manage Policy) | Permission matrix applied and tested per role |
| M3.3 **(security)** | Re-create **Identity Providers** (M1.2) and test logins | IdP logins pass |
| M3.4 **(security)** | **OPC UA:** trust the newly generated client and server certificates on third-party servers and clients. Anonymous OPC UA clients now get browse and read only (and anonymous access is off by default on new servers); restore write/call only through explicit role mappings, and only with approval | Anonymous and authenticated clients tested for browse, read, write, call |
| M3.5 | Open each project in the Designer to finish migrating Gateway and client event scripts; fix references broken by renames | No migration icons left |
| M3.6 | **Store and Forward:** the primary store maintenance value (8.1 "Max Records") is set to 0 (unlimited) on upgrade; size disk and set a limit if needed | Limit decided and applied |
| M3.7 **(alarm)** | **Alarm Metrics:** the Tag Browser Alarms folder is replaced by Alarm Metrics. Old scripts and bindings still work; plan moving them to Alarm Metrics | Binding list and migration plan reviewed by engineering |
| M3.8 | **Audit tables:** new 8.3 installs use lowercase audit table and column names (`audit_events`, `audit_events_id`). Upgraded Gateways keep their existing names. Fix queries and reports that hard-code case when a new 8.3 Gateway reads an 8.1 audit database | Audit reports run on 8.3 |
| M3.9 | **Historian:** confirm on the upgraded dev Gateway which historian type each migrated provider became and that the license covers it; decide whether new history goes to Core Historian or SQL Historian | Historian table updated in the architecture doc |
| M3.10 | Perspective File Upload now rejects files over 20 MB regardless of `fileSizeLimit` (raise `max-file-size` in `web.xml` if needed) | Upload use cases tested |
| M3.11 | Put `data/config` and `data/projects` under version control using IA's version control guide; the old internal config DB is no longer used | Repo, `.gitignore`, and scan workflow in place |

## Phase 4: Code migration (findings, not blockers)

Deprecated functions still work in 8.3 but new and touched code moves to the replacements:

| Deprecated | Replacement |
|---|---|
| `system.db.runNamedQuery` | `system.db.execQuery` / `execUpdate` / `execScalar` |
| `system.db.runQuery`, `runScalarQuery`, `runUpdateQuery` | Named queries via `exec*`, or `runPrepQuery` / `runScalarPrepQuery` / `runPrepUpdate` when SQL must be built at runtime |
| `system.tag.queryTagHistory`, `queryTagCalculations`, `storeTagHistory`, `browseHistoricalTags` | `system.historian.queryRawPoints`, `queryAggregatedPoints`, `storeDataPoints`, `browse` |
| `system.net.http*` | `system.net.httpClient` |

## Test and sign-off

- Upgrade rehearsal on dev/test with a restored production backup.
- Regression pass on every Perspective project with live tags.
- Alarm path test (tag alarm, pipeline, notification, acknowledgement) with engineering sign-off **(alarm)**.
- History continuity check across the upgrade window.
- Rollback plan: 8.1 Gateway backups plus the documented restore steps.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide
- https://www.docs.inductiveautomation.com/docs/8.3/system-architectures/hub-and-spoke-architecture
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execQuery
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-historian
