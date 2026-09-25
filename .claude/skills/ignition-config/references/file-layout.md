# Gateway `data/` Folder Layout

Applies to: Ignition 8.3.x

In 8.1 Gateway configuration lived in an internal SQLite database. In 8.3 it is externalized into `data/config`. After an upgrade from 8.1 the old internal database file is still present but is no longer used. The upgrade also writes a migration log Markdown file in the `config` folder that lists migrated tables, timings and anything left behind.

## The tree

Paths are relative to the Ignition install directory. The table follows IA's Gateway Folder Structure reference.

| Path | Holds | In a `.gwbk`? | Synced to redundant backup? |
|---|---|---|---|
| `data/config/resources/external` | Collection resources that are read-only in the Gateway, for example Docker volume resource collections | No | No |
| `data/config/resources/core` | The default resource collection | Yes | Yes |
| `data/config/resources/{mode}` | One folder per user-created deployment mode | Yes | Yes |
| `data/config/resources/local` | Collection resources for this machine only, for example local system properties | Yes (separate `/local-backup` folder for redundancy) | No |
| `data/config/ignition` | Platform files that must match on master and backup, for example OAuth2 email token files | Yes | Possible, depends on the redundant provider |
| `data/config/{module-id}` | Module files that must match on master and backup, for example the OPC UA trust store | Yes | Possible, depends on the redundant provider |
| `data/config/local/ignition` | Platform files that must differ between master and backup, for example hostname-specific certificates | Yes (separate `/local-backup` folder) | Possible, depends on the redundant provider |
| `data/config/local/{module-id}` | Module files that must differ between master and backup | Yes (separate `/local-backup` folder) | Possible, depends on the redundant provider |
| `data/var/ignition` | Transient platform data: Designer auth tokens, internal Alarm Journal, internal Audit Log, licensing, Store and Forward engine | No | Possible, depends on the redundant provider |
| `data/var/{module-id}` | Transient module data: Perspective and Vision auth tokens, Core Historian data, SFC state, Internal Historian (Legacy) | No | Possible, depends on the redundant provider |
| `data/projects` | Projects | Yes | Yes |

The `system` collection is built into Ignition. IA's folder reference does not list a folder for it under `data/config/resources`; never create one. To change a system resource, create an override from the Gateway web page.

## Known locations inside the tree

| What | Where | Notes |
|---|---|---|
| Tags and UDT instances | `data/config/resources/core/ignition/tag-definition/<provider>/<folder path>/` | JSON, stored by the path shown in the Tag Browser. Each folder holds `udts.json` for UDT instances (atomic tags go in a sibling JSON file) plus a `unary-resource.json` (live 8.3.9) |
| UDT definitions | `data/config/resources/core/ignition/tag-type-definition/<provider>/udts.json` | The Tag Browser `_types_` folder; one `udts.json` plus `unary-resource.json` per folder (live 8.3.9) |
| Tag providers | `data/config/resources/core/ignition/tag-provider/<name>/config.json` + `resource.json` | A provider created as files and loaded with a config scan works (live 8.3.9) |
| Custom Perspective themes | `data/config/resources/core/com.inductiveautomation.perspective/themes/<theme>/` | `config.json`, `resource.json`, `index.css` |
| Named queries | `data/projects/<project>/ignition/named-query/<name>/` | SQL plus JSON |
| Secrets Management keys | `data/config/ignition/keys/` | `root.json` and `kek.json`. Never commit; see `../../ignition-security/references/secrets.md` |
| Primary vs backup settings for one resource | `config.json` and `backupConfig.json` side by side | See `collections-and-modes.md` |
| Active deployment mode | `data/ignition.conf` | `-Dignition.config.mode=<Mode>` Java parameter |

Resources carry a `resource.json` whose `files` entry names where the data is stored, "most commonly `data.bin` or `config.json`". The `version` field identifies the resource format (for example named queries at `version: 2`); it is not a revision counter, so never bump it to force a reload. Run a scan instead.

The documented paths above follow `resources/<collection>/<module-id>/<type-id>/...`. The REST API resource routes use the same module ID and type ID pair: IA's custom themes page shows the themes folder `com.inductiveautomation.perspective/themes` and the route `/data/api/v1/resources/com.inductiveautomation.perspective/themes`. For other resource types, confirm the exact IDs in the Gateway's `/openapi` before scripting against them.

## Binary (`.bin`) resources

IA's version control guide lists these as still encoded as Java `.bin` files and recommends gitignoring them:

- Transaction Groups
- Client Tags
- Reports
- Alarm Pipelines

Do not hand-edit or diff-review them. Change them in the Designer or the Gateway web page. Alarm pipeline changes need human engineering review.

Vision windows are `.bin` by default; IA recommends switching Vision projects to XML encoding for version control. Vision is outside the scope of these skills.

## File naming

- Space and period are allowed except as the first or last character. Hyphen is allowed except as the first character.
- Not allowed anywhere: backtick, `/`, `\`, `?`, `*`, `:`, `|`, `"`, `<`, `>`.
- Names are limited to under 255 characters, and some operating systems and tools fail on **paths** longer than 255 characters. Tag folders become directories, so deep tag trees on Windows can hit this. Keep tag and folder names short.

## Stale page warning

IA's "Ignition 8 Deployment Best Practices" tutorial still says Gateway configuration is stored in the internal SQLite database. That is wrong for 8.3. Use the Gateway Folder Structure reference and the Version Control Guide instead, and do not cite the deployment best-practices page for 8.3 config storage.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/gateway-folder-structure
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/resource-json-file
- https://www.docs.inductiveautomation.com/docs/8.3/getting-started/installing-and-upgrading/ignition-8-upgrade-guide/81to83-upgrade-guide
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/creating-and-using-custom-perspective-themes
- https://www.docs.inductiveautomation.com/docs/8.3/platform/sql-in-ignition/named-queries
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/secrets-management
- https://www.docs.inductiveautomation.com/docs/8.3/platform/ignition-redundancy/setting-up-redundancy
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
