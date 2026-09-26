# Scan and Verify: Command Reference

Applies to: Ignition 8.3.x

Labels: **[IA docs]** from the IA 8.3 manual; **[live 8.3.9]** verified by this project on a live 8.3.9 Gateway (see the repository's `docs/verification.md`). Confirm any route on your own Gateway's `/openapi` before relying on it.

## Setup

The user sets two variables in their own shell (never in a committed file, never pasted into chat):

```sh
export IGNITION_GATEWAY_URL="https://gateway.example.local:8043"
# Prompt for the token so it never appears in shell history (bash/zsh):
read -rs IGNITION_API_TOKEN && export IGNITION_API_TOKEN
```

Loading it from a password manager's CLI or a git-ignored env file works too. Do not type `export IGNITION_API_TOKEN=<value>` with the literal value.

Check they exist without printing them:

```sh
test -n "$IGNITION_GATEWAY_URL" && echo "gateway url set"
test -n "$IGNITION_API_TOKEN" && echo "token set"
```

Rules for every command below:
- Pass the token only as `-H "X-Ignition-API-Token: $IGNITION_API_TOKEN"`. The value format is `<tokenName>:<secret>` **[live 8.3.9]**.
- Never add `-v`, `--verbose` or `--trace`: they print request headers, including the token.
- Use HTTPS. For a private CA, use `--cacert <file>` rather than turning off certificate checks.
- `-sS` keeps output quiet but still shows errors; `-w '\nHTTP %{http_code}\n'` prints the status code.

Status codes seen **[live 8.3.9]**: 401 = missing or bad token; 403 = the key's security level is not in the needed Gateway permission (GET needs Access and Read; POST scans need Write).

## Scan status (read-only)

`GET` on the scan routes returns status such as `{"scanActive": false, "lastScanTimestamp": <ms>, "lastScanDuration": <ms>}` **[live 8.3.9]**.

```sh
curl -sS -w '\nHTTP %{http_code}\n' \
  -H "X-Ignition-API-Token: $IGNITION_API_TOKEN" \
  "$IGNITION_GATEWAY_URL/data/api/v1/scan/config"

curl -sS -w '\nHTTP %{http_code}\n' \
  -H "X-Ignition-API-Token: $IGNITION_API_TOKEN" \
  "$IGNITION_GATEWAY_URL/data/api/v1/scan/projects"
```

Record `lastScanTimestamp` before scanning so you can prove a new scan ran.

## Trigger scans (writes; confirm first)

Config scan **[IA docs]**. Same as Scan File System on Platform > System > Modes, which scans the whole Ignition file system:

```sh
curl -sS -X POST -w '\nHTTP %{http_code}\n' \
  -H "X-Ignition-API-Token: $IGNITION_API_TOKEN" \
  "$IGNITION_GATEWAY_URL/data/api/v1/scan/config"
```

Project scan **[IA docs]**. Same as Scan File System on Platform > System > Projects:

```sh
curl -sS -X POST -w '\nHTTP %{http_code}\n' \
  -H "X-Ignition-API-Token: $IGNITION_API_TOKEN" \
  "$IGNITION_GATEWAY_URL/data/api/v1/scan/projects"
```

A POST scan also releases the scan lock if one is held **[live 8.3.9]**; related `GET`/`POST /data/api/v1/scan-lock/config` and `/scan-lock/projects` routes exist. Do not take or release scan locks unless the user asks.

POSTs are audit-logged with user, IP and key when Gateway auditing is enabled **[IA docs]**.

From inside a Gateway or Perspective script, `system.project.requestScan([timeout])` scans projects only (blocking; timeout in seconds, default 10) **[IA docs]**. There is no documented script function for a config scan; use the REST route.

## Wait for the scan to finish

```sh
for i in 1 2 3 4 5 6 7 8 9 10; do
  curl -sS -H "X-Ignition-API-Token: $IGNITION_API_TOKEN" \
    "$IGNITION_GATEWAY_URL/data/api/v1/scan/config"
  echo
  sleep 3
done
```

Stop when `scanActive` is false and `lastScanTimestamp` is newer than the value recorded before the POST.

## Verify resources

List names, enabled flag and modes for one resource type **[live 8.3.9]**:

```sh
curl -sS -w '\nHTTP %{http_code}\n' \
  -H "X-Ignition-API-Token: $IGNITION_API_TOKEN" \
  "$IGNITION_GATEWAY_URL/data/api/v1/resources/names/ignition/database-connection"
```

Response shape: `{"items":[{"name":"...","enabled":true,"modes":["core"]}]}`. Check that the changed resource is present, enabled as intended, and lists the intended collection or mode.

List full resources of a type **[IA docs]**:

```sh
curl -sS -H "X-Ignition-API-Token: $IGNITION_API_TOKEN" \
  "$IGNITION_GATEWAY_URL/data/api/v1/resources/list/ignition/database-connection"
```

The `<moduleId>/<typeId>` pair matches the folder under `data/config/resources/<collection>/`. Types seen on 8.3.9 include `ignition/database-connection`, `ignition/secret-provider`, `ignition/alarm-journal`, `ignition/api-token` and `com.inductiveautomation.historian/historian-provider`. Output of a `list` call can include configuration detail; do not paste it into shared places without reading it first.

## Verify tags

`GET /data/api/v1/tags/export` with parameters `provider`, `path`, `type`, `recursive`, `includeUdts` exists **[live 8.3.9]**. Read the allowed values for `type` and the other parameters from your Gateway's `/openapi` before use. Compare the export for the changed folder with the committed tag JSON under `data/config/resources/core/ignition/tag-definition/`.

If alarm properties differ, stop and flag for human engineering review.

## Verify through files and logs

When an API route is not available or not verified on your Gateway:

1. Read the files back from the Gateway's `data/` tree (or the mounted folder) and diff against the commit.
2. Gateway log: Gateway web page, Diagnostics > Logs. Filter by time since the scan and Min Level Warn or Error **[IA docs]**.
3. Containers: the official image sends the wrapper log to stdout, so use `docker logs <container>` **[IA docs]**.
4. Non-container installs: `wrapper.log` in the install directory's logs location (on Windows typically `C:\Program Files\Inductive Automation\Ignition\logs\`). It shows startup problems and `print` output from Gateway scripts; it cannot be viewed from the web page **[IA docs]**.
5. Designer: open changed views and scripts against live tags. This is still required before calling a view or script done.

## Bind-mount ownership

On a live 8.3.9 official Docker image, files written into a bind-mounted config folder had to be owned by the Gateway's user (uid 2003) or the Gateway faulted with "unable to create resource dir" **[live 8. Alternatively run the Gateway as the repo owner with `IGNITION_UID`/`IGNITION_GID`, which needs the container to start as root; see `../../ignition-config/references/docker.md`.3.9]**. After copying files into a mount, check ownership before scanning.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/openapi
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/api-keys
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-project/system-project-requestScan
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/diagnostics/diagnostics-logs
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/diagnostics/diagnostics-logs/wrapper-logs
- https://www.docs.inductiveautomation.com/docs/8.3/platform/advanced-deployments/docker-image
