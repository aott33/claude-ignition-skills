# Ignition 8.1 to 8.3 Upgrade Notes

Working notes for moving `claude-ignition-skills` from Ignition 8.1 to Ignition 8.3.
The frozen 8.1 line lives on branch [`release/8.1`](https://github.com/aott33/claude-ignition-skills/tree/release/8.1) (commit `747250c`, intended tag `v8.1-final`).

Status: steps 1 to 3 (inventory, change map, gap analysis). No skill has been rewritten yet; skill work waits for sign-off on the gap table in section 3.

---

## 1. Inventory (8.1 baseline)

### 1.1 How the repo is organized today

The repo is organized **by role**, not by ISA standard. There is no per-ISA folder layout: the five skills live flat under `.claude/skills/`, and every ISA standard is a cross-cutting topic inside several skills plus `docs/isa-standards.md`. The column "ISA standards touched" below records where each standard shows up.

None of the skills has a `references/` folder. Long material lives in `docs/` at the repo root and is linked with `../../../docs/...` relative paths, which break when a skill is copied on its own into `~/.claude/skills/`.

### 1.2 Skills

| Path | Name | Invocation | Description (current frontmatter) | ISA standards touched |
|---|---|---|---|---|
| `.claude/skills/ignition-dev/SKILL.md` | `ignition-dev` | auto + `/ignition-dev` | Developer mode for 8.1: Jython scripts, Perspective views, UDTs, tag configs | ISA-101, ISA-18.2, ISA-95, ISA-88 |
| `.claude/skills/ignition-architect/SKILL.md` | `ignition-architect` | auto + `/ignition-architect` | Architect mode for 8.1: Gateway architecture, UDT hierarchy, DB schema, ISA-95 model, integration | ISA-95, ISA-18.2, ISA-88, IEC 62443 |
| `.claude/skills/ignition-ui/SKILL.md` | `ignition-ui` | auto + `/ignition-ui` | Perspective UI designer for 8.1: screens, HMI layouts, faceplates, navigation | ISA-101, ISA-18.2 |
| `.claude/skills/ignition-plan/SKILL.md` | `ignition-plan` | auto + `/ignition-plan` | Planner for 8.1: PRDs, discovery, epics, sprints | ISA-95, ISA-101, ISA-18.2, ISA-88, IEC 62443 |
| `.claude/skills/ignition-review/SKILL.md` | `ignition-review` | manual only (`disable-model-invocation: true`) | Reviewer for 8.1: Jython 2.7, ISA, safety, validation evidence | ISA-18.2, ISA-101, ISA-95 |

Supporting material (not skills): `CLAUDE.md` (auto-loaded project context) and eight files in `docs/`: `jython-constraints.md`, `isa-standards.md`, `tag-structure.md`, `system-architectures.md`, `perspective-components.md`, `perspective-styles.md`, `validation-workflow.md`, `parallel-dev.md`.

### 1.3 8.1-specific assumptions

| # | Where | Assumption | Why it matters for 8.3 |
|---|---|---|---|
| A1 | every SKILL.md frontmatter and `Platform:` line, `CLAUDE.md`, `README.md` | "Ignition 8.1" hard-coded; `ignition-plan` says 8.3 "would require updated skills" | Version label and scope statement |
| A2 | `ignition-dev` (Version Control), `docs/validation-workflow.md` lines 88-205 | Tags, UDTs, images and **Gateway config live in the internal SQLite DB**; export with `system.tag.exportTags()` or the third-party ignition-git-module | 8.3 stores Gateway config on the filesystem; this guidance becomes wrong |
| A3 | `docs/validation-workflow.md`, `docs/parallel-dev.md` | Git tree shows only `projects/`; no `config/` resources, no resource collections, no deployment modes, no `.gitignore` guidance | 8.3 git workflow covers Gateway config too |
| A4 | `ignition-dev`, `ignition-ui` | `system.project.requestScan()` is the only way to make the Gateway pick up file edits | 8.3 adds REST scan endpoints for projects and config |
| A5 | `ignition-architect` Step 6, `docs/system-architectures.md` "Scan Classes" | Term "scan class" (8.1 already calls these Tag Groups; "scan class" is 7.x wording) | Terminology fix regardless of 8.3 |
| A6 | `ignition-architect` Steps 5, 8; `ignition-plan` Data Historian, Module Decisions | "Tag Historian" module writing to a SQL DB; historian config drives DB sizing | 8.3 historian changes (Core Historian, SQL historian split) |
| A7 | `ignition-architect` Step 8, `ignition-plan` | Module list without Event Streams, without the 8.3 historian options | New 8.3 modules |
| A8 | `ignition-architect` Step 9, `ignition-plan` epic ordering | "Gateway Configuration" is done by hand in the Gateway web UI, not as versioned files | 8.3 config-as-code and deployment modes change this phase |
| A9 | `ignition-plan` Licensing | 8.1 licensing statements (per-Gateway, unlimited clients/tags), no Maker Edition limits | 8.3 licensing and Maker limits need rechecking |
| A10 | all skills | Database connections, device connections and credentials never discussed; no secrets guidance | 8.3 secret providers and `system.secrets` |
| A11 | all skills | No REST API, API key, or MCP guidance | 8.3 Gateway REST API |
| A12 | `ignition-dev`, `ignition-review`, `docs/validation-workflow.md` | Validation relies on `ignition.nvim` LSP and `ignition-lint` only; no unit tests, no Perspective e2e tests | Testing gap (version-independent) |
| A13 | `ignition-ui`, `docs/perspective-styles.md` | Six built-in themes and theme-file locations as of 8.1 | Recheck against 8.3 Perspective |
| A14 | `ignition-ui` | "Perspective does NOT support audio alarms" | Recheck against 8.3 Perspective |
| A15 | `ignition-dev`, `ignition-review` | Perspective-only, Vision banned | Still valid as a scope choice; Vision is not removed in 8.3 |
| A16 | `ignition-review` | Rejects `system.db.runPrepQuery` with `?` placeholders as "string-built SQL" | Not version-specific, but inaccurate: prep queries are parameterized. Flag for review |
| A17 | `docs/validation-workflow.md` | Path `com.inductiveautomation.perspective/views/<View>/view.json`, `ignition/script-python/...` | Project resource layout (check whether it changed in 8.3) |
| A18 | none | No module-development guidance | 8.3 Module SDK (JDK, Gradle plugin) is a possible new skill |

No `.proj` export guidance and no Vision-only guidance were found in the skills (Vision is only mentioned to exclude it).
