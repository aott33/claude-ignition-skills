# claude-ignition-skills

A starter kit for using Claude Code on **Ignition 8.1 SCADA/MES** projects. No framework installs — just clone, open in Claude Code, and start building.

> **On Ignition 8.1?** The 8.1 skills are frozen on the [`release/8.1`](https://github.com/aott33/claude-ignition-skills/tree/release/8.1) branch (tag `v8.1-final`). `main` is moving to Ignition 8.3; see [docs/upgrade-notes.md](docs/upgrade-notes.md).

> **Platform:** Ignition 8.1, Perspective module only. Vision module projects require a separate skill set. Ignition 8.3 introduces breaking changes not covered here.

## The Problem

Generic AI tools don't understand Ignition. They hallucinate Jython 2.7 syntax, use Vision APIs in Perspective scripts, invent UDT properties, bind to non-existent tag paths, and misconfigure alarms. In industrial automation, these aren't just bugs — they're risks.

## How It Works

This repo provides **domain-aware context** through two mechanisms:

1. **`CLAUDE.md`** — Auto-loaded every session. Gives Claude the critical Ignition constraints (Jython 2.7 rules, Perspective-only scope, safety flagging, validation requirements) without you doing anything.

2. **Skills** — Role-specific playbooks Claude loads automatically when relevant, or that you invoke directly with `/skill-name`. Each skill enforces platform constraints, ISA standards, and safety practices for its domain.

No npm. No framework. Just clone and go.

## Quick Start

```bash
git clone https://github.com/your-username/claude-ignition-skills.git
cd claude-ignition-skills

# Open with Claude Code
claude .
```

`CLAUDE.md` is automatically loaded. Claude now knows this is an Ignition 8.1 Perspective project and will enforce Jython 2.7 constraints, safety flagging, and validation requirements in every session.

## Skills

Claude loads these automatically when relevant, or invoke directly with `/skill-name`.

### `/ignition-dev`
**Use when:** writing Jython scripts, Perspective views, UDT definitions, tag configurations, or any Ignition platform code.

Enforces Jython 2.7 constraints, Perspective-only APIs (`system.perspective.*` — never `system.gui.*`), all four binding types with expression binding preference, `java.lang.Throwable` error handling for Java/JDBC exceptions, named-query-only database access, UDT patterns, ISA standards in code, `system.project.requestScan()` for view propagation, and the full validation workflow.

```
/ignition-dev Write a UDT definition for a centrifugal pump with ISA-18.2 alarm config
```

### `/ignition-architect`
**Use when:** designing Gateway deployment architecture, UDT hierarchy, database schema, or integration architecture.

Covers the full Gateway architecture decision framework (Basic, Redundancy, Scale-Out, Hub-and-Spoke, Edge, Enterprise, Cloud), ISA-95 equipment hierarchy, database-driven master data model, UDT inheritance design, scan class design, historian configuration, Ignition module selection, implementation sequencing, and ISA-88 batch architecture.

```
/ignition-architect Design the Gateway architecture and UDT hierarchy for a multi-site dairy operation
```

### `/ignition-ui`
**Use when:** designing Perspective screens, navigation flows, operator UX, faceplates, or style systems.

Covers ISA-101 High Performance HMI principles, mandatory global styles and style classes (never hardcoded colors), expression binding patterns and the Integration Toolkit for performant UI logic, `system.perspective.*` navigation and popup APIs, `view.json` structure, `system.project.requestScan()` for Designer propagation, the full Perspective component catalog, and reusable parameterized view patterns.

```
/ignition-ui Design a tank farm overview screen following ISA-101 principles
```

### `/ignition-plan`
**Use when:** writing PRDs, conducting discovery, scoping epics, planning sprints, or defining acceptance criteria.

Covers industrial requirements discovery (equipment, alarms, operator workflows, integration systems, architecture type, migration strategy), PRD structure for Ignition 8.1 projects, FAT/SAT acceptance criteria, licensing guidance, epic ordering aligned with Ignition's implementation sequence, and safety scoping.

```
/ignition-plan Help me scope a PRD for a cheese production facility — continuous process, 3 sites
```

### `/ignition-review`
**Use when:** reviewing Jython scripts, Perspective views, UDT definitions, or architecture docs for production readiness.

Runs a structured review against: Jython 2.7 compliance, Vision API violations (`system.gui.*` = unconditional rejection), SQL injection (`system.db.runQuery` with string formatting = rejection), `java.lang.Throwable` error handling coverage, style class usage (no hardcoded colors), expression vs script binding performance, ISA standards, safety flags, and validation evidence. Returns `APPROVE` or `RETURN` with specific findings.

**Must be invoked manually** — Claude will not trigger this automatically.

```
/ignition-review Review this gateway event script and pump view.json for production readiness
```

## Reference Docs

Use `@` to pull these into context when you need detailed reference:

| Doc | Use for |
|---|---|
| `@docs/jython-constraints.md` | Jython 2.7 syntax, tag read/write patterns, `java.lang.Throwable` error handling |
| `@docs/isa-standards.md` | ISA-101, ISA-95, ISA-88, ISA-18.2, IEC 62443 |
| `@docs/tag-structure.md` | Tag paths, UDT patterns, ISA-95 folder structure, DB schema, alarm JSON |
| `@docs/system-architectures.md` | Gateway architecture patterns — Basic, Hub-and-Spoke, Scale-Out, Redundancy, Edge, Enterprise, Cloud |
| `@docs/perspective-components.md` | Perspective component reference with JSON examples |
| `@docs/perspective-styles.md` | Style classes, built-in themes, CSS variables, ISA-101 baseline style definitions |
| `@docs/validation-workflow.md` | ignition-lint + LSP + Gateway validation steps |
| `@docs/parallel-dev.md` | File isolation rules for multi-agent parallel work |

## Typical Workflows

### Starting a new project

```
/ignition-plan Help me scope a PRD for a water treatment SCADA system
```

### Designing the architecture

```
/ignition-architect Based on this PRD, design the Gateway architecture, UDT hierarchy, and implementation sequence
```

### Building screens

```
/ignition-ui Design the equipment detail faceplate for a centrifugal pump
```

### Writing code

```
/ignition-dev Implement the pump faceplate as a Perspective view.json with parameter-driven tag bindings
```

### Reviewing work

```
/ignition-review Review this Jython gateway script and pump view.json for production readiness
```

## Repo Structure

```
claude-ignition-skills/
├── CLAUDE.md                            # Auto-loaded: baseline Ignition 8.1 context
├── .claude/
│   └── skills/
│       ├── ignition-dev/
│       │   └── SKILL.md                 # /ignition-dev — auto-loaded when writing Ignition code
│       ├── ignition-architect/
│       │   └── SKILL.md                 # /ignition-architect — auto-loaded for architecture work
│       ├── ignition-ui/
│       │   └── SKILL.md                 # /ignition-ui — auto-loaded for Perspective UI work
│       ├── ignition-plan/
│       │   └── SKILL.md                 # /ignition-plan — auto-loaded for project planning
│       └── ignition-review/
│           └── SKILL.md                 # /ignition-review — manual only (disable-model-invocation)
├── docs/
│   ├── jython-constraints.md            # Jython 2.7 reference + java.lang.Throwable patterns
│   ├── isa-standards.md                 # ISA-101, 95, 88, 18.2, IEC 62443
│   ├── tag-structure.md                 # Tag paths, UDT patterns, DB schema, alarm JSON
│   ├── system-architectures.md          # Gateway architecture patterns and decision guide
│   ├── perspective-components.md        # Perspective component reference
│   ├── perspective-styles.md            # Style classes, themes, CSS variables
│   ├── validation-workflow.md           # ignition-lint + LSP + Gateway workflow
│   └── parallel-dev.md                  # File isolation for multi-agent parallel work
└── README.md
```

## ISA Standards Covered

| Standard | Coverage |
|---|---|
| **ISA-101** | High Performance HMI — color discipline, style classes, information density, navigation |
| **ISA-95** | Equipment hierarchy — tag folder structure, UDT design, DB schema |
| **ISA-88** | Batch control — procedural model, phase state machine, recipe management |
| **ISA-18.2** | Alarm management — priorities, states, deadband, shelving, rationalization |
| **IEC 62443** | OT cybersecurity — network zones, IT/OT boundaries, SIS scope |

## Target User

Lead Ignition Developer who:
- Has deep Ignition 8.1 expertise (UDTs, Perspective, alarms, historian)
- Is comfortable with Git and Claude Code
- Wants AI productivity gains without trusting generic tools in safety-critical environments

## Acknowledgments

- [Automation Professionals Integration Toolkit](https://www.automation-pros.com/toolkit/doc/) — expression functions reference
