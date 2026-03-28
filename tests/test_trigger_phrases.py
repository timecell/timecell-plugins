"""
Structural test: all commands must have trigger phrases and "When NOT to use" sections.

Every command across all plugin modules must:
1. Have trigger phrases in its YAML frontmatter description
2. Have a "## When NOT to use" section in the body

The financial-reasoning skill must also have both.
"""

import os
import re

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")

PLUGIN_MODULES = [
    "timecell-core",
    "timecell-bitcoin",
    "timecell-estate",
    "timecell-indian-mf",
]


def _find_command_files():
    """Find all command .md files across all plugin modules."""
    files = []
    for module in PLUGIN_MODULES:
        cmd_dir = os.path.join(REPO_ROOT, module, "commands")
        if os.path.isdir(cmd_dir):
            for fname in sorted(os.listdir(cmd_dir)):
                if fname.endswith(".md"):
                    files.append((module, fname, os.path.join(cmd_dir, fname)))
    return files


class TestTriggerPhrases:
    """Every command must have trigger phrases in its frontmatter description."""

    def test_all_commands_have_trigger_phrases(self):
        """Frontmatter description must contain 'Triggers:' with quoted phrases."""
        missing = []
        for module, fname, path in _find_command_files():
            with open(path) as f:
                content = f.read()
            # Extract frontmatter
            if content.startswith("---"):
                frontmatter = content.split("---")[1]
                if "Triggers:" not in frontmatter:
                    missing.append(f"{module}/commands/{fname}")
            else:
                missing.append(f"{module}/commands/{fname} (no frontmatter)")
        assert not missing, (
            "Commands missing trigger phrases in description:\n"
            + "\n".join(missing)
        )

    def test_trigger_phrases_have_quoted_examples(self):
        """Trigger phrases must include at least 3 quoted examples."""
        insufficient = []
        for module, fname, path in _find_command_files():
            with open(path) as f:
                content = f.read()
            if content.startswith("---"):
                frontmatter = content.split("---")[1]
                # Count quoted phrases (double-quoted strings)
                quotes = re.findall(r'"[^"]+?"', frontmatter)
                if len(quotes) < 3:
                    insufficient.append(
                        f"{module}/commands/{fname}: only {len(quotes)} trigger phrases (need >= 3)"
                    )
        assert not insufficient, (
            "Commands with too few trigger phrases:\n"
            + "\n".join(insufficient)
        )


class TestWhenNotToUse:
    """Every command must have a 'When NOT to use' section."""

    def test_all_commands_have_when_not_to_use(self):
        """Must contain '## When NOT to use' heading."""
        missing = []
        for module, fname, path in _find_command_files():
            with open(path) as f:
                content = f.read()
            if "## When NOT to use" not in content:
                missing.append(f"{module}/commands/{fname}")
        assert not missing, (
            "Commands missing '## When NOT to use' section:\n"
            + "\n".join(missing)
        )

    def test_when_not_to_use_has_items(self):
        """'When NOT to use' section must have at least 2 bullet points."""
        insufficient = []
        for module, fname, path in _find_command_files():
            with open(path) as f:
                content = f.read()
            match = re.search(
                r"## When NOT to use\n((?:- .+\n)+)", content
            )
            if match:
                bullets = [
                    line
                    for line in match.group(1).strip().split("\n")
                    if line.startswith("- ")
                ]
                if len(bullets) < 2:
                    insufficient.append(
                        f"{module}/commands/{fname}: only {len(bullets)} items (need >= 2)"
                    )
            else:
                insufficient.append(
                    f"{module}/commands/{fname}: section exists but no bullet items found"
                )
        assert not insufficient, (
            "Commands with insufficient 'When NOT to use' items:\n"
            + "\n".join(insufficient)
        )

    def test_financial_reasoning_skill_has_when_not_to_use(self):
        """Financial reasoning SKILL.md must have 'When NOT to use' section."""
        path = os.path.join(
            REPO_ROOT,
            "timecell-core",
            "skills",
            "financial-reasoning",
            "SKILL.md",
        )
        with open(path) as f:
            content = f.read()
        assert "## When NOT to use" in content, (
            "financial-reasoning SKILL.md missing '## When NOT to use' section"
        )

    def test_financial_reasoning_skill_has_triggers(self):
        """Financial reasoning SKILL.md must have trigger phrases in description."""
        path = os.path.join(
            REPO_ROOT,
            "timecell-core",
            "skills",
            "financial-reasoning",
            "SKILL.md",
        )
        with open(path) as f:
            content = f.read()
        if content.startswith("---"):
            frontmatter = content.split("---")[1]
            assert "Triggers:" in frontmatter or "Triggers on" in frontmatter, (
                "financial-reasoning SKILL.md missing trigger phrases in description"
            )
