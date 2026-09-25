# ISA Standards Reference for Ignition Projects

Applies to: Ignition 8.3.x

Quick reference for the four ISA standards that govern professional Ignition SCADA/MES development.

---

## ISA-101: High Performance HMI

Governs how operator interface screens should look and behave to reduce cognitive load and improve abnormal situation management.

### Core Principles

**Gray backgrounds, color for abnormal only**
- Background: neutral gray (`#808080` to `#888888` range)
- Normal state: monochromatic - no green for running, no color for healthy
- Abnormal state: red for critical, yellow/amber for warning
- Never use color to mean "good" - its absence of alarm is the signal

**Information density**
- Display only what operators need for the current task
- Remove decorative elements: 3D effects, photorealistic graphics, animations, gradients
- Prefer analog representations (bar graphs, linear scales, sparklines) over raw numbers
- Operators recognize pattern deviations faster from analog shapes

**Visual hierarchy**
- Place critical information (alarms, key process values) in the upper-left quadrant
- Use size, position, and contrast to establish importance - not color
- Consistent placement across all screens

**Navigation**
- Hierarchy-based navigation matching equipment structure (Site → Area → Equipment)
- Role-appropriate access (operator, supervisor, engineer)
- Consistent navigation elements on every screen - operators should never feel "lost"

**Alarm visualization**
- Persistent alarm banner visible on all screens
- Include: priority, timestamp, equipment context, acknowledgment status
- High contrast against gray background
- Blinking only for unacknowledged Critical alarms

**Screen types**
| Type | Purpose |
|---|---|
| Site Overview | Multi-area status summary |
| Area Overview | Single area equipment status |
| Equipment Detail | Individual equipment control and monitoring |
| Alarm Summary | Active alarm list with acknowledgment |
| Trend Display | Historical data visualization |

---

## ISA-95: Enterprise-Control System Integration

Defines the equipment hierarchy and data model for manufacturing operations. The standard model for organizing Ignition tag structures.

### Equipment Hierarchy (6 Levels)

```
Level 4-5: Enterprise / Business Systems (ERP)
Level 3:   Site / MES
Level 2:   Area (SCADA)
           └─ Line
              └─ Cell
                 └─ Equipment Module
                    └─ Control Module (Level 1)
```

### Mapping to Ignition

| ISA-95 Level | Ignition Tag Folder | Example |
|---|---|---|
| Site | Top-level tag folder | `[default]DairyPlant/` |
| Area | Second level | `[default]DairyPlant/Refrigeration/` |
| Line | Third level | `[default]DairyPlant/Refrigeration/CoolingLoop1/` |
| Cell | Fourth level | `[default]DairyPlant/Refrigeration/CoolingLoop1/CompressorBank/` |
| Equipment Module | UDT instance | `[default].../CompressorBank/Compressor1` |

**Tag path format:**
```
[default]Site/Area/Line/Cell/Equipment/Tag
```

### Why This Structure Matters

- Area-based alarm filtering: alarm pipelines route by `Area` folder
- Production reports aggregate by hierarchy level
- Navigation in Perspective mirrors plant organization
- Database-driven instantiation: add equipment by inserting rows in Equipment table

### Database Integration

ISA-95 hierarchy should also live in SQL for cross-system consistency:

```sql
Equipment (
    equipment_id,
    equipment_name,
    equipment_type,     -- maps to UDT definition name
    parent_id,          -- self-referential hierarchy
    isa95_level,        -- 'Site', 'Area', 'Line', 'Cell', 'EquipmentModule'
    area,
    line,
    cell
)
```

---

## ISA-18.2: Alarm Management

Governs alarm system design, rationalization, and performance measurement for industrial control systems.

### Alarm Priority Levels

Ignition alarm priorities are **Diagnostic, Low, Medium, High, Critical** (JSON values are the names). Map the rationalized scheme onto them by name, not by number:

| Ignition priority | Response requirement | Visual |
|---|---|---|
| Critical | Immediate - safety impact | Red, blinking |
| High | Urgent - within minutes | Red |
| Medium | Within shift | Yellow |
| Low | Awareness only | Yellow/cyan |
| Diagnostic | Not presented to operators (maintenance / system events) | Not shown on operator displays |

### Alarm States

```
[Process fault occurs] → Active (Unacknowledged)
                              ↓ operator sees it
                         Active (Acknowledged)
                              ↓ fault clears
                         Cleared (Acknowledged)
                              ↓ logged
                         [Return to normal]

Also: Suppressed (intentionally hidden during known conditions)
```

All state transitions must be logged for compliance.

### Performance Targets

