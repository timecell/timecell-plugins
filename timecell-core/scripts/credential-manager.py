#!/usr/bin/env python3
"""
TimeCell Credential Manager — secure local credential storage.

Stores API keys and secrets for integrations (IBKR, Zerodha, Deribit, etc.)
in .timecell/credentials.enc with encryption.

Security model:
- If `cryptography` package is available: uses Fernet (AES-128-CBC + HMAC-SHA256)
- Fallback: PBKDF2-derived key + XOR stream cipher + HMAC-SHA256 integrity
- Master key auto-generated on first use, stored in .timecell/.key (mode 0600)
- Credential file stored with mode 0600

Usage:
    python3 credential-manager.py <project_dir> store <service> <key>
    python3 credential-manager.py <project_dir> get <service>
    python3 credential-manager.py <project_dir> list
    python3 credential-manager.py <project_dir> delete <service>

Stdlib only — no pip dependencies required.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import stat
import sys
import time


# --- Encryption backends ---

def _has_fernet():
    """Check if cryptography package is available."""
    try:
        from cryptography.fernet import Fernet  # noqa: F401
        return True
    except ImportError:
        return False


def _fernet_encrypt(plaintext: bytes, key: bytes) -> bytes:
    """Encrypt using Fernet (AES-128-CBC + HMAC-SHA256)."""
    from cryptography.fernet import Fernet
    # Fernet expects a 32-byte URL-safe base64-encoded key
    fernet_key = base64.urlsafe_b64encode(key[:32])
    f = Fernet(fernet_key)
    return b"FERNET:" + f.encrypt(plaintext)


def _fernet_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    """Decrypt using Fernet."""
    from cryptography.fernet import Fernet
    fernet_key = base64.urlsafe_b64encode(key[:32])
    f = Fernet(fernet_key)
    return f.decrypt(ciphertext[7:])  # strip "FERNET:" prefix


def _derive_stream(key: bytes, length: int) -> bytes:
    """Derive a pseudorandom byte stream using PBKDF2 in counter mode."""
    stream = b""
    counter = 0
    while len(stream) < length:
        block = hashlib.pbkdf2_hmac(
            "sha256", key, counter.to_bytes(4, "big"), iterations=1000
        )
        stream += block
        counter += 1
    return stream[:length]


def _stdlib_encrypt(plaintext: bytes, key: bytes) -> bytes:
    """Encrypt using XOR stream cipher with PBKDF2-derived keystream + HMAC integrity."""
    # Generate random IV/salt for this encryption
    salt = secrets.token_bytes(16)
    # Derive encryption key from master key + salt
    derived = hashlib.pbkdf2_hmac("sha256", key, salt, iterations=100_000)
    # XOR encrypt
    stream = _derive_stream(derived, len(plaintext))
    ciphertext = bytes(a ^ b for a, b in zip(plaintext, stream))
    # HMAC for integrity
    mac = hmac.new(derived, ciphertext, hashlib.sha256).digest()
    # Format: STDLIB:<salt><mac><ciphertext>
    return b"STDLIB:" + salt + mac + ciphertext


def _stdlib_decrypt(data: bytes, key: bytes) -> bytes:
    """Decrypt stdlib-encrypted data."""
    payload = data[7:]  # strip "STDLIB:" prefix
    salt = payload[:16]
    mac = payload[16:48]
    ciphertext = payload[48:]
    # Derive same key
    derived = hashlib.pbkdf2_hmac("sha256", key, salt, iterations=100_000)
    # Verify integrity
    expected_mac = hmac.new(derived, ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected_mac):
        raise ValueError("Credential file integrity check failed — file may be corrupted or tampered")
    # XOR decrypt
    stream = _derive_stream(derived, len(ciphertext))
    return bytes(a ^ b for a, b in zip(ciphertext, stream))


def encrypt(plaintext: bytes, key: bytes) -> bytes:
    """Encrypt using best available backend."""
    if _has_fernet():
        return _fernet_encrypt(plaintext, key)
    return _stdlib_encrypt(plaintext, key)


def decrypt(ciphertext: bytes, key: bytes) -> bytes:
    """Decrypt using the backend indicated by the ciphertext prefix."""
    if ciphertext.startswith(b"FERNET:"):
        if not _has_fernet():
            raise RuntimeError(
                "Credentials were encrypted with Fernet but cryptography package is not installed. "
                "Install it with: pip install cryptography"
            )
        return _fernet_decrypt(ciphertext, key)
    elif ciphertext.startswith(b"STDLIB:"):
        return _stdlib_decrypt(ciphertext, key)
    else:
        raise ValueError("Unknown credential encryption format")


# --- Key management ---

def _key_path(project_dir: str) -> str:
    return os.path.join(project_dir, ".timecell", ".key")


def _cred_path(project_dir: str) -> str:
    return os.path.join(project_dir, ".timecell", "credentials.enc")


def _ensure_dir(project_dir: str):
    """Ensure .timecell directory exists with proper permissions."""
    tc_dir = os.path.join(project_dir, ".timecell")
    os.makedirs(tc_dir, exist_ok=True)


def _set_file_permissions(path: str):
    """Set file to owner-only read/write (0600)."""
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows or other platforms where chmod may not work


def get_or_create_key(project_dir: str) -> bytes:
    """Load master key from .timecell/.key, or generate one on first use."""
    _ensure_dir(project_dir)
    kp = _key_path(project_dir)

    if os.path.exists(kp):
        with open(kp, "rb") as f:
            key = f.read()
        if len(key) >= 32:
            return key[:32]

    # Generate new key
    key = secrets.token_bytes(32)
    with open(kp, "wb") as f:
        f.write(key)
    _set_file_permissions(kp)
    return key


# --- Credential store ---

def _load_store(project_dir: str, key: bytes) -> dict:
    """Load and decrypt the credential store. Returns empty dict if not found."""
    cp = _cred_path(project_dir)
    if not os.path.exists(cp):
        return {}

    with open(cp, "rb") as f:
        ciphertext = f.read()

    if not ciphertext:
        return {}

    plaintext = decrypt(ciphertext, key)
    return json.loads(plaintext.decode("utf-8"))


def _save_store(project_dir: str, key: bytes, store: dict):
    """Encrypt and save the credential store."""
    _ensure_dir(project_dir)
    cp = _cred_path(project_dir)
    plaintext = json.dumps(store, indent=2).encode("utf-8")
    ciphertext = encrypt(plaintext, key)

    with open(cp, "wb") as f:
        f.write(ciphertext)
    _set_file_permissions(cp)


def store_credential(project_dir: str, service: str, credential: str) -> str:
    """Store a credential for a service. Returns status message."""
    key = get_or_create_key(project_dir)
    store = _load_store(project_dir, key)
    existed = service in store
    store[service] = {
        "value": credential,
        "stored_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _save_store(project_dir, key, store)
    action = "updated" if existed else "stored"
    return f"Credential for '{service}' {action} successfully."


def get_credential(project_dir: str, service: str) -> str:
    """Retrieve a credential. Returns the value or raises KeyError."""
    key = get_or_create_key(project_dir)
    store = _load_store(project_dir, key)
    if service not in store:
        raise KeyError(f"No credential found for service '{service}'")
    return store[service]["value"]


def list_credentials(project_dir: str) -> list:
    """List stored service names with metadata (never values)."""
    key = get_or_create_key(project_dir)
    store = _load_store(project_dir, key)
    result = []
    for svc, data in sorted(store.items()):
        result.append({
            "service": svc,
            "stored_at": data.get("stored_at", "unknown"),
        })
    return result


def delete_credential(project_dir: str, service: str) -> str:
    """Delete a credential. Returns status message."""
    key = get_or_create_key(project_dir)
    store = _load_store(project_dir, key)
    if service not in store:
        raise KeyError(f"No credential found for service '{service}'")
    del store[service]
    _save_store(project_dir, key, store)
    return f"Credential for '{service}' deleted."


# --- CLI ---

USAGE = """Usage:
    credential-manager.py <project_dir> store <service> <key>
    credential-manager.py <project_dir> get <service>
    credential-manager.py <project_dir> list
    credential-manager.py <project_dir> delete <service>

Supported services: ibkr, zerodha, deribit, coingecko, google-sheets, or any custom name.
"""


def main():
    if len(sys.argv) < 3:
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    project_dir = sys.argv[1]
    command = sys.argv[2]

    try:
        if command == "store":
            if len(sys.argv) != 5:
                print("Usage: credential-manager.py <project_dir> store <service> <key>", file=sys.stderr)
                sys.exit(1)
            result = store_credential(project_dir, sys.argv[3], sys.argv[4])
            print(result)

        elif command == "get":
            if len(sys.argv) != 4:
                print("Usage: credential-manager.py <project_dir> get <service>", file=sys.stderr)
                sys.exit(1)
            value = get_credential(project_dir, sys.argv[3])
            print(value)

        elif command == "list":
            entries = list_credentials(project_dir)
            if not entries:
                print("No credentials stored.")
            else:
                print(json.dumps(entries, indent=2))

        elif command == "delete":
            if len(sys.argv) != 4:
                print("Usage: credential-manager.py <project_dir> delete <service>", file=sys.stderr)
                sys.exit(1)
            result = delete_credential(project_dir, sys.argv[3])
            print(result)

        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            print(USAGE, file=sys.stderr)
            sys.exit(1)

    except KeyError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
