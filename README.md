# claude-ignition-skills

Claude Code skills for **Ignition 8.3 SCADA/MES** projects, organized by role and grounded in ISA standards. No framework to install: copy the skills, open your project in Claude Code, and build.

> **On Ignition 8.1?** The 8.1 skills are frozen on the [`release/8.1`](https://github.com/aott33/claude-ignition-skills/tree/release/8.1) branch (tag [`v8.1-final`](https://github.com/aott33/claude-ignition-skills/releases/tag/v8.1-final)). `main` targets Ignition 8.3.x. What changed and why is in [docs/upgrade-notes.md](docs/upgrade-notes.md).

> **Scope:** Ignition 8.3.x, Perspective. Vision is still part of Ignition 8.3 but is out of scope for these skills.

## The Problem

Generic AI tools don't understand Ignition. They write Python 3 instead of Jython 2.7, use Vision APIs in Perspective, call functions that 8.3 deprecated, invent tag paths, put credentials in scripts, and misconfigure alarms. In industrial automation these aren't just bugs - they're risks.

Ignition 8.3 adds new ways to get it wrong: Gateway config is now files under `data/config`, some resources are still binary, scans work differently for projects and config, and secrets have their own providers and API.

## How It Works

1. **`CLAUDE.md`** - auto-loaded every session in this repo. The non-negotiables: Jython 2.7, scripting scope, database access rules, 8.3 platform rules, safety flags, validation.
2. **Skills** - each skill is a short `SKILL.md` plus a `references/` folder that Claude reads only when needed. There are three kinds:
   - **Role skills** load automatically when relevant, or run with `/skill-name`.
   - **Knowledge skills** load automatically and never appear as commands.
   - **Action skills** run only when you invoke them, because they touch live systems or produce a formal verdict.

## Install

Copy the skill folders (all of them; some link to each other's references) into one of the locations Claude Code reads.

**Project skills** (shared with your team through git):

```bash
git clone https://github.com/aott33/claude-ignition-skills.git
mkdir -p /path/to/your-ignition-repo/.claude/skills
cp -R claude-ignition-skills/.claude/skills/* /path/to/your-ignition-repo/.claude/skills/
cp claude-ignition-skills/CLAUDE.md /path/to/your-ignition-repo/   # optional: project-wide rules
```

**Personal skills** (available in every project on your machine):

```bash
mkdir -p ~/.claude/skills
cp -R claude-ignition-skills/.claude/skills/* ~/.claude/skills/
```

Or clone this repo and open it directly with `claude` to try the skills.

## Skills

| Skill | Kind | Use when |
|---|---|---|
| `/ignition-dev` | role | Writing Jython scripts, Perspective `view.json`, UDTs, tag config |
| `/ignition-architect` | role | Designing Gateway architecture, deployment modes, UDT hierarchy, historian, integration |
| `/ignition-ui` | role | Designing ISA-101 Perspective screens, faceplates, navigation, themes |
| `/ignition-plan` | role | PRDs, discovery, epics, licensing, 8.1 to 8.3 migration planning |
| `ignition-config` | knowledge | 8.3 config-as-code: `data/config` layout, resource collections, deployment modes, version control, REST API |
| `ignition-security` | knowledge | Secret providers, `system.secrets`, API keys, guard rails for agents working near a live Gateway |
| `/ignition-review` | action | Formal APPROVE/RETURN review of scripts, views, config diffs or architecture |
| `/ignition-deploy` | action | Commit changes, trigger native config/project scans, verify, promote between deployment modes |
| `/ignition-inspect` | action | Read-only inspection of a live Gateway through an MCP server |

Examples:

```
/ignition-dev Write a UDT definition for a centrifugal pump with ISA-18.2 alarm config
/ignition-architect Design dev/test/prod deployment modes for a two-site water utility
/ignition-ui Design a tank farm overview screen following ISA-101
/ignition-plan Plan the 8.1 to 8.3 upgrade for our three production Gateways
/ignition-review Review this gateway script and the config diff in this branch
/ignition-deploy Scan and verify the tag changes I just committed
```

## Companion Tools (install separately)

These skills point to the following tools instead of re-implementing them:

| Tool | Licence | Used for |
|---|---|---|
| [TheThoughtagen/ignition-ide-plugins](https://github.com/TheThoughtagen/ignition-ide-plugins) | MIT | `system.*` and expression reference, Jython unit tests, Playwright Perspective tests, `ignition-lint`, LSP |
| [WhiskeyHouse/ignition-mcp](https://github.com/WhiskeyHouse/ignition-mcp) | GPL-3.0 | MCP server for `/ignition-inspect`. Installed separately, never vendored. Deny its `script_run` tool |
| [inductiveautomation/ignition-module-starter](https://github.com/inductiveautomation/ignition-module-starter) | none found | Ignition 8.3 module development (JDK 17, `io.ia.sdk.modl`). Out of scope here |
| [TheThoughtagen/agentic-ignition-stack](https://github.com/TheThoughtagen/agentic-ignition-stack) | Apache-2.0 | Docker Compose 8.3 dev Gateway used to verify these skills |

## ISA Standards Covered

| Standard | Where |
|---|---|
| **ISA-101** High Performance HMI | `ignition-ui`, `ignition-review` |
| **ISA-95** Equipment hierarchy | `ignition-architect`, `ignition-dev`, `ignition-plan` |
| **ISA-88** Batch control | `ignition-architect`, `ignition-plan` |
| **ISA-18.2** Alarm management | `ignition-architect`, `ignition-dev`, `ignition-review` |
| **IEC 62443** OT cybersecurity | `ignition-security`, `ignition-architect`, `ignition-plan` |

The ISA summary lives in `.claude/skills/ignition-architect/references/isa-standards.md`.

## Repo Structure

```
claude-ignition-skills/
├── CLAUDE.md                     # auto-loaded 8.3 project rules
├── .claude/skills/
│   ├── ignition-dev/             # SKILL.md + references/ (Jython, validation, parallel dev, 8.3 API changes)
│   ├── ignition-architect/       # SKILL.md + references/ (tags, architectures, ISA standards)
│   ├── ignition-ui/              # SKILL.md + references/ (components, styles)
│   ├── ignition-plan/            # SKILL.md + references/
│   ├── ignition-review/          # SKILL.md + references/ (manual only)
│   ├── ignition-config/          # knowledge: collections, modes, file layout, git, REST API
│   ├── ignition-security/        # knowledge: secrets, API keys, guard rails
│   ├── ignition-deploy/          # action: scan, verify, promote
│   └── ignition-inspect/         # action: read-only MCP inspection
├── docs/
│   ├── upgrade-notes.md          # 8.1 to 8.3 inventory, verified change map, gap analysis
│   └── verification.md           # live 8.3 Gateway verification results
├── scripts/check_skills.py       # CI: frontmatter, links, em-dashes, 8.3 wording
└── THIRD_PARTY_NOTICES.md
```

## Target User

A lead Ignition developer who knows 8.x (UDTs, Perspective, alarms, historian), is comfortable with git and Claude Code, and wants AI help without trusting generic tools in safety-critical environments.

## Credits and Notices

- Technical facts are checked against the [Ignition 8.3 User Manual](https://www.docs.inductiveautomation.com/docs/8.3/intro) and IA release notes. Where a reference repo disagreed, the IA docs won (see `docs/upgrade-notes.md`).
- The skill layout (short SKILL.md with on-demand `references/`, knowledge vs action skills) was informed by the reference repos listed above. No text or code was copied; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- [Automation Professionals Integration Toolkit](https://www.automation-pros.com/toolkit/doc/) - expression functions reference.
- Ignition is a trademark of Inductive Automation. This project is not affiliated with Inductive Automation.
