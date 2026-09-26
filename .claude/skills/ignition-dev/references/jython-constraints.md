# Jython 2.7 Constraints for Ignition Development

Applies to: Ignition 8.3.x

Ignition scripts run on **Jython 2.7**, a Java implementation of Python 2.7. Ignition 8.3.8 moved from Jython 2.7.3 to 2.7.4; the language rules below did not change. They apply to Gateway event scripts, project library scripts, Perspective event handlers and transforms, and tag event scripts.

## Scripting scope

- **`system` is pre-scoped.** The runtime injects it into every script context. Never write `import system`.
- **`java.*` must be imported.** `import java.lang` before you use `java.lang.Throwable`.

```python
import java.lang  # needed for java.lang.Throwable

# system needs no import
system.util.getLogger('Project.Module').info('Ready')
```

## Hard constraints

### 1. No f-strings

```python
# WRONG: SyntaxError in Jython 2.7
name = f'Tank: {tankId}'

# CORRECT
name = 'Tank: %s' % tankId
msg = 'Level is %.2f%%' % level
name = 'Tank: {}'.format(tankId)
msg = 'Level is {:.2f}%'.format(level)
```

### 2. No type hints

```python
# WRONG: SyntaxError
def getTagValue(tagPath: str, defaultVal: float = 0.0) -> float:
    pass

# CORRECT: document types in the docstring
def getTagValue(tagPath, defaultVal=0.0):
    """
    Read one tag value.

    Args:
        tagPath (str): full tag path, e.g. [default]Site/Area/Tag
        defaultVal (float): returned when the read fails
    Returns:
        float: the tag value or defaultVal
    """
    pass
```

### 3. No walrus operator

```python
# WRONG: SyntaxError
if (value := system.tag.readBlocking(['[default]Tank/Level'])[0].value) > 80:
    pass

# CORRECT
value = system.tag.readBlocking(['[default]Tank/Level'])[0].value
if value > 80:
    pass
```

### 4. `print` is a statement

```python
# WRONG: prints a tuple in Jython 2.7
print('Pump started:', pumpId)    # ('Pump started:', 'P001')

# CORRECT
print 'Pump started:', pumpId     # Pump started: P001

# BEST for production
logger = system.util.getLogger('Project.Pumps')
logger.info('Pump started: %s' % pumpId)
```

### 5. Integer division

```python
5 / 2        # 2, not 2.5
5.0 / 2      # 2.5
float(x) / y
```

### 6. Unicode

`str` (bytes) and `unicode` are separate types. Use `u'...'` for non-ASCII text such as `u'Temperature (°C)'`, and do not mix encoded `str` and `unicode` in one concatenation.

### 7. No em-dashes

Do not put em-dashes in code, log messages or labels. Use " - ". They do not render correctly in Gateway logs and Perspective labels on every locale.

## Not available in Jython 2.7

| Python 3 feature | Status |
|---|---|
| `async` / `await` | Not available |
| `yield from` | Not available |
| `nonlocal` | Not available |
| `dataclasses`, `pathlib` | Not available |
| `f'...'` strings | Not available |
| `{**a, **b}` and `[*a, *b]` unpacking | Not available |
| `@` matrix operator | Not available |
| `from __future__ import annotations` | Not available |

List and dict comprehensions, lambdas, generators, `try/except/finally` and `with` blocks all work. Both `except Exception as e:` and `except Exception, e:` are valid; use the `as` form.

## Error handling: catch Java and Python exceptions

Ignition runs on the JVM. JDBC, OPC, HTTP and other Java-layer failures raise `java.lang.Throwable` subclasses, which `except Exception` does not catch. Wrap every `system.db.*`, `system.tag.*`, `system.historian.*`, `system.secrets.*` and external call in both:

```python
import java.lang

logger = system.util.getLogger('Project.Maintenance')

def resetFailedChunks(tagProvider):
    """Reset failed store-and-forward chunks. Returns a result dict."""
    try:
        count = system.db.execScalar('Maintenance/countFailed', {'provider': tagProvider})
        system.db.execUpdate('Maintenance/resetFailed', {'provider': tagProvider})
        message = 'Reset %s failed chunks for %s' % (count, tagProvider)
        logger.info(message)
        return {'message': message, 'resetCount': count}
    except java.lang.Throwable as ex:
        # JDBC and other Java-layer errors
        message = 'Reset failed: %s' % ex
    except Exception as ex:
        # Jython-layer errors
        message = 'Reset failed: %s' % ex
    logger.error(message)
    return {'message': message, 'resetCount': 0}
```

