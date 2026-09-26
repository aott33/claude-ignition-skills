---
name: ignition-config
description: Ignition 8.3 config-as-code facts - resource collections, deployment modes, data/config layout, git, REST API. Use when reading or editing Gateway config files. Not for Jython.
user-invocable: false
---

# Ignition 8.3 Configuration as Code

Applies to: Ignition 8.3.x

Background knowledge for any task that touches Gateway configuration files, deployment modes, version control of a Gateway, or the Gateway REST API. For the hands-on workflows, the user runs `/ignition-deploy` (commit, scan, verify, promote) or `/ignition-inspect` (read-only look at a live Gateway).

## The core fact

In 8.1 Gateway configuration lived in an internal SQLite database. In 8.3 it lives on the filesystem under `data/config/`, and projects live under `data/projects/`. After an upgrade the old internal database is still on disk but is no longer used. Treat any guide that says 8.3 config is in the internal database as stale.

## Resource collections (summary)

Collections are layered. A child inherits from its parent and can override it.

| Collection | Editable from the Gateway? | Use it for |
|---|---|---|
| `system` | No (built in, immutable; can be overridden) | Resources Ignition injects itself, for example the MariaDB JDBC driver |
| `external` | No (read-only in the Gateway) | Centrally managed config the Gateway must not change. IA says a VCS may place resources here, but `core` ranks above it: resources the Gateway generates in `core` (UDT definitions, `security-properties`) hide copies in `external` |
| `core` | Yes | The default and the shared base every mode inherits. In a git workflow, commit it (minus per-Gateway credentials; see `references/docker.md`) |
| `<mode>` | Yes | User-created deployment modes (Dev, Test, Prod...) that override `core` |
| `local` | Yes | Machine-specific data (for example certificate details). Modes do not inherit from it |

Inheritance order: `system`, then `external`, then `core`, then the active user-created mode. Only one mode is active. Details, `local` overrides (8.3.7+), redundancy caveats and `backupConfig.json`: see `references/collections-and-modes.md`.

## Rules to follow

1. **Changing the active mode is a restart.** It is set in `data/ignition.conf` with a `wrapper.java.additional.N=-Dignition.config.mode=<ModeName>` line. The Gateway web page cannot switch it. On a redundant pair the setting does not sync, so set both nodes and restart both.
2. **File edits are not picked up automatically.** After changing files under `data/config` (by hand, script or `git pull`), run a config scan: **Scan File System** on Platform > System > Modes, or `POST /data/api/v1/scan/config`. After changing project files, scan projects: Platform > System > Projects, `POST /data/api/v1/scan/projects`, or `system.project.requestScan([timeout])` from Gateway or Perspective scope. Do not rely on file watching.
3. **IA calls hand-editing config files a last resort.** Prefer the Gateway web page, the Designer or the REST API to create resources, overrides and modes. Edit files directly only when the user has chosen a files-first (git) workflow, and scan afterwards.
4. **Some resources are still binary.** Transaction Groups, Client Tags, Reports and Alarm Pipelines are stored as Java `.bin` files. IA recommends gitignoring them. Never try to hand-edit a `.bin` file.
5. **Never commit machine-specific or secret material.** Keep `config/local`, `config/resources/local`, certificates, keystores, `.resources/` caches and `*.digest.json` out of git, and the per-Gateway `core` resources (user sources, OPC UA connection, system properties, first-boot singletons). Use `references/gitignore.sample` as a starting point.
6. **Tag JSON paths can be long.** Tags are stored as JSON under `data/config/resources/core/ignition/tag-definition` following the Tag Browser path. Windows has a 255-character path limit; keep folder and tag names short.
7. **Projects are not overridable by modes.** Deployment modes, modules, projects and licenses cannot have resource overrides.
8. **Pair `resource.json` with its content file.** Do not commit a `resource.json` change without the matching `view.json` (IA team guidance; the same applies to Perspective `session-props/props.json`).

## Safety

- A change of mode or of a `core` resource can repoint a Gateway at different devices or databases. Treat mode switches and overrides of device, database, OPC UA or Gateway Network resources as **IT/OT boundary** changes: confirm the target network zone with the user before proposing them.
- Anything that touches alarm pipelines, alarm journals, alarm notification or interlocks needs **human engineering review**; say so explicitly.
- If a resource belongs to a Safety Instrumented System, **flag SIS scope** and require engineering review and **MOC** before any change.

## Where to look

| Need | File |
|---|---|
| Collections, inheritance, modes, `local` overrides, redundancy | `references/collections-and-modes.md` |
| The `data/` tree, what goes in a backup, where tags live | `references/file-layout.md` |
| IA's four version control layouts and post-pull steps | `references/version-control.md` |
| A `.gitignore` for a repo rooted at `data/` | `references/gitignore.sample` |
| REST API, OpenAPI, API key header, scan and resource routes | `references/rest-api.md` |
| Docker: image arguments, `IGNITION_UID`, licence files, mounting and committing `core`, what to gitignore, first-boot behaviour, resetting a Gateway | `references/docker.md` |
| Secrets, API key handling, agent guard rails | `../ignition-security/SKILL.md` |
| Deploy workflow with curl examples | `../ignition-deploy/references/scan-and-verify.md` |
