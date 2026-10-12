import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from app import config
from app.errors import ScanNotFound
from app.schemas import ScanOptions, ScanOut
from docscan.imageio import encode_png

# Permite solo caracteres alfanuméricos en el id para evitar path traversal (ej. "../")
ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")


class ScanRepository:
    def __init__(self, storage_dir: Path | None = None):
        self.storage_dir = storage_dir or config.STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _validate_id(self, scan_id: str) -> str:
        if not scan_id or not ID_REGEX.match(scan_id):
            raise ScanNotFound(scan_id)
        return scan_id

    def save(
        self,
        original_name: str,
        original_bytes: bytes,
        original_format: str,
        scan_image,
        corners: list[list[float]],
        options: ScanOptions,
    ) -> ScanOut:
        scan_id = uuid.uuid4().hex

        # Formato de la foto original (ej. 'jpg' o 'png')
        ext = original_format.lower()
        if not ext.startswith("."):
            ext = f".{ext}"

        # 1. Guardar la foto original tal como llegó
        orig_filename = f"{scan_id}-original{ext}"
        (self.storage_dir / orig_filename).write_bytes(original_bytes)

        # 2. Guardar el escaneo en PNG
        png_bytes = encode_png(scan_image)
        png_filename = f"{scan_id}.png"
        (self.storage_dir / png_filename).write_bytes(png_bytes)

        # 3. Armar y guardar metadatos JSON
        h, w = scan_image.shape[:2]
        now = datetime.now(timezone.utc).isoformat()

        meta = {
            "id": scan_id,
            "original_name": original_name,
            "url": f"{config.MEDIA_URL}/{png_filename}",
            "original_url": f"{config.MEDIA_URL}/{orig_filename}",
            "width": w,
            "height": h,
            "size_bytes": len(png_bytes),
            "corners": corners,
            "options": options.model_dump(),
            "created_at": now,
        }

        json_filename = f"{scan_id}.json"
        (self.storage_dir / json_filename).write_text(json.dumps(meta, indent=2), encoding="utf-8")

        return ScanOut(**meta)

    def get(self, scan_id: str) -> ScanOut:
        self._validate_id(scan_id)
        json_path = self.storage_dir / f"{scan_id}.json"
        if not json_path.exists():
            raise ScanNotFound(scan_id)
        return ScanOut(**json.loads(json_path.read_text(encoding="utf-8")))

    def list(self) -> list[ScanOut]:
        json_files = list(self.storage_dir.glob("*.json"))
        # Ordenar del más nuevo al más viejo por fecha de modificación
        json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        scans = []
        for p in json_files:
            try:
                scans.append(ScanOut(**json.loads(p.read_text(encoding="utf-8"))))
            except Exception:
                continue
        return scans

    def delete(self, scan_id: str) -> None:
        self._validate_id(scan_id)
        json_path = self.storage_dir / f"{scan_id}.json"
        if not json_path.exists():
            raise ScanNotFound(scan_id)

        # Borrar todos los archivos con ese prefijo (PNG, original y JSON)
        for path in self.storage_dir.glob(f"{scan_id}*"):
            path.unlink(missing_ok=True)