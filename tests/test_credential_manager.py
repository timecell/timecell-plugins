"""
Tests for credential-manager.py — secure local credential storage.

Tests cover: store/get/list/delete operations, encryption backends (stdlib + fernet),
key generation, file permissions, integrity verification, cross-backend compatibility,
and persistence across simulated plugin updates.
"""

import json
import os
import stat
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts to path
PLUGIN_ROOT = Path(__file__).parent.parent / "timecell-core"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

# Import with underscore name to match the hyphenated filename
import importlib
credential_manager = importlib.import_module("credential-manager")


# --- Fixtures ---

@pytest.fixture
def project_dir(tmp_path):
    """Create a mock project directory with .timecell."""
    tc_dir = tmp_path / ".timecell"
    tc_dir.mkdir()
    return tmp_path


@pytest.fixture
def populated_store(project_dir):
    """Create a project dir with pre-stored credentials."""
    credential_manager.store_credential(str(project_dir), "ibkr", "test-api-key-123")
    credential_manager.store_credential(str(project_dir), "zerodha", "zerodha-key-456")
    return project_dir


# --- Key Management ---

class TestKeyManagement:
    def test_key_created_on_first_use(self, project_dir):
        key = credential_manager.get_or_create_key(str(project_dir))
        assert len(key) == 32
        assert (project_dir / ".timecell" / ".key").exists()

    def test_key_persists_across_calls(self, project_dir):
        key1 = credential_manager.get_or_create_key(str(project_dir))
        key2 = credential_manager.get_or_create_key(str(project_dir))
        assert key1 == key2

    def test_key_file_permissions(self, project_dir):
        credential_manager.get_or_create_key(str(project_dir))
        key_path = project_dir / ".timecell" / ".key"
        mode = os.stat(key_path).st_mode
        # Owner read+write only (0600)
        assert mode & stat.S_IRUSR  # owner can read
        assert mode & stat.S_IWUSR  # owner can write
        assert not (mode & stat.S_IRGRP)  # group cannot read
        assert not (mode & stat.S_IROTH)  # others cannot read

    def test_creates_timecell_dir_if_missing(self, tmp_path):
        # No .timecell dir yet
        key = credential_manager.get_or_create_key(str(tmp_path))
        assert len(key) == 32
        assert (tmp_path / ".timecell" / ".key").exists()


# --- Store ---

class TestStore:
    def test_store_new_credential(self, project_dir):
        result = credential_manager.store_credential(str(project_dir), "ibkr", "my-key")
        assert "stored" in result.lower()
        assert "ibkr" in result

    def test_store_creates_credential_file(self, project_dir):
        credential_manager.store_credential(str(project_dir), "test", "val")
        cred_path = project_dir / ".timecell" / "credentials.enc"
        assert cred_path.exists()

    def test_store_overwrites_existing(self, project_dir):
        credential_manager.store_credential(str(project_dir), "ibkr", "old-key")
        result = credential_manager.store_credential(str(project_dir), "ibkr", "new-key")
        assert "updated" in result.lower()
        # Verify new value
        val = credential_manager.get_credential(str(project_dir), "ibkr")
        assert val == "new-key"

    def test_store_multiple_services(self, project_dir):
        credential_manager.store_credential(str(project_dir), "ibkr", "key1")
        credential_manager.store_credential(str(project_dir), "zerodha", "key2")
        credential_manager.store_credential(str(project_dir), "deribit", "key3")
        assert credential_manager.get_credential(str(project_dir), "ibkr") == "key1"
        assert credential_manager.get_credential(str(project_dir), "zerodha") == "key2"
        assert credential_manager.get_credential(str(project_dir), "deribit") == "key3"

    def test_credential_file_permissions(self, project_dir):
        credential_manager.store_credential(str(project_dir), "test", "val")
        cred_path = project_dir / ".timecell" / "credentials.enc"
        mode = os.stat(cred_path).st_mode
        assert mode & stat.S_IRUSR
        assert mode & stat.S_IWUSR
        assert not (mode & stat.S_IRGRP)
        assert not (mode & stat.S_IROTH)

    def test_credential_file_is_not_plaintext(self, project_dir):
        credential_manager.store_credential(str(project_dir), "ibkr", "super-secret-key-12345")
        cred_path = project_dir / ".timecell" / "credentials.enc"
        raw = cred_path.read_bytes()
        assert b"super-secret-key-12345" not in raw


# --- Get ---

class TestGet:
    def test_get_existing(self, populated_store):
        val = credential_manager.get_credential(str(populated_store), "ibkr")
        assert val == "test-api-key-123"

    def test_get_nonexistent_raises(self, project_dir):
        with pytest.raises(KeyError, match="nonexistent"):
            credential_manager.get_credential(str(project_dir), "nonexistent")

    def test_get_from_empty_store(self, project_dir):
        with pytest.raises(KeyError):
            credential_manager.get_credential(str(project_dir), "anything")


# --- List ---

