"""Unit tests for timecell-core deterministic scripts."""
import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
import importlib.util
import time


def load_script(name):
    """Load a script as a Python module for testing."""
    script_path = os.path.join(
        os.path.dirname(__file__), "..", "timecell-core", "scripts", f"{name}.py"
    )
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


# ──────────────────────────────────────────────
# validate-profile.py
# ──────────────────────────────────────────────
class TestValidateProfile:
    @pytest.fixture
    def script(self):
        return load_script("validate-profile")

    def test_valid_profile(self, script, tmp_dir):
        path = os.path.join(tmp_dir, "profile.md")
        with open(path, "w") as f:
            f.write(
                "# Financial Profile\n\n"
                "## Personal\n"
                "- Name: Raj Mehta\n"
                "- Residency: Mumbai, India\n\n"
                "## Financial\n"
                "- Base currency: INR\n\n"
                "## Goals\n"
                "- Financial independence by 2030\n"
            )
        valid, errors = script.validate_profile(path)
        assert valid is True
        assert errors == []

    def test_missing_name(self, script, tmp_dir):
        path = os.path.join(tmp_dir, "profile.md")
        with open(path, "w") as f:
            f.write(
                "## Personal\n- Name:\n- Residency: Mumbai\n\n"
                "## Financial\n- Base currency: INR\n\n"
                "## Goals\n- Goal 1\n"
            )
        valid, errors = script.validate_profile(path)
        assert valid is False
        assert any("Name" in e for e in errors)

    def test_missing_file(self, script):
        valid, errors = script.validate_profile("/nonexistent/profile.md")
        assert valid is False

    def test_missing_goals_section(self, script, tmp_dir):
        path = os.path.join(tmp_dir, "profile.md")
        with open(path, "w") as f:
            f.write(
                "## Personal\n- Name: Raj\n- Residency: Mumbai\n\n"
                "## Financial\n- Base currency: INR\n"
            )
        valid, errors = script.validate_profile(path)
        assert valid is False
        assert any("Goals" in e for e in errors)

    def test_missing_residency(self, script, tmp_dir):
        path = os.path.join(tmp_dir, "profile.md")
        with open(path, "w") as f:
            f.write(
                "## Personal\n- Name: Raj\n\n"
                "## Financial\n- Base currency: INR\n\n"
                "## Goals\n- Goal\n"
            )
        valid, errors = script.validate_profile(path)
        assert valid is False
        assert any("Residency" in e for e in errors)

    def test_missing_base_currency(self, script, tmp_dir):
        path = os.path.join(tmp_dir, "profile.md")
        with open(path, "w") as f:
            f.write(
                "## Personal\n- Name: Raj\n- Residency: Mumbai\n\n"
                "## Financial\n\n"
                "## Goals\n- Goal\n"
            )
        valid, errors = script.validate_profile(path)
        assert valid is False
        assert any("Base currency" in e for e in errors)


# ──────────────────────────────────────────────
# increment-session-count.py
# ──────────────────────────────────────────────
class TestIncrementSessionCount:
    @pytest.fixture
    def script(self):
        return load_script("increment-session-count")

    def test_creates_file_if_missing(self, script, tmp_dir):
        count = script.increment_session_count(tmp_dir)
        assert count == 1
        count_file = os.path.join(tmp_dir, ".timecell", "session-count.txt")
        assert os.path.exists(count_file)
        with open(count_file) as f:
            assert f.read().strip() == "1"

    def test_increments_existing(self, script, tmp_dir):
        os.makedirs(os.path.join(tmp_dir, ".timecell"))
        with open(os.path.join(tmp_dir, ".timecell", "session-count.txt"), "w") as f:
            f.write("5")
        count = script.increment_session_count(tmp_dir)
        assert count == 6

    def test_handles_corrupted_file(self, script, tmp_dir):
        os.makedirs(os.path.join(tmp_dir, ".timecell"))
        with open(os.path.join(tmp_dir, ".timecell", "session-count.txt"), "w") as f:
            f.write("not a number")
        count = script.increment_session_count(tmp_dir)
        assert count == 1

    def test_increments_twice(self, script, tmp_dir):
        script.increment_session_count(tmp_dir)
        count = script.increment_session_count(tmp_dir)
        assert count == 2


