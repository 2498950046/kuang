import json
import mimetypes
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.csv_preview import preview_csv, profile_csv, read_csv_rows
from app.database import get_db
from app.db_models.dataset import Dataset
from app.serializers import dataset_to_out
from app.zip_preview import profile_zip, read_zip_rows

router = APIRouter(prefix="/datasets", tags=["datasets"])

MAX_BYTES = 500 * 1024 * 1024
DEFAULT_PREVIEW_ROWS = 200
UPLOAD_CHUNK_SIZE = 1024 * 1024


class BatchDeletePayload(BaseModel):
    dataset_ids: list[str]


async def _save_upload_file(file: UploadFile, dest: Path, max_bytes: int) -> int:
    total = 0
    try:
        with dest.open("wb") as handle:
            while True:
                chunk = await file.read(UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(400, "File too large (max 500MB)")
                handle.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    return total


@router.get("")
def list_datasets(db: Session = Depends(get_db)):
    rows = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return {"datasets": [dataset_to_out(d).model_dump() for d in rows]}


@router.post("/upload")
async def upload_dataset(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    name: str | None = Form(None),
    description: str | None = Form(None),
):
    if not file.filename:
        raise HTTPException(400, "Missing file name")

    lower_name = file.filename.lower()
    is_csv = lower_name.endswith(".csv")
    is_zip = lower_name.endswith(".zip")
    if not is_csv and not is_zip:
        raise HTTPException(400, "Only CSV or ZIP datasets are supported")

    ds_id = str(uuid.uuid4())
    safe = "".join(c if c.isalnum() or c in "._-()" else "_" for c in file.filename)
    filename = f"{ds_id}_{safe}"
    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    dest = upload_root / filename
    size_bytes = await _save_upload_file(file, dest, MAX_BYTES)

    cols: list[str] = []
    samples = 0
    preview_payload: dict[str, object]
    try:
        if is_csv:
            cols, samples = preview_csv(dest)
            preview_payload = profile_csv(dest, sample_row_limit=DEFAULT_PREVIEW_ROWS)
        else:
            preview_payload = profile_zip(dest, sample_row_limit=DEFAULT_PREVIEW_ROWS)
            samples = int(preview_payload.get("row_count", 0))
            cols = list(preview_payload.get("columns", []))
            if samples <= 0:
                raise HTTPException(400, "ZIP dataset has no recognizable image files")
    except HTTPException:
        dest.unlink(missing_ok=True)
        raise
    except Exception as exc:
        dest.unlink(missing_ok=True)
        if is_zip:
            raise HTTPException(400, f"Unable to parse ZIP dataset: {exc}") from exc
        raise HTTPException(400, "Unable to parse dataset file") from exc

    default_description = "User uploaded CSV dataset" if is_csv else "User uploaded image ZIP dataset"
    d = Dataset(
        id=ds_id,
        name=(name or "").strip() or Path(file.filename).stem,
        description=(description or "").strip() or default_description,
        filename=filename,
        samples=samples,
        features=len(cols),
        columns_json=json.dumps(cols, ensure_ascii=False),
        size_bytes=size_bytes,
        status="ready",
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return {
        "dataset": dataset_to_out(d).model_dump(),
        "preview": preview_payload,
    }


@router.get("/{dataset_id}/preview")
def dataset_preview(
    dataset_id: str,
    sample_limit: int = Query(DEFAULT_PREVIEW_ROWS, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found")
    path = Path(settings.upload_dir) / ds.filename
    if not path.exists():
        raise HTTPException(404, "Dataset file not found")

    if ds.filename.lower().endswith(".zip"):
        return {
            "dataset": dataset_to_out(ds).model_dump(),
            "preview": profile_zip(path, sample_row_limit=sample_limit),
        }

    return {
        "dataset": dataset_to_out(ds).model_dump(),
        "preview": profile_csv(path, sample_row_limit=sample_limit),
    }


@router.get("/{dataset_id}/rows")
def dataset_rows(
    dataset_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_PREVIEW_ROWS, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found")
    path = Path(settings.upload_dir) / ds.filename
    if not path.exists():
        raise HTTPException(404, "Dataset file not found")

    if ds.filename.lower().endswith(".zip"):
        return {"dataset": dataset_to_out(ds).model_dump(), **read_zip_rows(path, offset=offset, limit=limit)}

    return {"dataset": dataset_to_out(ds).model_dump(), **read_csv_rows(path, offset=offset, limit=limit)}


@router.get("/{dataset_id}/image")
def dataset_zip_image(dataset_id: str, path: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found")
    if not ds.filename.lower().endswith(".zip"):
        raise HTTPException(400, "Only ZIP datasets support image preview")

    zip_path = Path(settings.upload_dir) / ds.filename
    if not zip_path.exists():
        raise HTTPException(404, "Dataset file not found")

    normalized = str(path).replace("\\", "/").strip("/")
    if not normalized:
        raise HTTPException(400, "Invalid image path")

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            if normalized not in zf.namelist():
                raise HTTPException(404, "Image not found in ZIP dataset")
            data = zf.read(normalized)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, f"Unable to read ZIP image: {exc}") from exc

    media_type, _ = mimetypes.guess_type(normalized)
    if not media_type:
        media_type = "application/octet-stream"
    return Response(content=data, media_type=media_type)


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found")

    path = Path(settings.upload_dir) / ds.filename
    path.unlink(missing_ok=True)

    db.delete(ds)
    db.commit()
    return {"ok": True, "dataset_id": dataset_id}


@router.post("/batch-delete")
def batch_delete_datasets(payload: BatchDeletePayload, db: Session = Depends(get_db)):
    ids = [x for x in payload.dataset_ids if isinstance(x, str) and x.strip()]
    if not ids:
        raise HTTPException(400, "dataset_ids is required")

    rows = db.query(Dataset).filter(Dataset.id.in_(ids)).all()
    if not rows:
        return {"ok": True, "deleted_count": 0, "dataset_ids": []}

    deleted_ids: list[str] = []
    for ds in rows:
        path = Path(settings.upload_dir) / ds.filename
        path.unlink(missing_ok=True)
        deleted_ids.append(ds.id)
        db.delete(ds)

    db.commit()
    return {"ok": True, "deleted_count": len(deleted_ids), "dataset_ids": deleted_ids}