## Common patterns

### Reading and writing tags

```python
import java.lang

logger = system.util.getLogger('Project.Tags')

paths = ['[default]Area1/Motor1/Speed', '[default]Area1/Motor1/Current']
try:
    results = system.tag.readBlocking(paths)
    speed = results[0].value
    speedQuality = results[0].quality
    if not speedQuality.isGood():
        logger.warn('Speed quality is %s' % speedQuality)

    writeResults = system.tag.writeBlocking(['[default]Tank1/Setpoint'], [75.0])
    if not writeResults[0].isGood():
        logger.warn('Setpoint write returned %s' % writeResults[0])
except java.lang.Throwable as ex:
    logger.error('Tag access failed: %s' % ex)
except Exception as ex:
    logger.error('Tag access failed: %s' % ex)
```

Setpoint writes that affect alarms or interlocks need engineering review (see the Safety section of the skill).

### Logging

```python
logger = system.util.getLogger('ProjectName.ModuleName')   # once, at module level

logger.trace('Entering %s' % funcName)
logger.debug('%s = %s' % (tagPath, value))
logger.info('Batch started: %s' % batchId)
logger.warn('High temperature: %.1f C' % temp)
logger.error('Tag write failed: %s' % tagPath)
```

### Database queries

Prefer `system.db.execQuery` with Named Queries for the best security and maintainability. Use `system.db.runPrepQuery` when you need to construct queries dynamically in script that can't be defined ahead of time.

```python
# Select, update and scalar reads through named queries
rows = system.db.execQuery('Equipment/getByArea', {'area': area})
changed = system.db.execUpdate('Equipment/setStatus', {'id': equipId, 'status': 1})
total = system.db.execScalar('Equipment/countByArea', {'area': area})

# Runtime-shaped SELECT: values in args, never in the SQL string
rows = system.db.runPrepQuery('SELECT id, name FROM equipment WHERE area = ?', [area], 'MES')

# REJECTED: a value formatted into SQL (injection risk)
# sql = "SELECT * FROM equipment WHERE area = '%s'" % area
```

Wrap each of these calls in the Java and Python `except` pair shown above. `runNamedQuery`, `runQuery`, `runScalarQuery` and `runUpdateQuery` are deprecated in 8.3; see [changed-in-8.3.md](changed-in-8.3.md).

### Datasets

`system.dataset.toPyDataSet` is deprecated in 8.3 with no replacement, because datasets no longer need wrapping. Do not add new `toPyDataSet` calls.

### Credentials

Never hard-code passwords, tokens or keys. Read them from a secret provider with `system.secrets.readSecretValue(providerName, secretName)` inside a `with` block so the value is cleared. Example in [changed-in-8.3.md](changed-in-8.3.md).

## Validation tools

- An Ignition-aware LSP (ignition-lsp, used by the Neovim, VS Code and Zed plugins) flags Jython 2.7 violations as you type.
- `ignition-lint` checks `view.json` files and scripts.
- Run the LSP first, then lint, then tests. Full sequence: [validation-workflow.md](validation-workflow.md).

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/new-in-this-version
- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execQuery
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execUpdate
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execScalar
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-runPrepQuery
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets/system-secrets-readSecretValue

## Embedding data in generated scripts

Generators that write `view.json` scripts often embed a lookup table. `json.dumps(table)` pasted into Jython source breaks it: `true`, `false` and `null` are not Python names, so the script fails at runtime and the binding shows a quality error **[live 8.3.9]**. Embed a JSON **string** and decode it at runtime:

```python
# generator (CPython): code = "\ttable = system.util.jsonDecode(" + json.dumps(json.dumps(TABLE)) + ")\n"
table = system.util.jsonDecode("{\"LeakSensor\": [[\"Wet\", true]]}")
```
