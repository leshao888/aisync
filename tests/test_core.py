from __future__ import annotations

import io
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from aisync.archive import safe_extract_tar_gz
from aisync.cli import main
from aisync.collector import discover_files
from aisync.errors import DangerError, ProfileError, RestoreError
from aisync.gitstore import commit_and_push
from aisync.platforms import default_config_dir
from aisync.processes import running_processes
from aisync.profile import list_profiles, load_profile, validate_profile


class CoreTests(unittest.TestCase):
    def test_codex_profile_loads(self):
        profile = load_profile("codex")
        self.assertEqual(profile.name, "codex")
        self.assertIn("sessions/**", profile.include)
        self.assertIn("auth.json", profile.deny)
        self.assertTrue(profile.supports_restore)
        self.assertEqual(profile.path.parent.name, "profiles")

    def test_claude_experimental_profile_loads_by_natural_name(self):
        profile = load_profile("claude")
        self.assertEqual(profile.name, "claude")
        self.assertEqual(profile.stability, "experimental")
        self.assertIn("projects/**", profile.include)
        self.assertIn(".credentials.json", profile.deny)
        self.assertFalse(profile.supports_restore)
        self.assertIn("claude", list_profiles())
        self.assertNotIn("claude.experimental", list_profiles())

    def test_discover_claude_allowlist_excludes_credentials_and_cache(self):
        profile = load_profile("claude")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "projects" / "example").mkdir(parents=True)
            (root / "projects" / "example" / "session.jsonl").write_text("{}\n", encoding="utf-8")
            (root / "history.jsonl").write_text("{}\n", encoding="utf-8")
            (root / ".credentials.json").write_text("secret\n", encoding="utf-8")
            (root / "cache").mkdir()
            (root / "cache" / "state.json").write_text("{}\n", encoding="utf-8")
            files = discover_files(profile, root)
        self.assertEqual(
            [item.rel for item in files],
            ["history.jsonl", "projects/example/session.jsonl"],
        )

    def test_claude_deny_file_inside_include_stops(self):
        profile = load_profile("claude")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "projects" / "example").mkdir(parents=True)
            (root / "projects" / "example" / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
            with self.assertRaises(DangerError):
                discover_files(profile, root)

    def test_discover_codex_allowlist(self):
        profile = load_profile("codex")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sessions").mkdir()
            (root / "sessions" / "one.jsonl").write_text("{}\n", encoding="utf-8")
            (root / "auth.json").write_text("secret", encoding="utf-8")
            (root / "plugins").mkdir()
            (root / "plugins" / "cache.txt").write_text("cache", encoding="utf-8")
            files = discover_files(profile, root)
        self.assertEqual([item.rel for item in files], ["sessions/one.jsonl"])

    def test_deny_file_inside_include_stops(self):
        profile = load_profile("codex")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills").mkdir()
            (root / "skills" / "my-token.txt").write_text("bad", encoding="utf-8")
            with self.assertRaises(DangerError):
                discover_files(profile, root)

    def test_sync_dry_run_does_not_create_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source"
            repo = tmp_path / "repo"
            (source / "sessions").mkdir(parents=True)
            (source / "sessions" / "one.jsonl").write_text("{}\n", encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--repo", str(repo), "sync", "codex", "--dry-run", "--source", str(source)])
            self.assertEqual(code, 0)
            self.assertFalse(repo.exists())
            self.assertIn("dry-run", out.getvalue())

    def test_claude_sync_dry_run_warns_experimental_without_creating_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source"
            repo = tmp_path / "repo"
            (source / "projects" / "example").mkdir(parents=True)
            (source / "projects" / "example" / "session.jsonl").write_text("{}\n", encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--repo", str(repo), "sync", "claude", "--dry-run", "--source", str(source)])
            self.assertEqual(code, 0)
            self.assertFalse(repo.exists())
            self.assertIn("WARN    experimental profile", out.getvalue())

    def test_claude_restore_is_blocked_before_repo_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            target = Path(tmp) / "target"
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--repo", str(repo), "restore", "claude", "--dry-run", "--target", str(target)])
            self.assertEqual(code, 1)
            self.assertFalse(repo.exists())
            self.assertFalse(target.exists())
            self.assertIn("Restore is disabled for profile: claude", out.getvalue())

    def test_recipient_add_list_remove_and_refuse_last_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            recipient_one = "age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"
            recipient_two = "age1lllllllllllllllllllllllllllllllllllllllllllllllllllllllllll"

            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--repo", str(repo), "init", "--no-git"]), 0)
                self.assertEqual(main(["--repo", str(repo), "recipient", "add", recipient_one]), 0)
                self.assertEqual(main(["--repo", str(repo), "recipient", "add", recipient_two]), 0)

            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(main(["--repo", str(repo), "recipient", "list"]), 0)
            self.assertIn(recipient_one, out.getvalue())
            self.assertIn(recipient_two, out.getvalue())

            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--repo", str(repo), "recipient", "remove", recipient_one]), 0)
            with redirect_stdout(io.StringIO()):
                code = main(["--repo", str(repo), "recipient", "remove", recipient_two])
            self.assertEqual(code, 2)

    def test_recipient_add_rejects_invalid_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            with redirect_stdout(io.StringIO()):
                code = main(["--repo", str(repo), "recipient", "add", "not-a-recipient"])
            self.assertEqual(code, 2)
            self.assertFalse(repo.exists())

    def test_profile_validation_rejects_absolute_pattern(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            raw = {
                "schema_version": 1,
                "name": "bad",
                "source": {"macos": "~/.bad"},
                "include": ["/absolute/path"],
                "deny": [],
            }
            with self.assertRaises(ProfileError):
                validate_profile(raw, path)

    def test_profile_validation_rejects_parent_escape_pattern(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            raw = {
                "schema_version": 1,
                "name": "bad",
                "source": {"macos": "~/.bad"},
                "include": ["../outside"],
                "deny": [],
            }
            with self.assertRaises(ProfileError):
                validate_profile(raw, path)

    def test_profile_validation_rejects_invalid_stability(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            raw = {
                "schema_version": 1,
                "name": "bad",
                "stability": "production",
                "source": {"macos": "~/.bad"},
                "include": ["sessions/**"],
                "deny": [],
            }
            with self.assertRaises(ProfileError):
                validate_profile(raw, path)

    def test_profile_validation_rejects_unknown_source_platform(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            raw = {
                "schema_version": 1,
                "name": "bad",
                "source": {"macos": "~/.bad", "ios": "~/.bad"},
                "include": ["sessions/**"],
                "deny": [],
            }
            with self.assertRaises(ProfileError):
                validate_profile(raw, path)

    def test_profile_validation_rejects_invalid_restore_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            raw = {
                "schema_version": 1,
                "name": "bad",
                "source": {"macos": "~/.bad"},
                "include": ["sessions/**"],
                "deny": [],
                "restore": {"default_mode": "delete"},
            }
            with self.assertRaises(ProfileError):
                validate_profile(raw, path)

    def test_profile_validation_rejects_non_map_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            raw = {
                "schema_version": 1,
                "name": "bad",
                "source": {"macos": "~/.bad"},
                "include": ["sessions/**"],
                "deny": [],
                "restore": "merge",
            }
            with self.assertRaises(ProfileError):
                validate_profile(raw, path)

    def test_profile_validation_rejects_non_list_process_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            raw = {
                "schema_version": 1,
                "name": "bad",
                "source": {"macos": "~/.bad"},
                "include": ["sessions/**"],
                "deny": [],
                "process_names": "Codex",
            }
            with self.assertRaises(ProfileError):
                validate_profile(raw, path)

    def test_profile_validation_rejects_non_boolean_capability(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            raw = {
                "schema_version": 1,
                "name": "bad",
                "source": {"macos": "~/.bad"},
                "include": ["sessions/**"],
                "deny": [],
                "capabilities": {"supports_restore": "yes"},
            }
            with self.assertRaises(ProfileError):
                validate_profile(raw, path)

    def test_profile_validation_rejects_merge_when_restore_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            raw = {
                "schema_version": 1,
                "name": "bad",
                "source": {"macos": "~/.bad"},
                "include": ["sessions/**"],
                "deny": [],
                "capabilities": {"supports_restore": False, "supports_merge": True},
            }
            with self.assertRaises(ProfileError):
                validate_profile(raw, path)

    def test_linux_default_config_uses_xdg_config_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            xdg = Path(tmp) / "xdg"
            with mock.patch("aisync.platforms.platform.system", return_value="Linux"), mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(xdg)},
                clear=False,
            ):
                self.assertEqual(default_config_dir(), xdg.resolve() / "aisync")

    def test_linux_process_detection_falls_back_to_proc(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = Path(tmp) / "proc"
            (proc / "100").mkdir(parents=True)
            (proc / "100" / "comm").write_text("codex\n", encoding="utf-8")
            (proc / "101").mkdir()
            (proc / "101" / "cmdline").write_bytes(b"/opt/bin/Claude Code\0--flag\0")
            with mock.patch("aisync.processes.platform.system", return_value="Linux"), mock.patch(
                "aisync.processes.shutil.which",
                return_value=None,
            ):
                self.assertEqual(running_processes(["codex", "Claude Code", "missing"], proc_root=proc), ["codex", "Claude Code"])

    def test_pull_requires_git_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            with redirect_stdout(io.StringIO()):
                code = main(["--repo", str(repo), "pull"])
            self.assertEqual(code, 1)

    def test_conflicts_reports_synced_repository(self):
        if not shutil.which("git"):
            self.skipTest("git is required for conflict tests")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            origin = tmp_path / "origin.git"
            repo = tmp_path / "repo"
            self._git(tmp_path, "init", "--bare", str(origin))
            self._init_git_repo(repo)
            self._git(repo, "remote", "add", "origin", str(origin))
            self._commit_file(repo, "README.md", "initial\n", "initial")
            self._git(repo, "push", "-u", "origin", "main")

            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--repo", str(repo), "conflicts"])
            self.assertEqual(code, 0)
            self.assertIn("state: synced", out.getvalue())

    def test_conflicts_reports_diverged_repository(self):
        if not shutil.which("git"):
            self.skipTest("git is required for conflict tests")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            origin = tmp_path / "origin.git"
            repo = tmp_path / "repo"
            other = tmp_path / "other"
            self._git(tmp_path, "init", "--bare", str(origin))
            self._init_git_repo(repo)
            self._git(repo, "remote", "add", "origin", str(origin))
            self._commit_file(repo, "README.md", "initial\n", "initial")
            self._git(repo, "push", "-u", "origin", "main")
            self._git(origin, "symbolic-ref", "HEAD", "refs/heads/main")

            self._git(tmp_path, "clone", str(origin), str(other))
            self._configure_git(other)
            self._commit_file(other, "remote.txt", "remote private text\n", "remote")
            self._git(other, "push", "origin", "main")
            self._commit_file(repo, "local.txt", "local private text\n", "local")

            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--repo", str(repo), "conflicts"])
            value = out.getvalue()
            self.assertEqual(code, 1)
            self.assertIn("state: diverged", value)
            self.assertNotIn("remote private text", value)
            self.assertNotIn("local private text", value)

    def test_commit_and_push_sets_upstream_on_first_push(self):
        if not shutil.which("git"):
            self.skipTest("git is required for push tests")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            origin = tmp_path / "origin.git"
            repo = tmp_path / "repo"
            self._git(tmp_path, "init", "--bare", str(origin))
            self._init_git_repo(repo)
            self._git(repo, "remote", "add", "origin", str(origin))
            for name in ["vault", "manifests", "profiles"]:
                (repo / name).mkdir()
            (repo / "vault" / "codex.age").write_text("encrypted\n", encoding="utf-8")
            (repo / "manifests" / "codex.json").write_text("{}\n", encoding="utf-8")
            (repo / "profiles" / "codex.yaml").write_text("name: codex\n", encoding="utf-8")
            (repo / "recipients.txt").write_text("age1fake\n", encoding="utf-8")
            (repo / ".gitignore").write_text("tmp/\n", encoding="utf-8")

            commit = commit_and_push(repo, "initial vault", push=True)
            upstream = self._git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").stdout.strip()
            self.assertIsNotNone(commit)
            self.assertEqual(upstream, "origin/main")

    def test_sync_stops_before_writing_when_vault_repo_diverged(self):
        if not shutil.which("git"):
            self.skipTest("git is required for conflict tests")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            origin = tmp_path / "origin.git"
            repo = tmp_path / "repo"
            other = tmp_path / "other"
            source = tmp_path / "source"
            (source / "sessions").mkdir(parents=True)
            (source / "sessions" / "one.jsonl").write_text("{}\n", encoding="utf-8")

            self._git(tmp_path, "init", "--bare", str(origin))
            self._init_git_repo(repo)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--repo", str(repo), "init", "--no-git"]), 0)
            self._git(repo, "remote", "add", "origin", str(origin))
            self._git(repo, "add", ".gitignore", "profiles", "recipients.txt")
            self._git(repo, "commit", "-m", "initial vault")
            self._git(repo, "push", "-u", "origin", "main")
            self._git(origin, "symbolic-ref", "HEAD", "refs/heads/main")

            self._git(tmp_path, "clone", str(origin), str(other))
            self._configure_git(other)
            self._commit_file(other, "remote.txt", "remote private text\n", "remote")
            self._git(other, "push", "origin", "main")
            self._commit_file(repo, "local.txt", "local private text\n", "local")

            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--repo", str(repo), "sync", "codex", "--source", str(source)])
            value = out.getvalue()
            self.assertEqual(code, 1)
            self.assertIn("Vault repository conflict detected: diverged", value)
            self.assertEqual(list((repo / "vault").glob("codex-*.age")), [])
            self.assertNotIn("remote private text", value)
            self.assertNotIn("local private text", value)

    def test_first_sync_push_allows_dirty_layout_without_upstream(self):
        if not shutil.which("git"):
            self.skipTest("git is required for first push tests")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_bin = tmp_path / "bin"
            fake_bin.mkdir()
            self._write_fake_tools(fake_bin)
            origin = tmp_path / "origin.git"
            repo = tmp_path / "repo"
            source = tmp_path / "source"
            (source / "sessions").mkdir(parents=True)
            (source / "sessions" / "one.jsonl").write_text("{}\n", encoding="utf-8")

            self._git(tmp_path, "init", "--bare", str(origin))
            env = {"PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}"}
            with mock.patch.dict(os.environ, env, clear=False), mock.patch("aisync.operations.running_processes", return_value=[]):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["--repo", str(repo), "init"]), 0)
                self._git(repo, "branch", "-M", "main")
                self._configure_git(repo)
                self._git(repo, "remote", "add", "origin", str(origin))
                (repo / "recipients.txt").write_text("age1fake\n", encoding="utf-8")
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["--repo", str(repo), "sync", "codex", "--source", str(source)]), 0)

            upstream = self._git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").stdout.strip()
            self.assertEqual(upstream, "origin/main")
            self.assertEqual(len(list((repo / "vault").glob("codex-*.age"))), 1)

    def test_doctor_reports_missing_identity_without_leaking_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            identity = Path(tmp) / "missing-identity.txt"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--repo", str(repo), "init", "--no-git"]), 0)
            (repo / "recipients.txt").write_text("age1fake\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"AISYNC_AGE_IDENTITY": str(identity)}, clear=False):
                out = io.StringIO()
                with redirect_stdout(out):
                    code = main(["--repo", str(repo), "doctor"])
            self.assertEqual(code, 1)
            self.assertIn("age identity missing", out.getvalue())
            self.assertNotIn("PRIVATE", out.getvalue())

    def test_secret_scan_failure_does_not_print_scanner_output_or_write_vault(self):
        if not shutil.which("git"):
            self.skipTest("git is required for scanner failure test")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_bin = tmp_path / "bin"
            fake_bin.mkdir()
            self._write_fake_tools(fake_bin)
            (fake_bin / "gitleaks").write_text(
                "#!/bin/sh\n"
                "printf 'leaked SUPER_SECRET_TOKEN_VALUE\\n'\n"
                "exit 1\n",
                encoding="utf-8",
            )
            (fake_bin / "gitleaks").chmod(0o755)
            source = tmp_path / "source"
            repo = tmp_path / "repo"
            (source / "sessions").mkdir(parents=True)
            (source / "sessions" / "one.jsonl").write_text("SUPER_SECRET_TOKEN_VALUE\n", encoding="utf-8")
            env = {"PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}"}
            with mock.patch.dict(os.environ, env, clear=False), mock.patch("aisync.operations.running_processes", return_value=[]):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["--repo", str(repo), "init"]), 0)
                self._configure_git(repo)
                (repo / "recipients.txt").write_text("age1fake\n", encoding="utf-8")
                out = io.StringIO()
                with redirect_stdout(out):
                    code = main(["--repo", str(repo), "sync", "codex", "--source", str(source), "--no-push"])
            value = out.getvalue()
            self.assertEqual(code, 2)
            self.assertIn("Scanner output is hidden", value)
            self.assertNotIn("SUPER_SECRET_TOKEN_VALUE", value)
            self.assertEqual(list((repo / "vault").glob("codex-*.age")), [])

    def test_history_reads_manifests_without_file_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            manifests = repo / "manifests"
            manifests.mkdir(parents=True)
            (manifests / "codex-20260715-120000.json").write_text(
                '{"profile":"codex","created_at":"2026-07-15T12:00:00Z","files":2,"bytes":10,"archive":"vault/codex.age"}\n',
                encoding="utf-8",
            )
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(main(["--repo", str(repo), "history", "codex"]), 0)
            value = out.getvalue()
            self.assertIn("profile=codex", value)
            self.assertIn("archive=vault/codex.age", value)
            self.assertNotIn("msg", value)

    def test_key_list_does_not_print_private_key_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            identity = Path(tmp) / "identity.txt"
            identity.write_text("# public key: age1fake\nFAKE-PRIVATE-KEY\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"AISYNC_AGE_IDENTITY": str(identity)}, clear=False):
                out = io.StringIO()
                with redirect_stdout(out):
                    self.assertEqual(main(["key", "list"]), 0)
            value = out.getvalue()
            self.assertIn("age1fake", value)
            self.assertNotIn("FAKE-PRIVATE-KEY", value)

    def test_safe_extract_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            archive = tmp_path / "bad.tar.gz"
            with tarfile.open(archive, "w:gz") as tar:
                payload = tmp_path / "payload.txt"
                payload.write_text("x", encoding="utf-8")
                tar.add(payload, arcname="../escape.txt")
            with self.assertRaises(RestoreError):
                safe_extract_tar_gz(archive, tmp_path / "out")

    def test_safe_extract_rejects_archive_symlink_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            archive = tmp_path / "bad-symlink.tar.gz"
            with tarfile.open(archive, "w:gz") as tar:
                link = tarfile.TarInfo("sessions/link")
                link.type = tarfile.SYMTYPE
                link.linkname = "../outside"
                tar.addfile(link)
            with self.assertRaises(RestoreError):
                safe_extract_tar_gz(archive, tmp_path / "out")

    def test_fake_tool_end_to_end_sync_and_restore(self):
        if not shutil.which("git"):
            self.skipTest("git is required for the end-to-end test")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_bin = tmp_path / "bin"
            fake_bin.mkdir()
            self._write_fake_tools(fake_bin)

            source = tmp_path / "source"
            repo = tmp_path / "repo"
            target = tmp_path / "target"
            identity = tmp_path / "identity.txt"
            (source / "sessions").mkdir(parents=True)
            (source / "sessions" / "one.jsonl").write_text('{"msg":"hello"}\n', encoding="utf-8")
            (source / "history.jsonl").write_text('{"item":"h"}\n', encoding="utf-8")
            identity.write_text("fake identity\n", encoding="utf-8")

            env = {
                "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
                "AISYNC_AGE_IDENTITY": str(identity),
            }
            with mock.patch.dict(os.environ, env, clear=False), mock.patch("aisync.operations.running_processes", return_value=[]):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["--repo", str(repo), "init"]), 0)
                subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
                subprocess.run(["git", "config", "user.name", "AIsync Test"], cwd=repo, check=True)
                (repo / "recipients.txt").write_text("age1fake\n", encoding="utf-8")
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["--repo", str(repo), "sync", "codex", "--source", str(source), "--no-push"]), 0)
                vaults = list((repo / "vault").glob("codex-*.age"))
                manifests = list((repo / "manifests").glob("codex-*.json"))
                self.assertEqual(len(vaults), 1)
                self.assertEqual(len(manifests), 1)
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["--repo", str(repo), "restore", "codex", "--target", str(target), "--no-pull"]), 0)

            self.assertEqual((target / "sessions" / "one.jsonl").read_text(encoding="utf-8"), '{"msg":"hello"}\n')
            self.assertEqual((target / "history.jsonl").read_text(encoding="utf-8"), '{"item":"h"}\n')
            self.assertTrue((repo / "backups" / "codex").exists())

    def _git(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def _configure_git(self, repo: Path) -> None:
        self._git(repo, "config", "user.email", "test@example.invalid")
        self._git(repo, "config", "user.name", "AIsync Test")

    def _init_git_repo(self, repo: Path) -> None:
        repo.mkdir(parents=True)
        self._git(repo, "init")
        self._git(repo, "branch", "-M", "main")
        self._configure_git(repo)

    def _commit_file(self, repo: Path, rel: str, content: str, message: str) -> None:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self._git(repo, "add", rel)
        self._git(repo, "commit", "-m", message)

    def _write_fake_tools(self, fake_bin: Path) -> None:
        age = fake_bin / "age"
        age.write_text(
            "#!/bin/sh\n"
            "out=''\n"
            "last=''\n"
            "while [ $# -gt 0 ]; do\n"
            "  case \"$1\" in\n"
            "    -o) shift; out=\"$1\" ;;\n"
            "    -r|-i) shift ;;\n"
            "    -d) ;;\n"
            "    *) last=\"$1\" ;;\n"
            "  esac\n"
            "  shift\n"
            "done\n"
            "cp \"$last\" \"$out\"\n",
            encoding="utf-8",
        )
        age.chmod(0o755)

        age_keygen = fake_bin / "age-keygen"
        age_keygen.write_text(
            "#!/bin/sh\n"
            "out=''\n"
            "while [ $# -gt 0 ]; do\n"
            "  if [ \"$1\" = '-o' ]; then shift; out=\"$1\"; fi\n"
            "  shift\n"
            "done\n"
            "printf '# public key: age1fake\\nFAKE-PRIVATE-KEY\\n' > \"$out\"\n",
            encoding="utf-8",
        )
        age_keygen.chmod(0o755)

        gitleaks = fake_bin / "gitleaks"
        gitleaks.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        gitleaks.chmod(0o755)


if __name__ == "__main__":
    unittest.main()
