import subprocess
import sys
from pathlib import Path

def run_cli(args, cwd=None):
    cmd = [sys.executable, "-m", "filedeletemanager.cli"] + args
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

def test_cli_age(tmp_path: Path):
    f = tmp_path / "a.log"
    f.write_text("x")
    # simula antigüedad con utime
    import os, time
    os.utime(f, (time.time() - 40000, time.time() - 40000))

    r = run_cli(["age", str(tmp_path), "--older-than", "1s"])
    assert r.returncode == 0
    assert not f.exists()

def test_cli_count(tmp_path: Path):
    a = tmp_path / "a.log"
    b = tmp_path / "b.log"
    a.write_text("a")
    b.write_text("b")

    import os, time
    # hace a.log más viejo que b.log
    now = time.time()
    os.utime(a, (now - 10, now - 10))  # a: 10s más viejo
    os.utime(b, (now, now))            # b: más reciente

    r = run_cli(["count", str(tmp_path), "--keep-last", "1", "--sort-key", "mtime"])
    assert r.returncode == 0
    assert not a.exists()     # se borra el viejo
    assert b.exists()         # queda el más nuevo

def test_cli_sizecap(tmp_path: Path):
    (tmp_path / "a.bin").write_bytes(b"\0" * 200)
    (tmp_path / "b.bin").write_bytes(b"\0" * 200)
    r = run_cli(["sizecap", str(tmp_path), "--max-total-bytes", "100"])
    assert r.returncode == 0
    # Debe haber borrado algo hasta quedar <= 100
    remaining = sum(p.stat().st_size for p in tmp_path.iterdir() if p.is_file())
    assert remaining <= 100

def test_cli_trash(tmp_path: Path):
    src = tmp_path / "src"
    trash = tmp_path / "trash"
    src.mkdir()
    (src / "x.tmp").write_text("x")
    r = run_cli(["trash", str(src), "--trash-dir", str(trash)])
    assert r.returncode == 0
    assert not (src / "x.tmp").exists()
    assert (trash / "x.tmp").exists()
