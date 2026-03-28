"""
Verify Dispatch / mobile output rules are present in plugin files.
"""

import os

PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..", "timecell-core")


def _read(rel_path: str) -> str:
    with open(os.path.join(PLUGIN_ROOT, rel_path)) as f:
        return f.read()


# --- Dispatch guide exists and has required content ---


class TestDispatchGuide:
    def test_dispatch_guide_exists(self):
        path = os.path.join(PLUGIN_ROOT, "references", "dispatch-guide.md")
        assert os.path.isfile(path), "dispatch-guide.md must exist in references/"

    def test_dispatch_guide_mentions_desktop_requirement(self):
        content = _read("references/dispatch-guide.md")
        assert "desktop must be" in content.lower() or "desktop" in content.lower()

    def test_dispatch_guide_mentions_no_react(self):
        content = _read("references/dispatch-guide.md")
        assert "React" in content or "artifact" in content.lower()

    def test_dispatch_guide_has_example_prompts(self):
        content = _read("references/dispatch-guide.md")
        assert "How am I doing?" in content

    def test_dispatch_guide_mentions_limitations(self):
        content = _read("references/dispatch-guide.md")
        assert "## Limitations" in content


# --- Mobile output rules in formatting.md ---


class TestMobileFormatting:
    def test_formatting_has_mobile_section(self):
        content = _read("references/formatting.md")
        assert "## Mobile / Dispatch Output" in content

    def test_formatting_max_3_columns(self):
        content = _read("references/formatting.md")
        assert "max 3 columns" in content

    def test_formatting_no_react_on_mobile(self):
        content = _read("references/formatting.md")
        assert "No React artifacts" in content

    def test_formatting_concise_length(self):
        content = _read("references/formatting.md")
        assert "50-150 words" in content

    def test_formatting_dispatch_detection_hint(self):
        content = _read("references/formatting.md")
        assert "Detection:" in content or "detection" in content.lower()


# --- timecell.md references mobile formatting ---


class TestTimecellMdMobileRef:
    def test_timecell_mentions_dispatch(self):
        content = _read("references/timecell.md")
        assert "Dispatch" in content

    def test_timecell_points_to_formatting(self):
        content = _read("references/timecell.md")
        assert "Mobile / Dispatch Output" in content or "mobile" in content.lower()


# --- session-start-reminder.md mentions Dispatch ---


class TestSessionStartDispatch:
    def test_session_start_mentions_dispatch(self):
        content = _read("references/session-start-reminder.md")
        assert "Dispatch" in content

    def test_session_start_mentions_mobile_formatting(self):
        content = _read("references/session-start-reminder.md")
        assert "mobile" in content.lower()
