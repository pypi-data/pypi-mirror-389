import subprocess
import sys


def test_cli_help():
    """Testing that the command `python -m tlsleuth --help` works"""
    result = subprocess.run([sys.executable, "-m", "tlsleuth", "--help"], capture_output=True)
    assert result.returncode == 0
    out = result.stdout or result.stderr
    assert b"usage" in out.lower() or b"--help" in out.lower()
