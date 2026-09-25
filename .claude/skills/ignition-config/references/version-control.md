# Version Control for Ignition 8.3

Applies to: Ignition 8.3.x

Because 8.3 stores Gateway configuration as files under `data/config`, the whole Gateway (not only projects) can live in git. IA's Version and Source Control Guide describes four ways to lay out a repository. Pick one per Gateway fleet and write it down.

## The four layouts

| # | Layout | What is in git | Good for | Watch out for |
|---|---|---|---|---|
| 1 | **Full data directory** ("subtractive") | The whole `data/` folder, with a `.gitignore` removing runtime files | One or two bare-metal or VM Gateways; fastest start | IA warns maintenance grows; one Gateway per repo; relies on a complete `.gitignore` (see `gitignore.sample`) |
| 2 | **Curated configuration mounts** ("additive") | Only chosen folders, bind-mounted into a container, typically `config` and `projects` | Containers and teams; small `.gitignore` | You must add anything else you need yourself (redundancy config, accepted certificates, custom modules) |
| 3 | **Projects only** | Only `data/projects` | Teams that manage Gateway config through the web page or API | Gateway config is not versioned |
| 4 | **Multi-Gateway repository** | `services/gateway-NN/` per Gateway plus `shared/` (for example `shared/projects`, `shared/common-config`) | Fleets; single source of truth | Needs the curated-mount approach; plan which config is shared and which is per Gateway |

For layout 2 IA's example `.gitignore` is only four lines: `**/config/local`, `**/config/resources/local`, `**/conversion-report.txt`, `**/.resources/`.

### Credential material that IA's list still commits

Tested on a live 8.3.9 Gateway (`data/` folder with IA's recommended `.gitignore`): git still tracked
- internal user sources (`ignition/user-source/<name>/users.json`) with password hashes,
- API key resources (`ignition/api-token/<name>/config.json`) with key hashes,
- resource `config.json` files holding **Embedded** secrets as JWE (`ciphertext`, `encrypted_key`), for example an OPC connection password.

None of these is plaintext, but they are credential material. Before the first commit, `git grep -lE '"ciphertext"|tokenHash|"password"'` and decide per file. Prefer **Referenced** secrets from a secret provider for anything that lives in git, and keep `data/config/ignition/keys/` out of git (our `gitignore.sample` adds it). See [../../ignition-security/SKILL.md](../../ignition-security/SKILL.md).

Deployment modes pair well with layouts 2 and 4: keep one config set and let the active mode switch device and database targets per environment (see `collections-and-modes.md`).

## Layout 2 in practice (tested on 8.3.9)

A Docker Compose stack that booted cleanly from a fresh clone mounted three things:
- `config/resources/external` (shared, versioned resources, with its `config-mode.json` manifest);
- the active mode folder `config/resources/<mode>` (per-environment overrides, including `security-properties`);
- `projects`.

`core` stayed in the Docker volume and out of git: each Gateway generates its own, and a partially committed `core` caused missing defaults and load errors. Changes made in the Gateway web UI land in `core`, so move deliberate changes into `external` or a mode folder before committing. Mount details and first-boot behaviour: `docker.md`.

## Bootstrapping a second Gateway (layout 1)

IA's sequence: install Ignition on the second machine **without starting the service**, delete its `data` directory, `git clone <repo> data`, then start the service. Never do this on a Gateway that holds anything you need; it replaces the whole data directory.

## After every pull: scan

A `git pull` changes files but the Gateway does not load them on its own. Run both scans:

| Scan | Web page | REST |
|---|---|---|
| Config | Platform > System > Modes > **Scan File System** (scans the whole Ignition file system) | `POST /data/api/v1/scan/config` |
| Projects | Platform > System > Projects > **Scan File System** | `POST /data/api/v1/scan/projects` |

Inside Gateway or Perspective scope, `system.project.requestScan([timeout])` scans projects only. It blocks until the scan finishes; the timeout is in seconds and defaults to 10. It does **not** scan Gateway config.

Curl examples: `../../ignition-deploy/references/scan-and-verify.md`.

## Commit rules

- **Keep `resource.json` with its content.** IA's team best practices say: do not commit a `resource.json` change without the matching `view.json` change. The same applies to `projects/*/com.inductiveautomation.perspective/session-props/props.json`.
- **Leave `.bin` resources alone.** Transaction Groups, Client Tags, Reports and Alarm Pipelines are Java `.bin` files; IA recommends gitignoring them. If you do track them, treat them as opaque and review them in the Designer, not in a diff.
- **Memory tag values.** `valueStore.idb` holds persisted Memory tag values when persistence is the default `database` setting; keep it out of git. If a tag value must be versioned, set its value persistence to `configuration` so the value is saved in the tag JSON. IA advises caution about how many tags do this.
- **No secrets in git.** Keep `.env` files, API tokens, certificates, keystores and `data/config/ignition/keys` out. Use secret providers (`../../ignition-security/references/secrets.md`) and IA's guidance to store secrets in environment variables rather than hardcode them. IA suggests a secret scanner such as GitGuardian.
- **Small, focused commits** with a consistent message convention (IA gives Conventional Commits as an example), short-lived branches, pull requests with review.
- **Keep `main` deployable**: run checks (lint, tests) in CI before merge.

## Environments

IA's team guidance, in brief:

- Keep Dev, QA and Prod as close as possible (same modules, same Gateway setup; containers help).
- Point devices at simulators in development and real PLCs only in production. Use deployment modes to override device and database resources per environment.
- Keep separate databases per environment; do not use production data in lower environments.
- Restrict who can change production; use role-based access and enable the audit log.

Any change that repoints a Gateway at production devices or databases crosses an **IT/OT boundary**; get explicit authorization.

## CI/CD and GitOps

IA describes CI pipelines (GitHub Actions, Jenkins, Azure DevOps) that lint and test config, then deploy to staging through the Gateway API before promotion to production, and GitOps controllers (ArgoCD, Flux, Kargo) that sync a repo to Gateways via mounts or API calls. The Gateway REST API is described in `rest-api.md`.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide/best-practices-for-team-environments
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-project/system-project-requestScan
