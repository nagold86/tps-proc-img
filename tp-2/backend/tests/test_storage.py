import numpy as np
import pytest
from app.errors import ScanNotFound
from app.repository import ScanRepository
from app.schemas import ScanOptions


@pytest.fixture
def repo(tmp_path):
    return ScanRepository(storage_dir=tmp_path)


def test_save_creates_all_three_files(repo, tmp_path):
    fake_img = np.zeros((100, 100, 3), dtype=np.uint8)
    original_bytes = b"\xff\xd8\xff\xe0fake_jpeg"
    options = ScanOptions()

    saved = repo.save(
        original_name="test.jpg",
        original_bytes=original_bytes,
        original_format="JPEG",
        scan_image=fake_img,
        corners=[[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]],
        options=options,
    )

    # Verificar que los 3 archivos existen en la carpeta
    assert (tmp_path / f"{saved.id}.png").exists()
    assert (tmp_path / f"{saved.id}-original.jpeg").exists()
    assert (tmp_path / f"{saved.id}.json").exists()


def test_get_scan_returns_saved_data(repo):
    fake_img = np.zeros((50, 50, 3), dtype=np.uint8)
    saved = repo.save(
        original_name="doc.png",
        original_bytes=b"fake_bytes",
        original_format="PNG",
        scan_image=fake_img,
        corners=[[0.0, 0.0], [50.0, 0.0], [50.0, 50.0], [0.0, 50.0]],
        options=ScanOptions(color_mode="grayscale"),
    )

    fetched = repo.get(saved.id)
    assert fetched.id == saved.id
    assert fetched.original_name == "doc.png"
    assert fetched.options.color_mode == "grayscale"


def test_get_unknown_scan_raises_scan_not_found(repo):
    with pytest.raises(ScanNotFound):
        repo.get("inexistente_123")


def test_delete_removes_all_files(repo, tmp_path):
    fake_img = np.zeros((20, 20, 3), dtype=np.uint8)
    saved = repo.save(
        original_name="delete_me.png",
        original_bytes=b"bytes",
        original_format="PNG",
        scan_image=fake_img,
        corners=[],
        options=ScanOptions(),
    )

    repo.delete(saved.id)

    # No debe quedar ningún archivo con ese ID
    assert list(tmp_path.glob(f"{saved.id}*")) == []

    # Un segundo delete o get debe dar ScanNotFound
    with pytest.raises(ScanNotFound):
        repo.delete(saved.id)


def test_persistence_survives_reinstantiation(tmp_path):
    """Simula reiniciar el servidor creando una instancia nueva del repositorio."""
    repo1 = ScanRepository(storage_dir=tmp_path)
    fake_img = np.zeros((30, 30, 3), dtype=np.uint8)
    saved = repo1.save(
        original_name="persistent.jpg",
        original_bytes=b"data",
        original_format="JPEG",
        scan_image=fake_img,
        corners=[],
        options=ScanOptions(),
    )

    # Se instancia un nuevo repo apuntando a la misma carpeta (como al reiniciar la API)
    repo2 = ScanRepository(storage_dir=tmp_path)
    fetched = repo2.get(saved.id)

    assert fetched.id == saved.id
    assert fetched.width == 30