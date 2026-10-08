"""Install or uninstall personal Codex, Claude Code, OpenCode, and Grok Build agent setup files."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile


def opencode_agents_match(installed, desired):
    """Accept configured agent fields while preserving unrelated personal settings."""
    try:
        config = json.loads(installed)
        required = json.loads(desired)["agents"]
    except (ValueError, UnicodeDecodeError):
        return False
    if not isinstance(config, dict) or not isinstance(config.get("agents"), dict):
        return False
    agents = config["agents"]
    return all(
        isinstance(agents.get(name), dict)
        and all(agents[name].get(key) == value for key, value in settings.items())
        for name, settings in required.items()
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-home", type=Path, default=Path.home())
    parser.add_argument("--dry-run", action="store_true")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--update", action="store_true", help="Back up and replace recognized earlier setup files")
    action.add_argument("--uninstall", action="store_true", help="Remove recognized setup files and preserve customized files")
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    home = args.target_home.expanduser().resolve()
    previous = json.loads((source / "previous-install-hashes.json").read_text())
    files = [
        ("codex/fast.toml", ".codex/agents/fast.toml"),
        ("codex/worker.toml", ".codex/agents/worker.toml"),
        ("codex/reviewer.toml", ".codex/agents/reviewer.toml"),
        ("codex/explorer.toml", ".codex/agents/explorer.toml"),
        ("codex/default.toml", ".codex/agents/default.toml"),
        ("delegation.md", ".codex/AGENTS.md"),
        ("claude/fast.md", ".claude/agents/fast.md"),
        ("claude/worker.md", ".claude/agents/worker.md"),
        ("claude/reviewer.md", ".claude/agents/reviewer.md"),
        ("delegation.md", ".claude/rules/delegation.md"),
        ("opencode/fast.md", ".config/opencode/agents/fast.md"),
        ("opencode/worker.md", ".config/opencode/agents/worker.md"),
        ("opencode/reviewer.md", ".config/opencode/agents/reviewer.md"),
        ("opencode/opencode.jsonc", ".config/opencode/opencode.jsonc"),
        ("delegation.md", ".config/opencode/AGENTS.md"),
        ("grok/fast.md", ".grok/agents/fast.md"),
        ("grok/worker.md", ".grok/agents/worker.md"),
        ("grok/reviewer.md", ".grok/agents/reviewer.md"),
        ("delegation.md", ".grok/rules/delegation.md"),
    ]

    if args.uninstall:
        preserved = False
        for relative_source, relative_target in files:
            target = home / relative_target
            if target.is_symlink() or (target.exists() and not target.is_file()):
                print(f"Preserved non-regular file: {target}")
                preserved = True
                continue
            if not target.exists():
                print(f"Not installed: {target}")
                continue
            installed = target.read_bytes()
            current = (source / relative_source).read_bytes()
            digest = hashlib.sha256(installed).hexdigest()
            # Empty personal files can predate this setup; leave them in place.
            recognized = installed and (installed == current or digest in previous.get(relative_target, []))
            if not recognized:
                print(f"Preserved customized or unrecognized file: {target}")
                preserved = True
                continue
            if args.dry_run:
                print(f"Would remove: {target}")
            else:
                target.unlink()
                print(f"Removed: {target}")
        if preserved:
            parser.exit(1, "Some files were preserved. Review the reported paths to finish removal manually.\n")
        return

    # Preflight every file so a conflict preserves the entire installed setup.
    changes = []
    for relative_source, relative_target in files:
        contents = (source / relative_source).read_bytes()
        target = home / relative_target
        if target.is_symlink() or (target.exists() and not target.is_file()):
            parser.exit(1, f"Refusing to replace non-regular file: {target}\n")
        old = target.read_bytes() if target.exists() else None
        if old is not None and old != contents:
            if relative_source == "opencode/opencode.jsonc" and opencode_agents_match(old, contents):
                # Preserve the complete personal config, including its formatting.
                changes.append((target, old, old))
                continue
            digest = hashlib.sha256(old).hexdigest()
            if digest not in previous.get(relative_target, []):
                parser.exit(1, f"Unrecognized existing instructions or agent; preserved unchanged: {target}\n")
            if not args.update:
                parser.exit(1, f"Recognized earlier setup at {target}. Rerun with --update to back up and replace it.\n")
        changes.append((target, contents, old))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    for target, contents, old in changes:
        action = "Already installed" if old == contents else "Update" if old is not None else "Install"
        if args.dry_run or old == contents:
            print(f"{action}: {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if old is not None:
            backup = target.with_name(target.name + ".bak-" + stamp)
            with backup.open("xb") as output:
                output.write(old)
            print(f"Backup: {backup}")
        if old is None:
            with target.open("xb") as output:
                output.write(contents)
        else:
            # Replace a complete file, so an interrupted write cannot truncate it.
            temporary_path = None
            try:
                with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
                    temporary_path = Path(output.name)
                    output.write(contents)
                shutil.copymode(target, temporary_path)
                temporary_path.replace(target)
            finally:
                if temporary_path is not None and temporary_path.exists():
                    temporary_path.unlink()
        print(f"{action}: {target}")


if __name__ == "__main__":
    main()
