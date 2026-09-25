# Review Checklists

Applies to: Ignition 8.3.x

Detailed checklists used by `/ignition-review`. The hard rejection criteria and output format live in `../SKILL.md`.

---

## 1. Database Query Review

Rule (verbatim):

> Prefer `system.db.execQuery` with Named Queries for the best security and maintainability. Use `system.db.runPrepQuery` when you need to construct queries dynamically in script that can't be defined ahead of time.

### Reject: values in SQL text

```python
# REJECT - value formatted into SQL
query = "SELECT * FROM Equipment WHERE area = '%s'" % area
system.db.runPrepQuery(query, [])

# REJECT - value concatenated into SQL, even inside a "prep" call
system.db.runPrepQuery("SELECT * FROM Equipment WHERE area = '" + area + "'", [])
```

### Accept: Named Query through the 8.3 API

```python
import java.lang

logger = system.util.getLogger('Equipment.Lookup')
try:
    rows = system.db.execQuery('Equipment/ByArea', {'area': area})
    count = system.db.execScalar('Equipment/CountByArea', {'area': area})
    changed = system.db.execUpdate('Equipment/SetStatus', {'id': equipId, 'status': status})
except java.lang.Throwable as ex:
    logger.error('Equipment query failed: %s' % ex)
except Exception as ex:
    logger.error('Equipment query failed: %s' % ex)
```

Signatures: `execQuery(path, [parameters], [tx], [project])` returns a Dataset; `execScalar(path, [parameters], [tx], [project])` returns a value or None; `execUpdate(path, [parameters], [tx], [getKey], [project])` returns rows affected or the generated key. In Gateway scope with no project given, the associated project or the Gateway scripting project is used; check that is the intended project.

### Accept: prepared query when the SQL shape is dynamic

`?` placeholders can only stand for values, never for table names, column names or SQL syntax. Identifiers must come from a fixed allowlist in code; values always go in the args list.

```python
import java.lang

SORT_COLUMNS = {'name': 'EquipmentName', 'area': 'AreaName', 'updated': 'LastUpdated'}

def getEquipment(area, sortKey):
    logger = system.util.getLogger('Equipment.Search')
    column = SORT_COLUMNS.get(sortKey, 'EquipmentName')
    query = 'SELECT EquipmentName, AreaName FROM Equipment WHERE AreaName = ? ORDER BY ' + column
    try:
        return system.db.runPrepQuery(query, [area], 'ProductionDB')
    except java.lang.Throwable as ex:
        logger.error('Equipment search failed: %s' % ex)
    except Exception as ex:
        logger.error('Equipment search failed: %s' % ex)
    return None
```

Check:
- [ ] Number of `?` equals the length of the args list.
- [ ] Every concatenated fragment is a constant or an allowlist lookup, never user or tag input.
- [ ] A Named Query was considered first; the reason the SQL cannot be defined ahead of time is stated.
- [ ] In Gateway scope the `database` argument is given (it is required there).
- [ ] Client-side (Perspective Session) calls: `runPrepQuery` is subject to the "Legacy Database Access" client permission; confirm the roles/zones are configured deliberately.

Exception: one-off migration or admin utilities may use other patterns only with documented justification and no production use. Values in SQL text are still rejected.

### Deprecated in 8.3: "deprecated - migrate" findings

| Deprecated | Replace with |
|---|---|
| `system.db.runNamedQuery` | `system.db.execQuery` / `execUpdate` |
| `system.db.runQuery` | `execQuery` or `runPrepQuery` |
| `system.db.runScalarQuery` | `execScalar` or `runScalarPrepQuery` |
| `system.db.runUpdateQuery` | `execUpdate` or `runPrepUpdate` |
| `system.db.runSFNamedQuery` | `execQuery` |
| `system.db.runSFUpdateQuery` | `execUpdateAsync` or `runSFPrepUpdate` |
| `system.db.clear*NamedQueryCache*` | `system.db.clearQueryCache` |
| `system.tag.queryTagHistory` | `system.historian.queryRawPoints` |
| `system.tag.queryTagCalculations` | `system.historian.queryAggregatedPoints` |
| `system.tag.storeTagHistory` | `system.historian.storeDataPoints` |
| `system.tag.browseHistoricalTags` | `system.historian.browse` |
| `system.tag.*Annotations` | `system.historian.*Annotations` |
| `system.tag.queryTagDensity` | No replacement; flag for a design decision |
| `system.net.http*` | `system.net.httpClient` |
| `system.dataset.toPyDataSet` | No replacement needed (datasets no longer need wrapping) |
| `system.dataset.toDataSet` | `system.dataset.toDataset` |