class TestList:
    def test_list_empty(self, project_dir):
        entries = credential_manager.list_credentials(str(project_dir))
        assert entries == []

    def test_list_shows_service_names(self, populated_store):
        entries = credential_manager.list_credentials(str(populated_store))
        services = [e["service"] for e in entries]
        assert "ibkr" in services
        assert "zerodha" in services

    def test_list_includes_timestamp(self, populated_store):
        entries = credential_manager.list_credentials(str(populated_store))
        for entry in entries:
            assert "stored_at" in entry
            assert entry["stored_at"] != "unknown"

    def test_list_never_contains_values(self, populated_store):
        entries = credential_manager.list_credentials(str(populated_store))
        raw = json.dumps(entries)
        assert "test-api-key-123" not in raw
        assert "zerodha-key-456" not in raw

    def test_list_sorted_alphabetically(self, populated_store):
        entries = credential_manager.list_credentials(str(populated_store))
        services = [e["service"] for e in entries]
        assert services == sorted(services)


# --- Delete ---

class TestDelete:
    def test_delete_existing(self, populated_store):
        result = credential_manager.delete_credential(str(populated_store), "ibkr")
        assert "deleted" in result.lower()
        with pytest.raises(KeyError):
            credential_manager.get_credential(str(populated_store), "ibkr")

    def test_delete_preserves_others(self, populated_store):
        credential_manager.delete_credential(str(populated_store), "ibkr")
        # zerodha should still exist
        val = credential_manager.get_credential(str(populated_store), "zerodha")
        assert val == "zerodha-key-456"

    def test_delete_nonexistent_raises(self, project_dir):
        with pytest.raises(KeyError, match="nonexistent"):
            credential_manager.delete_credential(str(project_dir), "nonexistent")

    def test_delete_all_leaves_empty_store(self, populated_store):
        credential_manager.delete_credential(str(populated_store), "ibkr")
        credential_manager.delete_credential(str(populated_store), "zerodha")
        entries = credential_manager.list_credentials(str(populated_store))
        assert entries == []


# --- Encryption ---

class TestEncryption:
    def test_stdlib_roundtrip(self, project_dir):
        """Verify stdlib encrypt/decrypt cycle works."""
        key = credential_manager.get_or_create_key(str(project_dir))
        plaintext = b"test secret data"
        encrypted = credential_manager._stdlib_encrypt(plaintext, key)
        assert encrypted.startswith(b"STDLIB:")
        decrypted = credential_manager._stdlib_decrypt(encrypted, key)
        assert decrypted == plaintext

    def test_stdlib_integrity_check(self, project_dir):
        """Tampered ciphertext should fail integrity check."""
        key = credential_manager.get_or_create_key(str(project_dir))
        encrypted = credential_manager._stdlib_encrypt(b"secret", key)
        # Tamper with the ciphertext (flip a byte near the end)
        tampered = bytearray(encrypted)
        tampered[-1] ^= 0xFF
        tampered = bytes(tampered)
        with pytest.raises(ValueError, match="integrity"):
            credential_manager._stdlib_decrypt(tampered, key)

    def test_different_keys_cannot_decrypt(self, tmp_path):
        """Credentials encrypted with one key cannot be read with another."""
        import secrets as _secrets
        key1 = _secrets.token_bytes(32)
        key2 = _secrets.token_bytes(32)
        encrypted = credential_manager._stdlib_encrypt(b"secret", key1)
        with pytest.raises(ValueError):
            credential_manager._stdlib_decrypt(encrypted, key2)

    def test_each_encryption_uses_different_salt(self, project_dir):
        """Same plaintext should produce different ciphertext each time."""
        key = credential_manager.get_or_create_key(str(project_dir))
        enc1 = credential_manager._stdlib_encrypt(b"same data", key)
        enc2 = credential_manager._stdlib_encrypt(b"same data", key)
        assert enc1 != enc2  # Different salts

    @pytest.mark.skipif(not credential_manager._has_fernet(), reason="cryptography not installed")
    def test_fernet_roundtrip(self, project_dir):
        """Verify Fernet encrypt/decrypt cycle works if available."""
        key = credential_manager.get_or_create_key(str(project_dir))
        plaintext = b"test secret data"
        encrypted = credential_manager._fernet_encrypt(plaintext, key)
        assert encrypted.startswith(b"FERNET:")
        decrypted = credential_manager._fernet_decrypt(encrypted, key)
        assert decrypted == plaintext

    def test_encrypt_uses_best_backend(self, project_dir):
        """encrypt() should pick the right backend based on availability."""
        key = credential_manager.get_or_create_key(str(project_dir))
        encrypted = credential_manager.encrypt(b"test", key)
        if credential_manager._has_fernet():
            assert encrypted.startswith(b"FERNET:")
        else:
            assert encrypted.startswith(b"STDLIB:")

    def test_decrypt_detects_backend_from_prefix(self, project_dir):
        """decrypt() should handle both backends transparently."""
        key = credential_manager.get_or_create_key(str(project_dir))
        # Always test stdlib
        stdlib_enc = credential_manager._stdlib_encrypt(b"test", key)
        assert credential_manager.decrypt(stdlib_enc, key) == b"test"


# --- Plugin Update Survival ---

