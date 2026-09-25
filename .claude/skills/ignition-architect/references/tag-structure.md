# Tag Structure, UDT Patterns, and ISA-95 Hierarchy

Applies to: Ignition 8.3.x

## Tag Path Format

```
[provider]path/to/tag
```

- **Default provider:** `[default]`
- **Remote provider (Gateway Network):** `[ProviderAlias]path/to/tag`
- OPC addressing is not a tag path. It lives in the tag's `opcServer` and `opcItemPath` properties (see "OPC UA Item Paths").

### Examples

```
[default]DairyPlant/Refrigeration/CoolingLoop1/Compressor1/Status
[default]DairyPlant/Pasteurization/HeatExchanger1/InletTemp
```

## Where Tags Live on Disk (8.3)

Tag configuration is JSON under `data/config/resources/core/ignition/tag-definition` (or the equivalent folder of another collection or deployment mode), stored by the path shown in the Tag Browser. UDT definitions are tag resources too, so tag and UDT changes can be reviewed in a git diff.

- Deep folder trees and long names make long file paths. Windows limits paths to 255 characters, so keep ISA-95 folder names short.
- Import tags from an 8.1 export with care: tag and project imports do not run the upgrade check that a Gateway backup restore does, so imported tags may need manual fixes.

## ISA-95 Folder Structure

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

- **Alarm filtering:** alarm displays and pipelines can filter by Area or Line in the display path or source path
- **Production reports:** aggregate by hierarchy level
- **Navigation:** Perspective menu tree mirrors plant organization
- **Database sync:** Equipment rows map 1:1 to tag folder paths

## UDT Definition Patterns

### Naming Conventions

| Type | Convention | Example |
|---|---|---|
| UDT Definition | `PascalCase` | `Compressor`, `CentrifugalPump`, `ConveyorSection` |
| UDT Instance | Descriptive | `compressor1`, `mainFeedPump`, `refrigerationCompA` |
| UDT Folder | Match ISA-95 level | `Refrigeration/CoolingLoop1/` |

### UDT Parameter Binding Pattern

Parameters use curly-brace references. In tag JSON a parameter binding is an object with `bindType: "parameter"`:

```json
"opcItemPath": {
  "bindType": "parameter",
  "binding": "ns=1;s={PLCPath}{BasePath}/Status"
}
```

With `PLCPath = [DairyPLC]` and `BasePath = Refrigeration/Compressor1`, the instance resolves to `ns=1;s=[DairyPLC]Refrigeration/Compressor1/Status`.

**Standard parameters:**

| Parameter | Purpose | Example value |
|---|---|---|
| `BasePath` | OPC path root | `Refrigeration/Compressor1` |
| `EquipmentName` | Human-readable name | `Compressor 1` |
| `PLCPath` | Device prefix | `[DairyPLC]` |
| `HistorianEnabled` | Enable history | `true` |
| `AreaPath` | ISA-95 area | `DairyPlant/Refrigeration` |

### UDT Inheritance Hierarchy

```
EquipmentModule (base)
├─ status (Boolean)
├─ alarmEnable (Boolean)
├─ maintenanceMode (Boolean)
└─ description (String)

  └─ Motor (extends EquipmentModule)
     ├─ runCommand (Boolean)
     ├─ runFeedback (Boolean)
     ├─ fault (Boolean)
     ├─ speed (Float4) - if VFD
     └─ runHours (Float8)

       └─ Pump (extends Motor)
          ├─ flowRate (Float4)
          ├─ inletPressure (Float4)
          └─ outletPressure (Float4)

  └─ Tank (extends EquipmentModule)
     ├─ level (Float4)
     ├─ levelPercent (Float4)
     ├─ temperature (Float4)
     ├─ pressure (Float4)
     └─ volume (Float4)
```

**Rules:**
- Parent data type (`typeId`) for inheritance when types share behaviour (all motors run/stop).
- Composition (nested UDT instances) for equipment with sub-components (a skid with motors and valves).
- **Define UDTs complete in one pass** (alarms, OPC bindings, history, parameters). Changing them after instances exist causes propagation work.

### Alarm Configuration in UDTs (ISA-18.2) - engineering review required

Alarms are a list under the member tag's `alarms` property, using the scripting/JSON property names from the Tag Alarm Properties page. Any new alarm, and any priority, setpoint or mode change, is flagged for human engineering review.

```json
{
  "name": "Temperature",
  "tagType": "AtomicTag",
  "valueSource": "opc",
  "dataType": "Float4",
  "tagGroup": "Default",
  "opcServer": "Ignition OPC UA Server",
  "opcItemPath": {
    "bindType": "parameter",
    "binding": "ns=1;s={PLCPath}{BasePath}/Temperature"
  },
  "alarms": [
    {
      "name": "HighTemp",
      "mode": "AboveValue",
      "setpointA": 85.0,
      "priority": "High",
      "label": "High Temperature",
      "deadband": 2.0,
      "deadbandMode": "Absolute",
      "ackMode": "Manual",
      "notes": "Consequence: product spoilage. Response: check cooling water flow. Response time: 5 min."
    }
  ]
}
```

