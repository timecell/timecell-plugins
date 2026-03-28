"""
Verify visual-templates.md exists, stays lean, and contains all required templates.
"""

import os

PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..", "timecell-core")
TEMPLATE_PATH = os.path.join(PLUGIN_ROOT, "references", "visual-templates.md")
TIMECELL_PATH = os.path.join(PLUGIN_ROOT, "references", "timecell.md")

MAX_CHARS = 4000  # budget — reference files must stay lean


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


class TestVisualTemplatesExist:
    def test_file_exists(self):
        assert os.path.exists(TEMPLATE_PATH), "visual-templates.md missing"

    def test_under_char_budget(self):
        content = _read(TEMPLATE_PATH)
        assert len(content) <= MAX_CHARS, (
            f"visual-templates.md is {len(content)} chars (budget: {MAX_CHARS})"
        )


class TestTemplateContent:
    def test_portfolio_dashboard_template(self):
        content = _read(TEMPLATE_PATH)
        assert "## 1. Portfolio Dashboard" in content

    def test_crash_survival_template(self):
        content = _read(TEMPLATE_PATH)
        assert "## 2. Crash Survival Waterfall" in content

    def test_guardrail_status_template(self):
        content = _read(TEMPLATE_PATH)
        assert "## 3. Guardrail Status Board" in content

    def test_goal_progress_template(self):
        content = _read(TEMPLATE_PATH)
        assert "## 4. Goal Progress" in content

    def test_all_templates_have_triggers(self):
        content = _read(TEMPLATE_PATH)
        # Each template section must specify when it triggers
        sections = content.split("\n## ")[1:]  # skip header
        for section in sections:
            assert "Triggers:" in section, (
                f"Section missing Triggers: {section[:50]}..."
            )

    def test_all_templates_have_data_sources(self):
        content = _read(TEMPLATE_PATH)
        sections = content.split("\n## ")[1:]
        for section in sections:
            assert "Data sources:" in section, (
                f"Section missing Data sources: {section[:50]}..."
            )


class TestNoReactCode:
    """S132b: TimeCell = intelligence layer. No JSX/React code in templates."""

    def test_no_jsx_tags(self):
        content = _read(TEMPLATE_PATH)
        assert "<div" not in content
        assert "<span" not in content
        assert "className=" not in content
        assert "useState" not in content
        assert "import React" not in content

    def test_no_tailwind_classes(self):
        content = _read(TEMPLATE_PATH)
        # Mentioning Tailwind as available is fine; using classes is not
        assert "flex-" not in content
        assert "bg-" not in content
        assert "text-sm" not in content


class TestTimecellMdIntegration:
    def test_timecell_references_visual_templates(self):
        content = _read(TIMECELL_PATH)
        assert "visual-templates.md" in content

    def test_timecell_has_visual_output_section(self):
        content = _read(TIMECELL_PATH)
        assert "## Visual Output" in content

    def test_timecell_text_vs_artifact_guidance(self):
        content = _read(TIMECELL_PATH)
        assert "text" in content.lower() and "artifact" in content.lower()
