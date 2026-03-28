"""
Regression tests for S135 Plugin Quality Audit findings.

Each test catches a specific audit finding so it cannot regress.
"""

import os
import glob

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
CORE_ROOT = os.path.join(REPO_ROOT, "timecell-core")
BITCOIN_ROOT = os.path.join(REPO_ROOT, "timecell-bitcoin")
ESTATE_ROOT = os.path.join(REPO_ROOT, "timecell-estate")


def _read(base, rel_path: str) -> str:
    with open(os.path.join(base, rel_path)) as f:
        return f.read()


def _all_md_files(*roots):
    """Yield all .md files under the given root directories."""
    for root in roots:
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                if fn.endswith(".md"):
                    yield os.path.join(dirpath, fn)


def _all_py_files(*roots):
    """Yield all .py files under the given root directories."""
    for root in roots:
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                if fn.endswith(".py"):
                    yield os.path.join(dirpath, fn)


# ---------------------------------------------------------------------------
# C1: Single entity concentration threshold must be WARNING > 30%, not 40%
# ---------------------------------------------------------------------------

class TestC1ConcentrationThreshold:
    def test_start_warns_at_30_percent(self):
        content = _read(CORE_ROOT, "commands/start.md")
        assert "WARNING > 30%" in content, (
            "start.md single entity WARNING threshold must be > 30% "
            "(was incorrectly > 40% before S135 fix)"
        )

    def test_start_does_not_warn_at_40_percent(self):
        content = _read(CORE_ROOT, "commands/start.md")
        assert "WARNING > 40%" not in content, (
            "start.md must not have WARNING > 40% for single entity — "
            "canonical threshold is > 30%"
        )


# ---------------------------------------------------------------------------
# C2: Runway must have all 5 graduated zones
# ---------------------------------------------------------------------------

class TestC2RunwayZones:
    def test_start_has_all_five_runway_zones(self):
        content = _read(CORE_ROOT, "commands/start.md")
        for zone in ["CRITICAL", "WARNING", "WATCH", "SAFE", "STRONG"]:
            assert zone in content, (
                f"start.md runway thresholds missing {zone} zone — "
                "must have all 5 graduated zones"
            )

    def test_start_runway_has_watch_zone(self):
        """Specifically test WATCH zone since C2 was about its absence."""
        content = _read(CORE_ROOT, "commands/start.md")
        assert "WATCH 18-24mo" in content, (
            "start.md runway must include WATCH 18-24mo zone "
            "(was collapsed into WARNING before S135 fix)"
        )


# ---------------------------------------------------------------------------
# H1: No command file should reference memory/profile.md
# ---------------------------------------------------------------------------

class TestH1ProfilePath:
    def test_no_command_references_memory_profile(self):
        """All commands should use profile.md, not memory/profile.md."""
        command_dirs = [
            os.path.join(CORE_ROOT, "commands"),
            os.path.join(BITCOIN_ROOT, "commands"),
            os.path.join(ESTATE_ROOT, "commands"),
            os.path.join(REPO_ROOT, "timecell-indian-mf", "commands"),
        ]
        violations = []
        for cmd_dir in command_dirs:
            if not os.path.isdir(cmd_dir):
                continue
            for fn in os.listdir(cmd_dir):
                if not fn.endswith(".md"):
                    continue
                filepath = os.path.join(cmd_dir, fn)
                with open(filepath) as f:
                    content = f.read()
                if "memory/profile.md" in content:
                    violations.append(filepath)
        assert not violations, (
            f"Commands must use 'profile.md' not 'memory/profile.md': "
            f"{violations}"
        )


# ---------------------------------------------------------------------------
# H2: No file should reference a "guardrails skill" — it's a reference file
# ---------------------------------------------------------------------------

