# Tag Structure, UDT Patterns, and ISA-95 Hierarchy

## Tag Path Format

```
[provider]path/to/tag
```

- **Default provider:** `[default]`
- **OPC-UA provider:** `[OPC-UA]ns=1;s=[Device]Path/Tag`
- **Remote provider (Gateway Network):** `[GatewayAlias]path/to/tag`

### Examples

```
[default]DairyPlant/Refrigeration/CoolingLoop1/Compressor1/Status
[default]DairyPlant/Pasteurization/HeatExchanger1/InletTemp
[OPC-UA]ns=1;s=[DairyPLC]Refrigeration/accumulatorLevel
```

## ISA-95 Folder Structure

Organize tag folders to match the six-level ISA-95 equipment hierarchy:

```
[default]
└─ {Site}/                          e.g. DairyPlant
   └─ {Area}/                       e.g. Refrigeration
      └─ {Line}/                    e.g. CoolingLoop1
         └─ {Cell}/                 e.g. CompressorBank
            └─ {Equipment}/         e.g. Compressor1  (UDT instance)
               ├─ Status            (from UDT)
               ├─ RunHours          (from UDT)
               ├─ SuctionPressure   (from UDT)
               └─ DischargePressure (from UDT)
```

### Why This Structure

- **Alarm filtering:** pipeline routes alarms by Area or Line folder
- **Production reports:** aggregate data by hierarchy level
- **Navigation:** Perspective menu tree mirrors plant organization
- **Database sync:** Equipment table rows map 1:1 to tag folder paths

## UDT Definition Patterns

### Naming Conventions

| Type | Convention | Example |
|---|---|---|
| UDT Definition | `PascalCase` | `Compressor`, `CentrifugalPump`, `ConveyorSection` |
| UDT Instance | Descriptive | `compressor1`, `mainFeedPump`, `refrigerationCompA` |
| UDT Folder | Match ISA-95 level | `Refrigeration/CoolingLoop1/` |

### UDT Parameter Binding Pattern

UDT definitions use parameters (curly brace syntax) resolved at instance creation:

```
Definition parameter: {BasePath}
OPC binding in definition: ns=1;s=[DairyPLC]{BasePath}/Status

Instance creation:
  BasePath = "Refrigeration/Compressor1"
  Resolves to: ns=1;s=[DairyPLC]Refrigeration/Compressor1/Status
```

**Standard parameters to define:**

| Parameter | Purpose | Example value |
|---|---|---|
| `BasePath` | OPC path root | `Refrigeration/Compressor1` |
| `EquipmentName` | Human-readable name | `Compressor 1` |
| `PLCPath` | PLC device path | `[DairyPLC]` |
| `HistorianEnabled` | Enable history logging | `true` |
| `AreaPath` | ISA-95 area for tag path | `DairyPlant/Refrigeration` |

### UDT Inheritance Hierarchy

```
EquipmentModule (base)
├─ status (Bool)
├─ alarmEnable (Bool)
├─ maintenanceMode (Bool)
└─ description (String)

  └─ Motor (extends EquipmentModule)
     ├─ runCommand (Bool)
     ├─ runFeedback (Bool)
     ├─ fault (Bool)
     ├─ speed (Float) — if VFD
     └─ runHours (Float)

       └─ Pump (extends Motor)
          ├─ flowRate (Float)
          ├─ inletPressure (Float)
          └─ outletPressure (Float)

  └─ Tank (extends EquipmentModule)
     ├─ level (Float)
     ├─ levelPercent (Float)
     ├─ temperature (Float)
     ├─ pressure (Float)
     └─ volume (Float)
```

**Rules:**
- Use `extends` for shared behavior (all motors have run/stop)
- Use composition (nested UDTs) for equipment that contains sub-components (skid contains motors + valves)
- **Define UDTs complete in one pass** — alarms, OPC bindings, historian config, all parameters — modifying after instances exist causes propagation issues

### Alarm Configuration in UDTs (ISA-18.2)

Each alarm tag in a UDT definition should include:

