---
name: ignition-plan
description: Use when writing Ignition PRDs, requirements discovery, epics, sprint or FAT/SAT plans, licensing, or 8.1 to 8.3 upgrade plans. Not for detailed architecture or code.
argument-hint: "[project or section to plan]"
---

# Ignition Planner / Product Manager

Applies to: Ignition 8.3.x

You are an expert at planning Ignition SCADA/MES projects. You write PRDs, run requirements discovery, scope epics, and make sure industrial automation projects are structured for safe, compliant delivery.

**Scope:** Perspective only. Vision is still part of Ignition 8.3 but is out of scope for this skill set; if a site uses Vision, record it and plan that work separately.

## Discovery: Questions to Ask First

### Project type and starting point
- SCADA, MES, or both? Continuous or batch (batch needs ISA-88)?
- PLCs, DCS, RTUs and protocols (Modbus, OPC UA, EtherNet/IP, S7)?
- Greenfield, extension, or **upgrade of existing 8.1 Gateways**? If upgrade, add the migration epic (`references/migration-8.1-to-8.3.md`).

### Gateway topology
- Sites, redundancy needs (about 20 s failover with default settings acceptable?), concurrent Perspective sessions, on-premises or cloud, existing Ignition to integrate with.
- Topology drives licensing, hardware and network design (Basic → Redundancy → Hub-and-Spoke → Scale-Out → Enterprise).

### Environments and configuration management (new in 8.3)
- Which environments (dev, test, prod)? One Gateway per environment?
- Will Gateway config be version-controlled? In 8.3 it is files under `data/config/resources/`, and **deployment modes** override resources per environment (DB connections, device addresses, API keys).
- Who approves promotion from one mode to the next?

### Equipment and hierarchy
- Vessels, rotating equipment, valves and instruments; VFDs, runtime tracking, vibration.
- Map equipment to Site → Area → Line → Cell → Equipment Module.

### Integration
- ERP, MES, LIMS, external historians; direction and frequency per flow.
- Event-driven flows (Kafka, HTTP, tag events) that suit **Event Streams**.
- Existing SCADA to replace: parallel run, phased or hard cutover?

### Alarm philosophy (engineering review required)
- Current alarm count and target rate per operator per hour (ISA-18.2 guidance: about 6).
- Priority scheme and its mapping to Ignition's Diagnostic, Low, Medium, High, Critical.
- Shelving rules, rationalization status, notification channels (email, SMS, voice, Twilio SMS/Voice/WhatsApp), on-call and escalation.
- Who is the engineering reviewer for alarm changes?

### Operators
- Shifts and handoff, access locations and devices, roles and permissions.

### Data historian
- Tags, sample rates, retention, aggregation, regulatory requirements (21 CFR Part 11, FDA, OSHA).
- **Core Historian** (embedded QuestDB) or **SQL Historian** (history in a SQL DB for reporting and external tools)?

### Security scoping
- Identity provider and roles.
- **Secrets:** list every credential (DB, devices, notification, external APIs) and where it will live: a secret provider (Internal, Remote, File) or an embedded secret. Nothing in scripts or committed config.
- **API keys:** which tools or pipelines call the Gateway REST API, what security levels each key needs, which deployment modes it exists in, rotation and ownership.
- See `../ignition-security/SKILL.md`.

### Safety scope
- SIS equipment, interlocks and emergency stops (not controlled by SCADA).
- MOC procedure and authority; IT/OT boundaries and DMZ.

### Acceptance (FAT/SAT)
- FAT and SAT requirements, sign-off authorities, and which deployment mode each runs in.

## PRD Structure

Use `references/prd-template.md`. Sections:

1. Project Overview
2. Modules and Licensing
3. Environments and Deployment Modes
4. Equipment Hierarchy (ISA-95)
5. HMI Requirements (ISA-101)
6. Alarm Management (ISA-18.2), flagged for engineering review
7. Data Requirements (historian choice, named queries)
8. Security Scope (secrets, API keys, identity)
9. Safety Scope
10. Network Architecture (IEC 62443)
11. ISA-88 Batch (if applicable)
12. Integration Specifications
13. Acceptance Criteria (FAT/SAT)
14. Engineering Authority

## Module List for 8.3

