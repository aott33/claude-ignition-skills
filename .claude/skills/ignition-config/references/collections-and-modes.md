# Resource Collections and Deployment Modes

Applies to: Ignition 8.3.x

## Collections

A collection is a group of Gateway resources. A deployment mode is a collection that the user creates and names. Every mode is a collection; not every collection is a mode.

Collections form an inheritance chain. A child takes its starting resources from its parent, and a resource definition in the child overrides the one it inherits.

| Order | Collection | What it is | Editable in the Gateway? |
|---|---|---|---|
| 1 | `system` | Built-in. Ignition uses it to inject required configuration, for example the MariaDB JDBC driver. Built-in Perspective themes are also system resources | No. Immutable, but you can create an override of a system resource in `core` or in a mode |
| 2 | `external` | Centrally managed configuration, changed only through the filesystem in the data directory. IA: "if you are using a version control system (VCS), this collection is where your VCS should place any relevant resources" | No. Read-only in the Gateway |
| 3 | `core` | Child of `external`. The default: a fresh Gateway, or one without modes, runs in `core`. Modes and overrides are usually created from here | Yes |
| 4 | `<mode>` | User-created deployment modes, for example `Dev`, `Test`, `Prod` | Yes |
| n/a | `local` | Data essential to this host, for example certificate details. Modes do **not** inherit anything from `local`, but use it to run on each machine. On a live 8.3.9 Gateway its manifest was `"parent": "<active mode>", "inheritable": false`, and API keys placed there worked | Yes |

**Changed in 8.3.7:** `local` can also hold resource definition overrides. Because of what `local` is, these overrides **do not carry over to a redundant backup Gateway**. Use them only for settings that must differ per machine.

### Which collection should hold a change?

| Situation | Put it in |
|---|---|
| Config delivered by git or a GitOps controller and never edited on the Gateway | `external` (needs its `config-mode.json` manifest; see `docker.md`) |
| A singleton setting that must win over what a fresh Gateway generates in `core` (for example `security-properties`) | The mode folder: `core` overrides `external` |
| Normal Gateway config on a Gateway without modes | `core` |
| A value that differs between environments (device address, DB connection, Gateway Network settings) | An override in the environment's mode |
| A value that differs per physical machine and must not follow a backup | `local` (8.3.7+) or a redundancy backup version (below) |
| A built-in system resource that needs different settings | An override of that system resource (lands in `core` if no mode exists) |

## Resource types

- **Named resources**: listed items with unique names, for example device connections or API keys. Can be created manually, overridden or duplicated.
- **Singleton resources**: one grouped set of properties, for example the Gateway Network Settings page. Can only be overridden, never duplicated.
- **System resources**: live in `system`; view-only until overridden.

Almost every Gateway resource can be overridden. **Exceptions: deployment modes, modules, projects and licenses** cannot have overrides.

## Deployment modes

### Create and edit

Platform > System > Modes on the Gateway web page. Each mode has a name plus optional title and description. Resource definitions are tied to the mode **name**, so IA recommends changing the title rather than the name. Deleting a mode deletes every resource definition assigned to it.

A mode cannot receive a definition if it already has one with the same name.

### Override vs duplicate

| Action | Result |
|---|---|
| Override (named or singleton) | Same name, assigned to a chosen mode. Shown under the original with **Show All** |
| Duplicate, new name, other mode | A separate resource, visible only when that mode is active |
| Duplicate, new name, same mode | A separate named resource in the same mode |
| Duplicate, same name, other mode | Same effect as an override |
| Duplicate, same name, same mode | Not allowed; the Gateway shows an error |

Once created, overrides are independent: deleting one does not affect the other. Toggling the mode banner on a singleton page only chooses which mode's settings you edit; it does not change the running mode.

### Select the active mode (restart required)

The web page cannot change the running mode. Add a Java parameter to `data/ignition.conf` in the install directory, using the next free index:

```
wrapper.java.additional.4=-Dignition.config.mode=Dev
```

Then restart the Gateway service. Only one mode can be active at a time.

**Redundancy:** the mode setting lives in `ignition.conf` and **does not sync** between master and backup. Set the same `-Dignition.config.mode` on both and restart both; otherwise a failover can bring up the backup with different device or database connections.

**Containers:** IA does not document a Docker environment variable for the mode. The Docker image page documents passing extra JVM arguments after `--` in the container command. Verified on a live 8.3.9 container: adding `-Dignition.config.mode=Dev` after `--` (for example in the Compose `command:`) and recreating the container made the Gateway run in `Dev`, applied the `Dev` overrides, and did **not** write anything to `ignition.conf`. Confirm the active mode with `GET /data/api/v1/gateway-info` (field `deploymentMode`, empty when running `core`) or on Platform > System > Modes.

**Creating a mode:** Platform > System > Modes, or `POST /data/api/v1/mode` with `{"name", "title", "description"}` (live 8.3.9; note the route is singular `/mode`, although IA's API Keys page says `/modes`). The Gateway creates `data/config/resources/<ModeName>/config-mode.json` with `"parent": "core"`. Files placed under that folder are overrides that apply only while the Gateway runs in that mode (verified: a `Dev` override was ignored in `core` and applied in `Dev`).

### Scan after file changes

Changes made on the Gateway web page are picked up immediately. Changes made through the filesystem (hand edits, scripts, `git pull`) are **not** recognized until you scan:

- Platform > System > Modes > **Scan File System**. This scans the entire Ignition file system, not only modes.
- `POST {{gateway_address}}/data/api/v1/scan/config`.
- The mode routes are listed in the Gateway's OpenAPI page under `/openapi#tag/config-management`.

IA warns that adding, copying or moving resource configurations, overrides and modes directly in the file structure "is not recommended and should only be used as a last resort". Prefer the web page or the REST API.

## Redundancy backup versions (`backupConfig.json`)

Separate from modes, a redundant pair can give the backup node different settings for one resource:

- On the resource's page or Edit panel, open the three-dots menu and choose **Add Backup Version**, then edit the **Backup** version.
- Backup settings are saved in `backupConfig.json`; primary settings stay in `config.json`.
- `backupConfig.json` can exist before redundancy is set up but is used only when the Gateway's role is Backup.
- Some pages accept a backup version but ignore it: Platform > System > Gateway Settings, Platform > System > Ignition Edge > Edge Settings, Platform > Security > General Settings.

Use this for per-node differences such as an OPC UA server address that differs by network segment. Such changes are **IT/OT boundary** changes; confirm the network zone with the user.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes/gateway-deployment-mode-examples
- https://www.docs.inductiveautomation.com/docs/8.3/platform/ignition-redundancy/setting-up-redundancy
- https://www.docs.inductiveautomation.com/docs/8.3/platform/advanced-deployments/docker-image
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/perspective-built-in-themes
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
