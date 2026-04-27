import threading
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.db_models.dataset import Dataset
from app.services.recommenders import evaluate_cv, get_dashboard, list_provider_health, parse_cv_zip_dataset, recommend, sensitivity


router = APIRouter(prefix="/recommenders", tags=["recommenders"])
_CV_EVAL_JOBS: dict[str, dict[str, Any]] = {}
_CV_EVAL_JOBS_LOCK = threading.Lock()


class RecommendRequest(BaseModel):
    user_id: str | None = None
    user_history: list[int]
    top_k: int = 10


class SensitivityRequest(BaseModel):
    user_id: str | None = None
    user_history: list[int] = []
    top_k: int = 10
    threshold: float = 0.0
    pred_len: int | None = None


@router.get("")
@router.get("/health")
def health() -> list[dict[str, Any]]:
    return list_provider_health()


@router.get("/dashboard")
def dashboard() -> dict[str, Any]:
    return get_dashboard()


@router.post("/{provider}/recommend")
def do_recommend(provider: str, payload: RecommendRequest) -> dict[str, Any]:
    try:
        return recommend(provider, payload.user_id, payload.user_history, payload.top_k)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}") from exc


@router.post("/{provider}/sensitivity")
def do_sensitivity(provider: str, payload: SensitivityRequest) -> dict[str, Any]:
    try:
        return sensitivity(
            provider=provider,
            user_id=payload.user_id,
            user_history=payload.user_history,
            top_k=payload.top_k,
            threshold=payload.threshold,
            pred_len=payload.pred_len,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}") from exc


@router.post("/{provider}/cv/evaluate")
async def do_cv_evaluate(
    provider: str,
    top_k: int = Form(5),
    threshold: float = Form(0.0),
    tta: bool = Form(False),
    labels_text: str | None = Form(None),
    dataset_id: str | None = Form(None),
    dataset_zip: UploadFile | None = File(None),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    samples = await _collect_cv_samples(
        db=db,
        dataset_id=dataset_id,
        dataset_zip=dataset_zip,
        files=files,
        labels_text=labels_text,
    )
    try:
        return evaluate_cv(
            provider=provider,
            samples=samples,
            top_k=top_k,
            threshold=threshold,
            tta=tta,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Real-time evaluation failed: {exc}") from exc


@router.post("/{provider}/cv/evaluate/start")
async def start_cv_evaluate(
    provider: str,
    top_k: int = Form(5),
    threshold: float = Form(0.0),
    tta: bool = Form(False),
    labels_text: str | None = Form(None),
    dataset_id: str | None = Form(None),
    dataset_zip: UploadFile | None = File(None),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    samples = await _collect_cv_samples(
        db=db,
        dataset_id=dataset_id,
        dataset_zip=dataset_zip,
        files=files,
        labels_text=labels_text,
    )
    job_id = uuid.uuid4().hex
    total = len(samples)
    with _CV_EVAL_JOBS_LOCK:
        _CV_EVAL_JOBS[job_id] = {
            "job_id": job_id,
            "provider": provider,
            "status": "queued",
            "processed": 0,
            "total": total,
            "progress": 0.0,
            "result": None,
            "error": None,
        }

    def _update_progress(done: int, total_count: int) -> None:
        bounded_total = max(1, int(total_count))
        bounded_done = max(0, min(int(done), bounded_total))
        progress = round((bounded_done / bounded_total) * 100.0, 2)
        with _CV_EVAL_JOBS_LOCK:
            job = _CV_EVAL_JOBS.get(job_id)
            if job is None:
                return
            job["processed"] = bounded_done
            job["total"] = bounded_total
            job["progress"] = progress

    def _run_job() -> None:
        with _CV_EVAL_JOBS_LOCK:
            job = _CV_EVAL_JOBS.get(job_id)
            if job is not None:
                job["status"] = "running"
        try:
            result = evaluate_cv(
                provider=provider,
                samples=samples,
                top_k=top_k,
                threshold=threshold,
                tta=tta,
                progress_callback=_update_progress,
            )
            with _CV_EVAL_JOBS_LOCK:
                job = _CV_EVAL_JOBS.get(job_id)
                if job is not None:
                    job["status"] = "completed"
                    job["processed"] = max(1, total)
                    job["total"] = max(1, total)
                    job["progress"] = 100.0
                    job["result"] = result
        except KeyError:
            with _CV_EVAL_JOBS_LOCK:
                job = _CV_EVAL_JOBS.get(job_id)
                if job is not None:
                    job["status"] = "failed"
                    job["error"] = f"Unknown provider: {provider}"
        except Exception as exc:  # noqa: BLE001
            with _CV_EVAL_JOBS_LOCK:
                job = _CV_EVAL_JOBS.get(job_id)
                if job is not None:
                    job["status"] = "failed"
                    job["error"] = f"Real-time evaluation failed: {exc}"

    threading.Thread(target=_run_job, daemon=True).start()
    return {"job_id": job_id, "status": "queued", "processed": 0, "total": total, "progress": 0.0}


@router.get("/{provider}/cv/evaluate/jobs/{job_id}")
def get_cv_evaluate_job(provider: str, job_id: str) -> dict[str, Any]:
    with _CV_EVAL_JOBS_LOCK:
        job = _CV_EVAL_JOBS.get(job_id)
        if job is None or job.get("provider") != provider:
            raise HTTPException(status_code=404, detail="Evaluation job not found")
        payload = {
            "job_id": job["job_id"],
            "provider": job["provider"],
            "status": job["status"],
            "processed": job["processed"],
            "total": job["total"],
            "progress": job["progress"],
            "error": job["error"],
        }
        if job["status"] == "completed":
            payload["result"] = job["result"]
        return payload


async def _collect_cv_samples(
    db: Session,
    dataset_id: str | None,
    dataset_zip: UploadFile | None,
    files: list[UploadFile] | None,
    labels_text: str | None,
) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []

    if dataset_id:
        ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if ds is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if not ds.filename.lower().endswith(".zip"):
            raise HTTPException(status_code=400, detail="Selected dataset is not a ZIP image dataset")
        dataset_path = Path(settings.upload_dir) / ds.filename
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail="Dataset file not found")
        try:
            samples.extend(parse_cv_zip_dataset(dataset_path))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Unable to parse dataset ZIP: {exc}") from exc

    if dataset_zip is not None:
        zip_bytes = await dataset_zip.read()
        if not zip_bytes:
            raise HTTPException(status_code=400, detail="Uploaded ZIP is empty")
        try:
            samples.extend(parse_cv_zip_dataset(zip_bytes))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Unable to parse ZIP test dataset: {exc}") from exc

    labels_map: dict[str, str] = {}
    if labels_text:
        for line in labels_text.splitlines():
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            if "," in text:
                name, label = text.split(",", 1)
            elif "\t" in text:
                name, label = text.split("\t", 1)
            else:
                continue
            labels_map[name.strip()] = label.strip()

    if files:
        for upload in files:
            name = upload.filename or "unnamed"
            payload = await upload.read()
            if not payload:
                continue
            samples.append(
                {
                    "name": name,
                    "path": name,
                    "bytes": payload,
                    "true_label": labels_map.get(name),
                }
            )

    if not samples:
        raise HTTPException(
            status_code=400,
            detail="Please upload test images, upload a class-folder ZIP, or choose a ZIP dataset from dataset library.",
        )
    return samples
