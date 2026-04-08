import os
import sqlite3
from typing import List, Dict, Any


# 这里使用 backend_all/backendAdmin 下的测试数据库
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # 指向 backend_all 目录
DB_PATH = os.path.join(
    BASE_DIR,
    "backendAdmin",
    "mineral_data_test",
    "table1&2.db",
)


def _connect() -> sqlite3.Connection:
    """创建到矿物样品 SQLite 数据库的连接"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _pick_table(cursor: sqlite3.Cursor) -> str:
    """
    自动选择合适的表：
    - 优先使用 “矿物样品图” 表；
    - 否则在表名中寻找包含“样品/标本/矿物/图”的表；
    - 都没有时，退回第一个表。
    """
    tables = [name for (name,) in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    if not tables:
        raise RuntimeError("数据库中未找到任何表")

    if "矿物样品图" in tables:
        return "矿物样品图"

    preferred = [t for t in tables if any(key in t for key in ("样品", "标本", "矿物", "图"))]
    return preferred[0] if preferred else tables[0]


def _choose_columns(columns: List[str], keywords: List[str]) -> List[str]:
    lowered = {c: c.lower() for c in columns}
    result = []
    for col, low in lowered.items():
        if any(k in low for k in keywords):
            result.append(col)
    return result


def _build_image_list(row_dict: Dict[str, Any], columns: List[str]) -> List[str]:
    images = []
    for col in columns:
        val = row_dict.get(col)
        if isinstance(val, str) and val.strip():
            images.append(val.strip())
    return images


def _infer_small_from_big(big_paths: List[str]) -> List[str]:
    """
    从大图路径推断小图路径：
    - /big/ -> /small/
    - \\big\\ -> \\small\\
    - 其它情况保持不变
    """
    small_paths = []
    for path in big_paths:
        if "/big/" in path:
            small_paths.append(path.replace("/big/", "/small/"))
        elif "\\big\\" in path:
            small_paths.append(path.replace("\\big\\", "\\small\\"))
        else:
            small_paths.append(path)
    return small_paths


def get_samples_by_name(mineral_name: str) -> List[Dict[str, Any]]:
    """
    根据矿物名称获取样品图片和描述信息。
    返回格式为：
    [
        {
            "sampleName": "矿物名-样品ID",
            "description": "描述",
            "bigImages": ["大图1", "大图2", ...],
            "smallImages": ["小图1", "小图2", ...]
        },
        ...
    ]
    """
    if not mineral_name:
        return []

    conn = _connect()
    try:
        cur = conn.cursor()
        table = _pick_table(cur)

        # 针对 “矿物样品图” 表的精确解析逻辑（与旧 backend 保持一致）
        if table == "矿物样品图":
            rows = cur.execute(
                "SELECT 矿物名, 矿物样品图, 每个样品的矿物ID, 每个样品特有的描述 "
                "FROM 矿物样品图 WHERE 矿物名 = ?",
                (mineral_name,),
            ).fetchall()

            samples: List[Dict[str, Any]] = []
            for row in rows:
                row_dict = dict(row)
                raw_urls = (row_dict.get("矿物样品图") or "").strip()
                if not raw_urls:
                    continue

                all_urls = [u.strip() for u in raw_urls.split(";") if u.strip()]
                big_images = [u for u in all_urls if "/big/" in u]
                small_images = [u for u in all_urls if "/small/" in u]

                if not small_images and big_images:
                    small_images = _infer_small_from_big(big_images)
                if not big_images:
                    big_images = [u for u in all_urls if "/small/" not in u]

                description = row_dict.get("每个样品特有的描述") or ""
                sample_id = row_dict.get("每个样品的矿物ID")
                base_name = row_dict.get("矿物名") or mineral_name
                sample_name = f"{base_name}-{sample_id}" if sample_id is not None else base_name

                samples.append(
                    {
                        "sampleName": sample_name,
                        "description": str(description),
                        "bigImages": big_images,
                        "smallImages": small_images or big_images,
                    }
                )

            return samples

        # 其它表：走通用兼容逻辑
        rows = cur.execute(f"SELECT * FROM '{table}'").fetchall()
        columns = [c[1] for c in cur.execute(f"PRAGMA table_info('{table}')").fetchall()]

        name_cols = _choose_columns(columns, ["名称", "标本名", "矿物", "name"])
        big_cols = _choose_columns(columns, ["大图", "big", "图片", "图像", "img", "photo"])
        small_cols = _choose_columns(columns, ["小图", "small", "缩略"])
        desc_cols = _choose_columns(columns, ["特有", "描述", "说明", "desc"])

        mineral_lower = mineral_name.lower()
        samples: List[Dict[str, Any]] = []

        for row in rows:
            row_dict = dict(row)
            candidate_names = [str(row_dict.get(col) or "").strip() for col in name_cols]
            if not candidate_names:
                candidate_names = [str(row_dict.get("名称") or row_dict.get("name") or "")]

            matched = any(mineral_lower in (name or "").lower() for name in candidate_names)
            if not matched:
                continue

            big_images = _build_image_list(row_dict, big_cols)
            if not big_images:
                # 如果没有专门的大图列，尝试从所有字符串列中提取 jpg/png
                for val in row_dict.values():
                    if isinstance(val, str) and (".jpg" in val.lower() or ".png" in val.lower()):
                        big_images.append(val.strip())

            small_images = _build_image_list(row_dict, small_cols)
            if not small_images and big_images:
                small_images = _infer_small_from_big(big_images)

            description = ""
            for col in desc_cols:
                if row_dict.get(col):
                    description = str(row_dict.get(col))
                    break

            samples.append(
                {
                    "sampleName": candidate_names[0] if candidate_names else mineral_name,
                    "description": description,
                    "bigImages": big_images,
                    "smallImages": small_images or big_images,
                }
            )

        return samples
    finally:
        conn.close()











