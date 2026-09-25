# Parallel Development: File Isolation Rules

Applies to: Ignition 8.3.x

When several agents or developers work on one Ignition system at once, conflicts are hard to avoid without deliberate isolation. Ignition resources are mostly JSON, and git cannot merge JSON reliably. In 8.3 this applies to Gateway config as well as projects, because tags, UDTs and connections are now files under `data/config/`.

## The core rule

**One agent or developer per file at a time.** Assign work by file or folder, not by feature.

---

## Isolation by resource type

### Perspective views

Each view is a folder with `view.json` and `resource.json`:
```
data/projects/<Project>/com.inductiveautomation.perspective/views/<ViewPath>/
```

**Rule:** one agent per view folder. Commit `view.json` and its `resource.json` together; IA's team guidance warns against committing a `resource.json` change without the matching `view.json` change. The same applies to `com.inductiveautomation.perspective/session-props/props.json`.

Safe:
```
Agent A -> views/Overview/
Agent B -> views/TankDetail/
Agent C -> views/AlarmSummary/
```

Unsafe:
```
Agent A -> views/TankDetail/  (adding an alarm banner)
Agent B -> views/TankDetail/  (adding a trend)
-> both edit the same view.json
```

### Project library scripts

```
data/projects/<Project>/ignition/script-python/<package>/code.py
```

**Rule:** one agent per script package. Python files merge line by line, but shared helper functions still conflict. Create a shared helper in one story first, merge it, then use it in dependent stories.

### Named queries

```
data/projects/<Project>/ignition/named-query/<QueryName>/
```

Each named query is a SQL file plus JSON metadata. **Rule:** one agent per query folder.

### Tags and UDTs (Gateway config)

In 8.3 tag configuration is JSON under `data/config/resources/core/ignition/tag-definition`, laid out by Tag Browser path. Organize tags by the ISA-95 hierarchy:
```
[default]Site/Area/Line/Cell/Equipment/
```

**Rule:** assign tag work by hierarchy branch, and never give overlapping branches to parallel agents. Because files follow the Tag Browser path, separate branches usually mean separate files.

Safe:
```
Agent A -> [default]DairyPlant/Refrigeration/
Agent B -> [default]DairyPlant/Pasteurization/
```

Unsafe:
```
Agent A -> [default]DairyPlant/Refrigeration/CoolingLoop1/
Agent B -> [default]DairyPlant/Refrigeration/   <- contains Agent A's branch
```

**UDT definitions:** one agent per UDT definition, written complete in one pass. A change to a definition reaches every instance, so a UDT edit is never parallel with work on its instances.

### Deployment-mode overrides

A resource can be overridden in another resource collection (for example a `<mode>` folder next to `core`). The base resource and its override are separate files but one logical resource. **Rule:** the same agent owns a resource and all of its overrides. See [../../ignition-config/SKILL.md](../../ignition-config/SKILL.md).

### Resources that are not diffable

Transaction Groups, Client Tags, Reports and Alarm Pipelines are still `.bin` files in 8.3, and IA recommends gitignoring them. Git cannot show or merge their changes. **Rule:** only one person changes each of these at a time, in the Gateway or Designer, and records the change in the story. Alarm pipeline changes also need engineering review.

---

## Git workflow

### Branches

One feature branch per story:

```bash
# {epic}-{story}-{slug}
git checkout -b 3-2-tank-detail-view
git checkout -b 4-1-motor-udt-definition
```

### Merge and rebase often

Long-lived branches collect merge debt. Merge finished stories promptly and rebase long-running branches on `main`:

```bash
git fetch origin main
git rebase origin/main
```

### After a pull on a Gateway

Pulled files are not live until the Gateway scans them. Scan projects and config as described in [validation-workflow.md](validation-workflow.md) (Stage 4).

### Merge strategy by file type

| File type | Strategy | Notes |
|---|---|---|
| `view.json` + `resource.json` | One wins; no JSON merge | Prevent by isolation |
| Tag and UDT JSON | One wins | Assign by hierarchy branch |
| Named query SQL + JSON | One wins | Prevent by isolation |
| Jython `code.py` | Line-level merge | Shared helpers still conflict |
| `.bin` resources | Not in git | One owner at a time |
| `.resources/`, `*.digest.json` | Not in git | Per-system cache |

---

## Story assignment checklist

- [ ] Each story owns distinct files or folders
- [ ] No two active stories touch the same view folder
- [ ] No two active stories touch the same UDT definition, or a UDT and its instances
- [ ] Script stories use different packages, or the shared helper is merged first
- [ ] Tag work is split by non-overlapping hierarchy branches
- [ ] A resource and its deployment-mode overrides have one owner
- [ ] `.bin` resources (including alarm pipelines) have a single named owner
- [ ] Stories that depend on a new shared helper are blocked until it merges

---

## Layout quick reference

```
data/
|- projects/<Project>/
|  |- project.json
|  |- com.inductiveautomation.perspective/
|  |  |- views/<ViewPath>/{view.json, resource.json}   <- one owner per view
|  |  `- session-props/props.json
|  `- ignition/
|     |- script-python/<package>/code.py               <- one owner per package
|     `- named-query/<QueryName>/                      <- one owner per query
`- config/resources/
   |- core/ignition/tag-definition/...                 <- assign by hierarchy branch
   `- <mode>/...                                       <- same owner as the base resource
```

Full layout, collections and `.gitignore`: [../../ignition-config/references/version-control.md](../../ignition-config/references/version-control.md).

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide/best-practices-for-team-environments
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/gateway-folder-structure
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/resource-json-file
- https://www.docs.inductiveautomation.com/docs/8.3/platform/sql-in-ignition/named-queries
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide
