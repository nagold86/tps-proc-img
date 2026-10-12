##Dejo comentado el código original, por si debemos realizar más cambios.
'''from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from app.schemas import ColorMode, ErrorOut, ScanOptions, ScanOut
from app.uploads import read_upload

router = APIRouter(prefix="/api/scans", tags=["scans"])


def empty_scan(scan_id: str = "", original_name: str = "", options: ScanOptions | None = None) -> ScanOut:
    """Placeholder answer with the right shape. Delete it once the endpoints are implemented."""
    return ScanOut(
        id=scan_id, original_name=original_name, url="", original_url="",
        width=0, height=0, size_bytes=0, corners=[],
        options=options or ScanOptions(), created_at=datetime.now(),
    )


@router.post(
    "",
    response_model=ScanOut,
    status_code=status.HTTP_201_CREATED,
    summary="Scan a photo and save the result",
    responses={400: {"model": ErrorOut}, 413: {"model": ErrorOut}, 422: {"model": ErrorOut}},
)
async def create_scan(
    file: Annotated[UploadFile, File(description="Photo of a document")],
    color_mode: Annotated[ColorMode, Form()] = "color",
    color_correction: Annotated[bool, Form()] = True,
    soften_colors: Annotated[float, Form(ge=0, le=1)] = 0.0,
):
    options = ScanOptions(color_mode=color_mode, color_correction=color_correction, soften_colors=soften_colors)
    upload = await read_upload(file)  # given: 413 FILE_TOO_LARGE / 400 INVALID_FILE / 400 UNSUPPORTED_FORMAT
    # TODO (team): scan upload.photo.image with docscan, save the result (PNG), the original
    # photo (upload.content) and the metadata, and return the saved scan.
    return empty_scan(original_name=upload.name, options=options)


@router.get("", response_model=list[ScanOut], summary="List the scans, newest first")
def list_scans():
    # TODO (team): read the saved scans.
    return []


@router.get("/{scan_id}", response_model=ScanOut, summary="Get a scan", responses={404: {"model": ErrorOut}})
def get_scan(scan_id: str):
    # TODO (team): read the scan, or answer 404 SCAN_NOT_FOUND.
    return empty_scan(scan_id)


@router.delete(
    "/{scan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a scan and its files",
    responses={404: {"model": ErrorOut}},
)
def delete_scan(scan_id: str):
    # TODO (team): delete the files of the scan, or answer 404 SCAN_NOT_FOUND.
    return None
'''


from typing import Annotated
from fastapi import APIRouter, File, Form, Response, UploadFile, status
from app.repository import ScanRepository
from app.schemas import ColorMode, ScanOptions, ScanOut
from app.uploads import read_upload
from docscan.scanner import Scanner

router = APIRouter(prefix="/api/scans", tags=["scans"])

# Instancias compartidas
scanner = Scanner()
repository = ScanRepository()


@router.post("", response_model=ScanOut, status_code=status.HTTP_201_CREATED)
async def create_scan(
    file: Annotated[UploadFile, File(description="Photo of a document")],
    color_mode: Annotated[ColorMode, Form()] = "color",
    color_correction: Annotated[bool, Form()] = True,
    soften_colors: Annotated[float, Form(ge=0, le=1)] = 0.0,
):
    options = ScanOptions(
        color_mode=color_mode,
        color_correction=color_correction,
        soften_colors=soften_colors,
    )

    # Validación de subida dada (413 si >10MB, 400 si archivo inválido/formato no permitido)
    upload = await read_upload(file)

    # Llamada al core (puede lanzar DocumentNotFound -> 422 DOCUMENT_NOT_FOUND)
    scanned_image, corners = scanner.scan(
        upload.photo.image,
        color_mode=options.color_mode,
        color_correction=options.color_correction,
        soften_colors=options.soften_colors,
    )

    # Persistencia en disco
    return repository.save(
        original_name=upload.name,
        original_bytes=upload.content,
        original_format=upload.photo.format,
        scan_image=scanned_image,
        corners=corners,
        options=options,
    )


@router.get("", response_model=list[ScanOut])
def list_scans():
    return repository.list()


@router.get("/{scan_id}", response_model=ScanOut)
def get_scan(scan_id: str):
    return repository.get(scan_id)


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan(scan_id: str):
    repository.delete(scan_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)