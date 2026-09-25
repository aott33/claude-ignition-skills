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

Pattern that worked (IA's "curated mounts" layout):

```yaml
volumes:
  - ignition-data:/usr/local/bin/ignition/data            # core, local, var, db live here
  - ./config/resources/external:/usr/local/bin/ignition/data/config/resources/external
  - ./config/resources/${MODE}:/usr/local/bin/ignition/data/config/resources/${MODE}
  - ./projects:/usr/local/bin/ignition/data/projects
command: -n gw -- -Dignition.config.mode=${MODE}
```

Observed rules **[live 8.3.9]**:

1. **Do not mount collections read-only (`:ro`).** The entrypoint `chown`s the data folder, fails on read-only mounts and the container restart-loops. The Gateway already treats `external` as read-only.
2. **A pre-filled `external` folder needs its manifest** `external/config-mode.json`. Without it the Gateway faults: `Resource collection path '.../external' exists but is not empty`. The file the Gateway itself writes:
   ```json
   {"title": "External", "description": "Externally managed configuration", "enabled": true, "inheritable": true, "parent": "system"}
   ```
3. **Committed mode folders work:** `<mode>/config-mode.json` with `"parent": "core"` is picked up at boot, and `-Dignition.config.mode=<mode>` selects it ("Config mode set to ..." in the log).
4. **Do not commit or pre-seed a partial `core`.** On a fresh volume with a partial `core`, the Gateway skipped default resources: no built-in OPC UA connection, and a user source named `temp` instead of `default`. It also logged migration errors, and resources whose data files were left out (for example `users.json`) failed to load. Let each Gateway generate its own `core` in the volume. Version shared resources in `external` and per-environment overrides in mode folders.
5. **First boot overwrites the active mode's `security-properties`** with defaults, even when the committed file differs. Restore it from git after the first boot (`git checkout -- <mode folder>`) and restart.
6. `core` is the child of `external`, so a resource the Gateway generates in `core` at first boot overrides the same resource in `external`. This happened with `security-properties`. Put singleton settings that must win into the **mode** folder, below `core`.
7. The `local` collection's manifest has `"parent": "<active mode>"` and `"inheritable": false`. Resources placed there, such as API keys, take effect.
8. Edits made in the Gateway web UI land in `core` (the volume), not in git. Move them to `external` or a mode folder to version them ("Move Definition" in the Gateway, or copy the files), then scan.

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
- https://forum.inductiveautomation.com/t/109762 (Maker and `GATEWAY_MODULES_ENABLED`)
