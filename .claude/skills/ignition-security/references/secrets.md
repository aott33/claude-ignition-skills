# Secrets Management and `system.secrets`

Applies to: Ignition 8.3.x

## Secret fields on Gateway resources

In 8.3 the old "password / re-type password" fields on devices, profiles and system settings are replaced by a secret field with three options:

| Option | Behavior |
|---|---|
| **None** | No secret. Always visible, greyed out when a secret is required |
| **Embedded** | Enter the value once (a SHOW toggle exists while typing). Once saved it is encrypted with Ignition's keys and can never be displayed again; use Update Password to change it |
| **Referenced** | Choose a secret provider and a secret name. Only available when a provider exists |

Moving from Embedded to Referenced later is a simple edit of the field on the Gateway page.

## Secret providers

Created on Platform > Security > Secret Provider (Create Secret Provider +).

| Type | Since | Notes |
|---|---|---|
| **Internal** | 8.3.0 | Secrets stored encrypted as files on the Gateway, referenced by name so several configs can share one. IA recommends a different secret per system or connection. Add and reset secrets on the provider's **Manage Secrets** panel; a saved value cannot be read back from the Gateway |
| **Remote** | 8.3.3 | Links to a provider on a remote Gateway over the Gateway Network; can list and read secrets but not create them. Access is **denied by default**; allow it in the relevant Security Zone's policy, Secret Provider Access section. This crosses Gateways, so treat it as an **IT/OT boundary** decision needing explicit authorization |
| **File** | 8.3.5 | Reads each secret from a file path, as `CLEARTEXT` (all bytes of the file; no trailing newline) or `CIPHERTEXT` (a flat JWE produced by Ignition). Suits Kubernetes, where secrets from Vault, Azure or AWS Secrets Manager are mounted as files |