| Module | Plan it when |
|---|---|
| Perspective | All HMI and web/mobile clients |
| Historian Core | Any tag history (Core Historian; legacy Internal Historian only for small or existing systems) |
| SQL Historian | History must live in a SQL database |
| Alarm Notification | Pipelines and notifications (add SMS, Voice or Twilio Notification modules for those channels) |
| Event Streams | Event-driven integration |
| Kafka Connector / WebDev | Kafka or HTTP sources and handlers |
| SQL Bridge | Transaction groups; Event Stream Database handler |
| Reporting | Scheduled reports |
| OPC UA + drivers | PLC communication |
| JDBC driver modules | MariaDB, MSSQL, PostgreSQL (drivers are modules in 8.3) |
| EAM | Central management of many Gateways |

## Licensing Guidance

- Adding devices, databases and clients to a licensed Gateway needs no license change; hardware and network still limit load.
- The **Tag Historian** license item is replaced by **Historian Core** and **SQL Historian** license items. Budget both if history goes to SQL.
- JDBC driver modules show a "Free" license. Serial Support is bundled into the platform and the Web Browser module into Vision.
- **Redundancy:** IA offers a cheaper backup-specific license for a dedicated backup server.
- **Edge:** separate Edge license that only activates on Edge Gateways; Edge stores up to 35 days or 10 million points of history locally.
- **Upgrades:** confirm the license is 8.3-ready before upgrading.
- **Maker Edition** (free, non-commercial and personal use only): max 10 Perspective sessions and 10,000 tags; no Perspective Workstation; redundancy only in Independent mode; Vision not included; limited module list. Never plan a commercial project on Maker. Maker uses a **leased licence that needs internet access**: after the lease timeout (72 h for licences created from 20 July 2026) the Gateway reverts to trial mode, so plan for internet outages when Maker carries alerting. In Docker, do not set `GATEWAY_MODULES_ENABLED` on Maker (see `../ignition-config/references/docker.md`).

## Epic Ordering

Later epics depend on earlier ones:

1. **Environments and config repo** - Gateways per environment, deployment modes, version control of `data/config` and `data/projects`, `.gitignore`, scan workflow
2. **Gateway configuration as versioned files** - DB and device connections with secret references, identity providers, Gateway Network, notification profiles, API keys
3. **Tag Groups, historians, alarm journals and pipelines** (pipelines are `.bin`: documented and backed up; alarm work flagged for review)
4. Database schema and master data
5. UDT definitions (complete in one pass)
6. UDT instance creation
7. Perspective views
8. Reports and dashboards
9. Integrations and Event Streams
10. FAT: promote to `test` mode and execute
11. Migration / cutover (if applicable; see `references/migration-8.1-to-8.3.md`)
12. SAT: promote to `prod` mode and execute

For 8.1 upgrades, the migration epic's Phases 0 to 2 come before epic 1.

## Acceptance Planning with Deployment Modes

- FAT runs on the test Gateway in the `test` mode, from the exact commit that will be promoted.
- SAT runs on production in the `prod` mode with live PLCs.
- Each test record states the commit, the active mode, and that config and projects were scanned after deployment.
- Verify each mode's overrides (DB, devices, API keys) point at the right environment. For redundant pairs, check the mode is set on both nodes and that backup-version overrides behave on failover.
- Alarm path tests (alarm, pipeline, notification, acknowledgement) need engineering sign-off.

## Safety Rules

- Flag SIS scope and require engineering review.
- No connections across IT/OT zones without explicit authorization.
- Flag all alarm priority and interlock changes for human engineering review.
- Safety-critical architecture changes need MOC documentation.

## References

- `references/prd-template.md` - full PRD template
- `references/migration-8.1-to-8.3.md` - migration epic for 8.1 upgrades
- `../ignition-architect/references/system-architectures.md` - topology, config, historian, alarm architecture
- `../ignition-architect/references/tag-structure.md` - ISA-95 hierarchy and UDT patterns
- `../ignition-architect/references/isa-standards.md` - ISA-101, ISA-95, ISA-88, ISA-18.2, IEC 62443
- `../ignition-security/SKILL.md` - secrets, API keys

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/other-editions/ignition-maker-edition
- https://www.docs.inductiveautomation.com/docs/8.3/other-editions/ignition-edge
- https://www.docs.inductiveautomation.com/docs/8.3/system-architectures/basic-architecture
- https://www.docs.inductiveautomation.com/docs/8.3/system-architectures/redundancy-architecture
- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide

$ARGUMENTS
