import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class LinuxInstallerFailureTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix" and shutil.which("bash"), "requires a POSIX shell")
    def _run_installer(self, home: Path, install_dir: Path, fake_bin: Path) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["OCI_PLATFORM_HOME"] = str(install_dir)
        env["REAL_PYTHON"] = sys.executable
        env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
        script = Path(__file__).resolve().parents[1] / "install.sh"
        return subprocess.run(
            [shutil.which("bash"), str(script)],
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )

    def _fake_python(self, fake_bin: Path) -> None:
        python = fake_bin / "python3.12"
        python.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "-c" ]; then case "$2" in *sys.version_info*) printf "3.12\\n"; exit 0;; esac; fi\n'
            'exec "$REAL_PYTHON" "$@"\n',
            encoding="utf-8",
        )
        python.chmod(0o755)

    def test_failed_clone_removes_only_the_partial_install_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            fake_bin = root / "bin"
            install_dir = root / "new-install"
            home.mkdir()
            fake_bin.mkdir()
            self._fake_python(fake_bin)
            fake_git = fake_bin / "git"
            fake_git.write_text(
                "#!/bin/sh\n"
                'if [ "$1" = "clone" ]; then\n'
                '  for arg in "$@"; do destination="$arg"; done\n'
                '  printf "partial clone" > "$destination/partial.txt"\n'
                "  exit 42\n"
                "fi\n"
                "exit 0\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)

            result = self._run_installer(home, install_dir, fake_bin)

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(install_dir.exists(), result.stdout + result.stderr)
            self.assertIn("removed incomplete installation directory", result.stderr)

    def test_venv_failure_removes_new_install_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            fake_bin = root / "bin"
            install_dir = root / "new-install"
            home.mkdir()
            fake_bin.mkdir()

            fake_python = fake_bin / "python3.12"
            fake_python.write_text(
                "#!/bin/sh\n"
                'if [ "$1" = "-c" ]; then case "$2" in *sys.version_info*) printf 3.12; exit 0;; esac; fi\n'
                'if [ "$1" = "-m" ] && [ "$2" = "venv" ]; then exit 43; fi\n'
                'exec "$REAL_PYTHON" "$@"\n',
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            fake_git = fake_bin / "git"
            fake_git.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_git.chmod(0o755)

            result = self._run_installer(home, install_dir, fake_bin)

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(install_dir.exists(), result.stdout + result.stderr)
            self.assertIn("removed incomplete installation directory", result.stderr)

    def test_existing_install_directory_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            fake_bin = root / "bin"
            install_dir = root / "existing-install"
            home.mkdir()
            fake_bin.mkdir()
            install_dir.mkdir()
            sentinel = install_dir / "keep-me.txt"
            sentinel.write_text("operator data", encoding="utf-8")
            self._fake_python(fake_bin)
            fake_git = fake_bin / "git"
            fake_git.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            fake_git.chmod(0o755)

            result = self._run_installer(home, install_dir, fake_bin)

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "operator data")


if __name__ == "__main__":
    unittest.main()
