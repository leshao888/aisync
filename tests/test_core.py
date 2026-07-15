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
from aisync.errors import DangerError, RestoreError
from aisync.profile import load_profile


class CoreTests(unittest.TestCase):
    def test_codex_profile_loads(self):
        profile = load_profile("codex")
        self.assertEqual(profile.name, "codex")
        self.assertIn("sessions/**", profile.include)
        self.assertIn("auth.json", profile.deny)

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