class TestH2GuardrailsSkillReference:
    def test_no_guardrails_skill_references(self):
        """design-rules.md and other files must not call guardrails a 'skill'."""
        violations = []
        for filepath in _all_md_files(CORE_ROOT):
            with open(filepath) as f:
                content = f.read().lower()
            # Match "guardrails skill" or "the guardrails skill" patterns
            if "`guardrails` skill" in content or "guardrails skill" in content:
                violations.append(filepath)
        assert not violations, (
            f"Files must not reference a 'guardrails skill' — "
            f"canonical source is computation-formulas.md: {violations}"
        )

    def test_no_skill_guardrails_as_source(self):
        """visual-templates.md must not cite skill-guardrails as source of truth."""
        violations = []
        for filepath in _all_md_files(CORE_ROOT):
            with open(filepath) as f:
                content = f.read()
            if "skill-guardrails" in content and "source of truth" in content.lower():
                violations.append(filepath)
        assert not violations, (
            f"Files must not cite skill-guardrails as source of truth — "
            f"use computation-formulas.md: {violations}"
        )


# ---------------------------------------------------------------------------
# H3: No file should contain fo-web references
# ---------------------------------------------------------------------------

class TestH3FoWebReferences:
    def test_no_fo_web_in_python_files(self):
        """No Python file should reference the dead fo-web codebase."""
        violations = []
        for filepath in _all_py_files(BITCOIN_ROOT):
            with open(filepath) as f:
                content = f.read()
            if "fo-web" in content or "fo_web" in content:
                violations.append(filepath)
        assert not violations, (
            f"Python files must not reference stale fo-web codebase: {violations}"
        )

    def test_no_fo_web_in_any_plugin(self):
        """No file across any plugin should reference fo-web."""
        plugin_roots = [CORE_ROOT, BITCOIN_ROOT, ESTATE_ROOT,
                        os.path.join(REPO_ROOT, "timecell-indian-mf")]
        violations = []
        for filepath in _all_md_files(*plugin_roots):
            with open(filepath) as f:
                content = f.read()
            if "fo-web" in content:
                violations.append(filepath)
        for filepath in _all_py_files(*plugin_roots):
            with open(filepath) as f:
                content = f.read()
            if "fo-web" in content or "fo_web" in content:
                violations.append(filepath)
        assert not violations, (
            f"Files must not reference stale fo-web codebase: {violations}"
        )


# ---------------------------------------------------------------------------
# M2: Asset class concentration must include WATCH zone
# ---------------------------------------------------------------------------

class TestM2AssetClassWatch:
    def test_start_has_asset_class_watch_zone(self):
        content = _read(CORE_ROOT, "commands/start.md")
        assert "WATCH > 40%" in content, (
            "start.md asset class thresholds must include WATCH > 40% zone"
        )


# ---------------------------------------------------------------------------
# PostCompact hook — profile context must survive compaction
# ---------------------------------------------------------------------------

class TestPostCompactHook:
    def test_hooks_json_has_post_compact(self):
        import json
        hooks_path = os.path.join(CORE_ROOT, "hooks", "hooks.json")
        with open(hooks_path) as f:
            hooks = json.load(f)
        assert "PostCompact" in hooks["hooks"], (
            "hooks.json must include PostCompact event to restore "
            "profile context after compaction"
        )

    def test_post_compact_references_script(self):
        import json
        hooks_path = os.path.join(CORE_ROOT, "hooks", "hooks.json")
        with open(hooks_path) as f:
            hooks = json.load(f)
        post_compact = hooks["hooks"]["PostCompact"]
        commands = [
            h["command"]
            for entry in post_compact
            for h in entry["hooks"]
            if h.get("type") == "command"
        ]
        assert any("post-compact-reminder.py" in cmd for cmd in commands), (
            "PostCompact hook must invoke post-compact-reminder.py"
        )

    def test_post_compact_script_exists(self):
        script_path = os.path.join(CORE_ROOT, "scripts", "post-compact-reminder.py")
        assert os.path.isfile(script_path), (
            "scripts/post-compact-reminder.py must exist"
        )
