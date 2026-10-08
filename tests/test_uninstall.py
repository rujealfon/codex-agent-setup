from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class UninstallTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="agent-uninstall-test-")
        self.addCleanup(self.directory.cleanup)
        self.home = Path(self.directory.name) / "home"
        installed = self.run_command()
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.installed_files = [path for path in self.home.rglob("*") if path.is_file()]
        self.assertEqual(len(self.installed_files), 16)

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
            ".grok/rules/delegation.md": "delegation.md",
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
