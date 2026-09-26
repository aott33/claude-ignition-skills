# Ignition System Architectures

Applies to: Ignition 8.3.x

Reference for choosing and designing Ignition Gateway deployments. The Gateway Network is the backbone for every multi-Gateway pattern.

---

## Architecture Decision Guide

| Need | Architecture |
|---|---|
| Single site, simple deployment | Basic |
| Add HA to any architecture | + Redundancy overlay |
| Multiple sites, centralized data | Hub-and-Spoke |
| High concurrent client load | Scale-Out (front-end / back-end split) |
| Many Gateways to manage centrally | Enterprise (EAM) |
| Network edge / IIoT / offline-capable | Edge |
| Reduce on-premise IT overhead | Cloud-Based |
| Security isolation (OT/IT) | Security architecture patterns |
| Separate dev / test / prod configuration | Deployment modes (see "Configuration Architecture") |

Architectures compose: a large enterprise typically combines Hub-and-Spoke + Redundancy + Scale-Out + EAM.

---

## Basic Architecture

**Use when:** single site, straightforward requirements, limited client load.

- One Gateway: PLC comms, tag execution, history, client connections.
- Adding devices, databases and clients to a Gateway needs no licensing change.
- A dual-NIC server can bridge the control network and the corporate network; restrict access by role and network location.
- Starting point; scale out or add spokes when growth demands it.

**Limitation:** single point of failure.

---

## Redundancy Architecture

**Use when:** the system cannot tolerate a Gateway outage.

- Two nodes: a **master** and a **backup**. The master manages configuration and replicates it to the backup, unless a resource has a Backup Version.
- With default settings, failover takes around 20 seconds. Perspective sessions reconnect to the node that is active.
- **Standby activity level:** *Cold* (backup connects to OPC servers but does not subscribe, less load, slower failover) or *Warm* (runs as if active except logging and device writes, faster failover).
- IA offers a cheaper backup-specific license for a dedicated backup server.
- Any Gateway in any pattern can be made a redundant pair. With a load balancer in Scale-Out, add an extra front-end instead of pairing front-ends.
- In the cloud, prefer Ignition redundancy to a cloud instance restart (minutes). Put both nodes on the same side (both cloud or both on site); one internet link is still a single point of failure.
- An Edge Gateway can only fail over to another Edge Gateway.

### Redundancy in 8.3 config

- **Backup Versions:** use "Add Backup Version" on a resource when the backup needs different settings (for example a different OPC UA address). The backup settings are saved in `backupConfig.json` next to `config.json` and apply only when the node role is Backup.
- The **deployment mode** is set in each node's `ignition.conf` and does **not** sync. Set the same `-Dignition.config.mode` on both nodes and restart both, or a failover may bring up different DB or device connections.
- Overrides stored in the **`local`** collection (allowed since 8.3.7) do not carry over to the backup.
- Apply the same root and KEK encryption key files to both nodes, or embedded and Internal-provider secrets encrypted on one node will not decrypt on the other.

---

## Scale-Out Architecture

**Use when:** high concurrent client load, or to isolate device I/O from client load.

| Gateway type | Responsibilities |
|---|---|
| **Back-End** | PLC comms, tag execution, usually history recording; shares tags through Remote Tag Providers |
| **Front-End** | Perspective sessions and reporting; no direct PLC connections |

- Add a back-end when adding PLCs; add a front-end when adding clients. A load balancer spreads sessions across front-ends.
- Both types need DB access: back-ends store, front-ends query. Databases can be clustered.
- A failing front-end does not stop data collection; a failing back-end affects only its part of the plant. Make back-ends redundant.

---

## Hub-and-Spoke Architecture

**Use when:** several sites each need local autonomy plus central aggregation.

| Component | Role |
|---|---|
| **Hub** | Aggregates spoke data, central reporting, enterprise dashboards |
| **Spoke** | Local PLCs, local history, local Perspective sessions for fallback |

- **Store and Forward** buffers spoke data (SQL Bridge or historian) during hub outages.
- **Split history**: log at the spoke and at the hub (Historian Splitter or remote history) to protect against disk loss.
- **Alarm notification at each spoke**, so notifications continue when the hub link is down.
- Hub reads spoke tags through a Remote Tag Provider: `[SpokeAlias]path/to/tag`.
- **8.1 to 8.3 caution:** an 8.3 Gateway cannot store data to an 8.1 Gateway (remote history, remote alarm journals, remote audit profiles, Edge Sync Services). Upgrade the central Gateway first.

---

## Edge Architectures

