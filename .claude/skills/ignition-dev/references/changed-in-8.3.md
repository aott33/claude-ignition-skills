# Scripting Changes in Ignition 8.3

Applies to: Ignition 8.3.x

Developer-facing list of the scripting API changes from 8.1 to 8.3. Deprecated functions still run in 8.3, so existing code keeps working, but new code must use the replacements. In a review, a deprecated call in existing code is a "deprecated - migrate" finding, not a rejection.

This is not a full `system.*` catalogue. For every other function, use the IA scripting reference (Sources) or the `ignition-api` skill in the TheThoughtagen/ignition-ide-plugins Claude Code plugin.

## system.db

Rule: Prefer `system.db.execQuery` with Named Queries for the best security and maintainability. Use `system.db.runPrepQuery` when you need to construct queries dynamically in script that can't be defined ahead of time.

| Deprecated | Replacement |
|---|---|
| `system.db.runNamedQuery` | `system.db.execQuery` (select), `system.db.execUpdate` (update) |
| `system.db.runQuery` | `system.db.execQuery` or `system.db.runPrepQuery` |
| `system.db.runScalarQuery` | `system.db.execScalar` or `system.db.runScalarPrepQuery` |
| `system.db.runUpdateQuery` | `system.db.execUpdate` or `system.db.runPrepUpdate` |
| `system.db.runSFNamedQuery` | `system.db.execQuery` |
| `system.db.runSFUpdateQuery` | `system.db.execUpdateAsync` or `system.db.runSFPrepUpdate` |
| `system.db.clearNamedQueryCache`, `system.db.clearAllNamedQueryCaches` | `system.db.clearCache` (the reference page is titled `clearQueryCache`; check the name in the Designer's autocomplete) |
| `system.db.dateFormat` | `system.date.format` |
| `system.db.refresh` | `system.vision.refreshBinding` (Vision only, out of scope) |

Signatures (from the 8.3 function pages):

| Function | Syntax | Returns | Scope |
|---|---|---|---|
| `execQuery` | `system.db.execQuery(path, [parameters], [tx], [project])` | Dataset | Gateway, Vision Client, Perspective Session |
| `execUpdate` | `system.db.execUpdate(path, [parameters], [tx], [getKey], [project])` | Integer: rows affected, or the generated key when `getKey=True` | Gateway, Vision Client, Perspective Session |
| `execScalar` | `system.db.execScalar(path, [parameters], [tx], [project])` | The single value, or `None` when no rows | Gateway, Vision Client, Perspective Session |
| `runPrepQuery` (Gateway) | `system.db.runPrepQuery(query, args, database, [tx])` | PyDataSet | Gateway |
| `runPrepQuery` (Perspective) | `system.db.runPrepQuery(query, args, [database], [tx])`; omitted database means the project default | PyDataSet | Vision Client, Perspective Session |

Notes:
- `path` is the full named query path, for example `'Equipment/getByArea'`. `parameters` is a dict.
- In Gateway scope with no `project`, the associated project or the Gateway scripting project is used. Pass `project=` by keyword to be explicit.
- For a named query that goes through Store and Forward, the `execUpdate` page points to `system.db.execUpdateAsync`.
- `runPrepQuery` placeholders (`?`) stand for values only. They cannot stand for table names, column names or SQL syntax. Pick identifiers from an allowlist in code; never format a value into the SQL string.
- In a Perspective session, `runPrepQuery` is subject to the Legacy Database Access client permission. The `exec*` functions have no client permission restriction.
- Named queries live at `data/projects/<project>/ignition/named-query/<name>` as a SQL file plus JSON metadata.

```python
import java.lang

logger = system.util.getLogger('Project.Batch')

def closeBatch(batchId, operator):
    """Close a batch. Returns rows affected, or 0 on failure."""
    try:
        return system.db.execUpdate(
            'Batch/close',
            {'batchId': batchId, 'operator': operator},
            project='Production'
        )
    except java.lang.Throwable as ex:
        logger.error('closeBatch %s failed: %s' % (batchId, ex))
    except Exception as ex:
        logger.error('closeBatch %s failed: %s' % (batchId, ex))
    return 0

SORT_COLUMNS = {'time': 't_stamp', 'area': 'area'}

def recentEvents(area, sortKey, database):
    """Runtime-shaped query: the ORDER BY column comes from an allowlist, values go in args."""
    column = SORT_COLUMNS.get(sortKey, 't_stamp')
    sql = 'SELECT t_stamp, area, message FROM events WHERE area = ? ORDER BY ' + column + ' DESC'
    try:
        return system.db.runPrepQuery(sql, [area], database)
    except java.lang.Throwable as ex:
        logger.error('recentEvents failed: %s' % ex)
    except Exception as ex:
        logger.error('recentEvents failed: %s' % ex)
    return None
```

## system.historian (replaces system.tag history functions)

| Deprecated | Replacement |
|---|---|
| `system.tag.queryTagHistory` | `system.historian.queryRawPoints` |
| `system.tag.queryTagCalculations` | `system.historian.queryAggregatedPoints` |
| `system.tag.storeTagHistory` | `system.historian.storeDataPoints` |
| `system.tag.browseHistoricalTags` | `system.historian.browse` |
| `system.tag.queryAnnotations` | `system.historian.queryAnnotations` |
| `system.tag.storeAnnotations` | `system.historian.storeAnnotations` |
| `system.tag.deleteAnnotations` | `system.historian.deleteAnnotations` |
| `system.tag.queryTagDensity` | No replacement |

Full `system.historian` list: `browse`, `deleteAnnotations`, `queryAggregatedPoints`, `queryAnnotations`, `queryMetadata`, `queryRawPoints`, `storeAnnotations`, `storeDataPoints`, `storeMetadata`, `updateRegisteredNodePath`, and `types.*` (`annotationPoint`, `dataPoint`, `metadataPoint`; 8.3.5). All are available in Gateway, Vision and Perspective scope.

| Function | Syntax | Returns |
|---|---|---|
| `queryRawPoints` | `system.historian.queryRawPoints(paths, startTime, [endTime], [columnNames], [returnFormat], [returnSize])` | Dataset |
| `queryAggregatedPoints` | `system.historian.queryAggregatedPoints(paths, startTime, endTime, [aggregates], [columnNames], [returnFormat], [returnSize])` | Dataset |
| `storeDataPoints` (1) | `system.historian.storeDataPoints(paths, values, [timestamps], [qualities])` | List of QualityCode |
| `storeDataPoints` (2, 8.3.5+) | `system.historian.storeDataPoints(datapoints)` with objects from `system.historian.types.dataPoint` | List of QualityCode |

Notes:
- `returnFormat` is `WIDE` (default), `TALL` or `CALCULATION`. `returnSize` on `queryRawPoints` only works with the Internal and Core Historians.
- Aggregates include `Average`, `SimpleAverage`, `Sum`, `Minimum`, `Maximum`, `MinMax`, `LastValue`, `Range`, `Count`, `CountOn`, `CountOff`, `DurationOn`, `DurationOff`, `Variance`, `StdDev`, `PctGood`, `PctBad`.
- `includeBounds`, `excludeObservations` and `fillModes` were removed in 8.3.9 (kept only for backward compatibility). Do not use them in new code.
- Paths: use the qualified form `histprov:<Historian>:/sys:<Gateway>:/prov:<TagProvider>:/tag:<Folder/Tag>`. The SQL Historian still needs the `drv:` form: `histprov:<Historian>:/drv:<Gateway>:<TagProvider>:/tag:<Folder/Tag>`.
- Do not use `system.historian.queryValues`: it is mentioned on one IA page but has no reference page.

```python
import java.lang

logger = system.util.getLogger('Project.Trend')

def lastHourAverage(path):
    """path: qualified historical path. Returns a Dataset or None."""
    end = system.date.now()
    start = system.date.addHours(end, -1)
    try:
        return system.historian.queryAggregatedPoints([path], start, end, ['Average'])
    except java.lang.Throwable as ex:
        logger.error('History query failed for %s: %s' % (path, ex))
    except Exception as ex:
        logger.error('History query failed for %s: %s' % (path, ex))
    return None
```

## system.secrets (8.3.1+)

| Function | Syntax | Since |
|---|---|---|
| `encrypt` | `system.secrets.encrypt(string, [charset])` or `system.secrets.encrypt(bytes)`; returns a JWE | 8.3.1 |
| `decrypt` | `system.secrets.decrypt(json)`; returns PyPlaintext | 8.3.1 |
| `getProviders` | `system.secrets.getProviders()` | 8.3.1 |
| `getSecrets` | `system.secrets.getSecrets(providerName)` | 8.3.1 |
| `readSecretValue` | `system.secrets.readSecretValue(providerName, secretName)`; returns PyPlaintext; scope Gateway, Vision Client, Perspective Session | 8.3.1 |
| `createEmbeddedSecretConfig` | `system.secrets.createEmbeddedSecretConfig(json)` | 8.3.8 |
| `createReferencedSecretConfig` | `system.secrets.createReferencedSecretConfig(providerName, secretName)` | 8.3.8 |
| `readConfiguredSecretValue` | `system.secrets.readConfiguredSecretValue(secretConfig)` | 8.3.8 |

PyPlaintext holds the secret; read it with `getSecretAsString()` or `getSecretAsBytes()`. Clear it when done, preferably with a `with ... as` block. IA notes that `readSecretValue` and PyPlaintext are not thread-safe. Never log a secret value.

```python
import java.lang

logger = system.util.getLogger('Project.Integration')

def callErp(url, body):
    try:
        with system.secrets.readSecretValue('Internal', 'erp-api-token') as token:
            headers = {'Authorization': 'Bearer ' + token.getSecretAsString()}
            return system.net.httpClient.post(url, data=body, headers=headers)
    except java.lang.Throwable as ex:
        logger.error('ERP call failed: %s' % ex)
    except Exception as ex:
        logger.error('ERP call failed: %s' % ex)
    return None
```

Secret providers (Internal, Remote from 8.3.3, File from 8.3.5) are covered in [../../ignition-security/SKILL.md](../../ignition-security/SKILL.md).

## Other changes

| Area | 8.1 | 8.3 |
|---|---|---|
| HTTP | `system.net.httpGet`, `httpPost` and the other `system.net.http*` functions | Deprecated; use `system.net.httpClient`. In 8.3 `system.net.httpClient` can be used directly as a shared instance (`system.net.httpClient.get(...)`), so you no longer need a module-level client variable |
| Datasets | `system.dataset.toPyDataSet(ds)` | Deprecated with no replacement: datasets no longer need wrapping. Iterate the dataset directly |
| Datasets | `system.dataset.toDataSet` | `system.dataset.toDataset` (single syntax) |
| Project scan | `system.project.requestScan()` | Still exists: `system.project.requestScan([timeout])`, timeout in seconds (default 10), blocks the thread, Gateway and Perspective Session scope. It scans **projects only**. Gateway config changes need `POST /data/api/v1/scan/config` or Scan File System on Platform > System > Modes |
| Expressions | `forceQuality(...)` | Deprecated; use `qualifiedValue(...)` |
| Vision functions | `system.gui.*`, `system.nav.*` and Vision parts of other namespaces | Moved to `system.vision.*` (out of scope here) |
| Alarms | Tag Browser Alarms folder | Replaced by the Alarm Metrics folder; the old folder is deprecated but scripts and bindings still work |
| New namespaces | none | `system.config`, `system.eventstream`, `system.historian`, `system.secrets`, `system.vision` |
| Jython | 2.7.3 | 2.7.4 from 8.3.8; Jython 2.7 rules unchanged |

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execQuery
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execUpdate
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execScalar
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-runPrepQuery
- https://www.docs.inductiveautomation.com/docs/8.3/platform/sql-in-ignition/named-queries
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-historian
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-historian/system-historian-queryRawPoints
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-historian/system-historian-queryAggregatedPoints
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-historian/system-historian-storeDataPoints
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets/system-secrets-readSecretValue
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-net/system-net-httpClient
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-project/system-project-requestScan
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/new-in-this-version