Old names still work in 8.3, which is why these are findings and not rejections. Also check historical tag paths: 8.3 uses `sys:` / `prov:` instead of `drv:`, except for the SQL Historian.

---

## 2. Secrets and Credentials

**Reject** any plaintext credential in:
- scripts (project library, Gateway events, tag events, Perspective events),
- view or session props, named queries, tag JSON,
- committed Gateway config (`data/config/...`), `.env` files, compose files or CI files in the repo.

Accept:
- Config secret fields set to **Referenced** (from a secret provider: Internal, Remote since 8.3.3, File since 8.3.5) or **Embedded** (encrypted by the Gateway).
- Scripts that read a secret at run time and clear it:

```python
import java.lang

logger = system.util.getLogger('Integration.Erp')
try:
    with system.secrets.readSecretValue('PlantSecrets', 'erp-api-token') as secret:
        token = secret.getSecretAsString()
        # use token for this call only; never log it
except java.lang.Throwable as ex:
    logger.error('Could not read ERP token: %s' % ex)
except Exception as ex:
    logger.error('Could not read ERP token: %s' % ex)
```

Check:
- [ ] `system.secrets` availability: base functions since 8.3.1; `createEmbeddedSecretConfig`, `createReferencedSecretConfig`, `readConfiguredSecretValue` since 8.3.8. Match the target Gateway version.
- [ ] Secrets are never logged, returned to a session, or written to tags.
- [ ] Files read by a File secret provider are not in git.
- [ ] API tokens (`X-Ignition-API-Token`) are not hardcoded in scripts, CI files or shell history. See `../../ignition-security/SKILL.md`.

---

## 3. Error Handling

Required pattern around `system.db.*`, `system.tag.*`, `system.historian.*`, `system.secrets.*` and external calls: `import java.lang`, then `except java.lang.Throwable` followed by `except Exception`, both logging through `system.util.getLogger`.

Flag any code that:
- [ ] Calls those APIs with no `java.lang.Throwable` handler.
- [ ] Reads tags without checking quality (`qv.quality.isGood()`).
- [ ] Ignores the QualityCode list returned by `system.tag.writeBlocking`.
- [ ] Has a bare `except:` or swallows exceptions without logging.

---

## 4. Script Scope API Validation

| Scope | Allowed | Not allowed |
|---|---|---|
| Gateway Event | `system.tag`, `system.db`, `system.historian`, `system.util` | `system.gui.*`, `system.vision.*`, `system.perspective.*` session calls without a session id |
| Perspective component event | `system.perspective.*`, `system.tag`, `system.db`, `self`, `event` | `system.gui.*`, `system.vision.*` |
| Perspective Gateway Event (Form Submission) | `system.db`, `system.tag`, `system.util`; the `session`, `name`, `data`, `formContext`, `sessionContext`, `retry` params | `system.gui.*`, `system.vision.*`; assumptions that submissions arrive in order (offline queues can reorder) |
| Tag Event | `system.tag`, `system.db`, `system.util` | All UI APIs; no session context |

---

## 5. Perspective View Checklist

### Structure
- [ ] Valid JSON (no trailing commas).
- [ ] `root` is a container; `meta.name` is `root`.
- [ ] Component `type` strings match those produced by the 8.3 Designer (no invented types).
- [ ] Custom properties in `custom`, not `props`.
- [ ] `meta.name` set on components referenced by scripts or message handlers.
- [ ] `view.json` and its `resource.json` change together.

### Bindings
- [ ] Tag paths verified to exist; view params used instead of hardcoded paths.
- [ ] Query bindings point to Named Queries with an appropriate Return Format and polling rate.
- [ ] Expression bindings preferred over script transforms.
- [ ] Event handlers have correct `type` and `config`.

