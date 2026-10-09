from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICIES = {
    ".codex/AGENTS.md": "codex/AGENTS.md",
    ".claude/rules/delegation.md": "claude/rules/delegation.md",
    ".config/opencode/AGENTS.md": "opencode/AGENTS.md",
    ".grok/rules/delegation.md": "grok/rules/delegation.md",
}
LEGACY_POLICY = (ROOT / "tests/fixtures/shared-delegation.md").read_bytes()


class UninstallTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="agent-uninstall-test-")
        self.addCleanup(self.directory.cleanup)
        self.home = Path(self.directory.name).resolve() / "home"
        installed = self.run_command()
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.installed_files = [path for path in self.home.rglob("*") if path.is_file()]
        self.assertEqual(len(self.installed_files), 19)

    def run_command(self, *arguments):
        return subprocess.run(
            [sys.executable, str(ROOT / "install-agents.py"), "--target-home", str(self.home), *arguments],
            capture_output=True,
            text=True,
        )

    def test_dry_run_preserves_every_file_and_real_uninstall_is_idempotent(self):
        preferences = self.home / ".claude/CLAUDE.md"
        preferences.write_text("My personal instructions\n")
        backup = self.home / ".codex/AGENTS.md.bak-example"
        backup.write_text("Earlier instructions\n")
        before = {path: path.read_bytes() for path in self.home.rglob("*") if path.is_file()}

        preview = self.run_command("--uninstall", "--dry-run")
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual({path: path.read_bytes() for path in before}, before)

        removed = self.run_command("--uninstall")
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertTrue(all(not path.exists() for path in self.installed_files))
        self.assertEqual(preferences.read_text(), "My personal instructions\n")
        self.assertEqual(backup.read_text(), "Earlier instructions\n")
        self.assertTrue((self.home / ".claude/agents").is_dir())

        repeated = self.run_command("--uninstall")
        self.assertEqual(repeated.returncode, 0, repeated.stderr)

    def test_grok_native_agents_and_policy_are_installed_exactly(self):
        expected = {
            ".grok/agents/fast.md": "grok/fast.md",
            ".grok/agents/worker.md": "grok/worker.md",
            ".grok/agents/reviewer.md": "grok/reviewer.md",
            ".grok/rules/delegation.md": "grok/rules/delegation.md",
        }
        installed = {
            str(path.relative_to(self.home))
            for path in (self.home / ".grok").rglob("*")
            if path.is_file()
        }
        self.assertEqual(installed, set(expected))
        for target, source in expected.items():
            with self.subTest(target=target):
                self.assertEqual((self.home / target).read_bytes(), (ROOT / source).read_bytes())

    def test_provider_policies_are_installed_exactly(self):
        for target, source in POLICIES.items():
            with self.subTest(target=target):
                self.assertEqual((self.home / target).read_bytes(), (ROOT / source).read_bytes())
        self.assertEqual(len({(self.home / target).read_bytes() for target in POLICIES}), 4)

    def install_legacy_policies(self):
        for target in POLICIES:
            (self.home / target).write_bytes(LEGACY_POLICY)

    def test_shared_legacy_policies_require_update_without_mutation(self):
        self.install_legacy_policies()
        before = {path: path.read_bytes() for path in self.installed_files}

        result = self.run_command()
        self.assertEqual(result.returncode, 1)
        self.assertIn("--update", result.stderr)
        self.assertEqual({path: path.read_bytes() for path in self.home.rglob("*") if path.is_file()}, before)

    def test_shared_legacy_policy_update_dry_run_preserves_every_file(self):
        self.install_legacy_policies()
        before = {path: path.read_bytes() for path in self.installed_files}
        entries = set(self.home.rglob("*"))

        result = self.run_command("--update", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({path: path.read_bytes() for path in self.installed_files}, before)
        self.assertEqual(set(self.home.rglob("*")), entries)
        for target in POLICIES:
            self.assertIn(f"Update: {self.home / target}", result.stdout)

    def test_shared_legacy_policies_upgrade_with_exact_backups(self):
        self.install_legacy_policies()
        result = self.run_command("--update")
        self.assertEqual(result.returncode, 0, result.stderr)
        backups = []
        for target, source in POLICIES.items():
            policy = self.home / target
            with self.subTest(target=target):
                self.assertEqual(policy.read_bytes(), (ROOT / source).read_bytes())
                matches = list(policy.parent.glob(policy.name + ".bak-*"))
                self.assertEqual(len(matches), 1)
                self.assertEqual(matches[0].read_bytes(), LEGACY_POLICY)
                backups.extend(matches)
        self.assertEqual(set(self.home.rglob("*.bak-*")), set(backups))

        removed = self.run_command("--uninstall")
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertTrue(all(not path.exists() for path in self.installed_files))
        self.assertTrue(all(path.read_bytes() == LEGACY_POLICY for path in backups))

    def test_customized_legacy_policy_blocks_all_updates_and_survives_uninstall(self):
        for target in POLICIES:
            with self.subTest(target=target):
                installed = self.run_command()
                self.assertEqual(installed.returncode, 0, installed.stderr)
                self.install_legacy_policies()
                custom = self.home / target
                custom.write_bytes(LEGACY_POLICY + b"\nMy personal delegation rule\n")
                before = {path: path.read_bytes() for path in self.installed_files}

                result = self.run_command("--update")
                self.assertEqual(result.returncode, 1)
                self.assertIn(str(custom), result.stderr)
                self.assertEqual({path: path.read_bytes() for path in self.home.rglob("*") if path.is_file()}, before)

                removed = self.run_command("--uninstall")
                self.assertEqual(removed.returncode, 1)
                self.assertEqual(custom.read_bytes(), before[custom])
                self.assertTrue(all(not path.exists() for path in self.installed_files if path != custom))
                custom.unlink()

    def test_uninstall_recognizes_shared_legacy_policies(self):
        self.install_legacy_policies()
        result = self.run_command("--uninstall")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(all(not path.exists() for path in self.installed_files))

    def test_update_replaces_previous_opencode_agents_and_backs_them_up(self):
        earlier = {}
        for name, current, previous in (
            ("fast", "#high", "#xhigh"),
            ("reviewer", "glm-5.3-flash#max", "glm-5.3#max"),
        ):
            agent = self.home / f".config/opencode/agents/{name}.md"
            old_description = {
                "fast": "Handles focused exploration and straightforward independent tasks.",
                "reviewer": "Reviews complex logic, bugs, and security risks.",
            }[name]
            lines = agent.read_text().replace(current, previous).splitlines()
            earlier[agent] = ("\n".join(
                "description: " + old_description if line.startswith("description: ") else line
                for line in lines
            ) + "\n").encode()
            agent.write_bytes(earlier[agent])

        upgraded = self.run_command("--update")
        self.assertEqual(upgraded.returncode, 0, upgraded.stderr)
        for agent, contents in earlier.items():
            self.assertEqual(agent.read_bytes(), (ROOT / "opencode" / agent.name).read_bytes())
            backups = list(agent.parent.glob(agent.name + ".bak-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), contents)

    def test_update_replaces_installed_glm_53_reviewer(self):
        agent = self.home / ".config/opencode/agents/reviewer.md"
        previous = agent.read_bytes().replace(
            b"opencode-go/glm-5.3-flash#max",
            b"opencode-go/glm-5.3#max",
        )
        agent.write_bytes(previous)

        upgraded = self.run_command("--update")
        self.assertEqual(upgraded.returncode, 0, upgraded.stderr)
        self.assertEqual(agent.read_bytes(), (ROOT / "opencode" / "reviewer.md").read_bytes())
        backups = list(agent.parent.glob(agent.name + ".bak-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), previous)

    def test_customized_opencode_jsonc_blocks_update_and_is_preserved_on_uninstall(self):
        config = self.home / ".config/opencode/opencode.jsonc"
        config.write_text(config.read_text() + "\n// Personal settings\n")
        before = {path: path.read_bytes() for path in self.installed_files}
        upgraded = self.run_command("--update")
        self.assertEqual(upgraded.returncode, 1)
        self.assertEqual({path: path.read_bytes() for path in before}, before)

        removed = self.run_command("--uninstall")
        self.assertEqual(removed.returncode, 1)
        self.assertEqual(config.read_bytes(), before[config])
        self.assertTrue(all(not path.exists() for path in self.installed_files if path != config))

    def test_update_preserves_compatible_personal_opencode_config_exactly(self):
        config = self.home / ".config/opencode/opencode.jsonc"
        personal = json.loads(config.read_text())
        personal["mcp"] = {"personal": {"type": "local", "command": ["my-mcp"]}}
        personal["agents"]["explore"]["temperature"] = 0.2
        personal["agents"]["personal"] = {"model": "my-provider/my-model"}
        contents = (json.dumps(personal, indent=4) + "\n\n").encode()
        config.write_bytes(contents)

        for arguments in (("--update", "--dry-run"), ("--update",), ("--update",)):
            with self.subTest(arguments=arguments):
                upgraded = self.run_command(*arguments)
                self.assertEqual(upgraded.returncode, 0, upgraded.stderr)
                self.assertEqual(config.read_bytes(), contents)
                self.assertEqual(list(config.parent.glob(config.name + ".bak-*")), [])

        removed = self.run_command("--uninstall")
        self.assertEqual(removed.returncode, 1)
        self.assertEqual(config.read_bytes(), contents)
        self.assertTrue(all(not path.exists() for path in self.installed_files if path != config))

    def test_opencode_model_conflict_blocks_update_before_any_write(self):
        config = self.home / ".config/opencode/opencode.jsonc"
        personal = json.loads(config.read_text())
        personal["agents"]["explore"]["model"] = "personal-provider/personal-model"
        personal["mcp"] = {"personal": {"type": "local", "command": ["my-mcp"]}}
        config.write_text(json.dumps(personal))
        policy = self.home / ".codex/AGENTS.md"
        policy.write_bytes(b"")
        before = {path: path.read_bytes() for path in self.installed_files}

        upgraded = self.run_command("--update")
        self.assertEqual(upgraded.returncode, 1)
        self.assertNotIn("Traceback", upgraded.stderr)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertEqual(set(self.home.rglob("*.bak-*")), set())

    def test_invalid_opencode_config_blocks_update_without_mutation(self):
        config = self.home / ".config/opencode/opencode.jsonc"
        policy = self.home / ".codex/AGENTS.md"
        policy.write_bytes(b"")
        for contents in ("{invalid json", "[]", '{"agents": []}'):
            with self.subTest(contents=contents):
                config.write_text(contents)
                before = {path: path.read_bytes() for path in self.installed_files}
                upgraded = self.run_command("--update")
                self.assertEqual(upgraded.returncode, 1)
                self.assertNotIn("Traceback", upgraded.stderr)
                self.assertEqual({path: path.read_bytes() for path in before}, before)
                self.assertEqual(set(self.home.rglob("*.bak-*")), set())

    def test_uninstall_preserves_grok_config_credentials_and_customized_agent(self):
        config = self.home / ".grok/config.toml"
        config.write_text('model = "dummy-personal-model"\n')
        credentials = self.home / ".grok/credentials.json"
        credentials.write_text('{"apiKey": "dummy-test-key"}\n')
        agent = self.home / ".grok/agents/worker.md"
        agent.write_text("My custom Grok agent\n")
        before = {path: path.read_bytes() for path in (config, credentials, agent)}

        removed = self.run_command("--uninstall")
        self.assertEqual(removed.returncode, 1)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertIn(str(agent), removed.stdout)
        self.assertTrue(all(not path.exists() for path in self.installed_files if path != agent))

    def test_customized_agent_and_instructions_are_preserved(self):
        policy = self.home / ".config/opencode/AGENTS.md"
        policy.write_text(policy.read_text() + "\nMy additional rule\n")
        agent = self.home / ".claude/agents/worker.md"
        agent.write_text("My custom agent\n")
        before = {path: path.read_bytes() for path in (policy, agent)}

        removed = self.run_command("--uninstall")
        self.assertEqual(removed.returncode, 1)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertFalse((self.home / ".codex/agents/fast.toml").exists())
        self.assertIn("Preserved", removed.stdout)

    def test_symlinks_and_directories_are_preserved(self):
        target = self.home / ".claude/agents/fast.md"
        external = Path(self.directory.name) / "external.md"
        external.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(external)
        directory = self.home / ".claude/agents/reviewer.md"
        directory.unlink()
        directory.mkdir()

        removed = self.run_command("--uninstall")
        self.assertEqual(removed.returncode, 1)
        self.assertTrue(target.is_symlink())
        self.assertTrue(external.is_file())
        self.assertTrue(directory.is_dir())

    def test_recorded_earlier_agent_is_removed_but_empty_personal_file_is_preserved(self):
        earlier_agent = self.home / ".claude/agents/fast.md"
        earlier_agent.write_text(
            "---\n"
            "name: fast\n"
            "description: Handles focused exploration and straightforward independent tasks.\n"
            "model: sonnet\n"
            "effort: low\n"
            "---\n\n"
            "Complete the assigned task within its stated scope.\n"
            "Return concise findings and describe any verification.\n"
        )
        empty_policy = self.home / ".codex/AGENTS.md"
        empty_policy.write_bytes(b"")

        removed = self.run_command("--uninstall")
        self.assertEqual(removed.returncode, 1)
        self.assertFalse(earlier_agent.exists())
        self.assertTrue(empty_policy.is_file())
        self.assertEqual(empty_policy.read_bytes(), b"")

    def test_update_and_uninstall_cannot_be_combined(self):
        before = {path: path.read_bytes() for path in self.installed_files}
        result = self.run_command("--update", "--uninstall")
        self.assertEqual(result.returncode, 2)
        self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_uninstall_after_upgrade_preserves_the_upgrade_backup(self):
        policy = self.home / ".codex/AGENTS.md"
        policy.write_bytes(b"")
        upgraded = self.run_command("--update")
        self.assertEqual(upgraded.returncode, 0, upgraded.stderr)
        backups = list(policy.parent.glob("AGENTS.md.bak-*"))
        self.assertEqual(len(backups), 1)

        removed = self.run_command("--uninstall")
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertFalse(policy.exists())
        self.assertEqual(backups[0].read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
