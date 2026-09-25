# Validation Workflow

Applies to: Ignition 8.3.x

Every Perspective view and Jython script goes through this sequence before it is marked complete. Fix problems at the earliest stage.

```
Edit file -> [1] LSP -> [2] ignition-lint -> [3] tests -> [4] Gateway scan -> [5] Designer
```

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
| Unknown component type | Check the type string against [../../ignition-ui/references/perspective-components.md](../../ignition-ui/references/perspective-components.md) |
| Script syntax error | Re-run Stage 1 on the extracted script |

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
