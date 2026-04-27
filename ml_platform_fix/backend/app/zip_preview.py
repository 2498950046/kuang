from pathlib import Path
from typing import Any

from app.image_archive import iter_zip_image_entries


def profile_zip_bytes(zip_bytes: bytes, sample_row_limit: int = 200) -> dict[str, Any]:
    sample_rows: list[dict[str, str]] = []
    class_counts: dict[str, int] = {}
    total = 0

    for image in iter_zip_image_entries(zip_bytes):
        total += 1
        label = str(image.get("label") or "")
        if label:
            class_counts[label] = class_counts.get(label, 0) + 1
        if sample_row_limit <= 0 or len(sample_rows) < sample_row_limit:
            sample_rows.append(
                {
                    "file_name": str(image["file_name"]),
                    "label": label,
                    "path": str(image["path"]),
                    "size_bytes": str(image["size_bytes"]),
                }
            )

    class_distribution = [
        {"label": key, "count": value}
        for key, value in sorted(class_counts.items(), key=lambda item: item[1], reverse=True)
    ]

    return {
        "row_count": total,
        "profiled_rows": total,
        "columns": ["file_name", "label", "path", "size_bytes"],
        "numeric_columns": [],
        "categorical_columns": [],
        "low_cardinality_columns": [],
        "high_cardinality_columns": [],
        "id_like_columns": [],
        "missing_summary": [],
        "analysis": {"scatter_plot": None, "corr_heatmap": None, "boxplots": [], "pca_projection": None},
        "sample_rows": sample_rows,
        "class_distribution": class_distribution[:100],
    }


def profile_zip(path: Path, sample_row_limit: int = 200) -> dict[str, Any]:
    sample_rows: list[dict[str, str]] = []
    class_counts: dict[str, int] = {}
    total = 0

    for image in iter_zip_image_entries(path):
        total += 1
        label = str(image.get("label") or "")
        if label:
            class_counts[label] = class_counts.get(label, 0) + 1
        if sample_row_limit <= 0 or len(sample_rows) < sample_row_limit:
            sample_rows.append(
                {
                    "file_name": str(image["file_name"]),
                    "label": label,
                    "path": str(image["path"]),
                    "size_bytes": str(image["size_bytes"]),
                }
            )

    class_distribution = [
        {"label": key, "count": value}
        for key, value in sorted(class_counts.items(), key=lambda item: item[1], reverse=True)
    ]

    return {
        "row_count": total,
        "profiled_rows": total,
        "columns": ["file_name", "label", "path", "size_bytes"],
        "numeric_columns": [],
        "categorical_columns": [],
        "low_cardinality_columns": [],
        "high_cardinality_columns": [],
        "id_like_columns": [],
        "missing_summary": [],
        "analysis": {"scatter_plot": None, "corr_heatmap": None, "boxplots": [], "pca_projection": None},
        "sample_rows": sample_rows,
        "class_distribution": class_distribution[:100],
    }


def read_zip_rows(path: Path, offset: int, limit: int) -> dict[str, Any]:
    safe_offset = max(0, int(offset))
    safe_limit = max(1, min(int(limit), 2000))
    rows: list[dict[str, str]] = []
    total = 0

    for image in iter_zip_image_entries(path):
        if total >= safe_offset and len(rows) < safe_limit:
            rows.append(
                {
                    "file_name": str(image["file_name"]),
                    "label": str(image.get("label") or ""),
                    "path": str(image["path"]),
                    "size_bytes": str(image["size_bytes"]),
                }
            )
        total += 1

    return {"total": total, "offset": safe_offset, "limit": safe_limit, "rows": rows}
