# routes/mineral.py
from flask import Blueprint, request, jsonify, current_app
import logging
from sqlalchemy import or_
from backendAdmin.utils.auth_decorators import token_required
from backendAdmin.utils.validate import validate_classification_sequence

# 创建蓝图
mineral_bp = Blueprint('mineral', __name__)
logger = logging.getLogger(__name__)


@mineral_bp.route('/delete_mineral', methods=['POST'])
@token_required
def delete_mineral():
    user = request.current_user
    logger.info(f"操作人: {user.username}")
    """删除矿物信息接口"""
    try:
        data = request.get_json()

        # 检查必要字段
        if not data or '中文名称' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必要字段：中文名称'
            }), 400

        mineral_name = data['中文名称']

        # 导入Neo4j管理器
        from backendAdmin.extensions import get_neo4j_driver
        from backendAdmin.models.neo4j_models import Neo4jMineralManager

        driver = get_neo4j_driver()
        if not driver:
            return jsonify({
                'success': False,
                'message': 'Neo4j数据库连接失败'
            }), 500

        manager = Neo4jMineralManager(driver)

        deleted = manager.delete_mineral(mineral_name)

        if deleted:

            # 清楚缓存
            from backendAdmin.utils.cache_manager import cache_manager

            cache_clear = cache_manager.clear_all_graph_caches()
            logger.info(f"成功删除矿物: {mineral_name}")
            return jsonify({
                'success': True,
                'message': f'成功删除矿物: {mineral_name}',
                'cache_clear': cache_clear
            })
        else:
            return jsonify({
                'success': False,
                'message': f'未找到矿物: {mineral_name}'
            }), 404

    except Exception as e:
        logger.error(f"删除矿物时出错: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@mineral_bp.route('/add_mineral', methods=['POST'])
@token_required  # 需要管理员登录
def add_mineral():
    user = request.current_user
    """添加矿物信息接口"""
    try:
        data = request.get_json()

        # 检查必要字段
        required_fields = ['中文名称']
        for field in required_fields:
            if field not in data or data.get('中文名称') == '':
                return jsonify({
                    'success': False,
                    'message': f'缺少必要字段: {field}'
                }), 400

        flag, message = validate_classification_sequence(data)
        if not flag:
            return jsonify({
                'success': False,
                'message': message
            }), 400

        # 导入Neo4j管理器
        from backendAdmin.extensions import get_neo4j_driver
        from backendAdmin.models.neo4j_models import Neo4jMineralManager
        from backendAdmin.utils.cache_manager import cache_manager

        driver = get_neo4j_driver()
        if not driver:
            return jsonify({
                'success': False,
                'message': 'Neo4j数据库连接失败'
            }), 500

        manager = Neo4jMineralManager(driver)

        # 获取并清理数据
        mineral_data = {
            '中文名称': manager.clean_string(data.get('中文名称', '暂无名称')),
            '英文名称': manager.clean_string(data.get('英文名称', '')),
            '化学式': manager.clean_string(data.get('化学式', '')),
            '产地': data.get('产地', ''),
            '颜色': data.get('颜色', ''),
            '发现年份': data.get('发现年份', ''),
            '基本描述': manager.clean_string(data.get('基本描述', ''))
        }

        # 添加分类字段
        for i in range(1, 4):  # 三个分类体系
            for j in range(1, 5):  # 每个体系4个级别
                col_name = f'标本分类{i}-{j}'
                if col_name in data:
                    mineral_data[col_name] = manager.clean_string(data[col_name])

        # 检查是否已存在
        existing = manager.get_mineral_by_name(mineral_data['中文名称'])
        if existing:
            return jsonify({
                'success': False,
                'message': '矿物已存在，请使用修改接口进行更新'
            }), 400

        with manager.driver.session() as session:
            # 1. 创建标本节点
            specimen_query = """
            MERGE (s:Specimen {name: $name})
            SET s.english_name = $english_name,
                s.chemical_formula = $chemical_formula,
                s.description = $description,
                s.created_at = timestamp(),
                s.updated_at = timestamp()
            RETURN s
            """

            session.run(
                specimen_query,
                name=mineral_data['中文名称'],
                english_name=mineral_data['英文名称'],
                chemical_formula=mineral_data['化学式'],
                description=mineral_data['基本描述']
            )

            # 2. 创建分类体系并连接（修改部分）
            all_category_nodes = []  # 存储所有创建的分类节点

            for system_num in ['1', '2', '3']:
                system_key = f'system{system_num}'
                system_data = {}

                # 提取当前系统的所有分类字段
                for level in range(1, 5):
                    col_name = f'标本分类{system_num}-{level}'
                    system_data[col_name] = mineral_data.get(col_name, '')

                # 获取当前系统所有有效的分类节点
                category_nodes = manager.create_and_get_category_hierarchy(system_data, system_key)
                all_category_nodes.extend(category_nodes)

                # 连接标本与所有分类节点
                for category_info in category_nodes:
                    category_query = """
                    MATCH (s:Specimen {name: $specimen_name})
                    MATCH (c:Category {name: $category_name, system: $system})
                    MERGE (s)-[:BELONGS_TO]->(c)
                    """
                    session.run(category_query,
                                specimen_name=mineral_data['中文名称'],
                                category_name=category_info['name'],
                                system=category_info['system'])

            # 3. 创建并连接产地节点
            if mineral_data['产地']:
                locations = manager.create_location_nodes(mineral_data['产地'])
                for location in locations:
                    if location:
                        location_query = """
                        MATCH (s:Specimen {name: $specimen_name})
                        MATCH (l:Location {name: $location_name})
                        MERGE (s)-[:FROM_LOCATION]->(l)
                        """
                        session.run(location_query,
                                    specimen_name=mineral_data['中文名称'],
                                    location_name=location)

            # 4. 创建并连接颜色节点
            if mineral_data['颜色']:
                colors = manager.create_color_nodes(mineral_data['颜色'])
                for color in colors:
                    if color:
                        color_query = """
                        MATCH (s:Specimen {name: $specimen_name})
                        MATCH (c:Color {name: $color_name})
                        MERGE (s)-[:HAS_COLOR]->(c)
                        """
                        session.run(color_query,
                                    specimen_name=mineral_data['中文名称'],
                                    color_name=color)

            # 5. 创建并连接年份节点
            if mineral_data['发现年份']:
                year_value = manager.create_year_node(mineral_data['发现年份'])
                if year_value:
                    year_query = """
                    MATCH (s:Specimen {name: $specimen_name})
                    MATCH (y:Year {name: $year_value})
                    MERGE (s)-[:DISCOVERED_IN]->(y)
                    """
                    session.run(year_query,
                                specimen_name=mineral_data['中文名称'],
                                year_value=year_value)

            logger.info(f"成功添加矿物: {mineral_data['中文名称']}")
            cache_clear = cache_manager.clear_all_graph_caches()
            return jsonify({
                'success': True,
                'message': '矿物信息添加成功',
                'data': {
                    'name': mineral_data['中文名称'],
                    'english_name': mineral_data['英文名称'],
                    'chemical_formula': mineral_data['化学式'],
                    'category_nodes': len(all_category_nodes),
                    'cache_clear': cache_clear
                }
            })

    except Exception as e:
        logger.error(f"添加矿物时出错: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'添加失败: {str(e)}'
        }), 500