**Use when:** deploying at the network edge on field or OEM hardware.

- **Edge Panel:** stand-alone local screens next to a PLC; paired with a central Gateway it gives local client fallback.
- **Edge IIoT** (formerly MQTT): an MQTT publisher next to the PLC for a wider IIoT architecture.
- Local storage on any Edge Gateway: up to 35 days or 10 million points of tag history; alarm journal and audit log for 7 days.
- Edge syncs tag history, alarm journal and audit data to a central Gateway over the Gateway Network, buffering with Store and Forward.
- Edge Gateways can be EAM agents of a central controller.
- Edge has one project, and needs an Edge license (a standard license works but is not recommended).

---

## Enterprise Architecture

**Use when:** managing many Gateways centrally.

- **Controller** Gateway runs the Enterprise Administration Module (EAM); other Gateways are **agents**.
- The controller monitors agents, raises alarms on agent problems, stores agent events in SQL, and pushes project resources to agents.
- 8.3 note: the Agent Recovery task was removed; other agent tasks cover similar operations. Some 8.3 resources (Gateway and Perspective event scripts) cannot be sent from an 8.3 controller to an 8.1 agent.
- In 8.3, versioned configuration and deployment modes are an alternative way to keep Gateways consistent; decide which mechanism owns which resources.

---

## Cloud-Based Architecture

**Use when:** reducing on-premise IT burden.

- Gateway and database on separate cloud servers (for example AWS EC2 and a managed SQL service); an Edge Gateway near the PLCs forwards data.
- PLC links via VPN, cellular or dedicated WAN. Design for internet loss; an on-site database for in-progress data is common.
- Follow IA's Security Hardening Guide for any internet-reachable Gateway.

---

## Configuration Architecture (8.3 config as code)

### Where config lives

Gateway configuration is on the filesystem, not in the internal SQLite DB (the old DB file stays after an upgrade but is unused):

```
data/config/resources/system/     built-in, immutable (can be overridden)
data/config/resources/external/   read-only from the Gateway; guard rails the web UI must not change
data/config/resources/core/       default collection and shared base; commit it (minus per-Gateway files)
data/config/resources/<mode>/     one folder per deployment mode
data/config/resources/local/      machine-specific data, not inherited by modes
data/projects/                    projects
```

Inheritance: `system` → `external` → `core` → deployment mode.

### Deployment modes as the promotion model

| Decision | Options |
|---|---|
| Environments | One Gateway per environment, each running its own mode (`dev`, `test`, `prod`) from the same repo |
| What goes in `external` | Read-only guard rails (for example API-key security levels); never resources the Gateway also generates in `core` |
| What goes in `core` | Shared config all environments use: tags, UDTs, historian, connections, themes. Committed to git |
| What goes in each mode | DB connections, device addresses, API keys and other per-environment overrides |
| What stays in `local` | Certificates and host-specific data; never committed |

- Modes are created under Platform > System > Modes; the active mode is chosen only in `ignition.conf` (`wrapper.java.additional.N=-Dignition.config.mode=<Mode>`) plus a restart.
- Projects, modules, licenses and modes themselves cannot be overridden per mode. Environment differences inside projects must come from Gateway resources.
- **Not JSON:** alarm pipelines, transaction groups, client tags and reports are stored as `.bin`, and IA recommends gitignoring them. Decide how they are reviewed (design documents) and protected (Gateway backups).
- After a `git pull`: `POST /data/api/v1/scan/config` (or the Scan File System button on Platform > System > Modes) for config, and a project scan for projects. `system.project.requestScan([timeout])` covers projects only.

See `../../ignition-config/SKILL.md` and `../../ignition-deploy/SKILL.md`.

---

## Tag Groups

Tag Groups set how often tags execute (OPC polling, expression evaluation, query tags). "Scan class" is 7.x wording; do not use it.

| Mode | Behaviour |
|---|---|
| **Direct** | One fixed rate in ms. The default Tag Group uses this mode |
| **Driven** | Runs at the Rate or the Leased/Driven Rate depending on a driving expression; One Shot runs once per false-to-true transition |
| **Leased** | Tags shown on an open view run at the Leased/Driven Rate; others run at the Rate. Viewing in the Tag Browser does not lease |

**Design rules:**
- Do not assign everything to one group; excessive polling loads the PLC, OPC server and Gateway.
- Match rate to process dynamics, not operator preference.
- History sampling (On Change, Periodic, or a Historical Tag Group) is separate from the Tag Group. A Historical Tag Group should be the same speed as or slower than the tag's Tag Group.

---

