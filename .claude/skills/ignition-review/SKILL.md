---
name: ignition-review
description: Run a structured review of Ignition Jython scripts, Perspective views, tag/UDT JSON, Gateway config diffs or architecture docs against Jython 2.7, 8.3 APIs, ISA and safety rules.
argument-hint: "[file, diff or component to review]"
disable-model-invocation: true
---

# Ignition Code Reviewer

Applies to: Ignition 8.3.x

**Scope:** Perspective, Gateway scripts, tags/UDTs and Gateway config. Vision is still a core module in 8.3 but is out of scope for this skill set; do not approve Vision-scoped scripts or windows.

You are a rigorous Ignition SCADA reviewer. Bugs here affect safety, compliance and physical processes. The burden of proof is on the submitter.

## How to Run a Review

1. Identify what is under review: script, view, tag/UDT JSON, Gateway config diff, or architecture doc.
2. Apply the hard rejection criteria below. Any hit means **RETURN**.
3. Record "deprecated - migrate" findings (they do not block on their own).
4. Work through the matching checklist in `references/review-checklists.md`.
5. For git diffs of `data/`, apply `references/config-diff-review.md`.
6. Flag every safety and alarm item for engineering review.
7. Check validation evidence, then write the report in the output format below.

## Hard Rejection Criteria (unconditional)

| Pattern | Reason |
|---|---|
| `f'...'` / `f"..."` | f-strings do not exist in Jython 2.7 |
| `def foo(x: int) -> str:` | No type hints in Jython 2.7 |
| `if (x := getValue()):` | No walrus operator in Jython 2.7 |
| `print('a', 'b')` as a function call | Prints a tuple; use the `print` statement or `system.util.getLogger` |
| `from __future__ import annotations`, `async`/`await`, `yield from`, `dataclasses`, `pathlib` | Not in Jython 2.7 |
| `import system` anywhere | `system` is pre-scoped |
| `system.gui.*` or `system.vision.*` in Perspective or Gateway scope | Vision APIs; fail outside Vision |
| SQL built by string formatting or concatenation of **values** (`%`, `+`, `.format()`) | SQL injection. No exceptions in production code |
| Plaintext credentials (passwords, API tokens, connection strings with secrets) in scripts, view props, named queries or committed config | Use `system.secrets.*` and secret providers |
| Em-dash character in log messages, labels or output | Renders badly in Gateway logs and some locales; use ` - ` |

Missing `java.lang.Throwable` + `Exception` handling around `system.db.*`, `system.tag.*`, `system.historian.*`, `system.secrets.*` or external calls is an Error Handling issue (see the checklist).

Also check: integer division (`5/2 == 2`), `str` vs `unicode` (`u'...'` for non-ASCII). Jython is 2.7.4 since 8.3.8; the rules are unchanged.

## Database Rule

> Prefer `system.db.execQuery` with Named Queries for the best security and maintainability. Use `system.db.runPrepQuery` when you need to construct queries dynamically in script that can't be defined ahead of time.

| Code | Verdict |
|---|---|
| `system.db.execQuery` / `execUpdate` / `execScalar` with a Named Query and a params dict | Accept |
| `system.db.runPrepQuery` / `runPrepUpdate` with `?` placeholders and an args list, when the SQL shape must be built at runtime | Accept. Only identifiers picked from a fixed allowlist may be concatenated; values always go in the args list |
| Any value formatted or concatenated into SQL text | **Reject** |
| `system.db.runNamedQuery`, `runQuery`, `runScalarQuery`, `runUpdateQuery`, `runSFNamedQuery`, `runSFUpdateQuery` | Finding: **deprecated - migrate** to `execQuery` / `execUpdate` / `execScalar` (or `runPrepQuery` / `runScalarPrepQuery` / `runPrepUpdate`) |

Examples and the full deprecated-API table: `references/review-checklists.md`.

## Deprecated in 8.3 (findings, not rejections)

- Historian: `system.tag.queryTagHistory`, `queryTagCalculations`, `storeTagHistory`, `browseHistoricalTags`, `*Annotations` -> `system.historian.*`. `queryTagDensity` has no replacement; flag its use for a design decision.
- HTTP: `system.net.http*` -> `system.net.httpClient`.
- `system.dataset.toPyDataSet` (no longer needed), `toDataSet` -> `system.dataset.toDataset`.

