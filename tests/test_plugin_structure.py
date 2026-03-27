"""Structural validation for all TimeCell plugins.

Checks manifests, frontmatter, cross-references, paths, and script quality.
Run on every commit — these catch broken file references and format violations.
"""
import os
import json
import re
import subprocess
import pytest

REPO_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
PLUGINS = ["timecell-core"]


@pytest.mark.parametrize("plugin", PLUGINS)
class TestPluginManifest:
    def test_plugin_json_exists(self, plugin):
        path = os.path.join(REPO_ROOT, plugin, ".claude-plugin", "plugin.json")
        assert os.path.exists(path), f"{plugin} missing .claude-plugin/plugin.json"

    def test_plugin_json_required_fields(self, plugin):
        path = os.path.join(REPO_ROOT, plugin, ".claude-plugin", "plugin.json")
        with open(path) as f:
            data = json.load(f)
        for field in ["name", "version", "description", "author"]:
            assert field in data, f"{plugin}: missing '{field}' in plugin.json"
        assert "name" in data["author"], f"{plugin}: missing 'author.name'"

    def test_plugin_json_semver(self, plugin):
        path = os.path.join(REPO_ROOT, plugin, ".claude-plugin", "plugin.json")
        with open(path) as f:
            data = json.load(f)
        assert re.match(
            r"^\d+\.\d+\.\d+", data["version"]
        ), f"{plugin}: version '{data['version']}' is not semver"


@pytest.mark.parametrize("plugin", PLUGINS)
class TestCommandFrontmatter:
    def test_all_commands_have_frontmatter(self, plugin):
        cmd_dir = os.path.join(REPO_ROOT, plugin, "commands")
        if not os.path.exists(cmd_dir):
            pytest.skip("No commands directory")
        for fname in os.listdir(cmd_dir):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(cmd_dir, fname)
            with open(path) as f:
                content = f.read()
            assert content.startswith("---"), f"{fname}: missing YAML frontmatter (must start with ---)"
            assert "description:" in content, f"{fname}: missing 'description' in frontmatter"
            assert "argument-hint:" in content, f"{fname}: missing 'argument-hint' in frontmatter"


@pytest.mark.parametrize("plugin", PLUGINS)
class TestSkillFrontmatter:
    def test_all_skills_have_frontmatter(self, plugin):
        skills_dir = os.path.join(REPO_ROOT, plugin, "skills")
        if not os.path.exists(skills_dir):
            pytest.skip("No skills directory")
        for skill_name in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, skill_name, "SKILL.md")
            if not os.path.exists(skill_path):
                continue
            with open(skill_path) as f:
                content = f.read()
            assert content.startswith("---"), f"{skill_name}/SKILL.md: missing YAML frontmatter"
            assert "name:" in content, f"{skill_name}/SKILL.md: missing 'name'"
            assert "description:" in content, f"{skill_name}/SKILL.md: missing 'description'"


@pytest.mark.parametrize("plugin", PLUGINS)
class TestNoHardcodedPaths:
    def test_no_absolute_paths(self, plugin):
        plugin_dir = os.path.join(REPO_ROOT, plugin)
        violations = []
        for root, dirs, files in os.walk(plugin_dir):
            for fname in files:
                if not fname.endswith((".md", ".py", ".json", ".sh")):
                    continue
                path = os.path.join(root, fname)
                with open(path) as f:
                    content = f.read()
                rel = os.path.relpath(path, REPO_ROOT)
                if "/Users/" in content:
                    violations.append(f"{rel}: contains /Users/")
                if "/home/" in content:
                    violations.append(f"{rel}: contains /home/")
        assert violations == [], f"Hardcoded paths found:\n" + "\n".join(violations)


@pytest.mark.parametrize("plugin", PLUGINS)
class TestHooksJson:
    def test_hooks_json_valid(self, plugin):
        path = os.path.join(REPO_ROOT, plugin, "hooks.json")
        if not os.path.exists(path):
            pytest.skip("No hooks.json")
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict), "hooks.json must be a JSON object"

    def test_hooks_reference_existing_scripts(self, plugin):
        path = os.path.join(REPO_ROOT, plugin, "hooks.json")
        if not os.path.exists(path):
            pytest.skip("No hooks.json")
        with open(path) as f:
            content = f.read()
        for m in re.finditer(r"python3\s+(scripts/\S+\.py)", content):
            script_path = os.path.join(REPO_ROOT, plugin, m.group(1))
            assert os.path.exists(script_path), f"hooks.json references missing script: {m.group(1)}"


