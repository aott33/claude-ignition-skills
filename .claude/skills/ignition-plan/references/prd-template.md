# PRD Template for Ignition Projects

Applies to: Ignition 8.3.x

Every industrial PRD includes these sections. Delete a section only with a written reason ("not applicable: continuous process").

---

## 1. Project Overview

- SCADA vs MES scope; continuous vs batch
- Greenfield, extension, or upgrade from 8.1 (if upgrade, include the migration epic from `migration-8.1-to-8.3.md`)
- Gateway topology (Basic / Redundant / Hub-and-Spoke / Scale-Out / Enterprise / Edge / Cloud)
- Concurrent Perspective session estimate and hardware sizing
- Integration touchpoints
- Scope statement: Perspective only. Vision exists in 8.3 but is out of scope for this skill set; record it if the site uses it

## 2. Modules and Licensing

| Module / item | Needed? | Why |
|---|---|---|
| Perspective | | |
| Historian Core (Core Historian, legacy Internal Historian) | | |
| SQL Historian | | |
| Alarm Notification (+ SMS, Voice or Twilio Notification) | | |
| Event Streams | | |
| Kafka Connector / WebDev | | |
| SQL Bridge | | |
| Reporting | | |
| OPC UA + drivers | | |
| JDBC driver modules (MariaDB, MSSQL, PostgreSQL) | | |
| EAM | | |
| Edge (Panel / IIoT) | | |

Record the edition (Standard, Edge, Maker) and the backup licenses for redundant pairs.

## 3. Environments and Deployment Modes

- Environments: dev, test, prod (one Gateway each, or as agreed)
- Deployment mode names and what each overrides (DB connections, device addresses, API keys)
- What is committed to version control (`external` / `core` / mode folders, projects) and what never is (`local`, certificates, keys)
- Resources that are `.bin` and not diffable (alarm pipelines, transaction groups, client tags, reports): how they are reviewed and backed up
- Promotion path and who approves each promotion

## 4. Equipment Hierarchy (ISA-95)

```
Enterprise → Site → Area → Line → Cell → Equipment Module
```

Major equipment by Area → Line → Cell, naming conventions and UDT definition names. Keep names short (tag JSON paths on Windows are limited to 255 characters).

## 5. HMI Requirements (ISA-101)

- Screen types: Site Overview, Area Overview, Equipment Detail, Alarm Summary, Trends
- Navigation by hierarchy; role-based access
- Neutral gray backgrounds, color for abnormal only; no decorative graphics
- Target devices and resolutions; Perspective App needs (offline mode works only in the mobile Perspective App)

## 6. Alarm Management (ISA-18.2) - engineering review required

- Priority scheme mapped to Ignition priorities (Critical, High, Medium, Low; Diagnostic not shown to operators) with response times
- Target alarm rate per operator per hour
- States and transition logging; alarm journal requirements
- Shelving: which alarms allow it, max duration, authorization, logging
- Rationalization method (consequence, response, response time per alarm)
- Notification: channels (email, SMS, voice, Twilio SMS/Voice/WhatsApp), rosters, escalation, on-call
- Pipelines are `.bin` global resources: document each pipeline in the design
- Named engineering reviewer for every alarm change; MOC for priority and interlock changes

## 7. Data Requirements

- History: tags, sample mode and rate, retention, aggregation, historian (Core Historian vs SQL Historian) per retention class
- Regulatory retention (21 CFR Part 11, FDA, OSHA as applicable)
- Named queries for navigation and reporting (`system.db.execQuery` / `execUpdate` / `execScalar`)
- Reports: production, batch records, shift summaries, compliance
- Integration flows (ERP/MES/LIMS; direction, frequency)

## 8. Security Scope

- Identity provider(s) and role model
- **Secrets:** every credential (DB, devices, notification, external APIs) and where it is stored: secret provider (Internal, Remote, File) or embedded secret. No credential in scripts or committed config
- **API keys:** each automation client (CI, deploy scripts, inspection tools), its security levels, the modes it exists in, rotation, and who holds it. Keys are shown once and stored hashed; mutating calls are audit-logged, reads are not
- Gateway Network trust (two-way authentication), Security Zones
- OPC UA access for anonymous vs authenticated clients
- See `../ignition-security/SKILL.md`

## 9. Safety Scope

- Explicit list of SIS equipment and boundary statement (SCADA does not control SIS)
- Engineering authority for safety-related configuration

## 10. Network Architecture (IEC 62443)

- OT zone (L2), DMZ (L3.5, Gateway), business network (L4-5)
- Every cross-zone conduit listed with explicit authorization

## 11. ISA-88 Batch Requirements (if applicable)

- Procedural and equipment models; recipe management; batch records

## 12. Integration Specifications

- Per integration: source, target, data model, frequency, protocol, error handling
- Event Streams where event-driven (source, filter/transform, handlers, error handler)
- Migration plan if replacing an existing system: parallel run, data migration, cutover

## 13. Acceptance Criteria (FAT / SAT)

- **FAT** on the test environment running the `test` deployment mode, from the tagged commit that will be promoted
- **SAT** on production running the `prod` mode, with live PLCs
- Deployment verification: the promoted commit, config scan and project scan completed, mode confirmed on each node (both nodes of a redundant pair)
- Mode overrides checked: each environment points at its own DB, devices and API keys
- Redundancy failover test, including backup-version overrides
- Performance: screen load time, alarm notification latency, history gap tolerance
- Alarm path test with engineering sign-off
- Sign-off authority per stage

## 14. Engineering Authority

- Configurations requiring MOC
- Certified engineer sign-off requirements
- Regulatory review triggers

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/secrets-management
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/api-keys
- https://www.docs.inductiveautomation.com/docs/8.3/platform/tags/tag-properties/tag-alarm-properties
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/alarm-notification/notification-profile-types
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/perspective-sessions/ignition-perspective-app/offline-mode
- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide
