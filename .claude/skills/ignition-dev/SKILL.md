---
name: ignition-dev
description: Ignition 8.3 developer mode. Use when writing Jython scripts, Perspective view.json, named queries, tag or UDT JSON. Not for architecture design or code review.
argument-hint: "[task or file to work on]"
---

# Ignition Developer

Applies to: Ignition 8.3.x

You write production-ready Jython scripts, Perspective views, named queries, tag and UDT configuration for Ignition SCADA/MES systems in industrial environments.

**Scope:** Perspective only. Vision is still a module in 8.3 but is out of scope for this skill set, so do not write `system.gui.*` or `system.vision.*` code.

## Before you write code

- Read [references/changed-in-8.3.md](references/changed-in-8.3.md) when a task touches `system.db`, `system.tag` history, `system.net`, secrets, datasets or scans. Many 8.1 habits are deprecated in 8.3.
- Read [references/jython-constraints.md](references/jython-constraints.md) for the full Jython 2.7 rule set and patterns.

## Jython 2.7 (hard rules)

8.3 runs Jython 2.7 (2.7.4 since 8.3.8). Python 3 syntax fails at runtime.

- No f-strings: `'Value: %s' % x` or `'Value: {}'.format(x)`
- No type hints: `def foo(x):` with a docstring
- No walrus operator: assign first, then test
- `print` is a statement; in production use `system.util.getLogger('Name')`
- `u'...'` for non-ASCII text; `5 / 2 == 2`, so use `5.0 / 2` for a decimal result
- `system` is pre-scoped: never write `import system`
- `import java.lang` before catching `java.lang.Throwable`
- No em-dashes in code, log messages or labels; use " - "

## Error handling

Java-layer errors (JDBC, OPC, HTTP) are not caught by `except Exception`. Wrap every `system.db.*`, `system.tag.*`, `system.historian.*`, `system.secrets.*` and external call:

```python
import java.lang

logger = system.util.getLogger('Project.Equipment')

def getEquipment(area):
    try:
        return system.db.execQuery('Equipment/getByArea', {'area': area})
    except java.lang.Throwable as ex:
        logger.error('getEquipment failed for area %s: %s' % (area, ex))
    except Exception as ex:
        logger.error('getEquipment failed for area %s: %s' % (area, ex))
    return None
```

## Database access

Prefer `system.db.execQuery` with Named Queries for the best security and maintainability. Use `system.db.runPrepQuery` when you need to construct queries dynamically in script that can't be defined ahead of time.

| Need | Call |
|---|---|
| Select from a named query | `system.db.execQuery(path, [parameters], [tx], [project])` returns a Dataset |
| Insert, update, delete via a named query | `system.db.execUpdate(path, [parameters], [tx], [getKey], [project])` returns rows affected or the generated key |
| Single value via a named query | `system.db.execScalar(path, [parameters], [tx], [project])` returns the value or `None` |
| Runtime-shaped SELECT | `system.db.runPrepQuery(query, args, database, [tx])` in Gateway scope (database is optional in Perspective) |

Rules:
- In Gateway scope, pass `project=` when the script is not tied to an obvious project; otherwise the associated project or the Gateway scripting project is used.
- With `runPrepQuery`, every value goes in `args` against a `?` placeholder. Only identifiers (table, column, sort direction) picked from a fixed allowlist in code may be concatenated.
- Never format or concatenate a value into SQL. This is always rejected in review.
- `runNamedQuery`, `runQuery`, `runScalarQuery` and `runUpdateQuery` are deprecated in 8.3. Do not use them in new code; migrate them when you touch the file.

## Script scopes

| Scope | Runs in | Notes |
|---|---|---|
| Gateway event script | Gateway, no session | No session context; no UI calls |
| Project library script | Wherever it is called from | Keep logic here; call it from events |
| Perspective event or transform | Gateway, on behalf of a session | `self`, `event`, `system.perspective.*` |
| Tag event script | Gateway | Keep it fast; no UI or session APIs |

Useful Perspective calls: `system.perspective.navigate`, `openPopup`, `closePopup`, `sendMessage`, and `print` for debugging only.

## Perspective bindings

Prefer expression bindings over script transforms: they are cheaper to run. Binding shapes inside `propConfig`:

```json
{"binding": {"type": "tag", "config": {"mode": "direct", "tagPath": "[default]Site/Area/Line1/Pump1/Speed"}}}
{"binding": {"type": "expr", "config": {"expression": "if({view.params.running}, 'Running', 'Stopped')"}}}
{"binding": {"type": "property", "config": {"path": "view.params.tagBasePath"}}}
```

Query bindings reference a named query by `config.queryPath`. When unsure of a binding's exact shape, copy it from a view saved by the Designer instead of guessing.

View files: `view.json` has `params` (the view's public API; document each one), `custom`, and `root` (always a container, `ia.container.flex` for responsive layouts). Put appearance in style classes, not inline colours. Component reference: [../ignition-ui/references/perspective-components.md](../ignition-ui/references/perspective-components.md); styles: [../ignition-ui/references/perspective-styles.md](../ignition-ui/references/perspective-styles.md).

## Tags and UDTs

- Paths: `[provider]Site/Area/Line/Cell/Equipment/Tag` (ISA-95); UDT parameters as `{BasePath}`.
- Verify a tag path exists before binding to it; a broken binding shows no data and no error.
- UDT definition names in PascalCase; complete the definition in one pass before creating instances.
- The polling rate setting is a **Tag Group** (never "scan class").
- History: use `system.historian.*` (`queryRawPoints`, `queryAggregatedPoints`, `storeDataPoints`), not the deprecated `system.tag.queryTagHistory` family.
- More: [../ignition-architect/references/tag-structure.md](../ignition-architect/references/tag-structure.md).

## Credentials

Never put passwords, API tokens or keys in scripts, named queries, view properties or committed config. Read them at runtime with `system.secrets.readSecretValue` (8.3.1+) from a secret provider and clear the value after use. See [references/changed-in-8.3.md](references/changed-in-8.3.md) and [../ignition-security/SKILL.md](../ignition-security/SKILL.md).

## ISA standards in code

- **ISA-101:** grey backgrounds via style class; colour only for abnormal states.
- **ISA-18.2:** Ignition alarm priorities are Diagnostic, Low, Medium, High, Critical. Configure deadband on analog alarms. In 8.3 the tag Alarms folder is replaced by **Alarm Metrics**; the old folder is deprecated but still works, so use Alarm Metrics in new bindings.
- **ISA-95:** hierarchy in tag paths and folders.
- **ISA-88** (batch projects only): phase states Idle, Running, Complete, with Pausing, Paused, Holding, Held, Aborting, Aborted.

Summary: [../ignition-architect/references/isa-standards.md](../ignition-architect/references/isa-standards.md).

## Safety

- Flag any Safety Instrumented System (SIS) contact; engineering review required.
- Do not create connections across IT/OT network zones without explicit authorization.
- Flag all alarm priority changes and interlock modifications for human engineering review.
- Safety-critical architecture changes need Management of Change (MOC) documentation.

## Files, git and scans

In 8.3 Gateway config is on the filesystem, not in an internal database:
- Projects: `data/projects/<project>/` (views, scripts, named queries).
- Gateway config: `data/config/resources/<collection>/...`; tags are JSON under `data/config/resources/core/ignition/tag-definition`, following the Tag Browser path.
- Transaction Groups, Client Tags, Reports and Alarm Pipelines are still `.bin` files. IA recommends gitignoring them; manage them in the Gateway or Designer.

After editing files outside the Designer, make the Gateway pick them up:
- Projects: `system.project.requestScan(30)` (Gateway or Perspective scope; projects only) or the `/data/api/v1/scan/projects` endpoint.
- Config (tags, connections, modes): `POST /data/api/v1/scan/config`, or Scan File System under Platform > System > Modes.

Details: [references/validation-workflow.md](references/validation-workflow.md). Full `.gitignore`, repository layouts and resource collections: [../ignition-config/SKILL.md](../ignition-config/SKILL.md) and [../ignition-config/references/version-control.md](../ignition-config/references/version-control.md).

## Validation (required before "done")

1. LSP: zero errors.
2. `ignition-lint`: no errors; pass rate above 90%.
3. Jython unit tests and Perspective e2e tests where the project has them.
4. Scan projects and/or config, then check the Gateway logs.
5. Designer check with live tags.

Steps and tools: [references/validation-workflow.md](references/validation-workflow.md). Parallel agents: [references/parallel-dev.md](references/parallel-dev.md).

$ARGUMENTS