- `priority` values: `Diagnostic`, `Low`, `Medium`, `High`, `Critical` (use the names, not numbers).
- `mode` values include `AboveValue`, `BelowValue`, `Equality`, `Bit`, `OnCondition`, and the 8.3 modes `WhenTrue` / `WhenFalse` for Boolean (or non-zero integer) tags.
- `ackMode`: `Unused`, `Auto` (acknowledged when cleared), `Manual`. `Unused` keeps the alarm out of pipelines under the default dropout conditions.
- `shelvingAllowed` (Boolean) controls whether operators can shelve the alarm.
- Summary displays read the **Alarm Metrics** folder (for example `ActiveCountCritical`, `HasActiveUnackedHigh`), which replaces the deprecated Alarms folder.

## Database-Driven Instantiation

The ISA-95 hierarchy lives in SQL, not only in tag folders:
- Add equipment by inserting a row (no Designer needed)
- ERP, MES and SCADA share one equipment model
- Database-driven Perspective navigation

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

### Named Queries

Prefer `system.db.execQuery` with Named Queries for the best security and maintainability. Use `system.db.runPrepQuery` when you need to construct queries dynamically in script that can't be defined ahead of time.

Named queries are project resources under `data/projects/<project>/ignition/named-query/<path>` (SQL plus JSON). Call them with `system.db.execQuery` (select), `system.db.execUpdate` (insert/update/delete) and `system.db.execScalar` (single value). `system.db.runNamedQuery` is deprecated in 8.3.

```sql
-- Equipment/getEquipmentByArea: drives area overview screens
SELECT equipment_id, equipment_name, equipment_type, tag_base_path
FROM Equipment
WHERE area = :area AND active = 1
ORDER BY equipment_name;

-- Equipment/getEquipmentHierarchy: drives the navigation tree
SELECT equipment_id, equipment_name, parent_id, isa95_level
FROM Equipment
WHERE site = :site AND active = 1
ORDER BY isa95_level, equipment_name;

-- Equipment/getAllActiveEquipment: feeds the instantiation script
SELECT equipment_name, equipment_type, tag_base_path, opc_base_path
FROM Equipment
WHERE isa95_level = 'EquipmentModule' AND active = 1;
```

### UDT Instantiation Script

Gateway-scope Jython 2.7, run from a project library function called by a Gateway event or a one-time admin action. In Gateway scope `execQuery` uses the associated project or the Gateway scripting project when no project is given.

```python
import java.lang

def instantiateEquipmentUDTs(provider='[default]'):
    """Create or update one UDT instance per active Equipment row."""
    logger = system.util.getLogger('UDTInstantiation')

    try:
        results = system.db.execQuery('Equipment/getAllActiveEquipment', {})
    except java.lang.Throwable as ex:
        logger.error('Equipment query failed: %s' % ex)
        return
    except Exception as ex:
        logger.error('Equipment query failed: %s' % ex)
        return

    for row in range(results.getRowCount()):
        name = results.getValueAt(row, 'equipment_name')
        type_name = results.getValueAt(row, 'equipment_type')
        tag_path = results.getValueAt(row, 'tag_base_path')
        opc_path = results.getValueAt(row, 'opc_base_path')

        tag_config = {
            'name': name,
            'tagType': 'UdtInstance',
            'typeId': type_name,
            'parameters': {
                'BasePath': opc_path,
                'EquipmentName': name,
            },
        }
        parent_path = provider + '/'.join(tag_path.split('/')[:-1])

        try:
            codes = system.tag.configure(parent_path, [tag_config], 'o')
        except java.lang.Throwable as ex:
            logger.error('configure failed for %s: %s' % (name, ex))
            continue
        except Exception as ex:
            logger.error('configure failed for %s: %s' % (name, ex))
            continue

        if codes and codes[0].isGood():
            logger.info('UDT instance %s at %s' % (name, parent_path))
        else:
            logger.warn('UDT instance %s at %s returned %s' % (name, parent_path, codes))
```

The `o` collision policy overwrites existing instances; use `m` (MergeOverwrite) to change only the given properties, or `a` to abort on existing tags.

## OPC UA Item Paths

```
ns=<namespace>;s=[<device>]<path>
```

- Set on the tag as `opcItemPath`, with `opcServer` naming the OPC UA connection (`Ignition OPC UA Server` for devices on the local Ignition OPC UA server).
- Device name in square brackets: `[DairyPLC]`.

```
ns=1;s=[DairyPLC]Refrigeration/Compressor1/Status
ns=1;s=[DairyPLC]Pasteurization/HeatExchanger1/InletTemp
```

- 8.3 uses OPC UA 1.05. Anonymous OPC UA clients get browse and read only by default; write and call need authenticated users or explicit role mappings.

## Tag Path Verification (Critical)

**Verify tag paths exist on the Gateway before creating Perspective bindings or scripts.**

Unverified paths:
- Cause silent binding failures in Perspective (no data, no error)
- Cause runtime errors in scripts that are hard to trace
- May not surface until production with live PLC data

Verification:
1. Designer → Tag Browser, or read the tag JSON under `data/config/resources/.../tag-definition`
2. Confirm the tag exists and returns Good quality
3. Then create the binding

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/platform/tags/tag-properties
- https://www.docs.inductiveautomation.com/docs/8.3/platform/tags/tag-properties/tag-alarm-properties
- https://www.docs.inductiveautomation.com/docs/8.3/platform/tags/tag-data-types
- https://www.docs.inductiveautomation.com/docs/8.3/platform/tags/tag-groups
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-tag/system-tag-configure
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execQuery
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execUpdate
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execScalar
- https://www.docs.inductiveautomation.com/docs/8.3/platform/sql-in-ignition/named-queries
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/gateway-folder-structure
- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide
