
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64
import csv
import os

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import logging
import json
from datetime import datetime
from werkzeug.utils import secure_filename
# 导入模块
from config import config
from cache import cache_manager
from neo4j_driver import driver
from agent import OptimizedIntelligentAgent, executor
from utils import generate_cache_key, allowed_file, generate_unique_filename
from mineral_sample_service import get_samples_by_name
import mysql.connector
from mysql.connector import Error
from audio_service.baidu_service import recognize_speech
# from audio_service.asr_service import get_asr_instance, init_asr_service

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask 应用初始化
app = Flask(__name__)
CORS(app)


# 初始化服务
def init_services():
    """初始化所有服务"""
    logger.info("正在初始化服务...")

    app.config['image_model'] = None
    app.config['image_classes'] = None
    app.config['image_device'] = None
    app.config['image_classification_module'] = None

    # 初始化图像模型
    if config.ENABLE_IMAGE_MODEL:
        try:
            from backend.image_module import image_classification_module, model_init

            inference_model, classes, device = model_init()
            app.config['image_model'] = inference_model
            app.config['image_classes'] = classes
            app.config['image_device'] = device
            app.config['image_classification_module'] = image_classification_module
            logger.info("图像模型初始化完成")
        except Exception as e:
            logger.error(f"图像模型初始化失败: {str(e)}")
    else:
        logger.info("图像模型已关闭，当前 backend 仅提供图谱与问答相关能力")

    # 初始化ASR服务（已切换为百度语音识别，无需本地ASR初始化）
    # try:
    #     # 配置ASR参数
    #     asr_config = {
    #         "model_size": "small",
    #         "device": "auto",
    #         "cache_dir": "./audio_service/asr_cache"
    #     }
    #     asr_service = init_asr_service(**asr_config)
    #     app.config['asr_service'] = asr_service
    #     logger.info("ASR服务初始化完成")
    # except Exception as e:
    #     logger.error(f"ASR服务初始化失败: {str(e)}")
    #     app.config['asr_service'] = None

    # 创建代理实例
    try:
        agent = OptimizedIntelligentAgent()
        app.config['agent'] = agent
        logger.info("智能代理初始化完成")
    except Exception as e:
        logger.error(f"智能代理初始化失败: {str(e)}")

    logger.info("所有服务初始化完成")


# --- API 路由 ---
@app.route('/graph', methods=['POST'])
def get_graph_data():
    """原始图数据API"""
    try:
        data = request.get_json()
        cypher_query = data.get('cypher', 'MATCH p=(n)-[r]->(m) RETURN p LIMIT 10')
        logger.info(f"收到 Cypher 查询请求: {cypher_query}")

        cache_key = generate_cache_key("graph", cypher_query)
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.info("从缓存返回查询结果")
            return jsonify(json.loads(cached_result))
        
        agent = app.config.get('agent')
        result = agent.execute_cypher_query(cypher_query)
        if result['success']:
            result_data = {"type": result["type"], "data": result["data"]}
            cache_manager.set(cache_key, json.dumps(result_data, ensure_ascii=False), config.QUERY_CACHE_TTL)
            logger.info("Cypher 查询执行成功，返回数据")
            return jsonify(result_data)
        else:
            return jsonify({"error": result["error"]}), 500

    except Exception as e:
        logger.error("原生 Cypher 查询失败", exc_info=True)
        return jsonify({"error": f"内部服务器错误: {type(e).__name__}"}), 500


@app.route('/ai/nl2cypher', methods=['POST'])
def natural_language_to_cypher():
    """优化的自然语言到Cypher查询转换"""
    try:
        data = request.get_json()
        question = data.get('question', '')

        logger.info(f"收到 NL2Cypher 请求: {question}")

        if not question:
            return jsonify({"error": "问题不能为空"}), 400

        cache_key = generate_cache_key("nl2cypher", question)
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.info("从缓存返回 NL2Cypher 结果")
            # print('cache: ' , cached_result)
            return jsonify(json.loads(cached_result))

        result = None
        agent = app.config.get('agent')
        for response_chunk in agent.unified_nl2cypher_and_rag(question, mode="nl2cypher"):
            if isinstance(response_chunk, dict) and response_chunk.get("success") is not None:
                result = response_chunk
                break

        if result is None:
            result = {"success": False, "error": "处理超时或失败"}

        if result.get("success"):
            cache_manager.set(cache_key, json.dumps(result, ensure_ascii=False), config.QUERY_CACHE_TTL)

        logger.info(f"NL2Cypher 处理完成: success={result.get('success')}")
        # print('result: ', result)
        return jsonify(result)

    except Exception as e:
        logger.error("NL2Cypher 处理失败", exc_info=True)
        return jsonify({"error": f"内部服务器错误: {str(e)}"}), 500


# 矿物类别检测
@app.route('/ai/mineral_dec', methods=['POST'])
def mineral_dec():
    '''接口基本信息
    接口地址: /ai/mineral_dec
    请求方法: POST
    Content-Type: multipart/form-data
    功能描述: 上传矿物图片进行类别识别
    响应格式: JSON

    请求参数
    1. 表单参数
    参数名	类型	必填	说明
    file	File	是	上传的图片文件
    '''
    # 确保上传目录存在
    if not os.path.exists(config.UPLOAD_FOLDER):
        os.makedirs(config.UPLOAD_FOLDER)
    try:
        image_classification_module = app.config.get('image_classification_module')
        if not config.ENABLE_IMAGE_MODEL or not image_classification_module:
            return jsonify({
                'code': 503,
                'message': '当前服务未启用矿物识别模型，请使用 8080 的智能鉴赏服务',
                'data': None
            }), 503

        # 检查是否有文件在请求中
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'message': '没有找到文件字段',
                'data': None
            }), 400

        file = request.files['file']

        # 检查是否选择了文件
        if file.filename == '':
            return jsonify({
                'code': 400,
                'message': '没有选择文件',
                'data': None
            }), 400

        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({
                'code': 400,
                'message': f'不支持的文件类型。允许的类型: {", ".join(config.ALLOWED_EXTENSIONS)}',
                'data': None
            }), 400

        # 生成安全的文件名
        original_filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(original_filename)

        # 完整的保存路径
        filepath = os.path.join(config.UPLOAD_FOLDER, unique_filename)

        # 保存文件
        file.save(filepath)

        inference_model = app.config.get('image_model')
        classes = app.config.get('image_classes')
        device = app.config.get('image_device')
        # 检测
        results = image_classification_module(filepath, inference_model, classes, device, topk=3)
        result_dicts = [{"name": config.mineral_translate_dic.get(name, '矿物名错误'), "confidence": confidence} for
                        name, confidence in results]
        # print("识别结果：", result_dicts)
        # 获取文件信息
        file_size = os.path.getsize(filepath)

        # 返回成功响应
        return jsonify({
            'code': 200,
            'message': '文件上传成功',
            'data': {
                'filename': unique_filename,
                'original_filename': original_filename,
                'filepath': filepath,
                'file_size': file_size,
                'file_size_readable': f"{file_size / 1024:.2f} KB",
                'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'url': f"/img/{unique_filename}",  # 可以访问的URL
                'result_dicts': result_dicts
            }
        })

    except Exception as e:
        app.logger.error(f"上传文件时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': None
        }), 500


@app.route('/ai/rag', methods=['POST'])
def intelligent_rag_answer():
    """优化的智能 RAG 问答 - 流式响应"""
    try:
        data = request.get_json()
        question = data.get('question', '')

        logger.info(f"收到智能 RAG 请求: {question}")

        if not question:
            return jsonify({"error": "问题不能为空"}), 400

        def generate_stream():
            """生成流式响应"""
            try:
                yield 'event: start\ndata: {"type": "start"}\n\n'
                agent = app.config.get('agent')
                for response_chunk in agent.unified_nl2cypher_and_rag(question, mode="rag"):
                    event_type = response_chunk.get('type', 'message')
                    data = json.dumps(response_chunk, ensure_ascii=False)
                    message = f'event: {event_type}\ndata: {data}\n\n'
                    yield message

                yield 'event: complete\ndata: {"type": "complete"}\n\n'

            except Exception as e:
                logger.error(f"RAG 流式处理失败: {e}")
                error_data = json.dumps({
                    'type': 'error',
                    'error': str(e)
                }, ensure_ascii=False)
                yield f'event: error\ndata: {error_data}\n\n'

        logger.info("开始 RAG 流式响应")
        response = Response(
            generate_stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache, no-transform',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
                'Content-Type': 'text/event-stream; charset=utf-8',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Cache-Control',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            }
        )
        return response

    except Exception as e:
        logger.error("RAG 请求处理失败", exc_info=True)
        return jsonify({"error": f"内部服务器错误: {str(e)}"}), 500


