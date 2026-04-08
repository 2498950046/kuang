import openai
import re
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any, Generator

# 导入Neo4j图类型中缺失的模块
from neo4j.graph import Node, Relationship, Path

from config import config
from cache import cache_manager
from neo4j_driver import driver
from utils import generate_cache_key, process_graph_result, process_table_result

logger = logging.getLogger(__name__)

# 初始化AI客户端
client = openai.OpenAI(
    api_key=config.AI_API_KEY,
    base_url=config.AI_BASE_URL
)
logger.info(f"AI客户端已初始化: Provider={config.AI_PROVIDER}, Model={config.AI_MODEL}")

# 用于并行任务的线程池
executor = ThreadPoolExecutor(max_workers=config.MAX_WORKERS)


class OptimizedIntelligentAgent:
    def __init__(self):
        self.conversation_history = []
        self._schema_cache = None
        self._schema_cache_time = None

    def call_llm(self, messages: List[Dict], stream: bool = False, **kwargs):
        """调用大型语言模型"""
        try:
            params = {
                "model": config.AI_MODEL,
                "messages": messages,
                "temperature": config.AI_TEMPERATURE,
                "max_tokens": config.AI_MAX_TOKENS,
                "stream": stream
            }
            params.update(kwargs)

            return client.chat.completions.create(**params)
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def get_schema_cached(self) -> Dict:
        """获取带有内存缓存优化的缓存Schema"""
        if (self._schema_cache and self._schema_cache_time and
                (datetime.now() - self._schema_cache_time).seconds < 300):
            return self._schema_cache

        cache_key = "neo4j_schema"
        cached_schema = cache_manager.get(cache_key)
        if cached_schema:
            schema = json.loads(cached_schema)
            self._schema_cache = schema
            self._schema_cache_time = datetime.now()
            return schema

        try:
            logger.info("正在从数据库获取Schema")
            with driver.session() as session:
                # 修改节点查询，使用Cypher的TYPE函数替代
                node_query = """
                    CALL db.labels() YIELD label
                    CALL {
                    WITH label
                    MATCH (n) 
                    WHERE ANY(l IN labels(n) WHERE l = label)
                    WITH n
                    RETURN n
                    }
                    WITH label, n
                    UNWIND keys(n) AS propertyKey
                    WITH label, propertyKey, 
                        n[propertyKey] AS exampleValue
                    WHERE exampleValue IS NOT NULL
                    WITH label AS nodeLabel, propertyKey AS propertyName, exampleValue
                    RETURN nodeLabel,
                        propertyName,
                        // 使用内置函数判断类型
                        CASE 
                            WHEN exampleValue IS NULL THEN 'null'
                            WHEN toInteger(exampleValue) IS NOT NULL AND toString(toInteger(exampleValue)) = toString(exampleValue) THEN 'Integer'
                            WHEN toFloat(exampleValue) IS NOT NULL AND toString(toFloat(exampleValue)) = toString(exampleValue) THEN 'Float'
                            WHEN exampleValue IS true OR exampleValue IS false THEN 'Boolean'
                            WHEN date(toString(exampleValue)) IS NOT NULL THEN 'Date'
                            WHEN datetime(toString(exampleValue)) IS NOT NULL THEN 'DateTime'
                            WHEN duration(toString(exampleValue)) IS NOT NULL THEN 'Duration'
                            WHEN point(toString(exampleValue)) IS NOT NULL THEN 'Point'
                            ELSE 'String'
                        END AS dataType,
                        COLLECT(DISTINCT exampleValue)[..3] AS exampleValues,
                        COUNT(*) AS valueCount
                    ORDER BY nodeLabel, propertyName
                    """

                # 修改关系查询，使用Cypher的TYPE函数替代
                rel_query = """
                    CALL db.relationshipTypes() YIELD relationshipType
                    CALL {
                    WITH relationshipType
                    MATCH ()-[r]-()
                    WHERE type(r) = relationshipType
                    WITH r
                    RETURN r
                    }
                    WITH relationshipType, r
                    UNWIND keys(r) AS propertyKey
                    WITH relationshipType, propertyKey, 
                        r[propertyKey] AS exampleValue
                    WHERE exampleValue IS NOT NULL
                    WITH relationshipType AS relType, propertyKey AS propertyName, exampleValue
                    RETURN relType AS relationshipType,
                        propertyName,
                        // 使用内置函数判断类型
                        CASE 
                            WHEN exampleValue IS NULL THEN 'null'
                            WHEN toInteger(exampleValue) IS NOT NULL AND toString(toInteger(exampleValue)) = toString(exampleValue) THEN 'Integer'
                            WHEN toFloat(exampleValue) IS NOT NULL AND toString(toFloat(exampleValue)) = toString(exampleValue) THEN 'Float'
                            WHEN exampleValue IS true OR exampleValue IS false THEN 'Boolean'
                            WHEN date(toString(exampleValue)) IS NOT NULL THEN 'Date'
                            WHEN datetime(toString(exampleValue)) IS NOT NULL THEN 'DateTime'
                            WHEN duration(toString(exampleValue)) IS NOT NULL THEN 'Duration'
                            WHEN point(toString(exampleValue)) IS NOT NULL THEN 'Point'
                            ELSE 'String'
                        END AS dataType,
                        COLLECT(DISTINCT exampleValue)[..3] AS exampleValues,
                        COUNT(*) AS valueCount
                    ORDER BY relationshipType, propertyName
                    """

                try:
                    node_result = list(session.run(node_query))
                    rel_result = list(session.run(rel_query))
                except Exception as query_error:
                    logger.warning(f"详细Schema查询失败，使用简化查询: {query_error}")
                    # 更简化的查询
                    simple_node_query = """
                        CALL db.labels() YIELD label
                        MATCH (n)
                        WHERE ANY(l IN labels(n) WHERE l = label)
                        WITH label, n
                        UNWIND keys(n) AS propertyKey
                        RETURN DISTINCT label AS nodeLabel, propertyKey AS propertyName
                        ORDER BY nodeLabel, propertyName
                        """
                    simple_rel_query = """
                                MATCH ()-[r]->()
                                WITH DISTINCT type(r) AS relationshipType, 
                                     CASE 
                                         WHEN size(keys(r)) = 0 THEN ['无属性']
                                         ELSE keys(r)
                                     END AS allKeys
                                UNWIND allKeys AS propertyName
                                RETURN relationshipType, propertyName
                                ORDER BY relationshipType, propertyName
                        """
                    node_result = list(session.run(simple_node_query))
                    rel_result = list(session.run(simple_rel_query))

                # 自定义JSON序列化器处理Neo4j特殊类型
                def neo4j_json_serializer(obj):
                    """处理Neo4j特殊数据类型的JSON序列化"""
                    if hasattr(obj, 'isoformat'):
                        # 处理DateTime、Date、Time等时间类型
                        return obj.isoformat()
                    elif isinstance(obj, (bytes, bytearray)):
                        # 处理二进制数据
                        return obj.hex()
                    elif hasattr(obj, '__str__'):
                        # 处理其他Neo4j特殊类型
                        return str(obj)
                    else:
                        # 默认处理，如果还是无法序列化会抛出异常
                        return obj

                # 修复：正确聚合节点属性，并处理特殊数据类型
                nodes_schema = {}
                for record in node_result:
                    node_label = record.get("nodeLabel")
                    if not node_label:
                        continue

                    if node_label not in nodes_schema:
                        nodes_schema[node_label] = {
                            "nodeLabel": node_label,
                            "properties": []
                        }

                    # 获取数据类型（如果有）
                    data_type = record.get("dataType", "Unknown")

                    # 处理exampleValues中的特殊数据类型
                    example_values = record.get("exampleValues", [])
                    serialized_example_values = []
                    for value in example_values:
                        try:
                            serialized_value = neo4j_json_serializer(value)
                            serialized_example_values.append(serialized_value)
                        except Exception as e:
                            logger.warning(f"无法序列化示例值 {value}: {e}")
                            serialized_example_values.append(str(value))

                    # 添加属性到列表中
                    property_info = {
                        "propertyName": record.get("propertyName"),
                        "dataType": data_type,
                        "exampleValues": serialized_example_values,
                        "valueCount": int(record.get("valueCount", 1))
                    }
                    nodes_schema[node_label]["properties"].append(property_info)

                # 修复：正确聚合关系属性，并处理特殊数据类型
                relationships_schema = {}
                for record in rel_result:
                    rel_type = record.get("relationshipType")
                    if not rel_type:
                        continue

                    if rel_type not in relationships_schema:
                        relationships_schema[rel_type] = {
                            "relationshipType": rel_type,
                            "properties": []
                        }

                    # 获取数据类型（如果有）
                    data_type = record.get("dataType", "Unknown")

                    # 处理exampleValues中的特殊数据类型
                    example_values = record.get("exampleValues", [])
                    serialized_example_values = []
                    for value in example_values:
                        try:
                            serialized_value = neo4j_json_serializer(value)
                            serialized_example_values.append(serialized_value)
                        except Exception as e:
                            logger.warning(f"无法序列化示例值 {value}: {e}")
                            serialized_example_values.append(str(value))

                    # 添加属性到列表中
                    property_info = {
                        "propertyName": record.get("propertyName"),
                        "dataType": data_type,
                        "exampleValues": serialized_example_values,
                        "valueCount": int(record.get("valueCount", 1))
                    }
                    relationships_schema[rel_type]["properties"].append(property_info)

                schema = {
                    "nodes": nodes_schema,
                    "relationships": relationships_schema
                }

                # 记录调试信息
                total_node_properties = sum(len(node_data["properties"]) for node_data in nodes_schema.values())
                total_rel_properties = sum(len(rel_data["properties"]) for rel_data in relationships_schema.values())
                logger.info(f"Schema获取完成: {len(nodes_schema)}种节点类型, {total_node_properties}个节点属性, "
                            f"{len(relationships_schema)}种关系类型, {total_rel_properties}个关系属性")

                # 使用自定义序列化器缓存Schema
                try:
                    serialized_schema = json.dumps(schema, default=neo4j_json_serializer, ensure_ascii=False)
                    cache_manager.set(cache_key, serialized_schema, config.SCHEMA_CACHE_TTL)
                    self._schema_cache = schema
                    self._schema_cache_time = datetime.now()
                except Exception as serialization_error:
                    logger.error(f"Schema序列化失败: {serialization_error}")
                    # 即使序列化失败也返回schema，但不缓存
                    self._schema_cache = schema
                    self._schema_cache_time = datetime.now()

                return schema
        except Exception as e:
            logger.error(f"获取Schema失败: {e}")
            raise

    def generate_cypher_queries(self, question: str, schema: dict) -> List[Dict]:
        # def generate_cypher_queries(self, question: str, entities: dict, schema: dict) -> List[Dict]:
        """生成优化的Cypher查询"""
        # cache_key = generate_cache_key("cypher_gen", question, entities)
        cache_key = generate_cache_key("cypher_gen", question)
        cached_queries = cache_manager.get(cache_key)
        if cached_queries:
            logger.info("正在从缓存中获取Cypher查询")
            return json.loads(cached_queries)

        try:
            # Ensure 'name' is properly defined before using it in the Cypher query
            if 'name' not in locals():
                name = "默认值"  # Replace "默认值" with an appropriate default value or handle it dynamically

            # entities_str = json.dumps(entities, ensure_ascii=False, indent=2)
            # - **提取的实体**: {entities_str}
            schema_str = json.dumps(schema, ensure_ascii=False, indent=2)

            prompt = f'''
            # 角色
            你是Neo4j Cypher查询专家，专注于矿石数据库的自然语言查询转换。基于用户问题意图和数据库Schema，生成返回图格式结果的最优Cypher查询。

            ---

            ## 1. 知识图谱schema
            {schema_str}

            **重要节点说明**：
            - Specimen（标本）：核心实体，属性有name、english_name、era、loc、discovery_man
            - Location（地点）：产地信息
            - Category（分类）：矿石分类
            - Donor（捐赠者）：捐赠人信息
            - Year（年份）：年代信息

            **重要关系说明**（均为无属性关系）：
            - BELONGS_TO：标本属于分类
            - DISCOVERED_IN:标本与年份的关系
            - FROM_LOCATION：标本与地点的关系
            - DONATED_BY：标本与捐赠者的关系
            - HAS_SUBCATEGORY：分类之间的层级关系

            ---

            ## 2. 用户输入
            - **问题**: {question}

            ---

            ## 3. 查询生成规则

            ### 3.1 查询目标
            生成1个最匹配的Cypher查询，必须返回图格式：
            - 如果只查询单个节点：`RETURN n`
            - **只要在 MATCH 中使用了关系模式 `(n)-[:REL]->(m)`，就必须显式声明关系变量并返回：写成 `(n)-[r:REL]->(m)`，并在 RETURN 中包含 `r`，即 `RETURN n, r, m`。**

            ### 3.2 查询模式
            1. **单节点查询**：`MATCH (s:Specimen) WHERE ... RETURN s`
            2. **关联查询（必须显式写出关系变量 r 并在 RETURN 中返回）**：`MATCH (s:Specimen)-[r:REL_TYPE]->(x) WHERE ... RETURN s, r, x`
            3. **多关系查询**：使用`|`合并多个关系类型，如`[:BELONGS_TO|DISCOVERED_IN]`

            ### 3.3 条件匹配
            - **名称匹配**：`WHERE s.name CONTAINS '关键词'`
            - **精确匹配**：`WHERE s.name = '精确名称'`
            - **多条件**：使用`AND`连接，如`WHERE s.name CONTAINS '铁' AND s.loc CONTAINS '湖南'`
            - **年代匹配**：`WHERE s.era = '1996'`（era字段存储具体年份）

            ### 3.4 结果处理
            - **必须加LIMIT**：所有查询末尾加 `LIMIT 500`
            - **去重**：确保结果不重复
            - **性能**：优先使用简单查询，避免复杂嵌套

            ---

            ## 4. 示例查询

            ### 4.1 简单查询
            **问题**："查询磁铁矿标本"
            **查询**：`MATCH (s:Specimen) WHERE s.name CONTAINS '磁铁矿' RETURN s LIMIT 500`

            **问题**："查询1996年的矿石"
            **查询**：`MATCH (s:Specimen) WHERE s.era = '1996' RETURN s LIMIT 500`

            ### 4.2 关联查询（示例中都显式使用关系变量 r，并在 RETURN 中包含 r）
            **问题**："查询湖南的矿石及其产地"
            **查询**：`MATCH (s:Specimen)-[r:FROM_LOCATION]->(l:Location) WHERE s.loc CONTAINS '湖南' RETURN s, r, l LIMIT 500`

            **问题**："查询张三捐赠的标本"
            **查询**：`MATCH (s:Specimen)-[r:DONATED_BY]->(d:Donor) WHERE d.name CONTAINS '张三' RETURN s, r, d LIMIT 500`

            ### 4.3 综合查询
            **问题**："查询1996年在山东发现的铁矿"
            **查询**：`MATCH (s:Specimen)-[r:FROM_LOCATION]->(l:Location) WHERE s.era = '1996' AND s.loc CONTAINS '山东' AND s.name CONTAINS '铁' RETURN s, r, l LIMIT 500`

            ### 4.4 分类查询
            **问题**："查询金属矿物分类的标本"
            **查询**：`MATCH (s:Specimen)-[r:BELONGS_TO]->(c:Category) WHERE c.name CONTAINS '金属矿物' RETURN s, r, c LIMIT 500`

            ### 4.5 多关系查询
            **问题**："查询标本的完整信息"
            **查询**：`MATCH (s:Specimen)
                        OPTIONAL MATCH (s)-[r1:BELONGS_TO]->(c)
                        OPTIONAL MATCH (s)-[r2:FROM_LOCATION]->(l)
                        OPTIONAL MATCH (s)-[r3:DONATED_BY]->(d)
                        RETURN s, r1, r2, r3, c, l, d LIMIT 500`

            ---

            ## 5. 输出格式
            ```json
            {{
            "queries": [
                {{"purpose": "查询目的说明", "cypher": "MATCH ... RETURN ... LIMIT 500"}}
            ]
            }}

            关键要求：

                - **强制返回完整关联图结构**：对于任何搜索查询，如果匹配到任何节点，生成的Cypher查询**必须**通过 `OPTIONAL MATCH (matchedNode)-[r]-(relatedNode)` 的形式，来查找并返回这些匹配节点的所有直接关联边 `r` 及其相连的节点 `relatedNode`。最终的 `RETURN` 语句**必须**包含所有匹配到的节点、所有这些节点的直接关联边以及这些边连接到的所有相关节点（例如 `RETURN matchedNode, r, relatedNode`）。即使原始问题只提及节点，也应强制拓展查询以返回其完整的直接关联图谱。

                - 必须包含 `LIMIT 500`

                - 只生成 1 个最优查询

                - 不要额外解释，只返回 JSON
                '''

            # print(prompt)
            response = self.call_llm([
                {"role": "system", "content": "你是一位专业的Neo4j Cypher查询专家，专注于根据问题生成查询语句。"},
                {"role": "user", "content": prompt}
            ])
            # print(f'llm: {response}')
            result_text = response.choices[0].message.content.strip()

            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                queries_data = json.loads(json_match.group())

                if 'queries' in queries_data:
                    validated_queries = []
                    for query_info in queries_data['queries']:
                        cypher = query_info.get('cypher', '').strip()

                        if cypher:
                            cypher = self.validate_and_fix_cypher(cypher)
                            if cypher:
                                validated_queries.append({
                                    'purpose': query_info.get('purpose', '未知目的'),
                                    'cypher': cypher
                                })

                    queries_data['queries'] = validated_queries

                cache_manager.set(cache_key, json.dumps(queries_data, ensure_ascii=False), config.QUERY_CACHE_TTL)

                return queries_data['queries']
            else:
                raise ValueError("无法解析查询生成结果")

        except Exception as e:
            logger.error(f"Cypher查询生成失败: {e}")
            raise

    def validate_and_fix_cypher(self, cypher: str) -> str:
        """验证并修复Cypher查询"""
        try:
            cypher = re.sub(r'\s+', ' ', cypher).strip()

            if re.search(r'\bRETURN\s*$', cypher, re.IGNORECASE):
                if 'path' in cypher.lower():
                    cypher += ' path LIMIT 500'
                elif re.search(r'\b(p|person)\b.*\b(e|event)\b', cypher, re.IGNORECASE):
                    cypher += ' p, r, e LIMIT 500'
                elif re.search(r'\b(p|person)\b', cypher, re.IGNORECASE):
                    cypher += ' p LIMIT 500'
                else:
                    cypher += ' * LIMIT 500'

            elif not re.search(r'\bRETURN\b', cypher, re.IGNORECASE):
                if 'path' in cypher.lower():
                    cypher += ' RETURN path LIMIT 500'
                else:
                    cypher += ' RETURN * LIMIT 500'

            if not re.search(r'\bLIMIT\b', cypher, re.IGNORECASE):
                cypher += ' LIMIT 500'

            return cypher

        except Exception as e:
            logger.warning(f"Cypher修复失败: {e}")
            return ""

    def execute_cypher_query(self, cypher_query: str, max_retries: int = 3) -> Dict:
        """执行一个Cypher查询,带有重试机制，并在需要时自动补充节点之间的关系。

        行为说明：
        - 第一次严格按照传入的 Cypher 执行，得到原始结果；
        - 如果结果中包含节点但没有任何关系（links 为空），则自动再查一次这些节点之间的所有关系，
          并把补充出来的关系一起返回给前端。

        这样可以保证：
        - 你在 Cypher 里哪怕只 `RETURN` 节点（比如 `RETURN s, l`），前端依然能看到这些节点之间的边；
        - 和在 Neo4j Browser 图视图里查看“节点之间的关系”的体验一致。
        """
        global driver
        import time

        for attempt in range(max_retries):
            try:
                logger.info(f"正在执行Cypher查询 (尝试 {attempt + 1}/{max_retries}): {cypher_query}")

                with driver.session(default_access_mode='READ') as session:
                    result = session.run(cypher_query)
                    keys = result.keys()
                    records_list = list(result)

                    is_graph = any(
                        isinstance(value, (Node, Relationship, Path))
                        for record in records_list
                        for value in record.values()
                    )

                    if is_graph:
                        # 第一次按照原始结果处理
                        graph_data = process_graph_result(records_list)

                        # 如果有节点但没有任何关系，则自动补一次这些节点之间的关系
                        if graph_data.get("nodes") and not graph_data.get("links"):
                            try:
                                node_ids = [n["id"] for n in graph_data["nodes"]]
                                if node_ids:
                                    rel_query = """
                                    MATCH (a)-[r]-(b)
                                    WHERE elementId(a) IN $ids AND elementId(b) IN $ids
                                    RETURN r
                                    """
                                    rel_result = session.run(rel_query, ids=node_ids)
                                    rel_records = list(rel_result)
                                    if rel_records:
                                        # 基于「原始记录 + 关系记录」统一生成图数据
                                        combined = process_graph_result(records_list + rel_records)
                                        graph_data = combined
                                        logger.info(
                                            f"已为 {len(node_ids)} 个节点自动补充 "
                                            f"{len(graph_data.get('links', []))} 条关系"
                                        )
                            except Exception as auto_rel_error:
                                # 自动补关系失败不影响原始结果，只记录日志
                                logger.warning(f"自动补充关系时出错，将仅返回原始结果: {auto_rel_error}")

                        data = graph_data
                        result_type = "graph"
                    else:
                        data = process_table_result(keys, records_list)
                        result_type = "table"

                    logger.info(f"Cypher查询执行成功，返回 {len(records_list)} 条记录")
                    return {"success": True, "type": result_type, "data": data}

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Cypher执行尝试 {attempt + 1} 失败: {error_msg}")

                # 如果是连接错误，尝试重新初始化驱动
                if "ConnectionResetError" in error_msg or "Unable to retrieve routing" in error_msg:
                    if attempt < max_retries - 1:
                        logger.info("检测到连接问题，等待后重试...")
                        time.sleep(2 ** attempt)  # 指数退避: 1秒, 2秒, 4秒

                        try:
                            from neo4j_driver import initialize_neo4j_driver
                            driver = initialize_neo4j_driver()
                            logger.info("Neo4j驱动已重新初始化")
                        except Exception as reinit_error:
                            logger.error(f"重新初始化驱动失败: {reinit_error}")

                        continue
                    else:
                        logger.error(f"Cypher执行在 {max_retries} 次尝试后仍然失败: {error_msg}")
                        return {
                            "success": False,
                            "error": f"数据库连接错误，请稍后重试。详情: {error_msg}"
                        }
                else:
                    # 非连接错误，直接返回
                    logger.error(f"Cypher执行失败: {error_msg}")
                    return {"success": False, "error": error_msg}

        return {
            "success": False,
            "error": f"查询在 {max_retries} 次尝试后失败"
        }

    def execute_single_query(self, queries: List[Dict]) -> List[Dict]:
        """执行单个查询，返回结果列表，适配原有的格式"""
        # 检查传入的是否为列表，如果不是，则将其转换为一个单元素列表
        if isinstance(queries, dict):
            queries = queries['queries']

        if not queries:
            return []

        query_info = queries[0]
        result = self.execute_cypher_query(query_info['cypher'])

        if result['success']:
            return [{
                "purpose": query_info['purpose'],
                "data": result,
                "query": query_info['cypher']
            }]
        else:
            return []

    def format_all_context_data(self, context_data: List[Dict]) -> str:
        """简化版矿石信息格式化 - 适合LLM处理"""
        if not context_data:
            return "未找到相关信息。"

        all_specimens = []
        all_categories = []
        all_colors = []
        all_locations = []
        all_years = []

        for item in context_data:
            data = item.get("data", {})

            if data.get("type") == "graph":
                nodes = data.get("data", {}).get("nodes", [])

                # 收集各种类型的信息
                for node in nodes:
                    category = node.get("category", "")
                    name = node.get("name", "")
                    props = node.get("properties", {})

                    if category == "Specimen":
                        all_specimens.append({
                            "name": name,
                            "english_name": props.get("english_name", ""),
                            "chemical_formula": props.get("chemical_formula", ""),
                            "description": props.get("description", "")
                        })
                    elif category == "Category":
                        all_categories.append({
                            "name": name,
                            "level": props.get("level", ""),
                            "system": props.get("system", "")
                        })
                    elif category == "Color":
                        all_colors.append(name)
                    elif category == "Location":
                        all_locations.append(name)
                    elif category == "Year":
                        all_years.append(name)

        # 生成格式化文本
        if not all_specimens:
            return "未找到相关矿石标本信息。"

        formatted_parts = []
        formatted_parts.append("## 矿石标本查询结果")

        for i, specimen in enumerate(all_specimens):
            formatted_parts.append(f"\n### 标本 {i + 1}: {specimen.get('name', '未知')}")

            # 基本信息
            if specimen.get('english_name'):
                formatted_parts.append(f"- **英文名称**: {specimen['english_name']}")
            if specimen.get('chemical_formula'):
                formatted_parts.append(f"- **化学式**: {specimen['chemical_formula']}")

            # 关联信息
            if all_categories:
                formatted_parts.append("\n**分类信息**:")
                for cat in all_categories:
                    level_text = f" (级别{cat['level']})" if cat.get('level') else ""
                    system_text = f" [{cat['system']}]" if cat.get('system') else ""
                    formatted_parts.append(f"  - {cat['name']}{level_text}{system_text}")

            if all_colors:
                formatted_parts.append(f"\n**颜色**: {', '.join(all_colors)}")

            if all_locations:
                formatted_parts.append(f"\n**产地**: {', '.join(all_locations)}")

            if all_years:
                formatted_parts.append(f"\n**发现年份**: {', '.join(all_years)}")

            # 详细描述
            if specimen.get('description'):
                desc = specimen['description']
                if len(desc) > 600:
                    desc = desc[:600] + "..."
                formatted_parts.append(f"\n**详细描述**:\n{desc}")

        return "\n".join(formatted_parts)

    def unified_nl2cypher_and_rag(self, question: str, mode: str = "rag") -> Generator[Dict, None, None]:
        """统一的NL2Cypher和RAG处理流程"""
        logger.info(f"开始统一处理: {question}, 模式: {mode}")

        try:
            if mode == "rag":
                yield {"type": "step", "step": "处理", "message": "正在提取实体和获取Schema..."}

            schema_future = executor.submit(self.get_schema_cached)
            # entities_future = executor.submit(self.extract_entities_cached, question)

            schema = schema_future.result()
            # entities = entities_future.result()

            # if mode == "rag":
            # yield {"type": "entities", "data": entities}

            if mode == "rag":
                yield {"type": "step", "step": "生成查询策略", "message": "正在生成优化的检索查询..."}

            # queries = self.generate_cypher_queries(question, entities, schema)
            # print('=============>', schema)
            queries = self.generate_cypher_queries(question, schema)
            if isinstance(queries, dict) and 'queries' in queries:
                queries_list = queries['queries']
            else:
                queries_list = queries

            if mode == "rag":
                yield {"type": "retrieval_plan", "data": {"queries": queries}}

            if mode == "rag":
                yield {"type": "step", "step": "执行查询", "message": "正在执行检索查询..."}

            # 使用新的单次查询执行方法
            all_context_data = self.execute_single_query(queries)

            # if mode == "nl2cypher":
            #     if queries and all_context_data:
            #         first_query = queries[0]
            #         first_result = all_context_data[0] if all_context_data else None
            #         if first_result and first_result.get('data', {}).get('success'):
            #             return {
            #                 "success": True,
            #                 "question": question,
            #                 "cypher": first_query['cypher'],
            #                 "result": first_result['data'],
            #                 "attempts": 1
            #             }
            #     return {"success": False, "error": "无法生成有效的Cypher查询"}
            if mode == "nl2cypher":
                if queries_list and all_context_data:
                    first_query = queries_list[0]
                    first_result = all_context_data[0] if all_context_data else None
                    if first_result and first_result.get('data', {}).get('success'):
                        # 将 return 语句改为 yield，并添加 'complete' 类型以标识结束

                        # 构建回答提示：不再限制长度，不允许省略号
                        prompt_ans_short = f"""根据以下数据回答用户问题，请给出完整答案，不要省略，不要使用“等”“...”。

查询到的数据：
                        {first_result.get('data', '没有查询到信息')}

                        用户问题：{question}

要求：
1) 完整呈现关键信息（如化学式、名称等），不要截断或省略。
2) 如果数据不足以回答，就回答：抱歉，暂时无法回答此问题。
3) 直接给出答案，不要额外解释。
                        """

                        # 3. 非流式调用LLM
                        final_response = self.call_llm([
                            {"role": "system",
                             "content": "你是一位矿物专家助手。请根据提供的数据直接给出问题的简洁答案，不要解释，不要添加任何额外信息。"},
                            {"role": "user", "content": prompt_ans_short}
                        ], stream=False)

                        # 4. 处理响应并生成最终答案
                        try:
                            # 不再截断回答，前端需要完整展示
                            full_answer = final_response.choices[0].message.content.strip()
                        except Exception as e:
                            logger.error(f"提取回答时异常: {e}")
                            full_answer = "提取回答时出错"

                        yield {
                            "type": "complete",
                            "success": True,
                            "question": question,
                            "cypher": first_query['cypher'],
                            "result": first_result['data'],
                            "short_answer": full_answer,
                            "answer": full_answer,  # 兼容前端字段，返回完整答案
                            "attempts": 1
                        }
                        return  # 结束生成器

                # 将失败的 return 语句也改为 yield
                yield {"type": "error", "success": False, "error": "无法生成有效的Cypher查询"}
                return  # 结束生成器

            if all_context_data:
                yield {
                    "type": "retrieval_result",
                    "purpose": all_context_data[0]['purpose'],
                    "success": True,
                    "data": all_context_data[0]['data']
                }

            yield {"type": "step", "step": "组织上下文", "message": "正在组织所有检索到的信息..."}

            formatted_context = self.format_all_context_data(all_context_data)
            yield {"type": "context", "data": formatted_context}

            yield {"type": "step", "step": "生成专业回答", "message": "正在基于检索到的信息生成专业的回答..."}
            # print("all:==>", all_context_data)
            # print("format: ==>", formatted_context)
            final_prompt = f"""
                        你是一名地质矿物学数据分析助手，专门负责矿石标本信息查询和分析。你的任务是严格根据下方的[
                            查询到的数据]
                        来回答[用户问题]。

                [查询到的数据]
                {formatted_context}

                [用户问题]
                {question}

                [回答规则]
                1. ** 完全基于数据 **: 你的答案必须完全来自[查询到的数据]。不要使用你自己的任何背景知识或数据以外的信息。
                2. ** 直接引用 **: 在可能的情况下，直接从数据中提取信息来构建答案，如标本名称、产地、年代、分类等。
                3. ** 信息未找到 **: 如果[查询到的数据]
                中没有足够的信息来回答[用户问题]，你必须明确声明：“根据查询到的信息，无法回答此问题。”
                4. ** 简洁明了 **: 使用清晰、直接的语言来回答问题，避免冗长和不必要的描述。
                5. ** 良好格式 **: 适当地使用Markdown格式来突出重点，如表格、列表等。

                [重要指导]
                1. ** 数据准确性 **: 严格遵循提供的数据，确保所有标本名称、产地、年代、分类等信息的准确性。
                2. ** 信息完整 **: 应完整准确地提供所有相关信息，不用
                "等标本"、"等产地"
                来省略。
                3. ** 逻辑结构 **: 按以下顺序组织答案信息：
                - 标本基本信息（名称、英文名、年代、产地、发现人）
                - 分类信息（所属分类及层级）
                - 关联信息（产地详情、捐赠者信息）
                - 统计分析（如果有多个标本）
                4. ** 表格呈现 **: 如果有多个标本或需要对比信息，优先使用Markdown表格呈现。
                5. ** 科学严谨 **: 使用专业但易懂的地质矿物学术语，确保表述科学严谨。
                6. ** 关系分析 **: 分析标本与分类、产地、捐赠者之间的关系和关联。
                如果无结果：
                ## 查询结果

                ** 根据查询到的信息，无法回答此问题。 **

                请严格遵循上述规则和重要指导来生成你的答案: """

            final_response = self.call_llm([
                {"role": "system", "content": "你是一位专业的矿物专家，拥有深厚的矿物知识和丰富的研究经验。"},
                {"role": "user", "content": final_prompt}
            ], stream=True)

            full_answer = ""
            for chunk in final_response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_answer += content
                    yield {"type": "answer_chunk", "content": content, "full_content": full_answer,
                           "context": formatted_context}

            yield {
                "type": "complete",
                "final_answer": full_answer,
                "retrieved_context": formatted_context,
                "raw_context_data": all_context_data,
                "context": formatted_context,
            }

        except Exception as e:
            logger.error(f"统一处理流程失败: {e}")
            if mode == "rag":
                yield {"type": "error", "error": f"处理过程中发生错误: {str(e)}"}
            else:
                return {"success": False, "error": str(e)}


# 创建代理实例
agent = OptimizedIntelligentAgent()
