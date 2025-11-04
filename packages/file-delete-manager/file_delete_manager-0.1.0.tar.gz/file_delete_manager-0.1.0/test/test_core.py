import os
import time
from pathlib import Path

import pytest

from filedeletemanager.core import (
    DeleteOptions,
    delete_by_age,
    delete_by_count,
)

# --------------------------
# Helpers
# --------------------------
def make_file(path: Path, size: int = 0, mtime_offset: int = 0) -> Path:
    """
    Crea un archivo con 'size' bytes y modifica su mtime restando mtime_offset segundos.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        if size > 0:
            f.write(b"\0" * size)
    if mtime_offset:
        now = time.time()
        os.utime(path, (now - mtime_offset, now - mtime_offset))
    return path


# --------------------------
# delete_by_age
# --------------------------

def test_delete_by_age_deletes_older(tmp_path: Path):
    # file1: 2 días de antigüedad -> debe borrarse si older_than = 1 día
    f1 = make_file(tmp_path / "old.log", size=10, mtime_offset=2 * 24 * 3600)
    # file2: 1 hora -> NO debe borrarse
    f2 = make_file(tmp_path / "new.log", size=10, mtime_offset=3600)

    deleted = delete_by_age(tmp_path, older_than="1d")
    assert deleted == 1
    assert not f1.exists()
    assert f2.exists()

def test_delete_by_age_respects_include_exclude(tmp_path: Path):
    f1 = make_file(tmp_path / "a.log", mtime_offset=40_000)
    f2 = make_file(tmp_path / "b.tmp", mtime_offset=40_000)
    f3 = make_file(tmp_path / "important_a.log", mtime_offset=40_000)

    opt = DeleteOptions(
        include_patterns=["*.log", "*.tmp"],  # incluir ambos
        exclude_patterns=["important_*"],     # excluir los importantes
    )
    deleted = delete_by_age(tmp_path, older_than="1s", options=opt)
    assert deleted == 2
    assert not f1.exists()
    assert not f2.exists()
    assert f3.exists()

def test_delete_by_age_dry_run(tmp_path: Path):
    f = make_file(tmp_path / "x.log", mtime_offset=10_000)
    opt = DeleteOptions(dry_run=True)
    deleted = delete_by_age(tmp_path, older_than="1s", options=opt)
    assert deleted == 0
    assert f.exists(), "En dry-run no debe eliminar"

def test_delete_by_age_delete_empty_dirs(tmp_path: Path):
    d = tmp_path / "sub"
    d.mkdir()
    f = make_file(d / "x.log", mtime_offset=10_000)
    opt = DeleteOptions(delete_empty_dirs=True)
    deleted = delete_by_age(tmp_path, older_than="1s", options=opt)
    assert deleted == 1
    # el archivo fue borrado y el directorio debería eliminarse también
    assert not d.exists()


# --------------------------
# delete_by_count
# --------------------------

def test_delete_by_count_keeps_last_by_mtime(tmp_path: Path):
    # Creamos 5 archivos con mtimes crecientes: f1 (viejo) ... f5 (nuevo)
    files = []
    for i in range(5):
        # mtime_offset mayor => más viejo
        files.append(make_file(tmp_path / f"f{i+1}.log", mtime_offset=(5 - i) * 1000))

    deleted = delete_by_count(tmp_path, keep_last=2)
    assert deleted == 3

    # Los 2 más recientes (menor offset) deben quedar: f4, f5
    survivors = {tmp_path / "f4.log", tmp_path / "f5.log"}
    for p in files:
        if p in survivors:
            assert p.exists()
        else:
            assert not p.exists()

def test_delete_by_count_with_sort_by_size(tmp_path: Path):
    # Tamaños: a=100, b=80, c=60, d=40 (sort reverse=True mantendría a y b)
    a = make_file(tmp_path / "a.bin", size=100)
    b = make_file(tmp_path / "b.bin", size=80)
    c = make_file(tmp_path / "c.bin", size=60)
    d = make_file(tmp_path / "d.bin", size=40)

    deleted = delete_by_count(tmp_path, keep_last=2, sort_key="size")
    assert deleted == 2
    assert a.exists()
    assert b.exists()
    assert not c.exists()
    assert not d.exists()

def test_delete_by_count_respects_filters(tmp_path: Path):
    a = make_file(tmp_path / "a.log", size=10)
    b = make_file(tmp_path / "b.log", size=10)
    c = make_file(tmp_path / "c.tmp", size=10)

    opt = DeleteOptions(include_patterns=["*.log"])
    deleted = delete_by_count(tmp_path, keep_last=1, options=opt)
    # entre a.log y b.log se mantiene 1, c.tmp no participa
    assert deleted == 1
    # Debe quedar el más nuevo (creado el último): b.log
    assert not a.exists()
    assert b.exists()
    assert c.exists()

def test_delete_by_count_dry_run(tmp_path: Path):
    a = make_file(tmp_path / "a.log")
    b = make_file(tmp_path / "b.log")
    opt = DeleteOptions(dry_run=True)
    deleted = delete_by_count(tmp_path, keep_last=1, options=opt)
    assert deleted == 0
    assert a.exists() and b.exists()
