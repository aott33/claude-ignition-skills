# Validation Workflow

Applies to: Ignition 8.3.x

Every Perspective view and Jython script goes through this sequence before it is marked complete. Fix problems at the earliest stage.

```
Edit file -> [1] LSP -> [2] ignition-lint -> [3] tests -> [4] Gateway scan -> [4b] render check (views) -> [5] Designer
```

Labels: **[IA docs]** from the IA 8.3 manual; **[live 8.3.9]** verified on a live 8.3.9 Gateway (see the repository's `docs/verification.md`); **[observed in the 8.3.9 module]** read from the Perspective module's files, not a documented API.

---

## Stage 1: LSP (scripts)

**Catches:** Python 3 syntax in Jython (f-strings, type hints, `print()`), undefined names, unknown `system.*` functions, deprecated calls.

**Tool:** an Ignition-aware language server. TheThoughtagen/ignition-ide-plugins ships `ignition-lsp` with editor plugins for Neovim (`ignition.nvim`), VS Code and Zed. Install it per that repository's README.

**Pass:** zero errors in the diagnostics list. In Neovim:

```
:lua vim.diagnostic.setloclist()
:lopen
```

Do not go on to Stage 2 with LSP errors.

### Offline Jython syntax check (no LSP, no Gateway)

Compile scripts with real Jython 2.7.4, the version 8.3.8 and later run. Use `org.python:jython-standalone:2.7.4` from Maven Central (the 8.3.9 check used a jar with sha1 `df61c8c28ce458bc84d92a12aaaf20b15dbc55db`) and any system Java:

```python
# jycheck.py - run with: java -jar jython-standalone-2.7.4.jar jycheck.py file1.py file2.py
import sys
bad = 0
for fn in sys.argv[1:]:
    try:
        compile(open(fn).read(), fn, 'exec')
        print 'OK   %s' % fn
    except SyntaxError, ex:
        bad += 1
        print 'FAIL %s: %s' % (fn, ex)
sys.exit(1 if bad else 0)
```

- Jython 2.7.4 `compile()` rejects f-strings and type annotations.
- **Python 3's `lib2to3` is not a Jython check.** Its Python 2 grammar accepted both f-strings and annotations in a test on Python 3.11.
- To check view scripts, extract each one from `view.json` and wrap it in its function header, then compile it:
  - script transforms: `def transform(self, value, quality, timestamp):`;
  - `onChange` scripts: `def valueChanged(self, previousValue, currentValue, origin, missedEvents):`;
  - `script` actions: `def runAction(self, event):`.

  These are the headers the 8.3.9 module uses **[observed in the 8.3.9 module]**. The verified project's extracted scripts all compiled this way **[live 8.3.9]**.
- A compile pass checks syntax only. Names and `system.*` signatures still need the LSP, lint or a run on a test Gateway.

---

## Stage 2: ignition-lint (views and scripts)

**Catches:** invalid `view.json` structure, malformed bindings, unknown component types, Jython syntax errors inside view scripts, naming and expression problems.

**Tool:** an `ignition-lint` command-line linter for Ignition project files. One maintained option is the `ignition-lint-toolkit` package on PyPI (repository TheThoughtagen/ignition-lint):

```bash
pip install ignition-lint-toolkit

# Lint any directory (finds view.json and .py files)
ignition-lint --target path/to/project

# Lint a whole project with the full rule profile
ignition-lint --project data/projects/MyProject --profile full

# Fail the run on errors (for CI or a pre-commit hook)
ignition-lint --project data/projects/MyProject --fail-on error
```

Check `ignition-lint --help` for the options of the version you installed.

**Severity handling:**

| Severity | Action |
|---|---|
| Error (invalid JSON, broken binding, script syntax error) | Block: fix before continuing |
| Warning | Fix, or record the justification in the change description |
| Other levels | Advisory |

**Pass:** zero errors and a pass rate above 90% (project rule).

Common fixes:

| Problem | Fix |
|---|---|
| Invalid JSON | Trailing commas, missing brackets, unescaped quotes |
| Malformed binding | Compare with a binding saved by the Designer; for tags, `config.tagPath` and `config.mode` |
| Unknown component type | Check the type string against a Designer-saved view or the module's `ia.components.json` (below); see [../../ignition-ui/references/perspective-components.md](../../ignition-ui/references/perspective-components.md) |
| Script syntax error | Re-run Stage 1 on the extracted script |

### Component ids and schemas from the Perspective module

Do not guess component `type` ids or prop names. Read them from the module your Gateway runs.
- In the Docker image the built-in modules are in `/usr/local/bin/ignition/user-lib/modules` **[IA docs]**.
- The `.modl` file is a zip archive **[observed in the 8.3.9 module]**.

```bash
# Read-only copy out of a local test container; use the module file of the Gateway version you target
docker cp <container>:/usr/local/bin/ignition/user-lib/modules/Perspective-module.modl .
unzip -q Perspective-module.modl -d modl
unzip -q -o modl/perspective-common-*.jar 'ia.components.json' 'schemas/*' 'descriptors/*' -d common
python3 -c "import json; print([c['id'] for c in json.load(open('common/ia.components.json'))['components']])"
```

What you get **[observed in the 8.3.9 module]**:
- `ia.components.json`: 70 components in 8.3.9, each with `id`, a `schema` holding every prop with its default, and `childPositionSchema`.
- `schemas/`: binding config schemas (`binding-tag.json`, `binding-expr.json` and so on), transforms, `style-properties.schema.json`, `session-props.json`.
- `descriptors/`: the objects that event scripts receive, for example `page_startup.json`.
- `perspective-icons-*.jar`: the built-in icon SVGs, a reference for the sprite format.

Every prop a hand-written component omits takes its schema default (see the Alarm Status Table notes in `../../ignition-ui/references/perspective-components.md`), so check those defaults.

---

## Stage 3: Tests (install, do not rebuild)

This skill set does not ship its own test framework. Use the TheThoughtagen/ignition-ide-plugins Claude Code plugin:

```bash
claude plugin marketplace add TheThoughtagen/ignition-ide-plugins
claude plugin install ignition-scada@ignition-tools
```

The plugin provides:
- **Jython unit tests:** an `init-testing` command that scaffolds a test framework into the project, and a `test` command that runs tests on a Gateway.
- **Perspective e2e tests:** an `init-e2e` command that scaffolds Playwright tests for Perspective views; `test` runs them too.

Cautions when using it:
- The Jython test runner is exposed through WebDev endpoints in the project. Deploy them only on development or test Gateways, never on production.
- The plugin's docs trigger scans through a third-party scan module. Use the native 8.3 scans from Stage 4 instead.
- Tests that write tags must target simulator or test tags, never live process tags.

**Pass:** all tests green where the project has tests. If a project has no tests yet, say so in the change description instead of claiming a pass.

---

## Stage 4: Gateway pickup (native 8.3 scans)

Do not rely on the Gateway noticing file edits on its own. IA documents that changes made through the file system (file edits, VCS) are not recognized automatically for Gateway config, and its version control guide says to scan config and projects after a `git pull`. After editing files, trigger the scan that matches what changed.

| What changed | How to scan |
|---|---|
| Project files under `data/projects/` (views, scripts, named queries) | `system.project.requestScan(30)` from a Gateway or Perspective script; or Scan File System on Platform > System > Projects; or the `/data/api/v1/scan/projects` endpoint |
| Gateway config under `data/config/` (tags, UDTs, connections, modes) | `POST /data/api/v1/scan/config`; or Scan File System on Platform > System > Modes (this button scans the whole Ignition file system) |

`system.project.requestScan([timeout])` scans **projects only**; it blocks up to `timeout` seconds (default 10). It does not load tag or other config changes.

REST scans need an API key sent in the `X-Ignition-API-Token` header:

```bash
# Token from an environment variable, never typed into a committed file
curl -sS -X POST \
  -H "X-Ignition-API-Token: $IGNITION_API_TOKEN" \
  "https://gateway.example:8043/data/api/v1/scan/config"

curl -sS -X POST \
  -H "X-Ignition-API-Token: $IGNITION_API_TOKEN" \
  "https://gateway.example:8043/data/api/v1/scan/projects"
```

Both scans are `POST` (the Gateway's `/openapi` spec lists "Request Configuration Scan" and "Request Project Scan"). A `GET` on the same paths returns scan status: `{"scanActive": false, "lastScanTimestamp": ..., "lastScanDuration": ...}`. Verified on a live 8.3.9 Gateway:

- The token value is `<tokenName>:<secret>`. No token returns 401.
- What a key can do depends on the Gateway's Access, Read and Write permissions (Security > General Settings) matched against the key's security levels. `GET` calls need Access and Read; the scan `POST`s need **Write**. A key whose level is not in those permissions gets 403 even on `GET /data/api/v1/gateway-info`.

Check `lastScanTimestamp` moved after your `POST` to confirm the scan ran. API key creation and storage: [../../ignition-security/SKILL.md](../../ignition-security/SKILL.md).

**Pass:** the Gateway logs show the project or config reload with no errors for the resources you changed.

---

## Stage 4b: Render check in a headless browser (views)

A scan with no errors does not prove a view works. In a verified 8.3.9 project (the repository's `docs/verification.md`, fourth verification) two major defects passed the project scan with no Gateway log warning:
- a style class that never compiled;
- alarm rows in the component's default colours.

Both were found by rendering the views and reading the served CSS and computed styles **[live 8.3.9]**. Take screenshots and run these checks before you say a view works. This stage supplements Stage 5; it does not replace the Designer check.

**Where:** a local or dev test Gateway only.
- Writing project files that a running Gateway reads (for example a bind mount), and triggering its scans, applies changes to that Gateway. Get the user's explicit approval first (CLAUDE.md, live Gateways).
- Never render-test against production.

**How** **[live 8.3.9]**:
- A project whose security settings allow anonymous sessions is served at `http://<gateway>:8088/data/perspective/client/<project>/<route>`, with no login.
- A throwaway test project works the same way: add a project folder under `data/projects`, run a project scan, render it, then delete the folder and scan again. `GET /data/api/v1/projects/list` confirms it is gone.
- That project's harness used Python Playwright with Chromium:
  - it launched Chromium with `--no-proxy-server` for a Gateway on `127.0.0.1`;
  - it waited 7 to 8 s after `domcontentloaded`;
  - its renders covered 390x844, 768x1024 and 1440x900, in each theme.
- Choose the theme per run with `?theme=<name>` when the project handles it (see `../../ignition-ui/references/perspective-styles.md`). Otherwise set the `href` of `link[href*="/themes/"]` to `/data/perspective/themes/<theme>.css` and wait for its `load` event.
- Click components by `meta.domId`, for example `#MenuToggle`, not by text or position.

**Checks** (its acceptance run used all of them; the first six ran on 32 route x size x theme renders) **[live 8.3.9]**:

| Check | How | Catches |
|---|---|---|
| Page errors, console errors and warnings | `page.on("pageerror")`, `page.on("console")`; expect zero | Missing icon names (`React.cloneElement(...) ... null`), client exceptions |
| Error placeholders | Visible elements (non-zero box) whose class contains `error`, `Error` or `missing` | Components or embedded views that failed to load |
| Quality overlays | Visible elements whose class contains `quality` (base theme `.ia_qualityOverlay--error`, `--unknown`) | Bad or unknown binding quality |
| Bad values in text | `Bad_`, `Uncertain`, `NaN`, `undefined`, `null`, unresolved `{...}` in visible text | Broken bindings and transforms. `document.body.innerText` also holds Perspective's hidden session panel text ("No Connection to Gateway", "Trial Mode Active", "... by null"); check visible elements or allow-list those strings |
| Theme | `link[href*="/themes/"]` ends in `<theme>.css` | Theme not applied |
| Layout | `document.documentElement.scrollWidth <= innerWidth`; leaf text elements whose `scrollWidth > clientWidth` with overflow not visible | Horizontal scroll; text cut off by ellipsis at phone width |
| Styles really apply | The served `/data/perspective/style-classes/<project>/<hash>/style.css` contains `.psc-<escaped path>` for every class a view uses; `getComputedStyle` on sample elements matches the theme variables | Nested (non-leaf) style classes that never compile; properties a class cannot emit; inline defaults that beat a class |
| Static colours | No hex, `rgb()`, `hsl()` or named colours in `view.json` or `style.json`, only `var(--...)`. Colour values belong in the theme: write the ISA-101 baseline classes as `var(--isa-fault)`, `var(--isa-warning)` and so on, with the hex values from the baseline tables defined as `--isa-*` variables in the theme | Hardcoded colours that break theming |

Also check the Gateway log for warnings and errors over the render window.

**Alarm scenarios:**
- Raise or clear alarms only on simulated or test tags on a local test Gateway, and only with the user's approval.
- Do not acknowledge alarms yourself: acknowledging is an operator action an agent must never do (`../../ignition-security/references/agent-guardrails.md`). When a test needs the acknowledged state, ask the user to acknowledge.
- Put the simulation back to its normal state afterwards.
- Any change to alarm colours, blinking or acknowledgement that the render check leads to goes through engineering review.

**Trial Gateways** **[live 8.3.9]**:
- A trial Gateway counts down its trial window, and the session status panel shows "Remaining trial time".
- Read `GET /data/api/v1/trial` (`licenseMode`, `trialState`, `trialSecondsLeft`, `expired`) before a long render run and during it, so an expiring trial is not mistaken for a view defect. The 8.3.9 `/openapi` lists only `GET` on this route.
- Do not reset a trial yourself: `../../ignition-security/references/agent-guardrails.md` denies `rig_trial_reset` because it changes licensing state. If the trial is about to expire, stop and ask the user.

**Pass:** zero findings in the table above at every target size and theme, screenshots reviewed, and a clean Gateway log.

---

## Stage 5: Designer check

Open the Designer and confirm the change against live data. This catches what static checks cannot:
- A tag exists but has the wrong data type for the binding.
- Components interact badly at runtime.
- Script logic fails with real values.
- Parameters arrive wrong in embedded views or popups.
- Too many bindings or an expensive query slow the view.

Perspective views:
- [ ] View opens without errors
- [ ] All components render (none blank or hidden by mistake)
- [ ] Tag bindings show live values with good quality
- [ ] Event handlers run without errors
- [ ] Parameters pass correctly to embedded views and popups
- [ ] Layout works at the target screen sizes

Jython scripts:
- [ ] Script compiles in the Designer
- [ ] Runs without exceptions in a test context
- [ ] Side effects are correct (tag writes succeed, queries return expected data)

---

## Project and config layout (8.3)

```
data/
|- projects/
|  `- <Project>/
|     |- project.json
|     |- com.inductiveautomation.perspective/
|     |  |- views/<ViewPath>/view.json        <- lint here (plus resource.json)
|     |  `- session-props/props.json
|     `- ignition/
|        |- script-python/<package>/code.py   <- LSP here
|        `- named-query/<QueryName>/          <- SQL file plus JSON metadata
`- config/
   |- resources/
   |  |- core/ignition/tag-definition/...     <- tag JSON, by Tag Browser path
   |  |- external/  local/  <mode>/           <- other resource collections
   `- ...
```

Each project resource folder has a `resource.json` with metadata and a file manifest. Commit a `resource.json` change only together with the matching data file change (for example `view.json`).

---

## Version control in 8.3

In 8.1 tags, UDTs and Gateway config lived in an internal SQLite database and had to be exported. In 8.3 they are files, so there is no export step:

| Resource | 8.3 storage | Git approach |
|---|---|---|
| Perspective views, project scripts, named queries | JSON, `.py` and SQL files under `data/projects/` | Commit directly |
| Tags and UDT definitions | JSON under `data/config/resources/` (tags under `core/ignition/tag-definition`) | Commit directly. Tag files follow the Tag Browser path; mind the 255-character path limit on Windows |
| Database and device connections, other Gateway config | JSON under `data/config/resources/` | Commit, but never commit plaintext credentials; use secret providers |
| Transaction Groups, Client Tags, Reports, Alarm Pipelines | `.bin` files | IA recommends gitignoring them. Manage them in the Gateway or Designer |
| `.resources/` folders, `*.digest.json` | Per-system cache | Gitignore |
| `data/config/resources/local`, `data/config/local` | Machine-specific | Gitignore |

After `git pull` on a Gateway, run both scans from Stage 4.

For IA's full recommended `.gitignore`, the four repository layouts (whole `data/`, curated container mounts, projects only, several Gateways in one repo) and resource collection rules, see [../../ignition-config/SKILL.md](../../ignition-config/SKILL.md) and [../../ignition-config/references/version-control.md](../../ignition-config/references/version-control.md).

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide/best-practices-for-team-environments
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-project/system-project-requestScan
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/api-keys
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/gateway-folder-structure
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/resource-json-file
- https://www.docs.inductiveautomation.com/docs/8.3/platform/sql-in-ignition/named-queries
- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide
- https://www.docs.inductiveautomation.com/docs/8.3/platform/advanced-deployments/docker-image (built-in module folder)
- https://repo1.maven.org/maven2/org/python/jython-standalone/2.7.4/jython-standalone-2.7.4.jar (Jython 2.7.4 standalone jar; `.sha1` beside it)