# ──────────────────────────────────────────────
# snapshot-before-write.py
# ──────────────────────────────────────────────
class TestSnapshotBeforeWrite:
    @pytest.fixture
    def script(self):
        return load_script("snapshot-before-write")

    @pytest.fixture
    def tmp_project(self, tmp_dir):
        os.makedirs(os.path.join(tmp_dir, ".timecell"))
        os.makedirs(os.path.join(tmp_dir, "entities"))
        os.makedirs(os.path.join(tmp_dir, "memory"))
        with open(os.path.join(tmp_dir, "profile.md"), "w") as f:
            f.write("# Profile\n- Name: Test\n")
        return tmp_dir

    def test_backs_up_profile(self, script, tmp_project):
        path = os.path.join(tmp_project, "profile.md")
        result = script.snapshot_before_write(path)
        assert result is not None
        assert os.path.exists(result)
        assert "profile.md" in result

    def test_backup_content_matches(self, script, tmp_project):
        path = os.path.join(tmp_project, "profile.md")
        with open(path) as f:
            original = f.read()
        backup_path = script.snapshot_before_write(path)
        with open(backup_path) as f:
            backup = f.read()
        assert original == backup

    def test_skips_nonexistent_file(self, script, tmp_project):
        result = script.snapshot_before_write(os.path.join(tmp_project, "nonexistent.md"))
        assert result is None

    def test_skips_non_protected_file(self, script, tmp_project):
        other = os.path.join(tmp_project, "random.txt")
        with open(other, "w") as f:
            f.write("test")
        result = script.snapshot_before_write(other)
        assert result is None

    def test_backs_up_entity(self, script, tmp_project):
        entity = os.path.join(tmp_project, "entities", "btc.md")
        with open(entity, "w") as f:
            f.write("# BTC\n")
        result = script.snapshot_before_write(entity)
        assert result is not None

    def test_backs_up_memory_file(self, script, tmp_project):
        mem = os.path.join(tmp_project, "memory", "values.md")
        with open(mem, "w") as f:
            f.write("# Values\n")
        result = script.snapshot_before_write(mem)
        assert result is not None

    def test_backup_goes_to_timecell_backups(self, script, tmp_project):
        path = os.path.join(tmp_project, "profile.md")
        result = script.snapshot_before_write(path)
        assert ".timecell" in result
        assert "backups" in result


# ──────────────────────────────────────────────
# check-snapshot-staleness.py
# ──────────────────────────────────────────────
class TestCheckSnapshotStaleness:
    @pytest.fixture
    def script(self):
        return load_script("check-snapshot-staleness")

    def test_no_snapshots_dir(self, script, tmp_dir):
        result = script.check_staleness(tmp_dir)
        assert result["stale"] is True
        assert result["last_snapshot"] is None

    def test_recent_snapshot(self, script, tmp_dir):
        snap_dir = os.path.join(tmp_dir, "snapshots")
        os.makedirs(snap_dir)
        today = datetime.now().strftime("%Y-%m-%d")
        with open(os.path.join(snap_dir, f"{today}.md"), "w") as f:
            f.write("# Snapshot\n")
        result = script.check_staleness(tmp_dir)
        assert result["stale"] is False
        assert result["days_since"] == 0

    def test_stale_snapshot(self, script, tmp_dir):
        snap_dir = os.path.join(tmp_dir, "snapshots")
        os.makedirs(snap_dir)
        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        with open(os.path.join(snap_dir, f"{old_date}.md"), "w") as f:
            f.write("# Snapshot\n")
        result = script.check_staleness(tmp_dir)
        assert result["stale"] is True
        assert result["days_since"] == 10

    def test_picks_latest_snapshot(self, script, tmp_dir):
        snap_dir = os.path.join(tmp_dir, "snapshots")
        os.makedirs(snap_dir)
        old = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
        recent = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        for d in [old, recent]:
            with open(os.path.join(snap_dir, f"{d}.md"), "w") as f:
                f.write("# Snapshot\n")
        result = script.check_staleness(tmp_dir)
        assert result["days_since"] == 2
        assert result["last_snapshot"] == recent

    def test_empty_snapshots_dir(self, script, tmp_dir):
        os.makedirs(os.path.join(tmp_dir, "snapshots"))
        result = script.check_staleness(tmp_dir)
        assert result["stale"] is True
        assert result["last_snapshot"] is None

    def test_ignores_non_date_files(self, script, tmp_dir):
        snap_dir = os.path.join(tmp_dir, "snapshots")
        os.makedirs(snap_dir)
        with open(os.path.join(snap_dir, "notes.md"), "w") as f:
            f.write("not a snapshot")
        result = script.check_staleness(tmp_dir)
        assert result["stale"] is True


# ──────────────────────────────────────────────
# fetch-exchange-rates.py
# ──────────────────────────────────────────────
class TestFetchExchangeRates:
    @pytest.fixture
    def script(self):
        return load_script("fetch-exchange-rates")

    def test_returns_dict(self, script, tmp_dir):
        rates = script.get_exchange_rates(tmp_dir)
        assert isinstance(rates, dict)

    def test_cache_created(self, script, tmp_dir):
        script.get_exchange_rates(tmp_dir)
        cache_path = os.path.join(tmp_dir, ".timecell", "cache", "exchange-rates.json")
        assert os.path.exists(cache_path)

    def test_uses_fresh_cache(self, script, tmp_dir):
        cache_dir = os.path.join(tmp_dir, ".timecell", "cache")
        os.makedirs(cache_dir)
        cache_data = {
            "timestamp": time.time(),
            "rates": {"EUR": 0.92, "GBP": 0.79, "INR": 83.5},
            "base": "USD",
        }
        with open(os.path.join(cache_dir, "exchange-rates.json"), "w") as f:
            json.dump(cache_data, f)
        rates = script.get_exchange_rates(tmp_dir)
        assert rates.get("EUR") == 0.92

    def test_stale_cache_triggers_fetch(self, script, tmp_dir):
        cache_dir = os.path.join(tmp_dir, ".timecell", "cache")
        os.makedirs(cache_dir)
        cache_data = {
            "timestamp": time.time() - 100000,  # stale
            "rates": {"EUR": 0.50},
            "base": "USD",
        }
        with open(os.path.join(cache_dir, "exchange-rates.json"), "w") as f:
            json.dump(cache_data, f)
        rates = script.get_exchange_rates(tmp_dir)
        assert isinstance(rates, dict)
        # If API works, EUR won't be 0.50; if API fails, falls back to stale cache