## Historian Architecture

| Option | Module | Notes |
|---|---|---|
| **Core Historian** | Historian Core | Embedded QuestDB: partitioning, dedup, archiving, native aggregation. Store and Forward is used only when there are pending writes to the database; with none pending, the Core Historian skips it entirely (IA 8.1 to 8.3 upgrade guide). Default memory 10% of system RAM. Prefer the Discrete deadband style, or deadband off with Periodic sampling, to avoid costly out-of-order writes |
| **Internal Historian (Legacy)** | Historian Core | SQLite; for small or existing systems. Supports pruning and remote sync |
| **SQL Historian** | SQL Historian | History in a SQL DB; partitioning and pruning per historian. Suits reporting, external tools, long retention |
| **Remote Historian** | Historian Core | Reads or stores to a history provider on another Gateway over the Gateway Network |
| **Historian Splitter** | Historian Core | Writes to two providers at once (redundancy, migration, archive) |
| **DB Table Historian** | Historian Core | Read-only access to existing SQL history tables |

- The Tag Historian license item is replaced by the **Historian Core** and **SQL Historian** license items.
- Retention is set per historian, so group tags with different retention needs into different historians.
- External tools should read Core Historian data through Ignition (for example `system.historian.queryRawPoints` behind a WebDev endpoint) rather than querying storage directly.
- Scripts use `system.historian.*`; the `system.tag` history functions are deprecated.

---

## Integration Architecture: Event Streams

Event Streams are project resources that move event data through stages: **Source → Encoder → Filter → Transform → (second Encoder) → Buffer → Handler(s) → Error Handler**. Filter and Transform are optional scripts; the second Encoder follows Transform when transforms are enabled.

| Sources | Handlers |
|---|---|
| Kafka (Kafka Connector module) | Kafka (Kafka Connector module) |
| HTTP Endpoint (WebDev) | Database (SQL Bridge) |
| Event Listener | HTTP (WebDev) |
| Tag Event | Gateway Event |
| | Gateway Message |
| | Logger |
| | Script |
| | Tag |

- MQTT and Sparkplug are not built-in Event Stream sources; use MQTT modules or tags for those.

### MQTT ingest (plain JSON, non-Sparkplug)

- **MQTT Engine:** Cirrus Link MQTT Engine (8.3 builds v5.x) connects to third-party brokers. Its **Custom Namespaces** turn plain JSON topics (for example from Zigbee2MQTT or ESPHome) into tags. It also adds MQTT and Sparkplug Event Stream sources. IA lists Cirrus Link modules as supported on Maker Edition.
- **Enforce read-only at the broker too:** give Ignition's MQTT user a role that can only SUBSCRIBE to sensor topics. With the HiveMQ File RBAC extension, a publish by that user to a device command topic (for example `zigbee2mqtt/+/set`) was dropped and the connection closed. The command never reached subscribers (tested with HiveMQ CE 2026.5). This backs up a "monitoring only" scope independently of Ignition permissions.
- **Key device publish rights to `${{username}}`, not `${{clientid}}`** (HiveMQ File RBAC). A rule on the client ID let a device user connect with another client ID and publish under another device's prefix; keyed to the username it could not (tested with HiveMQ CE 2026.5).
- **MQTT Engine with a custom namespace only:** disable the Default namespace's Sparkplug B. Otherwise Engine subscribes to `spBv1.0/#`; a broker that denies that drops the connection, and Engine does not reconnect (Cirrus docs and forum; not yet tested live).
- **HiveMQ CE:** the Docker image allows anonymous clients (allow-all extension) unless `HIVEMQ_ALLOW_ALL_CLIENTS` is set to anything but `true`. The entrypoint then deletes the extension (verified in the 2026.5 image).
- An alarm pipeline's **Event Stream Source** block feeds an Event Stream with an Event Listener source (alarm-related; engineering review).
- Handlers run in order; the Buffer can batch events and has a max queue size (0 = unlimited).

---

## Alarm Architecture (engineering review required)

All alarm design changes need human engineering review; priority and interlock changes need MOC.

- **Priorities:** Diagnostic, Low, Medium, High, Critical.
- **Pipelines** are global resources (created under the Global node in the Designer), stored as `.bin`. Each needs at least one notification profile and roster on the Gateway first.
- **Notification profiles** (Alarm Notification module): Email, Simple One-Way Email, SMS (SMS module), Voice (Voice module), and Twilio SMS, Twilio Voice and Twilio WhatsApp (Twilio Notification module). Roster contact details must match the address a notification is sent to for acknowledgement to work.
- **Alarm journals** are part of the filesystem-based config (8.3.0).
- **Alarm Metrics** tag folder replaces the Alarms folder (old folder deprecated, still works).
- **Hub-and-Spoke:** notify from each spoke.

