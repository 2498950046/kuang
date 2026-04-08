import json
import hashlib
import os
from datetime import datetime

from neo4j.graph import Node, Relationship, Path
from typing import Dict, List, Any
from config import config


def sanitize_value(value):
    """Data cleansing utility"""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    return str(value)


def generate_cache_key(*args) -> str:
    """Generate cache key"""
    content = json.dumps(args, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(content.encode()).hexdigest()


def process_graph_result(records: List[Any]) -> Dict:
    """Process graph data results"""
    nodes, links, node_ids = [], [], set()

    def add_node(node):
        node_id = str(node.element_id)
        if node_id not in node_ids:
            node_ids.add(node_id)
            node_props = dict(node)
            category = next(iter(node.labels), "未知")
            name = node_props.get("Name") or node_props.get("name") or "未命名"
            nodes.append({
                "id": node_id,
                "name": str(name),
                "category": category,
                "properties": sanitize_value(node_props)
            })

    def add_link(rel):
        rel_props = dict(rel)
        rel_props['type'] = rel.type
        links.append({
            "source": str(rel.start_node.element_id),
            "target": str(rel.end_node.element_id),
            "name": rel.type,
            "properties": sanitize_value(rel_props)
        })

    for record in records:
        for value in record.values():
            if isinstance(value, Path):
                for node in value.nodes:
                    add_node(node)
                for rel in value.relationships:
                    add_link(rel)
            elif isinstance(value, Node):
                add_node(value)
            elif isinstance(value, Relationship):
                add_node(value.start_node)
                add_node(value.end_node)
                add_link(value)

    return {"nodes": nodes, "links": links}


def process_table_result(keys: List[str], records: List[Any]) -> Dict:
    """Process table data results"""
    headers = list(keys)
    rows = [dict(zip(headers, map(sanitize_value, record.values()))) for record in records]
    return {"headers": headers, "rows": rows}


# 图片上传

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def generate_unique_filename(filename):
    """生成唯一文件名（避免重名）"""
    # 获取文件扩展名
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    # 使用时间戳和随机字符串生成唯一文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    random_str = os.urandom(4).hex()  # 生成8位随机字符串

    if ext:
        return f"{timestamp}_{random_str}.{ext}"
    else:
        return f"{timestamp}_{random_str}"