@pytest.mark.parametrize("plugin", PLUGINS)
class TestPythonScripts:
    def test_scripts_compile(self, plugin):
        scripts_dir = os.path.join(REPO_ROOT, plugin, "scripts")
        if not os.path.exists(scripts_dir):
            pytest.skip("No scripts")
        for fname in os.listdir(scripts_dir):
            if not fname.endswith(".py"):
                continue
            path = os.path.join(scripts_dir, fname)
            result = subprocess.run(
                ["python3", "-m", "py_compile", path],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f"{fname} syntax error: {result.stderr}"

    def test_scripts_stdlib_only(self, plugin):
        scripts_dir = os.path.join(REPO_ROOT, plugin, "scripts")
        if not os.path.exists(scripts_dir):
            pytest.skip("No scripts")

        stdlib = {
            "sys", "os", "json", "re", "shutil", "time", "datetime",
            "pathlib", "tempfile", "urllib", "hashlib", "collections",
            "importlib", "subprocess", "io", "math", "typing",
        }

        for fname in os.listdir(scripts_dir):
            if not fname.endswith(".py"):
                continue
            path = os.path.join(scripts_dir, fname)
            with open(path) as f:
                for i, line in enumerate(f, 1):
                    m = re.match(r"^(?:from\s+(\S+)|import\s+(\S+))", line.strip())
                    if m:
                        mod = (m.group(1) or m.group(2)).split(".")[0]
                        assert mod in stdlib or mod.startswith("_"), (
                            f"{fname}:{i} imports non-stdlib: {mod}"
                        )


class TestMarketplace:
    def test_marketplace_json_exists(self):
        path = os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")
        assert os.path.exists(path), "Missing .claude-plugin/marketplace.json"

    def test_marketplace_lists_all_plugins(self):
        path = os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")
        with open(path) as f:
            data = json.load(f)
        assert "plugins" in data
        names = [p["name"] for p in data["plugins"]]
        assert "timecell" in names, "marketplace.json missing 'timecell' plugin"

    def test_marketplace_sources_exist(self):
        path = os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")
        with open(path) as f:
            data = json.load(f)
        for plugin in data["plugins"]:
            source = os.path.join(REPO_ROOT, plugin["source"])
            assert os.path.isdir(source), f"Plugin source dir missing: {plugin['source']}"


@pytest.mark.parametrize("plugin", PLUGINS)
class TestCrossReferences:
    def test_command_skill_refs_exist(self, plugin):
        """Commands that reference skills should reference existing skills."""
        cmd_dir = os.path.join(REPO_ROOT, plugin, "commands")
        if not os.path.exists(cmd_dir):
            pytest.skip("No commands")
        for fname in os.listdir(cmd_dir):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(cmd_dir, fname)
            with open(path) as f:
                content = f.read()
            for m in re.finditer(r'`(\w[\w-]+)`\s+skill', content):
                skill_name = m.group(1)
                skill_path = os.path.join(REPO_ROOT, plugin, "skills", skill_name, "SKILL.md")
                assert os.path.exists(skill_path), (
                    f"{fname} references skill '{skill_name}' but {skill_path} doesn't exist"
                )

    def test_reference_file_refs_exist(self, plugin):
        """Commands that reference files in references/ should reference existing files."""
        cmd_dir = os.path.join(REPO_ROOT, plugin, "commands")
        if not os.path.exists(cmd_dir):
            pytest.skip("No commands")
        for fname in os.listdir(cmd_dir):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(cmd_dir, fname)
            with open(path) as f:
                content = f.read()
            for m in re.finditer(r"references/([\w-]+\.md)", content):
                ref_path = os.path.join(REPO_ROOT, plugin, "references", m.group(1))
                assert os.path.exists(ref_path), (
                    f"{fname} references 'references/{m.group(1)}' but it doesn't exist"
                )
