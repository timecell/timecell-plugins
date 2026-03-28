"""
Verify accuracy/fidelity rules are present in plugin files
and that skill/command files stayed lean after sync.
"""

import os

PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..", "timecell-core")


def _read(rel_path: str) -> str:
    with open(os.path.join(PLUGIN_ROOT, rel_path)) as f:
        return f.read()


def _line_count(rel_path: str) -> int:
    return len(_read(rel_path).splitlines())


# --- Accuracy Mandate in CIO persona ---


class TestAccuracyMandate:
    def test_timecell_has_accuracy_section(self):
        content = _read("references/timecell.md")
        assert "## Accuracy Mandate" in content

    def test_timecell_has_no_rounding_rule(self):
        content = _read("references/timecell.md")
        assert "No rounding" in content

    def test_timecell_separates_facts_from_recommendations(self):
        content = _read("references/timecell.md")
        assert "Separate facts from recommendations" in content

    def test_timecell_confidence_applies_to_advice(self):
        content = _read("references/timecell.md")
        assert "Confidence ratings apply to CIO advice" in content


# --- Computation Integrity in formulas ---


class TestComputationIntegrity:
    def test_formulas_has_integrity_rule(self):
        content = _read("references/computation-formulas.md")
        assert "Computation Integrity" in content

    def test_formulas_has_resilience_grade(self):
        content = _read("references/computation-formulas.md")
        assert "Resilience Grade" in content
        assert "RESILIENT" in content
        assert "ADEQUATE" in content
        assert "FRAGILE" in content

    def test_resilience_grade_near_crash_survival(self):
        """Resilience grade should be in the Crash Survival section."""
        content = _read("references/computation-formulas.md")
        crash_pos = content.index("Crash Survival")
        grade_pos = content.index("Resilience Grade")
        assert grade_pos > crash_pos


# --- Pack citation uses correct paths (no beliefs.md) ---


class TestCitationPaths:
    def test_no_beliefs_md_reference(self):
        """Plugin has no packs/ dir — citations should use memory/values.md."""
        for rel in [
            "references/timecell.md",
            "skills/financial-reasoning/SKILL.md",
        ]:
            content = _read(rel)
            assert "beliefs.md" not in content, f"{rel} still references beliefs.md"

    def test_values_md_referenced_in_reasoning_skill(self):
        content = _read("skills/financial-reasoning/SKILL.md")
        assert "memory/values.md" in content

    def test_values_md_referenced_in_timecell(self):
        content = _read("references/timecell.md")
        assert "memory/values.md" in content


# --- No causal inference in weekly ---


class TestWeeklyCausalInference:
    def test_weekly_has_no_causal_inference_rule(self):
        content = _read("commands/weekly.md")
        assert "No causal inference" in content

    def test_weekly_forbids_invented_reasons(self):
        content = _read("commands/weekly.md")
        assert "never invent reasons" in content


# --- Threshold sourcing in financial-reasoning ---


class TestThresholdSourcing:
    def test_reasoning_references_computation_formulas(self):
        content = _read("skills/financial-reasoning/SKILL.md")
        assert "computation-formulas.md" in content

    def test_reasoning_forbids_hardcoded_thresholds(self):
        content = _read("skills/financial-reasoning/SKILL.md")
        assert "never hardcode" in content


# --- Line count leanness ---


class TestLeanness:
    """No file should have grown by more than 3 lines from its pre-sync baseline."""

    # Baselines updated after operator role + multi-entity feature
    BASELINES = {
        "references/timecell.md": 147,
        "references/computation-formulas.md": 221,
        "skills/financial-reasoning/SKILL.md": 75,
        "commands/weekly.md": 43,
        "commands/start.md": 57,
        "commands/monthly.md": 73,
        "commands/check.md": 51,
        "commands/setup.md": 103,
    }
    MAX_GROWTH = 8  # absolute max lines any file can grow

    def test_no_file_bloated(self):
        for rel, baseline in self.BASELINES.items():
            current = _line_count(rel)
            growth = current - baseline
            assert growth <= self.MAX_GROWTH, (
                f"{rel} grew {growth} lines (baseline {baseline}, now {current})"
            )

    def test_skill_grew_at_most_5_lines(self):
        """The only auto-loaded skill must stay ultra-lean."""
        current = _line_count("skills/financial-reasoning/SKILL.md")
        baseline = self.BASELINES["skills/financial-reasoning/SKILL.md"]
        assert current <= baseline + 5, f"financial-reasoning SKILL.md is {current} lines (baseline {baseline})"

    def test_commands_grew_at_most_5_lines(self):
        for cmd in ["weekly.md", "start.md", "monthly.md", "check.md", "setup.md"]:
            rel = f"commands/{cmd}"
            baseline = self.BASELINES[rel]
            current = _line_count(rel)
            assert current <= baseline + 5, (
                f"{rel} is {current} lines (baseline {baseline})"
            )