**Making JWE ciphertext** for the File provider: call `system.secrets.encrypt(...)` or `POST /data/api/v1/encryption/encrypt` (search "encryption" on the Gateway's `/openapi`). If ciphertext is shared between Gateways, each one needs the encryption key that produced it.

## The key system underneath

- A fresh install ships with a **default encryption key that is identical on every Ignition install**. It works, but IA recommends customizing the Root Key and creating Encryption Key Sets.
- Customizing requires an explicit opt-in because you then own key maintenance. You get a Root Key (`root.json`, encrypted by an environment password) and a KEK set (`kek.json`, encrypted by the Root Key), stored in `data/config/ignition/keys/`.
- The environment password is not stored by Ignition. It is supplied through `IGNITION_ROOT_KEY_PASSWORD_FILE` (path to a file holding it) or `IGNITION_ROOT_KEY_PASSWORD`. Without it nothing decrypts and the Gateway fails the startup check; a manual unseal option exists on the Gateway and in the CLI.
- If the keys folder is missing but one of those variables is set, a new Root Key and KEK set are generated at startup.
- Tool: `ignition-secrets-tool.sh` (Linux/macOS) or `ignition-secrets-tool.bat` (Windows) to generate, list and rotate keys.
- **Redundancy:** copy `root.json` and `kek.json` to both master and backup, or secrets encrypted on one node will not decrypt on the other.
- **Git and backups:** never commit `data/config/ignition/keys/` or the environment password.
- An upgrade keeps an existing customized key system; without one it is treated like a fresh install.

## `system.secrets` functions

`system.secrets` is new in **8.3.1**. Three functions were added in **8.3.8**. Scope for all: Gateway, Vision Client, Perspective Session. Prefer Gateway scope for anything that reads a plaintext value, and never send plaintext to a client or session property.

| Signature | Returns | Since |
|---|---|---|
| `system.secrets.encrypt(string, [charset])` | Dictionary holding the JWE (keys such as `ciphertext`, `encrypted_key`, `iv`, `protected`, `tag`), or None if empty. `charset` defaults to UTF-8 | 8.3.1 |
| `system.secrets.encrypt(bytes)` | Same; `bytes` must be a Java-compatible byte array | 8.3.1 |
| `system.secrets.decrypt(json)` | `PyPlaintext` | 8.3.1 |
| `system.secrets.getProviders()` | List of provider metadata (name, description, type) | 8.3.1 |
| `system.secrets.getSecrets(providerName)` | List of secret metadata (names) for that provider | 8.3.1 |
| `system.secrets.readSecretValue(providerName, secretName)` | `PyPlaintext`. Not thread-safe | 8.3.1 |
| `system.secrets.createEmbeddedSecretConfig(json)` | Dictionary: an Embedded SecretConfig built from `encrypt` output. Raises ValueError with no JSON | 8.3.8 |
| `system.secrets.createReferencedSecretConfig(providerName, secretName)` | Dictionary: a Referenced SecretConfig. Raises ValueError on empty arguments | 8.3.8 |
| `system.secrets.readConfiguredSecretValue(secretConfig)` | `PyPlaintext`. Can raise ValueError, SecretException or JsonParseException | 8.3.8 |

On a Gateway older than 8.3.8, do not use the last three.

## `PyPlaintext` handling

- Methods: `getSecretAsString()`, `getSecretAsString(charset)`, `getSecretAsBytes()`, `clear()`.
- Clear it when done. The preferred way is a `with ... as` block; otherwise call `clear()` yourself.
- A string from `getSecretAsString()` stays in memory until garbage collection; the byte array from `getSecretAsBytes()` is the same buffer that `clear()` wipes. Keep the plaintext's lifetime as short as possible.
- `readSecretValue` and `PyPlaintext` are not thread-safe; do not share one across threads.

### Example: use a referenced secret in a Gateway script

```python
import java.lang

logger = system.util.getLogger('Integration.Vendor')

def pushBatchToVendor(batchId):
    """Send one batch to the vendor API using a token held in a secret provider.
    sendToVendor() is this project's own function; it must never log the token."""
    try:
        with system.secrets.readSecretValue('Plant_Secrets', 'vendor-api-token') as plaintext:
            return sendToVendor(batchId, plaintext.getSecretAsString())
    except java.lang.Throwable as ex:
        logger.error('Vendor push failed for batch %s: %s' % (batchId, ex))
    except Exception as ex:
        logger.error('Vendor push failed for batch %s: %s' % (batchId, ex))
    return None
```

### Example: build a referenced secret config (8.3.8+)

```python
import java.lang

logger = system.util.getLogger('Config.Secrets')

try:
    secretConfig = system.secrets.createReferencedSecretConfig('Plant_Secrets', 'plc-line3')
except java.lang.Throwable as ex:
    logger.error('Could not build secret config: %s' % ex)
    secretConfig = None
except Exception as ex:
    logger.error('Could not build secret config: %s' % ex)
    secretConfig = None
```

The resulting dictionary goes into a resource property that takes a secret (IA's example passes one as a device `password` property). Creating devices or other connections from script is an **IT/OT boundary** change; get authorization first.

## Review checklist

- [ ] No literal passwords, tokens or keys anywhere in scripts, views, named queries, tags or committed files.
- [ ] Every `PyPlaintext` is in a `with` block or cleared.
- [ ] No plaintext written to a log, a tag, a session property, a component or a return value sent to a client.
- [ ] `system.secrets.*` calls wrapped with `java.lang.Throwable` and `Exception` handlers.
- [ ] 8.3.8-only functions not used on older Gateways.
- [ ] Production Gateway uses a customized Root Key; key files and environment password kept out of git.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/secrets-management
- https://www.docs.inductiveautomation.com/docs/8.3/platform/security/secrets-management/secrets-management-key-cli-tool
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets/system-secrets-encrypt
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets/system-secrets-decrypt
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets/system-secrets-getProviders
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets/system-secrets-getSecrets
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets/system-secrets-readSecretValue
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets/system-secrets-createEmbeddedSecretConfig
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets/system-secrets-createReferencedSecretConfig
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-secrets/system-secrets-readConfiguredSecretValue
- https://www.docs.inductiveautomation.com/docs/8.3/new-in-this-version
- https://inductiveautomation.com/downloads/releasenotes/8.3.3
- https://inductiveautomation.com/downloads/releasenotes/8.3.5