@mineral_bp.route('/get_mineral', methods=['POST'])
def get_mineral():
    """查询矿物信息接口"""
    try:
        data = request.get_json()

        # 检查必要字段
        if not data or '中文名称' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必要字段：中文名称'
            }), 400

        mineral_name = data['中文名称']

        # 导入Neo4j管理器
        from backendAdmin.extensions import get_neo4j_driver
        from backendAdmin.models.neo4j_models import Neo4jMineralManager

        driver = get_neo4j_driver()
        if not driver:
            return jsonify({
                'success': False,
                'message': 'Neo4j数据库连接失败'
            }), 500

        manager = Neo4jMineralManager(driver)
        mineral_data = manager.get_mineral_by_name(mineral_name)

        if mineral_data:
            return jsonify({
                'success': True,
                'message': '查询成功',
                'data': mineral_data
            })
        else:
            return jsonify({
                'success': False,
                'message': f'未找到矿物: {mineral_name}'
            }), 404

    except Exception as e:
        logger.error(f"查询矿物时出错: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@mineral_bp.route('/update_mineral', methods=['POST'])
def update_mineral():
    """修改矿物信息接口"""
    try:
        data = request.get_json()

        flag, message = validate_classification_sequence(data)
        if not flag:
            return jsonify({
                'success': False,
                'message': message
            }), 400

        # 检查必要字段
        required_fields = ['中文名称']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必要字段: {field}'
                }), 400

        # 导入Neo4j管理器
        from backendAdmin.extensions import get_neo4j_driver
        from backendAdmin.models.neo4j_models import Neo4jMineralManager
        from backendAdmin.utils.cache_manager import cache_manager

        driver = get_neo4j_driver()
        if not driver:
            return jsonify({
                'success': False,
                'message': 'Neo4j数据库连接失败'
            }), 500

        manager = Neo4jMineralManager(driver)

        # 获取并清理数据
        mineral_data = {
            '中文名称': manager.clean_string(data.get('中文名称', '')),
            '英文名称': manager.clean_string(data.get('英文名称', '')),
            '化学式': manager.clean_string(data.get('化学式', '')),
            '产地': data.get('产地', ''),
            '颜色': data.get('颜色', ''),
            '发现年份': data.get('发现年份', ''),
            '基本描述': manager.clean_string(data.get('基本描述', ''))
        }

        # 添加分类字段
        for i in range(1, 4):  # 三个分类体系
            for j in range(1, 5):  # 每个体系4个级别
                col_name = f'标本分类{i}-{j}'
                if col_name in data:
                    mineral_data[col_name] = manager.clean_string(data[col_name])

        # 检查矿物是否存在
        existing = manager.get_mineral_by_name(mineral_data['中文名称'])
        if not existing:
            return jsonify({
                'success': False,
                'message': '矿物不存在，请先添加该矿物'
            }), 404

        with manager.driver.session() as session:
            # 1. 更新标本节点
            specimen_query = """
            MATCH (s:Specimen {name: $name})
            SET s.english_name = $english_name,
                s.chemical_formula = $chemical_formula,
                s.description = $description,
                s.updated_at = timestamp()
            RETURN s
            """

            session.run(
                specimen_query,
                name=mineral_data['中文名称'],
                english_name=mineral_data['英文名称'],
                chemical_formula=mineral_data['化学式'],
                description=mineral_data['基本描述']
            )
            # 2. 删除旧的分类关系
            delete_category_query = """
            MATCH (s:Specimen {name: $name})-[r:BELONGS_TO]->(c:Category)
            DELETE r
            """
            session.run(delete_category_query, name=mineral_data['中文名称'])

            # 3. 创建新的分类体系并连接
            all_category_nodes = []  # 存储所有创建的分类节点

            for system_num in ['1', '2', '3']:
                system_key = f'system{system_num}'
                system_data = {}

                # 提取当前系统的所有分类字段
                for level in range(1, 5):
                    col_name = f'标本分类{system_num}-{level}'
                    system_data[col_name] = mineral_data.get(col_name, '')

                # 获取当前系统所有有效的分类节点（所有层级）
                category_nodes = manager.create_and_get_category_hierarchy(system_data, system_key)
                all_category_nodes.extend(category_nodes)

                # 连接标本与所有分类节点（包括上层）
                for category_info in category_nodes:
                    category_query = """
                    MATCH (s:Specimen {name: $specimen_name})
                    MATCH (c:Category {name: $category_name, system: $system})
                    MERGE (s)-[:BELONGS_TO]->(c)
                    """
                    session.run(category_query,
                                specimen_name=mineral_data['中文名称'],
                                category_name=category_info['name'],
                                system=category_info['system'])

            # 4. 删除旧的产地关系
            delete_location_query = """
            MATCH (s:Specimen {name: $name})-[r:FROM_LOCATION]->(l:Location)
            DELETE r
            """
            session.run(delete_location_query, name=mineral_data['中文名称'])

            # 5. 创建并连接新的产地节点
            if mineral_data['产地']:
                locations = manager.create_location_nodes(mineral_data['产地'])
                for location in locations:
                    if location:
                        location_query = """
                        MATCH (s:Specimen {name: $specimen_name})
                        MATCH (l:Location {name: $location_name})
                        MERGE (s)-[:FROM_LOCATION]->(l)
                        """
                        session.run(location_query,
                                    specimen_name=mineral_data['中文名称'],
                                    location_name=location)

            # 6. 删除旧的颜色关系
            delete_color_query = """
            MATCH (s:Specimen {name: $name})-[r:HAS_COLOR]->(c:Color)
            DELETE r
            """
            session.run(delete_color_query, name=mineral_data['中文名称'])

            # 7. 创建并连接新的颜色节点
            if mineral_data['颜色']:
                colors = manager.create_color_nodes(mineral_data['颜色'])
                for color in colors:
                    if color:
                        color_query = """
                        MATCH (s:Specimen {name: $specimen_name})
                        MATCH (c:Color {name: $color_name})
                        MERGE (s)-[:HAS_COLOR]->(c)
                        """
                        session.run(color_query,
                                    specimen_name=mineral_data['中文名称'],
                                    color_name=color)

            # 8. 删除旧的年份关系
            delete_year_query = """
            MATCH (s:Specimen {name: $name})-[r:DISCOVERED_IN]->(y:Year)
            DELETE r
            """
            session.run(delete_year_query, name=mineral_data['中文名称'])

            # 9. 创建并连接新的年份节点
            if mineral_data['发现年份']:
                year_value = manager.create_year_node(mineral_data['发现年份'])
                if year_value:
                    year_query = """
                    MATCH (s:Specimen {name: $specimen_name})
                    MATCH (y:Year {name: $year_value})
                    MERGE (s)-[:DISCOVERED_IN]->(y)
                    """
                    session.run(year_query,
                                specimen_name=mineral_data['中文名称'],
                                year_value=year_value)

            logger.info(f"成功更新矿物: {mineral_data['中文名称']}")
            cache_clear = cache_manager.clear_all_graph_caches()
            return jsonify({
                'success': True,
                'message': '矿物信息更新成功',
                'data': {
                    'name': mineral_data['中文名称'],
                    'english_name': mineral_data['英文名称'],
                    'chemical_formula': mineral_data['化学式'],
                    'cache_clear': cache_clear
                }
            })

    except Exception as e:
        logger.error(f"更新矿物时出错: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@mineral_bp.route('/get_all_minerals', methods=['GET'])
def get_all_minerals():
    """获取所有矿物列表接口"""
    try:
        # 导入Neo4j管理器
        from backendAdmin.extensions import get_neo4j_driver
        from backendAdmin.models.neo4j_models import Neo4jMineralManager

        driver = get_neo4j_driver()
        if not driver:
            return jsonify({
                'success': False,
                'message': 'Neo4j数据库连接失败'
            }), 500

        manager = Neo4jMineralManager(driver)
        minerals = manager.get_all_minerals()

        return jsonify({
            'success': True,
            'message': '查询成功',
            'data': minerals,
            'count': len(minerals)
        })

    except Exception as e:
        logger.error(f"获取所有矿物时出错: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500