---

## Credentials and Secrets

- Secret fields are **None**, **Embedded** (encrypted with the Gateway's keys) or **Referenced** (from a secret provider).
- Providers: **Internal**; **Remote** (8.3.3, reads a provider on another Gateway over the Gateway Network; access defaults to deny in the Security Zone policy); **File** (8.3.5, reads cleartext or JWE files, useful with Kubernetes-mounted secrets).
- Use Referenced secrets for DB, device and notification credentials so committed config holds no secret values. Details: `../../ignition-security/SKILL.md`.

---

## Security Architecture Patterns

**Framework alignment:** IEC 62443, NIST CSF, Zero Trust as the regulatory environment requires.

| Service type | Gateways | Characteristics |
|---|---|---|
| **Stateless (user-facing)** | Front-ends for Perspective, Reporting | Load-balanced, identically configured |
| **Stateful (machine-facing)** | I/O Gateways with PLCs, historians, databases | Segmented from internet/user access |

### Network Zone Model (IEC 62443)

```
Level 4-5: Enterprise network (ERP, corporate IT)
           ↕ Firewall / DMZ
Level 3.5: DMZ - Ignition Gateway, historian
           ↕ Firewall
Level 2:   Control network - SCADA clients, HMI stations
           ↕ Firewall
Level 1:   Field network - PLCs, controllers
Level 0:   Safety network - SIS (isolated, no SCADA connection)
```

- OPC UA goes down to Level 1/2; web clients come up from Level 4-5.
- **Never** connect OT and business networks directly; route through the DMZ, and only with explicit authorization.
- 8.3 OPC UA: anonymous clients get browse and read only by default; write and call need authenticated users or explicit role mappings. Anonymous access to Ignition's OPC UA server is itself off by default ("Anonymous Access Allowed" = false).

### SIS Boundary

- SIS is on an isolated network; SCADA reads status at most and never controls it.
- Any design touching SIS: certified safety engineer review + MOC documentation.

---

## Gateway Network

- Configured under **Network > Gateway Network** (Settings and Connections tabs).
- Used for Remote Tag Providers, remote history, remote alarm journals, EAM, Remote secret providers.
- **Require Two-Way Authentication** is true by default for new installs: both ends must trust each other's certificates. Approve connections on the Incoming Connections tab.
- 8.3 uses Protobuf instead of Java serialization. **Allow Java Serialization** must stay enabled while 8.1 Gateways are on the network. 8.3 Gateways talk only to 8.1 or 8.3 Gateways.

---

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/system-architectures
- https://www.docs.inductiveautomation.com/docs/8.3/system-architectures/basic-architecture
- https://www.docs.inductiveautomation.com/docs/8.3/system-architectures/redundancy-architecture
- https://www.docs.inductiveautomation.com/docs/8.3/system-architectures/scale-out-architecture
- https://www.docs.inductiveautomation.com/docs/8.3/system-architectures/hub-and-spoke-architecture
- https://www.docs.inductiveautomation.com/docs/8.3/system-architectures/edge-architectures
- https://www.docs.inductiveautomation.com/docs/8.3/system-architectures/enterprise-architecture
- https://www.docs.inductiveautomation.com/docs/8.3/system-architectures/cloud-based-architecture
- https://www.docs.inductiveautomation.com/docs/8.3/other-editions/ignition-edge
- https://www.docs.inductiveautomation.com/docs/8.3/platform/ignition-redundancy
- https://www.docs.inductiveautomation.com/docs/8.3/platform/ignition-redundancy/setting-up-redundancy
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/gateway-folder-structure
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-project/system-project-requestScan
- https://www.docs.inductiveautomation.com/docs/8.3/platform/tags/tag-groups
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/tag-historian/configuring-tag-history
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/tag-historian/tag-history-providers
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/tag-historian/tag-history-providers/internal-historian-questdb
- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/modules-overview/core-modules/sql-historian-module
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/ignition-historian-guide
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/event-streams
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/event-streams/types-of-sources
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/event-streams/types-of-handlers
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/alarm-notification/alarm-notification-pipelines
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/alarm-notification/alarm-notification-pipelines/pipeline-blocks
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/alarm-notification/notification-profile-types
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/secrets-management
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway-network
- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide
- https://inductiveautomation.com/downloads/releasenotes/8.3.0
