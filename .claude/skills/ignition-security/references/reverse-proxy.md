# Exposing Perspective through a reverse proxy

Applies to: Ignition 8.3.x

IA's Perspective proxy page forwards all of `/data/`, `/system/`, `/res/`, `/idp/` and `/.well-known/`. That also exposes the REST API and WebDev. For an internet-facing Gateway, deny those paths **before** the Perspective locations, keep the Gateway admin on the LAN or VPN, and rate-limit at the proxy (IA's hardening guide: Ignition does not broadly rate-limit).

## Tested nginx layout [live 8.3.9]

Verified with Ignition 8.3.9, nginx 1.29 and Keycloak 26.7.4 in Docker. Every deny rule returned 404 and Perspective resources returned 200.

```nginx
resolver 127.0.0.11 valid=30s;                       # Docker DNS: resolve upstreams per request
map $http_upgrade $connection_upgrade { default upgrade; '' close; }
limit_req_zone $binary_remote_addr zone=perspective:10m rate=20r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=10r/m;

server {
    listen 443 ssl;
    server_name home.example.net;                     # dedicated subdomain (path prefixes break Ignition resource URLs)
    underscores_in_headers on;                        # Perspective custom headers
    set $ignition http://ignition:8088;

    location ^~ /app                 { return 404; }  # Gateway web admin (8.3)
    location ^~ /web/                { return 404; }
    location ^~ /openapi             { return 404; }  # /openapi and /openapi.json
    location ^~ /data/api/           { return 404; }  # REST API
    location ^~ /system/webdev/      { return 404; }
    location ^~ /system/eventstream/ { return 404; }  # Event Stream HTTP sources
    location = /StatusPing           { return 404; }

    location = / { return 302 /data/perspective/client/<project>/; }
    location ^~ /data/federate/ { limit_req zone=login burst=10 nodelay; include proxy-common.conf; proxy_pass $ignition; }
    location ^~ /idp/           { limit_req zone=login burst=10 nodelay; include proxy-common.conf; proxy_pass $ignition; }
    location ^~ /data/        { limit_req zone=perspective burst=100 nodelay; include proxy-common.conf; proxy_pass $ignition; }
    location ^~ /system/      { limit_req zone=perspective burst=100 nodelay; include proxy-common.conf; proxy_pass $ignition; }
    location ^~ /res/         { include proxy-common.conf; proxy_pass $ignition; }
    location ^~ /.well-known/ { include proxy-common.conf; proxy_pass $ignition; }
    location / { return 404; }                        # also blocks /Start (Gateway UI landing page)
}
```

`proxy-common.conf`:
- `proxy_http_version 1.1`
- `Upgrade` / `Connection $connection_upgrade`
- `Host`, `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Forwarded-Host`, `X-Forwarded-Port 443`
- `proxy_pass_request_headers on`
- a long `proxy_read_timeout` for websockets

Notes:
- `proxy_pass $variable` with a resolver lets nginx start even when an optional upstream is down. Without a URI part it passes the original request path unchanged.
- **Default server:** add a `default_server` on 443 that returns `444`, so unknown hostnames get nothing.
- **Gateway side:** enable "Use Proxy Forwarded Headers" only when clients cannot reach the Gateway directly (IA: a security risk otherwise). Set the public address to the subdomain and port 443 (Docker `-a <host> -h 80 -s 443`), and enable Force Secure Redirect.
- **Keycloak as the OIDC provider for MFA** (IA article "Using Keycloak with Ignition"):
  - Proxy only `/realms/` and `/resources/`, and deny `/admin/` and `/realms/master/` publicly.
  - Keycloak flags: `start --http-enabled=true --proxy-headers=xforwarded --hostname=https://auth.example.net --hostname-admin=http://localhost:8180`.
  - Ignition's OIDC callback is `/data/federate/callback/oidc`.

## Test it

After every Ignition or proxy change, check from outside the network (or with `curl --resolve host:443:127.0.0.1`):
- `/app`, `/openapi`, `/data/api/v1/gateway-info`, `/system/webdev/...` and `/Start` return 404;
- `/` redirects to the Perspective client;
- `/res/perspective/js/` returns 200.

The exact websocket paths Perspective uses under `/system/` and `/data/` are not documented, which is why those prefixes stay open behind the deny rules.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/perspective-sessions/perspective-session-proxy-considerations
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/network/web-server-settings
- https://inductiveautomation.com/resources/article/ignition-security-hardening-guide
- https://inductiveautomation.com/resources/article/using-keycloak-with-ignition
- https://www.keycloak.org/server/reverseproxy
