# Running Ignition 8.3 in Docker (field notes)

Applies to: Ignition 8.3.x

Behaviour of the official `inductiveautomation/ignition` image. Items marked **[live 8.3.9]** were observed on a live 8.3.9 Gateway while building a Docker Compose stack (see the repository's `docs/verification.md`); items marked **[IA docs]** come from the Docker image page.

## Image basics

- Runtime arguments go after the image name **[IA docs]**:
  - `-n` Gateway name, `-m` max JVM memory (MB);
  - `-a` public address, `-h` public HTTP port, `-s` public HTTPS port. Set all three together;
  - JVM arguments go after `--`, for example `-- -Dignition.config.mode=prod`.
- Any environment variable can take a `_FILE` suffix to read its value from a file (Docker secrets) **[IA docs]**.
- `GET /StatusPing` returns `{"state":"RUNNING"}` when ready. Use it for health checks; `curl` is available in the image **[live 8.3.9]**.
- The Gateway root `/` redirects to `/Start` (the Gateway web UI) **[live 8.3.9]**.

## Run as the repo owner (`IGNITION_UID` / `IGNITION_GID`)

- The docs say the entrypoint updates file ownership to `IGNITION_UID`/`IGNITION_GID` and then steps down from root **[IA docs]**.
- **The container must start as root for this to happen** (`user: "0:0"` in Compose). Otherwise the image runs as uid 2003 and silently ignores `IGNITION_UID` **[live 8.3.9]**.
- With it working, files the Gateway writes into bind-mounted folders belong to the host user, so they can be edited and committed without `sudo`.
- Without it, bind-mounted folders must be owned by uid 2003. If they are not, the Gateway faults with `Unable to create 'core' resource collection` (`AccessDeniedException`) **[live 8.3.9]**.

## Licences and editions

- `IGNITION_EDITION=maker|standard|edge`. Maker uses a leased licence: `IGNITION_LICENSE_KEY` and `IGNITION_ACTIVATION_TOKEN` (or their `_FILE` forms) **[IA docs]**.
- **An empty `IGNITION_LICENSE_KEY_FILE` / `IGNITION_ACTIVATION_TOKEN_FILE` makes the Gateway fault** at startup in any edition. The error is `NullPointerException ... EnvironmentVariable.resolveEnvVarFile` from `LeasedActivationStrategy` **[live 8.3.9]**. Keep the licence variables in a separate Compose override file, and enable it only once the files hold real values; without it the Gateway runs in trial mode.
- Maker: do not set `GATEWAY_MODULES_ENABLED`. IA forum staff report it causes "Not eligible for use with Ignition Maker Edition" (IGN-14320).
- Leased licences need internet access; after the timeout (72 h for licences created from 20 July 2026) the Gateway reverts to trial mode **[IA docs]**.

## Mounting version-controlled config

Pattern that booted cleanly from a fresh clone in two deployment modes (IA's "curated mounts" layout) **[live 8.3.9]**:

```yaml
volumes:
  - ignition-data:/usr/local/bin/ignition/data                          # db, var, logs, keys
  - ./config/resources:/usr/local/bin/ignition/data/config/resources    # core, <mode>, external, local
  - ./projects:/usr/local/bin/ignition/data/projects
command: -n gw-${MODE} -- -Dignition.config.mode=${MODE}
```

**Commit `core`.** It is the shared base every deployment mode inherits. IA: "Deployment modes and resource definition overrides are typically created from core", and both examples in IA's Version Control Guide track it. Gitignore `local/`, `.resources/` and `migration-log-*.md`, plus the per-Gateway `core` resources in rule 4 (all listed in `gitignore.sample`).

Observed rules **[live 8.3.9]**:

1. **Do not mount collections read-only (`:ro`).** The entrypoint `chown`s the data folder, fails on read-only mounts and the container restart-loops. The Gateway already treats `external` as read-only.
2. **A pre-filled `external` folder needs its manifest** `external/config-mode.json`. Without it the Gateway faults: `Resource collection path '.../external' exists but is not empty`. The file the Gateway itself writes:
   ```json
   {"title": "External", "description": "Externally managed configuration", "enabled": true, "inheritable": true, "parent": "system"}
   ```
3. **Committed mode folders work:** `<mode>/config-mode.json` with `"parent": "core"` is picked up at boot, and `-Dignition.config.mode=<mode>` selects it ("Config mode set to ..." in the log).
4. **Leave these `core` resources out of git; each Gateway creates them on first boot.** With them ignored, a fresh clone booted in `dev` and in `prod` with 0 errors, and first boot changed no committed file.
   - Credentials: `ignition/user-source/` (password hashes), `ignition/identity-provider/temp/`, and `ignition/opc-connection/`. The built-in OPC UA connection password is an Embedded secret encrypted with that Gateway's own key.
   - `ignition/system-properties/` (holds the Gateway name set by `-n`).
   - `ignition/gateway-network-queue-settings/`, `ignition/gateway-network-proxy-rules/` and `ignition/quickstart/`. First boot migrates the image's seed settings into these. If they are committed, it logs `Error migrating table ...` with `PushConflictException: CREATE conflict ... already exists` on every start.
   - `com.inductiveautomation.opcua/one-time/`. If committed, the OPC UA module skips creating its `opcua-module` user source and the `Ignition OPC UA Server` connection.
   - Committing everything except these is what works. An earlier attempt that committed only part of `core` failed for the reasons above.
5. **First boot overwrites the active mode's `security-properties`** with defaults, even when the committed file differs. Restore it from git after the first boot (`git checkout -- <mode folder>`) and restart.
6. **`core` ranks above `external`,** so a resource the Gateway generates in `core` hides the same resource in `external`.
   - Seen with `security-properties`: put singleton settings that must win into the **mode** folder.
   - Seen with UDT definitions: every start creates an empty `tag-type-definition/<provider>` resource in `core`, and it comes back after deletion. UDT definitions committed to `external` therefore never load. Keep tags and UDTs in `core`.
7. The `local` collection's manifest has `"parent": "<active mode>"` and `"inheritable": false`. Resources placed there, such as API keys, take effect.
8. **Edits made in the Gateway web UI, the Designer or the tag import API land in `core`,** which with this layout is the git working tree. Review them with `git diff`. The tag import API writes to `core` even for a provider defined in a mode folder.
9. **Memory-tag values need the provider's Value Persistence set to `Configuration`** to reach the files. With the default `Database`, a written value goes to `valueStore.idb` in the volume, and a fresh clone loses it. This includes UDT instance overrides of memory members such as alarm limits. Set `"valuePersistence": "Configuration"` in the tag provider's `config.json`; IA advises caution with fast-changing tags, because every write rewrites a file.
10. **Resetting a Gateway:** `docker compose down -v` no longer clears its config. Also run `git clean -fdX config/resources`, which removes the generated, ignored files including `local` API keys. Otherwise the next first boot hits the CREATE conflicts in rule 4 and creates a duplicate `temp_0` identity provider.
11. A fresh 8.3.9 Gateway has **no historian provider**. Create one (see `rest-api.md`) and commit it in `core`.

## Secrets as files

- Bind-mounted secret files keep their host permissions, and several containers read them as non-root users (PostgreSQL's init scripts run as `postgres`).
- A working pattern: the secrets folder is `700` (other host users cannot enter it) and the files inside are `644`.
- To use a single secret in a one-off container, mount the **file**, not the folder. A container user cannot traverse a `700` folder.

## Reverse proxy

See `../../ignition-security/references/reverse-proxy.md` for a tested nginx layout that exposes only Perspective.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/platform/advanced-deployments/docker-image
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/platform-environment-variables
- https://www.docs.inductiveautomation.com/docs/8.3/platform/licensing-and-activation/leased-licensing
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://forum.inductiveautomation.com/t/109762 (Maker and `GATEWAY_MODULES_ENABLED`)
