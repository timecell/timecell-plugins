"""
Regression test: all plugin commands must use tc: prefix.

Every command file across all plugin modules must:
1. Have a heading that starts with /tc: (the internal reference name)
2. Have YAML frontmatter with a description field

This prevents future commands from missing the prefix and causing
collisions with user's other plugins or global skills.
"""

import os
import re

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")

# All plugin modules that contain commands
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


class TestCommandPrefix:
    """Every command must use tc: prefix in its heading."""

    def test_all_commands_have_tc_prefix_in_heading(self):
        """The first H1 heading must contain /tc: to ensure proper namespacing."""
        missing = []
        for module, fname, path in _find_command_files():
            with open(path) as f:
                content = f.read()
            # Find the first H1 heading
            match = re.search(r"^# (.+)$", content, re.MULTILINE)
            if not match:
                missing.append(f"{module}/commands/{fname}: no H1 heading found")
            elif "/tc:" not in match.group(1):
                missing.append(
                    f"{module}/commands/{fname}: heading '{match.group(1)}' missing /tc: prefix"
                )
        assert not missing, "Commands missing tc: prefix:\n" + "\n".join(missing)

    def test_all_commands_have_frontmatter(self):
        """Every command must have YAML frontmatter with a description field."""
        missing = []
        for module, fname, path in _find_command_files():
            with open(path) as f:
                content = f.read()
            if not content.startswith("---"):
                missing.append(f"{module}/commands/{fname}: no YAML frontmatter")
            elif "description:" not in content.split("---")[1]:
                missing.append(f"{module}/commands/{fname}: frontmatter missing description")
        assert not missing, "Commands missing frontmatter:\n" + "\n".join(missing)

    def test_no_unprefixed_command_references_in_estate(self):
        """Estate commands must not reference old unprefixed command names."""
        old_names = ["/estate-check", "/custody-audit", "/create-key-package"]
        violations = []
        estate_dir = os.path.join(REPO_ROOT, "timecell-estate", "commands")
        if os.path.isdir(estate_dir):
            for fname in os.listdir(estate_dir):
                if fname.endswith(".md"):
                    with open(os.path.join(estate_dir, fname)) as f:
                        content = f.read()
                    for old_name in old_names:
                        # Match /estate-check but not /tc:estate-check
                        pattern = rf"(?<!/tc:){re.escape(old_name[1:])}"
                        if re.search(rf"/{pattern}", content):
                            violations.append(f"{fname}: still references '{old_name}'")
        assert not violations, "Old unprefixed references:\n" + "\n".join(violations)

    def test_command_count(self):
        """Verify expected number of commands across all modules."""
        files = _find_command_files()
        # Core: 5, Bitcoin: 1, Estate: 4, Indian MF: 1 = 11 total
        assert len(files) == 11, f"Expected 11 commands, found {len(files)}: {[f[1] for f in files]}"
