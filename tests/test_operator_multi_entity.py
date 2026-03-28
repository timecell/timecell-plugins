"""
Structural validation for operator role + multi-entity /start feature.
Verifies all required content exists across modified plugin files.
"""

import os
import subprocess

PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..", "timecell-core")


def _read(rel_path: str) -> str:
    with open(os.path.join(PLUGIN_ROOT, rel_path)) as f:
        return f.read()


# --- commands/start.md ---


class TestStartCommand:
    def test_has_role_check_section(self):
        content = _read("commands/start.md")
        assert "Role Check" in content

    def test_role_check_before_step_3(self):
        content = _read("commands/start.md")
        role_pos = content.index("Role Check")
        step3_pos = content.index("Step 3")
        assert role_pos < step3_pos

    def test_has_operator_greeting(self):
        content = _read("commands/start.md")
        assert "operator" in content.lower()

    def test_has_multi_entity_view(self):
        content = _read("commands/start.md")
        assert "multi-entity" in content.lower()

    def test_has_managed_by_filter(self):
        content = _read("commands/start.md")
        assert "managed_by" in content

    def test_preserves_2_tool_budget(self):
        content = _read("commands/start.md")
        assert "2 tool calls max" in content

    def test_role_check_uses_zero_tool_calls(self):
        content = _read("commands/start.md")
        assert "0 tool calls" in content

    def test_has_operator_footer(self):
        content = _read("commands/start.md")
        assert "strategy deferred to principals" in content


# --- references/timecell.md ---


class TestTimecellPersona:
    def test_has_operator_role_section(self):
        content = _read("references/timecell.md")
        assert "## Operator Role" in content

    def test_operator_suppresses_strategy(self):
        content = _read("references/timecell.md")
        assert "strategy recommendations" in content.lower() or "strategy" in content

    def test_operator_suppresses_memory_enrichment(self):
        content = _read("references/timecell.md")
        assert "memory enrichment" in content.lower()

    def test_operator_preserves_guardrails(self):
        content = _read("references/timecell.md")
        operator_section_start = content.index("## Operator Role")
        operator_section = content[operator_section_start:content.index("## Plugin-Aware")]
        assert "guardrail" in operator_section.lower()

    def test_operator_blocks_setup(self):
        content = _read("references/timecell.md")
        assert "/tc:setup" in content

    def test_operator_section_before_plugin_aware(self):
        content = _read("references/timecell.md")
        op_pos = content.index("## Operator Role")
        plugin_pos = content.index("## Plugin-Aware")
        assert op_pos < plugin_pos


# --- references/computation-formulas.md ---


class TestComputationFormulas:
    def test_has_entity_aggregation_section(self):
        content = _read("references/computation-formulas.md")
        assert "Entity Aggregation" in content

    def test_has_managed_entities_formula(self):
        content = _read("references/computation-formulas.md")
        assert "managed_by" in content

    def test_has_cross_entity_alert_rules(self):
        content = _read("references/computation-formulas.md")
        assert "Cross-Entity Alert Rules" in content

    def test_has_custodian_concentration_rule(self):
        content = _read("references/computation-formulas.md")
        assert "Custodian concentration" in content or "custodian" in content.lower()

    def test_has_inactivity_rule(self):
        content = _read("references/computation-formulas.md")
        assert "30 days" in content

    def test_entity_aggregation_before_session_count(self):
        content = _read("references/computation-formulas.md")
        agg_pos = content.index("Entity Aggregation")
        session_pos = content.index("Session Count")
        assert agg_pos < session_pos


# --- references/formatting.md ---


class TestFormattingRules:
    def test_has_inr_section(self):
        content = _read("references/formatting.md")
        assert "INR Formatting" in content

    def test_has_rupee_symbol(self):
        content = _read("references/formatting.md")
        assert "₹" in content

    def test_has_crore_notation(self):
        content = _read("references/formatting.md")
        assert "Crore" in content or "Cr" in content

    def test_has_lakh_notation(self):
        content = _read("references/formatting.md")
        assert "Lakh" in content


# --- references/lifecycle.md ---


class TestLifecycle:
    def test_has_operator_bypass(self):
        content = _read("references/lifecycle.md")
        assert "Operator Bypass" in content

    def test_operator_bypass_before_stage_1(self):
        content = _read("references/lifecycle.md")
        bypass_pos = content.index("Operator Bypass")
        stage1_pos = content.index("Stage 1")
        assert bypass_pos < stage1_pos


# --- skills/financial-reasoning ---


class TestFinancialReasoning:
    def test_has_operator_role_check(self):
        content = _read("skills/financial-reasoning/SKILL.md")
        assert "operator" in content.lower()

    def test_redirects_strategy_to_principal(self):
        content = _read("skills/financial-reasoning/SKILL.md")
        assert "principal" in content.lower()


# --- scripts/validate-profile.py ---


class TestValidateProfile:
    def test_script_validates_role_field(self):
        content = _read("scripts/validate-profile.py")
        assert "role" in content.lower()

    def test_script_accepts_principal_and_operator(self):
        content = _read("scripts/validate-profile.py")
        assert "principal" in content
        assert "operator" in content

    def test_script_warns_on_unknown_role(self):
        content = _read("scripts/validate-profile.py")
        assert "Unknown role" in content or "unknown role" in content.lower()

    def test_valid_profile_no_role(self):
        """Profile without role field should still be valid (defaults to principal)."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "validate_profile",
            os.path.join(PLUGIN_ROOT, "scripts", "validate-profile.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Create a minimal valid profile
        import tempfile

        profile = (
            "# Profile\n\n"
            "- Name: Test User\n"
            "- Residency: Singapore\n"
            "- Base currency: SGD\n\n"
            "## Goals\n\n- Save $1M by 2030\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(profile)
            f.flush()
            valid, errors, warnings = mod.validate_profile(f.name)
        os.unlink(f.name)
        assert valid, f"Expected valid but got errors: {errors}"
        assert len(warnings) == 0

    def test_valid_profile_with_operator_role(self):
        """Profile with role: operator should be valid."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "validate_profile",
            os.path.join(PLUGIN_ROOT, "scripts", "validate-profile.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        import tempfile

        profile = (
            "# Profile\n\n"
            "- Name: Arvind Sharma\n"
            "- Residency: India\n"
            "- Base currency: INR\n"
            "- Role: operator\n\n"
            "## Goals\n\n- Manage 3 entities\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(profile)
            f.flush()
            valid, errors, warnings = mod.validate_profile(f.name)
        os.unlink(f.name)
        assert valid, f"Expected valid but got errors: {errors}"
        assert len(warnings) == 0

    def test_unknown_role_produces_warning(self):
        """Profile with role: admin should produce a warning."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "validate_profile",
            os.path.join(PLUGIN_ROOT, "scripts", "validate-profile.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        import tempfile

        profile = (
            "# Profile\n\n"
            "- Name: Test User\n"
            "- Residency: Singapore\n"
            "- Base currency: SGD\n"
            "- Role: admin\n\n"
            "## Goals\n\n- Test\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(profile)
            f.flush()
            valid, errors, warnings = mod.validate_profile(f.name)
        os.unlink(f.name)
        assert valid, f"Expected valid but got errors: {errors}"
        assert len(warnings) == 1
        assert "admin" in warnings[0].lower()