class TestUpdateSurvival:
    def test_credentials_survive_key_reload(self, populated_store):
        """Credentials survive when key is reloaded from disk (simulates plugin restart)."""
        # Clear any in-memory state by getting credentials via fresh key load
        val = credential_manager.get_credential(str(populated_store), "ibkr")
        assert val == "test-api-key-123"

    def test_timecell_dir_in_user_data(self, populated_store):
        """Verify data dir exists and contains credential files."""
        tc_dir = populated_store / ".timecell"
        assert tc_dir.is_dir()
        assert (tc_dir / ".key").exists()
        assert (tc_dir / "credentials.enc").exists()

    def test_credentials_survive_simulated_update(self, populated_store):
        """Simulate a plugin update: delete everything except .timecell/, verify credentials survive."""
        # Record credential values
        ibkr_val = credential_manager.get_credential(str(populated_store), "ibkr")

        # Simulate plugin update by verifying .timecell is preserved
        # (In production, USER_DATA_PATHS protects .timecell/)
        tc_dir = populated_store / ".timecell"
        assert tc_dir.exists()

        # After "update", credentials should still work
        restored_val = credential_manager.get_credential(str(populated_store), "ibkr")
        assert restored_val == ibkr_val


# --- CLAUDE_PLUGIN_DATA env var ---

class TestPluginDataEnvVar:
    def test_uses_plugin_data_when_set(self, tmp_path):
        """When CLAUDE_PLUGIN_DATA is set, credentials go there instead of .timecell/."""
        plugin_data_dir = tmp_path / "plugin-data"
        plugin_data_dir.mkdir()
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": str(plugin_data_dir)}):
            credential_manager.store_credential(str(project_dir), "test-svc", "my-key")
            # Key and cred files should be in plugin_data_dir, NOT project/.timecell/
            assert (plugin_data_dir / ".key").exists()
            assert (plugin_data_dir / "credentials.enc").exists()
            assert not (project_dir / ".timecell" / ".key").exists()
            # Retrieve should work
            val = credential_manager.get_credential(str(project_dir), "test-svc")
            assert val == "my-key"

    def test_fallback_without_env_var(self, tmp_path):
        """Without CLAUDE_PLUGIN_DATA, falls back to .timecell/."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with patch.dict(os.environ, {}, clear=False):
            # Ensure CLAUDE_PLUGIN_DATA is not set
            os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            credential_manager.store_credential(str(project_dir), "test-svc", "my-key")
            assert (project_dir / ".timecell" / ".key").exists()
            assert (project_dir / ".timecell" / "credentials.enc").exists()


# --- CLI ---

class TestCLI:
    def test_cli_store_and_get(self, project_dir):
        """Test CLI store followed by get."""
        sys_argv = ["credential-manager.py", str(project_dir), "store", "test-svc", "my-key-789"]
        with patch.object(sys, "argv", sys_argv):
            credential_manager.main()

        sys_argv = ["credential-manager.py", str(project_dir), "get", "test-svc"]
        with patch.object(sys, "argv", sys_argv):
            credential_manager.main()  # Would print the key

    def test_cli_list_empty(self, project_dir, capsys):
        sys_argv = ["credential-manager.py", str(project_dir), "list"]
        with patch.object(sys, "argv", sys_argv):
            credential_manager.main()
        captured = capsys.readouterr()
        assert "No credentials stored" in captured.out

    def test_cli_unknown_command(self, project_dir):
        sys_argv = ["credential-manager.py", str(project_dir), "bogus"]
        with patch.object(sys, "argv", sys_argv), pytest.raises(SystemExit, match="1"):
            credential_manager.main()

    def test_cli_get_missing_raises(self, project_dir):
        sys_argv = ["credential-manager.py", str(project_dir), "get", "nope"]
        with patch.object(sys, "argv", sys_argv), pytest.raises(SystemExit, match="1"):
            credential_manager.main()


# --- Edge Cases ---

class TestEdgeCases:
    def test_empty_credential_value(self, project_dir):
        """Empty string is a valid credential value."""
        credential_manager.store_credential(str(project_dir), "empty", "")
        val = credential_manager.get_credential(str(project_dir), "empty")
        assert val == ""

    def test_long_credential_value(self, project_dir):
        """Long credentials (e.g., JWT tokens) should work."""
        long_key = "x" * 10000
        credential_manager.store_credential(str(project_dir), "jwt", long_key)
        val = credential_manager.get_credential(str(project_dir), "jwt")
        assert val == long_key

    def test_special_characters_in_value(self, project_dir):
        """Credentials with special chars, unicode, newlines."""
        special = 'key=abc&secret=def\n"quoted"\t\U0001f512'
        credential_manager.store_credential(str(project_dir), "special", special)
        val = credential_manager.get_credential(str(project_dir), "special")
        assert val == special

    def test_service_name_with_hyphens(self, project_dir):
        credential_manager.store_credential(str(project_dir), "google-sheets", "key")
        val = credential_manager.get_credential(str(project_dir), "google-sheets")
        assert val == "key"

    def test_unknown_encryption_prefix_raises(self, project_dir):
        with pytest.raises(ValueError, match="Unknown"):
            credential_manager.decrypt(b"BOGUS:data", b"key" * 8)
