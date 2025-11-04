from pathlib import Path

from filedeletemanager.core import DeleteOptions
from filedeletemanager.rules import delete_if_over_size, move_to_trash

def make_file(path: Path, size: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"\0" * size)
    return path

# --------------------------
# delete_if_over_size
# --------------------------

def test_delete_if_over_size_by_mtime(tmp_path: Path):
    # Total = 600; max_total=300 -> hay que borrar hasta <= 300
    f1 = make_file(tmp_path / "old1.log", 100)  # más viejo si creamos primero
    f2 = make_file(tmp_path / "old2.log", 200)
    f3 = make_file(tmp_path / "new.log", 300)

    # sort por mtime (borra antiguos primero): se deberían borrar f1 y f2 (100+200)
    deleted = delete_if_over_size(tmp_path, max_total_bytes=300, options=DeleteOptions())
    assert deleted == 2
    assert not f1.exists()
    assert not f2.exists()
    assert f3.exists()

def test_delete_if_over_size_by_biggest_first(tmp_path: Path):
    f1 = make_file(tmp_path / "a.bin", 100)
    f2 = make_file(tmp_path / "b.bin", 400)
    f3 = make_file(tmp_path / "c.bin", 200)
    # total = 700; max = 300; con sort_key=size debería borrar primero b(400) -> ya queda 300
    deleted = delete_if_over_size(tmp_path, max_total_bytes=300, options=DeleteOptions(), sort_key="size")
    assert deleted == 1
    assert not f2.exists()
    assert f1.exists() and f3.exists()

def test_delete_if_over_size_respects_filters(tmp_path: Path):
    f1 = make_file(tmp_path / "a.log", 200)
    f2 = make_file(tmp_path / "b.tmp", 200)
    # Incluimos solo *.log, max_total=100 -> borrará a.log (200)
    opt = DeleteOptions(include_patterns=["*.log"])
    deleted = delete_if_over_size(tmp_path, max_total_bytes=100, options=opt)
    assert deleted == 1
    assert not f1.exists()
    assert f2.exists()

def test_delete_if_over_size_dry_run(tmp_path: Path):
    f1 = make_file(tmp_path / "a.bin", 500)
    deleted = delete_if_over_size(tmp_path, max_total_bytes=100, options=DeleteOptions(dry_run=True))
    assert deleted == 0
    assert f1.exists()

# --------------------------
# move_to_trash
# --------------------------

def test_move_to_trash_moves_files(tmp_path: Path):
    src = tmp_path / "src"
    trash = tmp_path / "trash"
    src.mkdir()
    f1 = make_file(src / "x.tmp", 10)
    f2 = make_file(src / "y.log", 10)

    moved = move_to_trash(src, trash, options=DeleteOptions())
    assert moved == 2
    assert not f1.exists() and not f2.exists()
    # en trash deben existir con el mismo nombre
    assert (trash / "x.tmp").exists()
    assert (trash / "y.log").exists()

def test_move_to_trash_respects_filters(tmp_path: Path):
    src = tmp_path / "src"
    trash = tmp_path / "trash"
    src.mkdir()
    f1 = make_file(src / "keep.log", 10)
    f2 = make_file(src / "del.tmp", 10)

    opt = DeleteOptions(include_patterns=["*.tmp"])
    moved = move_to_trash(src, trash, options=opt)
    assert moved == 1
    assert f1.exists() and not f2.exists()
    assert (trash / "del.tmp").exists()

def test_move_to_trash_dry_run(tmp_path: Path):
    src = tmp_path / "src"
    trash = tmp_path / "trash"
    src.mkdir()
    f = make_file(src / "a.bin", 1)

    moved = move_to_trash(src, trash, options=DeleteOptions(dry_run=True))
    assert moved == 0
    assert f.exists()
    assert not (trash / "a.bin").exists()
