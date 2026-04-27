import io
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".gif",
    ".tif",
    ".tiff",
    ".jfif",
}


def normalize_zip_name(name: str) -> str:
    return name.replace("\\", "/").strip("/")


def zip_entry_label(path: str) -> str | None:
    parts = normalize_zip_name(path).split("/")
    return parts[-2] if len(parts) > 1 else None


def _has_supported_extension(name: str) -> bool:
    return Path(name).suffix.lower() in IMAGE_EXTENSIONS


def _has_image_signature(header: bytes) -> bool:
    if not header:
        return False
    return (
        header.startswith(b"\xFF\xD8\xFF")
        or header.startswith(b"\x89PNG\r\n\x1a\n")
        or header.startswith((b"GIF87a", b"GIF89a"))
        or header.startswith(b"BM")
        or (len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP")
        or header.startswith((b"II*\x00", b"MM\x00*"))
    )


@contextmanager
def _open_zip(source: Path | bytes):
    if isinstance(source, Path):
        with zipfile.ZipFile(source, "r") as zf:
            yield zf
        return
    with zipfile.ZipFile(io.BytesIO(source), "r") as zf:
        yield zf


def _is_supported_image_member(zf: zipfile.ZipFile, info: zipfile.ZipInfo, filename: str) -> bool:
    if _has_supported_extension(filename):
        return True
    try:
        with zf.open(info, "r") as handle:
            header = handle.read(64)
    except Exception:
        return False
    return _has_image_signature(header)


def iter_zip_image_entries(
    source: Path | bytes,
    *,
    include_bytes: bool = False,
    max_items: int | None = None,
) -> Iterator[dict[str, Any]]:
    count = 0
    with _open_zip(source) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            filename = normalize_zip_name(info.filename)
            if not filename:
                continue
            if not _is_supported_image_member(zf, info, filename):
                continue

            payload = zf.read(info) if include_bytes else None
            yield {
                "file_name": Path(filename).name,
                "path": filename,
                "label": zip_entry_label(filename),
                "size_bytes": int(info.file_size),
                "bytes": payload,
            }
            count += 1
            if max_items is not None and count >= max_items:
                break