```json
{
  "name": "HighTemp",
  "dataType": "Boolean",
  "alarm": {
    "priority": 2,
    "displayPath": "{EquipmentName}/High Temperature",
    "label": "High Temperature",
    "setpointA": 85.0,
    "deadband": 2.0,
    "ackMode": "Auto",
    "notes": "Response: check cooling water flow. Response time: 5 min."
  }
}
```

Priority values: `1` = Critical, `2` = High, `3` = Medium, `4` = Low

## Database-Driven Instantiation

The ISA-95 hierarchy should live in a SQL database, not just in Ignition tag folders. This enables:
- Add equipment by inserting a row (no Designer needed)
- ERP/MES/SCADA share the same equipment model
- Database-driven Perspective navigation (equipment lists, drill-down)

### Core Schema

```sql
CREATE TABLE Equipment (
    equipment_id    INT PRIMARY KEY,
    equipment_name  VARCHAR(100) NOT NULL,
    equipment_type  VARCHAR(50),          -- maps to UDT definition name
    parent_id       INT REFERENCES Equipment(equipment_id),
    isa95_level     VARCHAR(20),          -- 'Site','Area','Line','Cell','EquipmentModule'
    site            VARCHAR(50),
    area            VARCHAR(50),
    line            VARCHAR(50),
    cell            VARCHAR(50),
    tag_base_path   VARCHAR(200),         -- e.g. DairyPlant/Refrigeration/CoolingLoop1/Compressor1
    opc_base_path   VARCHAR(200),         -- e.g. Refrigeration/Compressor1
    active          BOOLEAN DEFAULT TRUE
);

CREATE TABLE EquipmentType (
    type_name       VARCHAR(50) PRIMARY KEY,  -- matches UDT definition name
    udt_type_id     VARCHAR(200),             -- Ignition UDT path
    description     VARCHAR(200)
);
```

### Named Queries for Perspective Navigation

```sql
-- getEquipmentByArea: drives area overview screens
SELECT equipment_id, equipment_name, equipment_type, tag_base_path
FROM Equipment
WHERE area = :area AND active = 1
ORDER BY equipment_name;

-- getEquipmentHierarchy: drives navigation tree
SELECT equipment_id, equipment_name, parent_id, isa95_level
FROM Equipment
WHERE site = :site AND active = 1
ORDER BY isa95_level, equipment_name;
```

### UDT Instantiation Script

Jython script to create UDT instances from database (run as Gateway Event or one-time script):

```python
def instantiateEquipmentUDTs():
    logger = system.util.getLogger('UDTInstantiation')

    results = system.db.runNamedQuery('getAllActiveEquipment', {})

    for row in range(results.rowCount):
        name = results.getValueAt(row, 'equipment_name')
        type_name = results.getValueAt(row, 'equipment_type')
        tag_path = results.getValueAt(row, 'tag_base_path')
        opc_path = results.getValueAt(row, 'opc_base_path')

        tag_config = {
            'name': name,
            'typeId': 'UDTs/%s' % type_name,
            'parameters': {
                'BasePath': opc_path,
                'EquipmentName': name,
            }
        }

        parent_path = '[default]%s' % '/'.join(tag_path.split('/')[:-1])
        system.tag.configure(parent_path, [tag_config], 'o')
        logger.info('Created UDT instance: %s at %s' % (name, parent_path))
```

## OPC-UA Path Format

```
ns=<namespace>;s=[<device>]<path>
```

- `ns=1` is typically the correct namespace for OPC-UA servers
- Device name in square brackets: `[DairyPLC]`
- Path matches PLC address book structure

```
ns=1;s=[DairyPLC]Refrigeration/Compressor1/Status
ns=1;s=[DairyPLC]Pasteurization/HeatExchanger1/InletTemp
```

## Tag Path Verification (Critical)

**Always verify tag paths exist in Gateway before creating Perspective bindings or Jython scripts.**

Unverified paths:
- Cause silent binding failures in Perspective (shows no data, no error)
- Cause runtime exceptions in Jython scripts that are hard to debug
- May not surface until production with live PLC data

Verification steps:
1. Open Ignition Designer → Tag Browser
2. Navigate to the tag path manually
3. Confirm the tag exists and returns a good quality value
4. Then create the binding