@app.route('/ai/schema', methods=['GET'])
def get_schema():
    """获取知识图谱模式信息"""
    logger.info("收到模式请求")
    try:
        agent = app.config.get('agent')
        schema = agent.get_schema_cached()
        logger.info("成功检索并返回模式")
        return jsonify({"success": True, "schema": schema})

    except Exception as e:
        logger.error("模式请求处理失败", exc_info=True)
        return jsonify({"error": f"内部服务器错误: {str(e)}"}), 500


@app.route('/admin/cache/status', methods=['GET'])
def cache_status():
    """缓存状态监控"""
    try:
        if cache_manager.cache_enabled:
            info = cache_manager.redis_client.info()
            return jsonify({
                "cache_type": "Redis",
                "status": "已连接",
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0)
            })
        else:
            return jsonify({
                "cache_type": "内存",
                "status": "活跃",
                "cache_size": len(cache_manager.memory_cache),
                "cached_keys": list(cache_manager.memory_cache.keys())
            })
    except Exception as e:
        logger.error("获取缓存状态失败", exc_info=True)
        return jsonify({"error": f"获取缓存状态失败: {str(e)}"}), 500


@app.route('/admin/cache/clear', methods=['POST'])
def clear_cache():
    """清除缓存"""
    agent = app.config.get('agent')
    try:
        if cache_manager.cache_enabled:
            cache_manager.redis_client.flushdb()
            message = "Redis 缓存已清除"
        else:
            cache_manager.memory_cache.clear()
            message = "内存缓存已清除"

        agent._schema_cache = None
        agent._schema_cache_time = None

        logger.info(message)
        return jsonify({"success": True, "message": message})

    except Exception as e:
        logger.error("清除缓存失败", exc_info=True)
        return jsonify({"error": f"清除缓存失败: {str(e)}"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查 - 增强版"""
    health_status = {
        "status": "健康",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }

    # 检查数据库连接
    try:
        with driver.session() as session:
            result = session.run("RETURN 1").single()
            if result:
                health_status["services"]["database"] = "已连接"
            else:
                health_status["services"]["database"] = "响应异常"
                health_status["status"] = "部分健康"
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        health_status["services"]["database"] = f"连接失败: {str(e)[:50]}"
        health_status["status"] = "不健康"

    # 检查AI服务（快速测试，不影响主要状态）
    try:
        agent = app.config.get('agent')
        test_response = agent.call_llm(
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        health_status["services"]["ai_service"] = "已连接"
    except Exception as e:
        logger.warning(f"AI服务健康检查失败: {e}")
        health_status["services"]["ai_service"] = f"异常: {str(e)[:50]}"
        # AI服务失败不影响整体健康状态

    # 检查缓存
    health_status["services"]["cache"] = "已连接" if cache_manager.cache_enabled else "内存回退"

    status_code = 200 if health_status["status"] == "健康" else 503
    return jsonify(health_status), status_code


@app.route('/api/mineral_samples', methods=['GET'])
def mineral_samples():
    """根据矿物名称返回样品图片及描述（迁移自原 backend 接口）"""
    try:
        name = (request.args.get('name') or '').strip()
        if not name:
            return jsonify({"success": False, "error": "参数 name 不能为空"}), 400

        samples = get_samples_by_name(name)
        return jsonify({"success": True, "samples": samples})
    except Exception as e:
        logger.error("获取矿物样品失败", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/mineral/table2_description', methods=['GET'])
def get_table2_description_by_id():
    """从 table1&2.db 的「矿物样品图」表按 id 取「每个样品特有的描述」，id 为图片文件夹名 _ 前的数字"""
    try:
        import sqlite3
        table2_id = request.args.get('id', type=int)
        if table2_id is None:
            return jsonify({'code': 400, 'message': '缺少 id 参数', 'data': None}), 400

        # 数据库在 backend_all/backendAdmin/mineral_data_test/table1&2.db
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(backend_dir)
        db_path = os.path.join(root_dir, 'backendAdmin', 'mineral_data_test', 'table1&2.db')
        if not os.path.isfile(db_path):
            return jsonify({'code': 200, 'data': {'description': '', '特有描述': ''}})

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        table_name = '矿物样品图'
        cursor.execute("PRAGMA table_info({})".format(table_name.replace("'", "''")))
        columns = [col[1] for col in cursor.fetchall()]
        if not columns:
            conn.close()
            return jsonify({'code': 200, 'data': {'description': '', '特有描述': ''}})
        # 表中 id 列可能为 ID 或 id，用实际列名
        id_col = next((c for c in columns if c.upper() == 'ID'), 'id')
        cursor.execute(
            'SELECT * FROM {} WHERE "{}" = ?'.format(table_name.replace("'", "''"), id_col.replace('"', '""')),
            (table2_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return jsonify({'code': 200, 'data': {'description': '', '特有描述': ''}})
        row_dict = dict(zip(columns, row))
        desc = (
            row_dict.get('每个样品特有的描述')
            or row_dict.get('特有描述')
            or row_dict.get('描述')
            or row_dict.get('description')
        )
        if desc is None:
            for col_name, val in row_dict.items():
                if val is not None and val != '' and '描述' in str(col_name):
                    desc = val
                    break
        desc = desc or ''
        if isinstance(desc, bytes):
            desc = desc.decode('utf-8', errors='replace')
        desc = str(desc).strip()
        return jsonify({'code': 200, 'data': {'description': desc, '特有描述': desc}})
    except Exception as e:
        logger.exception("table2_description 错误: %s", e)
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


# 宝玉石基本信息获取
@app.route('/gems/gems_main', methods=['POST'])
def get_gem_by_name():
    """
    根据矿物中文名称获取矿物基本信息

    请求参数 (JSON格式):
    {
        "name": "红宝石",  # 矿物中文名称
        "exact_match": true  # 可选，是否精确匹配，默认为false（模糊匹配）
    }

    返回参数:
    {
        "code": 200,
        "message": "成功",
        "data": [
            {
                "id": 1,
                "name": "红宝石",
                "type": "Ruby",
                "image_url": "https://example.com/image.jpg",
                "color": "#e0115f",
                "info": "宝石描述信息"
            }
        ]
    }
    """
    try:
        # 1. 获取请求数据
        data = request.get_json()

        if not data:
            return jsonify({
                'code': 400,
                'message': '请求数据不能为空',
                'data': []
            }), 400

        gem_name = data.get('name')
        if not gem_name:
            return jsonify({
                'code': 400,
                'message': '矿物名称不能为空',
                'data': []
            }), 400

        exact_match = data.get('exact_match', False)

        # 2. 连接到数据库
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'code': 500,
                'message': '数据库连接失败',
                'data': []
            }), 500

        cursor = conn.cursor(dictionary=True)

        # 3. 构建查询
        if exact_match:
            # 精确匹配查询
            query = """
                SELECT id, name, type, image_url, color, info 
                FROM gems 
                WHERE name = %s
            """
            params = (gem_name,)
        else:
            # 模糊匹配查询
            query = """
                SELECT id, name, type, image_url, color, info 
                FROM gems 
                WHERE name LIKE %s
            """
            params = (f'%{gem_name}%',)

        # 4. 执行查询
        cursor.execute(query, params)
        results = cursor.fetchall()

        # 5. 关闭连接
        cursor.close()
        conn.close()

        # 6. 处理结果
        if not results:
            return jsonify({
                'code': 404,
                'message': f'未找到矿物: {gem_name}',
                'data': []
            }), 404

        # 7. 返回结果
        return jsonify({
            'code': 200,
            'message': '查询成功',
            'data': results
        })

    except Exception as e:
        print(f"接口错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': []
        }), 500


# 添加批量查询接口
@app.route('/gems/gems_batch', methods=['POST'])
def get_gems_batch():
    """
    批量查询矿物信息

    请求参数:
    {
        "names": ["红宝石", "蓝宝石", "钻石"],
        "fields": ["id", "name", "type"]  # 可选，指定返回字段
    }
    """
    try:
        data = request.get_json()
        if not data or 'names' not in data:
            return jsonify({
                'code': 400,
                'message': '请求参数不完整',
                'data': []
            }), 400

        gem_names = data.get('names', [])
        if not gem_names:
            return jsonify({
                'code': 400,
                'message': '矿物名称列表不能为空',
                'data': []
            }), 400

        # 默认返回所有字段
        if 'fields' not in data:
            fields = ['id', 'name', 'type', 'image_url', 'color', 'info']
        else:
            fields = data.get('fields', ['id', 'name', 'type', 'image_url', 'color', 'info'])
            if not fields:
                fields = ['id', 'name', 'type', 'image_url', 'color', 'info']

        field_str = ', '.join(fields)

        # 创建数据库连接
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'code': 500,
                'message': '数据库连接失败',
                'data': []
            }), 500

        cursor = conn.cursor(dictionary=True)

        # 构建IN查询
        placeholders = ', '.join(['%s'] * len(gem_names))
        query = f"""
            SELECT {field_str}
            FROM gems
            WHERE name IN ({placeholders})
        """

        cursor.execute(query, gem_names)
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            'code': 200,
            'message': '查询成功',
            'data': results,
            'count': len(results)
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': []
        }), 500


# 宝石详细信息获取
@app.route('/gems/gems_detail', methods=['POST'])
def get_gem_detail():
    """
    根据矿物名称获取宝石详细信息（包含JSON字段）

    请求参数 (JSON格式):
    {
        "gem_name": "坦桑石",  # 宝石名称
    }

    返回参数:
    {
        "code": 200,
        "message": "成功",
        "data": {
            "id": "690ef0ab4b36a72239be3dd9",
            "gem_name": "坦桑石",
            "basic_info": {
                "标本名": "坦桑石",
                "矿物名称": "黝帘石",
                "英文名": "zoisite",
                "晶体化学式": "Ca2Al3(Si2O7)(SiO4)O(OH)",
                "标本分类": ["宝玉石", "天然珠宝玉石", "天然宝石"],
                "产地": "样品产地",
                "年代": "标本产出时代",
                "编号": "标本自编号",
                "捐赠人": "标本捐赠人",
                "标本描述": "坦桑石(Zoisite)为硅酸盐矿物..."
            },
            "material_properties": {
                "化学成分": "Ca2Al3(Si2O7)(SiO4)O(OH)，可含V、Cr、Mn",
                "结晶状态": "晶质体",
                "晶系": "斜方晶系",
                "常见颜色": {
                    "坦桑石": ["蓝", "紫蓝", "蓝紫"],
                    "其它": ["褐色", "黄绿色", "粉色"]
                },
                "光泽": "玻璃光泽",
                "解理": "一组完全解理",
                "摩氏硬度": 8,
                "密度": "3.35 (+0.10/-0.25) g/cm3",
                "光性特征": "非均质体，二轴晶，正光性",
                "多色性": {
                    "坦桑石": ["蓝色", "紫红色", "绿黄色"],
                    "褐色": ["绿色", "紫色", "浅蓝色"],
                    "黄绿色": ["暗蓝色", "黄绿色", "紫色"]
                },
                "折射率": "1.691–1.700 (±0.005)",
                "双折射率": "0.008–0.013",
                "紫外荧光": "无",
                "吸收光谱": {
                    "蓝色": ["595 nm", "528 nm"],
                    "黄色": ["455 nm"]
                },
                "放大检查": ["气液包体", "阳起石包体", "石墨包体", "十字石包体"],
                "特殊光学效应": ["猫眼效应(稀少)"],
                "附加说明": "绿色黝帘石常与红宝石晶体及黑色角闪石共生..."
            },
            "treatments": {
                "热处理": "褐色调黝帘石加热后产生紫蓝色，稳定，不可测",
                "覆膜处理": "表面覆上蓝色薄膜，放大检查可见薄膜脱落"
            }
        }
    }
    """
    try:
        data = request.get_json()
        gem_name = data.get('gem_name')

        if not gem_name:
            return jsonify({
                'code': 400,
                'message': '宝石名称不能为空',
                'data': {}
            }), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({
                'code': 500,
                'message': '数据库连接失败',
                'data': {}
            }), 500

        with conn.cursor() as cursor:
            query = """
                   SELECT id, gem_name, basic_info, material_properties, treatments
                   FROM gems_info 
                   WHERE gem_name = %s
               """
            cursor.execute(query, (gem_name,))

            # 获取列名
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()

        conn.close()

        if not row:
            return jsonify({
                'code': 404,
                'message': f'未找到宝石: {gem_name}',
                'data': {}
            }), 404

        # 手动将元组转换为字典
        result_dict = dict(zip(columns, row))


        # 处理JSON字段
        processed_result = {
            'id': result_dict.get('id'),
            'gem_name': result_dict.get('gem_name')
        }

        # 解析JSON字段
        try:
            # basic_info
            basic_info = result_dict.get('basic_info')
            if basic_info and isinstance(basic_info, str):
                processed_result['basic_info'] = json.loads(basic_info)
            else:
                processed_result['basic_info'] = basic_info or {}

            # material_properties
            material = result_dict.get('material_properties')
            if material and isinstance(material, str):
                processed_result['material_properties'] = json.loads(material)
            else:
                processed_result['material_properties'] = material or {}

            # treatments
            treatments = result_dict.get('treatments')
            if treatments and isinstance(treatments, str):
                processed_result['treatments'] = json.loads(treatments)
            else:
                processed_result['treatments'] = treatments or {}

        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            # 如果解析失败，返回原始数据
            processed_result.update({
                'basic_info': result_dict.get('basic_info'),
                'material_properties': result_dict.get('material_properties'),
                'treatments': result_dict.get('treatments')
            })

        return jsonify({
            'code': 200,
            'message': '查询成功',
            'data': processed_result
        })

    except Exception as e:
        print(f"接口错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        }), 500


# 获得根据宝石名获得宝石的特定详细信息属性
@app.route('/gems/gems_property', methods=['POST'])
def get_gem_property():
    """
    获取宝石的特定属性

    请求参数:
    {
        "gem_name": "红宝石",
        "property_type": "material_properties",  # basic_info, material_properties, treatments
        "property_keys": ["化学成分", "摩氏硬度", "密度"]  # 可选，指定要获取的属性
    }
    """
    try:
        data = request.get_json()

        gem_name = data.get('gem_name')
        property_type = data.get('property_type', 'material_properties')
        property_keys = data.get('property_keys', [])

        if not gem_name:
            return jsonify({
                'code': 400,
                'message': '宝石名称不能为空',
                'data': {}
            }), 400

        # 验证property_type
        valid_types = ['basic_info', 'material_properties', 'treatments']
        if property_type not in valid_types:
            return jsonify({
                'code': 400,
                'message': f'属性类型必须是: {", ".join(valid_types)}',
                'data': {}
            }), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({
                'code': 500,
                'message': '数据库连接失败',
                'data': {}
            }), 500

        with conn.cursor() as cursor:
            # 查询指定的JSON字段
            query = f"""
                SELECT {property_type}
                FROM gems_info 
                WHERE gem_name = %s
            """

            cursor.execute(query, (gem_name,))

            # 获取列名
            columns = [desc[0] for desc in cursor.description]
            result_tuple = cursor.fetchone()

        conn.close()

        if not result_tuple:
            return jsonify({
                'code': 404,
                'message': f'未找到宝石: {gem_name}',
                'data': {}
            }), 404

        # 将元组转换为字典
        result = {}
        if len(columns) > 0 and len(result_tuple) > 0:
            result[columns[0]] = result_tuple[0]

        # print(f"查询结果: {result}")
        # print(f"结果类型: {type(result)}")

        # 解析JSON
        json_str = result.get(property_type) if isinstance(result, dict) else None
        if not json_str:
            return jsonify({
                'code': 200,
                'message': '该宝石没有对应的属性数据',
                'data': {}
            })

        try:
            properties = json.loads(json_str)

            # 如果指定了要获取的key，则只返回这些key
            if property_keys:
                filtered_properties = {}
                for key in property_keys:
                    if key in properties:
                        filtered_properties[key] = properties[key]
                properties = filtered_properties

            return jsonify({
                'code': 200,
                'message': '查询成功',
                'data': {
                    'gem_name': gem_name,
                    'property_type': property_type,
                    'properties': properties
                }
            })

        except json.JSONDecodeError as e:
            return jsonify({
                'code': 500,
                'message': '数据格式错误',
                'data': {}
            }), 500

    except Exception as e:
        print(f"属性查询接口错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "API 未找到"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error("内部服务器错误", exc_info=True)
    return jsonify({"error": "内部服务器错误"}), 500


# 语音识别端点（百度语音识别）
@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    """语音转文字API接口 - 使用百度语音识别"""
    try:
        if 'audio' in request.files:
            file = request.files['audio']

            # 读取文件内容
            file_data = file.read()

            # 检查文件是否是PCM格式
            if file.filename.endswith('.pcm'):
                # 直接处理PCM数据
                audio_base64 = base64.b64encode(file_data).decode('utf-8')

                # 调用百度语音识别
                result = recognize_speech(
                    audio_base64=audio_base64,
                    filename=file.filename
                )
                return jsonify(result)
            else:
                return jsonify({
                    'success': False,
                    'error': '只支持PCM格式音频, 且采样频率为16000'
                }), 400

    except Exception as e:
        app.logger.error(f"语音识别失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500


# 矿物基本信息：从 backendAdmin/mineral_data_test/矿物基本信息.csv 读取
def _get_mineral_info_csv_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base_dir, '..', 'backendAdmin', 'mineral_data_test', '矿物基本信息.csv'))


def _load_mineral_info_from_csv():
    path = _get_mineral_info_csv_path()
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


@app.route('/mineral/info', methods=['POST'])
def get_mineral_info():
    """矿物基本信息获取，仅从 矿物基本信息.csv 查询。"""
    try:
        data = request.get_json() or {}
        mineral_id = data.get('mineral_id')
        mineral_name = data.get('mineral_name')

        if not mineral_id and not mineral_name:
            return jsonify({
                'code': 400,
                'message': '请输入矿物ID或矿物名称',
                'data': {}
            }), 400

        csv_path = _get_mineral_info_csv_path()
        if not os.path.isfile(csv_path):
            app.logger.error(f"mineral/info: CSV 不存在: {csv_path}")
            return jsonify({
                'code': 500,
                'message': '矿物基本信息数据文件不存在',
                'data': {}
            }), 500

        rows = _load_mineral_info_from_csv()
        if not rows:
            return jsonify({
                'code': 404,
                'message': '未找到对应的矿物信息',
                'data': {}
            }), 404

        result = None
        if mineral_id is not None:
            sid = str(mineral_id).strip()
            for row in rows:
                if row.get('id', '').strip() == sid:
                    result = row
                    break
        else:
            name = (mineral_name or '').strip()
            for row in rows:
                if (row.get('中文名称') or '').strip() == name:
                    result = row
                    break

        if not result:
            return jsonify({
                'code': 404,
                'message': '未找到对应的矿物信息',
                'data': {}
            }), 404

        processed_result = {k: v for k, v in result.items() if v is not None and str(v).strip() != ''}

        return jsonify({
            'code': 200,
            'message': '查询成功',
            'data': processed_result
        })

    except Exception as e:
        app.logger.error(f"mineral/info 接口错误: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}',
            'data': {}
        }), 500


# mysql数据库连接
def get_db_connection():
    """创建数据库连接"""
    try:
        conn = mysql.connector.connect(**config.DB_CONFIG)
        return conn
    except Error as e:
        print(f"数据库连接错误: {e}")
        return None


# 应用启动
if __name__ == '__main__':
    init_services()
    print("\n" + "=" * 60)
    print("🚀 智能知识图谱问答系统 v3.0 正在启动...")
    print(f"📊 Neo4j 连接: {config.NEO4J_URI}")
    print(f"🤖 AI 模型: {config.AI_MODEL} ({config.AI_PROVIDER})")
    print(f"💾 缓存方式: {'Redis' if cache_manager.cache_enabled else '内存'}")
    print(f"⚡ 线程池: {config.MAX_WORKERS} 个工作线程")
    print("\n🌐 服务运行在: http://127.0.0.1:5000")
    print("📋 API 端点:")
    print("  - POST /ai/nl2cypher        (优化的自然语言到 Cypher)")
    print("  - POST /ai/rag              (优化的 RAG，带流式传输)")
    print("  - GET  /ai/schema           (获取数据库模式)")
    print("  - POST /ai/debug/*         (调试端点)")
    print("  - GET  /admin/*            (管理端点)")
    print("  - GET  /health              (健康检查)")
    print("  - POST /ai/mineral_dec       (矿物识别)")
    print("  - POST /mineral/info         (矿物基本信息)")
    print("  - POST /api/speech-to-text  (语音识别)")
    print("\n按 Ctrl+C 退出")
    print("=" * 60 + "\n")

    try:
        app.run(debug=False, port=5000, threaded=True)
        # app.run(host='0.0.0.0', debug=False, port=5001, threaded=True)
    except KeyboardInterrupt:
        print("\n正在关闭服务...")
        executor.shutdown(wait=True)
        driver.close()
        print("服务已安全关闭")
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        print(f"❌ 应用启动失败: {e}")
    finally:
        try:
            driver.close()
        except:
            pass