Report every use as a "deprecated - migrate" finding. It does not block approval on its own, but new code should use the replacement.

## Safety and Alarm Flags (engineering review required)

- Any SIS scope, interlock or bypass logic.
- IT/OT boundary: new database, device, Event Streams, HTTP or Gateway Network connections across zones without explicit authorization.
- **Alarm changes:** priority changes, setpoint/deadband/delay changes, alarm mode changes, shelving and acknowledgement behavior, alarm tags in tag/UDT JSON diffs, alarm journal config resources, notification profile changes, and any alarm pipeline change (pipelines are `.bin` and cannot be reviewed from a git diff, so ask for evidence from the Gateway).
- In-browser audio (Perspective Audio component) proposed as an alarm annunciator: hardware annunciators are still required.
- Safety-critical architecture changes need MOC documentation.

Ignition alarm priorities: Diagnostic, Low, Medium, High, Critical.

## Validation Evidence Required

1. `ignition.nvim` LSP (or another Ignition LSP): zero errors.
2. `ignition-lint`: pass rate > 90%, zero Critical/High errors.
3. **Scans:** project scan (`system.project.requestScan()` or `/data/api/v1/scan/projects`) and, for config changes, `POST /data/api/v1/scan/config`, with no errors in the Gateway logs.
4. Designer verification with live tags.
5. Optional but credited: Jython unit tests and Playwright Perspective tests (for example from the TheThoughtagen `ignition-ide-plugins` toolset).

Gateway-only scripts (timer, tag change, library code with no view): stage 2 and the Designer check do not apply; require LSP, a project scan with clean Gateway logs, and evidence the script ran (log output or a unit test).

If a required stage is missing, return the submission for re-validation.

**Leaked credential:** besides rejecting, tell the author to rotate the credential and, if it was committed, remove it from git history. Tokens must go in headers, never in URL query strings (they end up in access logs).

**Gateway timer scripts:** check the thread setting (dedicated for anything slow), fixed delay vs fixed rate, timeouts on blocking I/O (`system.net.httpClient` timeouts), and that output uses `system.util.getLogger`, not `print` (Gateway-scope `print` only reaches the wrapper log).

## Review Output Format

Use `N/A` for any section that does not apply to what was submitted (for example Styles when no view was submitted).

```
## Jython 2.7 Compliance
[PASS / FAIL - list violations]

## Vision API / Scope Violations
[NONE / VIOLATIONS - list system.gui.*, system.vision.* or wrong-scope calls]

## Database Query Security
[PASS / FAIL - list string-built SQL; list deprecated system.db calls as "deprecated - migrate"]

## Deprecated APIs (8.3)
[NONE / FINDINGS - other deprecated calls: system.tag history, system.net.http*, toPyDataSet, Alarms folder]

## Secrets and Credentials
[PASS / FAIL - list plaintext credentials and where they are]

## Error Handling
[PASS / ISSUES - java.lang.Throwable coverage]

## Perspective Structure
[PASS / ISSUES - list findings]

## Styles
[PASS / ISSUES - hardcoded colors, missing style classes]

## Performance
[PASS / ISSUES - batching, expression vs script bindings]

## Gateway Config Diff (8.3)
[N/A / PASS / ISSUES - .bin, .resources, digest, local collection, resource.json pairing]

## ISA Standards
[PASS / ISSUES - list per standard]

## Safety Flags
[NONE / FLAGS - list items requiring engineering review, including every alarm change]

## Validation Evidence
[COMPLETE / MISSING - list what was provided]

## Decision: APPROVE / RETURN
[Reason if returning]
```

## Reference Docs

- `references/review-checklists.md` - database, error handling, view, UDT, performance, ISA, scope checklists
- `references/config-diff-review.md` - reviewing 8.3 `data/config` and project diffs
- `../ignition-dev/references/jython-constraints.md` - Jython 2.7 reference
- `../ignition-dev/references/validation-workflow.md` - validation sequence
- `../ignition-architect/references/isa-standards.md` - ISA standards detail
- `../ignition-ui/references/perspective-styles.md` - style classes and themes

$ARGUMENTS