### Styles
- [ ] Colors via style classes and theme variables, not inline on each component.
- [ ] ISA-101 gray background class on the root.
- [ ] Alarm/state colors switched by expression binding to style classes.
- [ ] No user style class names starting with `ia_`.

### 8.3 components
- [ ] **Form:** design does not assume Submit/Cancel can be hidden; `submissionHandler` names an existing Form Submission Gateway Event; handler tolerates `retry` and out-of-order submissions; writes use `execUpdate` with error handling.
- [ ] **Drawing:** symbols stay gray in normal state; colors come from classes or theme variables; SVG attributes tested in a session.
- [ ] **Audio:** not used as the only audible alarm. Flag for engineering review if used for alarms.
- [ ] **Offline Mode:** only relied on in the mobile app; no control actions or alarm response depend on it.

### ignition-lint
- [ ] Lint report with pass rate > 90%, zero Critical/High, Medium findings justified.

If no lint evidence is provided, return the submission.

---

## 6. Tag and UDT Checklist

- [ ] Definition names `PascalCase`; instance names reflect physical equipment.
- [ ] Parameters defined on the definition (`BasePath`, `EquipmentName`); parameter references use `{Param}` syntax.
- [ ] Inheritance valid (child UDTs reference an existing parent).
- [ ] Tag Groups (not "scan classes") chosen deliberately; no sub-second groups without justification.
- [ ] Alarm definitions: setpoint, Ignition priority (Diagnostic/Low/Medium/High/Critical), label, consequence text, deadband, delays. **Any alarm change is flagged for engineering review.**
- [ ] 8.3 alarm modes "When True" / "When False" used as intended; references to the deprecated Alarms tag folder moved to Alarm Metrics (finding).
- [ ] Tag JSON diffs under `data/config/resources/<collection>/ignition/tag-definition` reviewed like code (see `config-diff-review.md`).

---

## 7. Performance

- [ ] `system.tag.readBlocking` / `writeBlocking` not called in a loop; batch paths into one call.
- [ ] Script bindings replaced by expressions where possible.
- [ ] Named Queries bounded (parameters, limits); query bindings use Cache & Share or sensible polling.
- [ ] No sub-second bindings on views with many components.
- [ ] No expensive work in handlers that fire on every value change.

---

## 8. ISA Standards

### ISA-18.2 alarms (all items need engineering review when changed)
- [ ] Priority chosen by consequence and required response time, using Ignition priorities:
  - Critical: immediate action, safety or major consequence. Red, blinking while unacknowledged.
  - High: action within minutes. Red.
  - Medium: action within the shift. Amber.
  - Low: awareness. Amber.
  - Diagnostic: system or maintenance information; presentation set by the alarm philosophy.
- [ ] Deadband on analog alarms; on/off delays where chattering is possible.
- [ ] Documented consequence and response for each alarm.
- [ ] Shelving and acknowledgement behavior tested (8.3 fixed shelving bugs; retest any workaround).
- [ ] Alarm pipeline or notification profile changes reviewed on the Gateway (pipelines are `.bin`).

### ISA-101 HMI
- [ ] Gray background by style class on all screens.
- [ ] Color only for abnormal states; no green for "running".
- [ ] No decorative 3D, gradients, photos or animation.
- [ ] Alarm banner on every screen.
- [ ] Navigation follows Site > Area > Equipment.

### ISA-95 tag structure
- [ ] Paths follow `[default]Site/Area/Line/Cell/Equipment/Tag`, no skipped levels.
- [ ] Consistent naming; UDT instances at the correct level.

---

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execQuery
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execUpdate
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execScalar
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-runPrepQuery
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-clearQueryCache
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-historian
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets/system-secrets-readSecretValue
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/secrets-management
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-tag/system-tag-writeBlocking
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/scripting-in-perspective/perspective-session-events-scripts
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/components/perspective-components/perspective-input-palette/perspective-form
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/perspective-sessions/ignition-perspective-app/offline-mode
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/working-with-perspective-components/bindings-in-perspective/query-bindings-in-perspective
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/style-classes
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/alarm-notification
