# Ignition SCADA Project Context

This is an **Ignition 8.3 SCADA/MES project** (Perspective). All code and configuration must respect Ignition platform constraints. For Ignition 8.1 projects, use the `release/8.1` branch of this repo instead.

## Critical: Jython 2.7

Ignition 8.3 scripts run on **Jython 2.7** (2.7.4 since 8.3.8), not Python 3. Violations cause silent runtime failures.

| Forbidden (Python 3) | Use instead |
|---|---|
| `f'Value: {x}'` | `'Value: %s' % x` or `'Value: {}'.format(x)` |
| `def foo(x: int) -> str:` | `def foo(x):` (docstring for docs) |
| `if (x := getValue()):` | `x = getValue()` then `if x:` |
| `print('a', 'b')` | `print 'a', 'b'` or `system.util.getLogger()` |
| `str` as unicode | `u'string'` prefix for unicode literals |

## Ignition Scripting Scope

- **`system` is pre-scoped** in all Ignition script contexts (Gateway, Perspective, tag events). Never write `import system` - it is unnecessary and wrong.
- **`java.lang` must be imported explicitly** when catching Java exceptions: `import java.lang` before using `java.lang.Throwable`.
- Always catch both Java and Python exceptions for any `system.db.*`, `system.tag.*`, `system.historian.*`, `system.secrets.*`, or external resource call:

```python
import java.lang

logger = system.util.getLogger('Module')
try:
    rows = system.db.execQuery('Equipment/getByArea', {'area': area})
except java.lang.Throwable as ex:
    logger.error('Failed: {}'.format(ex))
except Exception as ex:
    logger.error('Failed: {}'.format(ex))
```

## Database Access

- **Prefer `system.db.execQuery` with Named Queries for the best security and maintainability. Use `system.db.runPrepQuery` when you need to construct queries dynamically in script that can't be defined ahead of time.**
- Named-query writes use `system.db.execUpdate`; single values use `system.db.execScalar`.
- `system.db.runNamedQuery`, `runQuery`, `runScalarQuery` and `runUpdateQuery` are deprecated in 8.3. Do not use them in new code; migrate existing calls.
- Never format or concatenate values into SQL. With `runPrepQuery`, values always go in the `?` argument list.

## Ignition 8.3 Platform Rules

- **Gateway config is files**, not the internal database: `data/config/resources/{system,external,core,local,<mode>}`. Projects live in `data/projects`.
- **Still binary**: alarm pipelines, transaction groups, client tags and reports are `.bin` resources. Do not hand-edit them.
- **Scans**: `system.project.requestScan()` rescans projects only. Gateway config changes need `POST /data/api/v1/scan/config` (or Platform > System > Modes > Scan File System).
- **History**: use `system.historian.*` (for example `queryRawPoints`, `queryAggregatedPoints`), not the deprecated `system.tag.queryTagHistory` family.
- **Credentials**: never put passwords, API keys or tokens in scripts, resource files or git. Use secret providers and `system.secrets.*`.
- **Terminology**: Tag Groups, not scan classes.

## String Formatting Rules

- **No em-dashes** in scripts, log messages, labels, or docs. Use ` - ` (space-hyphen-space) instead. Em-dashes do not render correctly in Gateway logs or Perspective labels on all locales.

## Safety-Critical Requirements

- **Flag SIS scope**: Note any Safety Instrumented System configurations and require engineering review
- **IT/OT boundaries**: Do not create connections across network zones without explicit authorization
- **Alarm changes**: Flag all alarm priority changes, alarm pipeline or journal changes, and interlock modifications for human engineering review
- **MOC**: Safety-critical architecture changes require Management of Change documentation
- **Live gateways**: never run gateway scripts or write config through an API or MCP tool without explicit confirmation

## Validation Before Completion

Any Perspective view or Jython script is not complete until validated:
1. LSP (for example `ignition.nvim`) - zero errors
2. `ignition-lint` - pass rate > 90%, zero Critical/High findings
3. Scan: project scan for views and scripts, config scan for Gateway resources
4. Designer verification with live tags (plus unit or e2e tests where the project has them)

## Skills

| Command | Use when... |
|---|---|
| `/ignition-dev` | Writing scripts, views, UDTs, tag configs |
| `/ignition-architect` | Designing system architecture, UDT hierarchy, DB model, deployment modes |
| `/ignition-ui` | Designing Perspective screens and UX flows |
| `/ignition-plan` | Writing PRDs, discovery, requirements, epics, 8.1 to 8.3 migrations |
| `/ignition-review` | Reviewing code, views, config diffs, or architecture for correctness |
| `/ignition-deploy` | Committing config or project changes, scanning, verifying, promoting between modes |
| `/ignition-inspect` | Read-only inspection of a live Gateway over MCP |

Knowledge skills loaded automatically when relevant: `ignition-config` (8.3 config-as-code, collections, deployment modes, REST API) and `ignition-security` (secrets, API keys, agent guard rails). Each skill keeps its long reference material in its own `references/` folder.