- Target: **~6 alarms per operator per hour** during normal operations (ISA-18.2 recommended maximum)
- Flood threshold: >10 alarms in 10 minutes
- Each alarm needs rationalization: consequence, required response, response time

### Ignition-Specific Configuration

**Deadband:** Configure on analog alarms to prevent nuisance alarms from signal noise
- Set as percentage of setpoint or absolute value
- Example: temperature alarm at 80°C with 2°C deadband - re-arms only when temp drops below 78°C

**Shelving:** Temporary suppression during known conditions (maintenance, startup)
- Must be time-limited (set maximum duration per project policy)
- Must be logged with authorization level
- Used for: equipment in maintenance mode, known transient conditions during startup

**Shelving allowed:** set per alarm with the `shelvingAllowed` property; disable it on alarms that must never be shelved.

**Alarm modes:** 8.3 adds `WhenTrue` / `WhenFalse` for Boolean (or non-zero integer) tags alongside `AboveValue`, `BelowValue`, `Bit` and the other modes.

**Alarm Metrics:** per-priority counts such as `ActiveCountCritical` and `HasActiveUnackedHigh` live in the Alarm Metrics tag folder, which replaces the deprecated Alarms folder. Bind alarm summary indicators to these.

**Engineering review:** every alarm priority, setpoint, mode, shelving or pipeline change is flagged for human engineering review; priority and interlock changes need MOC.

**Alarm rationalization:** Every configured alarm should have documented:
- Consequence if unacknowledged
- Required operator response
- Response time requirement
- Priority justification

---

## ISA-88: Batch Control

Applies to: food & beverage, pharmaceuticals, specialty chemicals, cosmetics. Does NOT apply to continuous processes (oil refinery, power generation, water treatment).

### Procedural Model

```
Recipe          - product definition (what to make)
  └─ Procedure  - overall sequence (how to make it)
       └─ Unit Procedure  - operations on a single unit
            └─ Operation  - major processing action (fill, heat, mix)
                 └─ Phase - discrete step with defined states
```

### Equipment Model

```
Process Cell        - batch execution boundary
  └─ Unit           - major equipment (reactor, tank)
       └─ Equipment Module - physical equipment (agitator, jacket)
            └─ Control Module - device (valve, motor, sensor)
```

Maps to UDT hierarchy - design UDT inheritance to reflect this structure.

### Phase State Machine

Phases follow a defined state machine:

```
                    ┌──── Pausing ───→ Paused
                    │
Idle → Running ─────┼──── Holding ───→ Held
                    │
                    ├──── Stopping ──→ Stopped
                    │
                    ├──── Aborting ──→ Aborted
                    │
                    └──── Complete
```

Implement state transitions in Jython with `system.tag.writeBlocking(tagPaths, values, [timeout])` (or `system.tag.writeAsync`), wrapped in `try` / `except java.lang.Throwable` / `except Exception`, and check the returned quality codes.

### Recipe Types

| Type | Description |
|---|---|
| Master Recipe | Product template (defines the product) |
| Control Recipe | Runtime copy (specific batch execution) |
| Batch Record | Execution history (for compliance/QA) |

---

## IEC 62443: OT Cybersecurity

Framework for securing industrial automation and control systems.

### Network Zones and Conduits

| Zone | Level | Examples |
|---|---|---|
| Enterprise Network | Level 4-5 | ERP, email, corporate IT |
| DMZ | Level 3.5 | Ignition Gateway, historian |
| Control Network | Level 2 | SCADA, HMI stations |
| Field Network | Level 1 | PLCs, controllers |
| Safety Network | Level 0 | SIS, safety PLCs (isolated) |

**Conduits** = defined communication paths between zones with controlled protocols and monitoring.

### Ignition in the Architecture

Ignition Gateway typically lives in the **DMZ (Level 3.5)**:
- OPC-UA connections down to Level 1/2 control network
- Web/client connections up to Level 4-5 business network
- Gateway Network connections to other Gateways

**Do not** create direct connections between the OT zone and business network without explicit DMZ routing.

### Safety Instrumented System (SIS) Boundary

SIS systems (emergency shutdowns, safety interlocks) are:
- On an isolated network
- Not controlled by SCADA
- Not modified by AI tools or general development processes
- Subject to SIL (Safety Integrity Level) certification

Any design touching SIS scope requires certified safety engineer review and Management of Change (MOC) documentation.

---

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/platform/tags/tag-properties/tag-alarm-properties
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-tag/system-tag-writeBlocking
- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide

ISA-101, ISA-95, ISA-18.2, ISA-88 and IEC 62443 content summarizes the standards themselves, not IA documentation.
