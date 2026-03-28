# Credential Management

Secure local storage for API keys and integration secrets.

## When to Suggest Storing Credentials

Suggest credential storage when the user:
- Configures a new integration (IBKR, Zerodha, Deribit, Google Sheets, CoinGecko)
- Provides an API key in conversation (store it immediately, never leave keys in chat history)
- Asks about connecting external accounts
- Runs a fetch script that requires authentication

## How to Store/Retrieve

```bash
# Store a credential
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/credential-manager.py" "<project_dir>" store <service> <key>

# Retrieve a credential (for use in fetch scripts)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/credential-manager.py" "<project_dir>" get <service>

# List stored services (shows names only, never values)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/credential-manager.py" "<project_dir>" list

# Delete a credential
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/credential-manager.py" "<project_dir>" delete <service>
```

## Supported Services

Any string works as a service name. Recommended naming:
- `ibkr` — Interactive Brokers API key
- `zerodha` — Zerodha Kite API key
- `deribit` — Deribit API credentials
- `coingecko` — CoinGecko Pro API key
- `google-sheets` — Google Sheets service account JSON path or API key
- Custom names for any future integration

## Security Model

**Encryption:** If `cryptography` Python package is installed, uses Fernet (AES-128-CBC + HMAC-SHA256). Otherwise falls back to PBKDF2-derived XOR stream cipher with HMAC-SHA256 integrity verification. Both backends are tagged in the ciphertext — upgrading to Fernet later works without re-entry.

**Key storage:** Master key auto-generated on first use. Stored at `.timecell/.key` with 0600 permissions (owner-only). No passphrase required — the threat model is local file access protection, not remote attack resistance.

**File permissions:** Both `.timecell/.key` and `.timecell/credentials.enc` are set to mode 0600.

**Update safety:** `.timecell/` is in USER_DATA_PATHS — credentials survive plugin updates.

**Limitation:** The stdlib fallback (XOR + HMAC) provides integrity verification and obfuscation but is not equivalent to AES. For high-security environments, install `cryptography`: `pip install cryptography`.

## CIO Behavior

- When a user shares an API key in conversation, store it and confirm: "Stored your [service] API key securely in .timecell/credentials.enc."
- Never echo credential values back to the user after storage.
- When a fetch script needs credentials, retrieve them programmatically — do not ask the user to paste keys again.
- On `list`, show service names and storage dates only.
