# models/neo4j_models.py
import logging
import re
import pandas as pd


class Neo4jMineralManager:
    def __init__(self, driver):
        self.driver = driver
        self.logger = logging.getLogger(__name__)

    def close(self):
        """关闭Neo4j连接"""
        if self.driver:
            self.driver.close()

    def clean_string(self, input_str):
        """清理字符串函数"""
        if not input_str or pd.isna(input_str):
            return ''

        result = str(input_str).strip()
        # 移除多余的空格和空白字符
        result = re.sub(r'\s+', ' ', result)
        return result

    def clean_location_string(self, location_str):
        """清理产地字符串"""
        if not location_str or pd.isna(location_str):
            return []

        cleaned_str = self.clean_string(location_str)
        if not cleaned_str:
            return []

        locations = []
        # 先用分号分割
        parts = re.split(r'[;；]', cleaned_str)
        for part in parts:
            # 再用顿号、逗号分割
            sub_locations = re.split(r'[、，,]', part)
            for loc in sub_locations:
                loc = loc.strip()
                if loc and loc not in ['暂无', '未知', '无', '等']:
                    locations.append(loc)

        return list(set(locations))  # 去重

    def create_category_hierarchy(self, category_data, system='system1'):
        """创建分类层级关系"""
        with self.driver.session() as session:
            for i in range(1, 5):
                col_name = f'标本分类{system[-1]}-{i}'
                if col_name in category_data and category_data[col_name]:
                    category_name = self.clean_string(category_data[col_name])
                    if category_name:
                        # 创建分类节点
                        query = """
                        MERGE (c:Category {name: $category_name})
                        SET c.level = $level, c.system = $system
                        RETURN c
                        """
                        session.run(query,
                                    category_name=category_name,
                                    level=i,
                                    system=system)

                        # 如果有父分类，创建关系
                        if i > 1:
                            parent_col = f'标本分类{system[-1]}-{i - 1}'
                            if parent_col in category_data and category_data[parent_col]:
                                parent_name = self.clean_string(category_data[parent_col])
                                if parent_name:
                                    relation_query = """
                                    MATCH (parent:Category {name: $parent_name, system: $system})
                                    MATCH (child:Category {name: $child_name, system: $system})
                                    MERGE (parent)-[:HAS_SUBCATEGORY]->(child)
                                    """
                                    session.run(relation_query,
                                                parent_name=parent_name,
                                                child_name=category_name,
                                                system=system)

            # 返回最细的分类（叶子节点）
            for i in range(4, 0, -1):
                col_name = f'标本分类{system[-1]}-{i}'
                if col_name in category_data and category_data[col_name]:
                    category_name = self.clean_string(category_data[col_name])
                    if category_name:
                        return category_name
            return None

    def create_year_node(self, year_value):
        """创建年份节点"""
        if not year_value:
            return None

        year_str = self.clean_string(year_value)
        if not year_str or year_str in ['暂无', '未知', '无', '暂无无年份信息']:
            return None

        with self.driver.session() as session:
            query = "MERGE (y:Year {name: $year_value}) RETURN y"
            result = session.run(query, year_value=year_str)
            return year_str if result.single() else None

    def create_color_nodes(self, color_str):
        """创建颜色节点"""
        if not color_str:
            return []

        cleaned_color_str = self.clean_string(color_str)
        if not cleaned_color_str or cleaned_color_str in ['暂无', '未知', '无']:
            return []

        colors = []
        # 先按中文逗号分割
        parts = re.split(r'[，,]', cleaned_color_str)
        for part in parts:
            # 再按顿号分割
            sub_parts = re.split(r'[、]', part)
            for color in sub_parts:
                color = color.strip()
                if color and color not in ['暂无', '未知', '无', '等']:
                    colors.append(color)

        colors = list(set(colors))  # 去重

        with self.driver.session() as session:
            for color in colors:
                query = "MERGE (c:Color {name: $color_name})"
                session.run(query, color_name=color)

        return colors

    def create_location_nodes(self, location_str):
        """创建产地节点"""
        if not location_str:
            return []

        locations = self.clean_location_string(location_str)

        with self.driver.session() as session:
            for location in locations:
                cleaned_location = self.clean_string(location)
                if cleaned_location:
                    query = "MERGE (l:Location {name: $location_name})"
                    session.run(query, location_name=cleaned_location)

        return locations

    def get_mineral_by_name(self, chinese_name):
        """根据中文名称查询矿物信息"""
        with self.driver.session() as session:
            # 查询标本基本信息
            query = """
            MATCH (s:Specimen {name: $name})
            OPTIONAL MATCH (s)-[:BELONGS_TO]->(c:Category)
            OPTIONAL MATCH (s)-[:FROM_LOCATION]->(l:Location)
            OPTIONAL MATCH (s)-[:HAS_COLOR]->(color:Color)
            OPTIONAL MATCH (s)-[:DISCOVERED_IN]->(y:Year)
            RETURN s.name as 中文名称,
                   s.english_name as 英文名称,
                   s.chemical_formula as 化学式,
                   s.description as 基本描述,
                   collect(DISTINCT l.name) as 产地,
                   collect(DISTINCT color.name) as 颜色,
                   collect(DISTINCT y.name) as 发现年份,
                   collect(DISTINCT {system: c.system, name: c.name, level: c.level}) as 分类
            """

            result = session.run(query, name=self.clean_string(chinese_name))
            record = result.single()

            if not record:
                return None

            # 构建返回数据
            mineral_data = {
                '中文名称': record['中文名称'],
                '英文名称': record['英文名称'] if record['英文名称'] else '',
                '化学式': record['化学式'] if record['化学式'] else '',
                '基本描述': record['基本描述'] if record['基本描述'] else '',
                '产地': '、'.join(record['产地']) if record['产地'] else '',
                '颜色': '、'.join(record['颜色']) if record['颜色'] else '',
                '发现年份': record['发现年份'][0] if record['发现年份'] else '',
            }

            # 处理分类信息
            categories = record['分类']
            for cat in categories:
                if cat:
                    system_num = cat['system'][-1]  # system1 -> 1
                    level = cat['level']
                    mineral_data[f'标本分类{system_num}-{level}'] = cat['name']

            return mineral_data

    def delete_mineral(self, mineral_name):
        """删除矿物信息"""
        with self.driver.session() as session:
            # 删除标本节点及其所有关系
            delete_query = """
            MATCH (s:Specimen {name: $name})
            DETACH DELETE s
            RETURN count(s) as deleted_count
            """

            result = session.run(delete_query, name=self.clean_string(mineral_name))
            deleted_count = result.single()['deleted_count']
            return deleted_count > 0

    def get_all_minerals(self):
        """获取所有矿物列表"""
        with self.driver.session() as session:
            query = """
            MATCH (s:Specimen)
            OPTIONAL MATCH (s)-[:FROM_LOCATION]->(l:Location)
            RETURN s.name as 中文名称,
                   s.english_name as 英文名称,
                   s.chemical_formula as 化学式,
                   collect(DISTINCT l.name) as 产地,
                   s.description as 基本描述
            ORDER BY s.name
            """

            result = session.run(query)
            minerals = []

            for record in result:
                mineral = {
                    '中文名称': record['中文名称'],
                    '英文名称': record['英文名称'] if record['英文名称'] else '',
                    '化学式': record['化学式'] if record['化学式'] else '',
                    '产地': '、'.join(record['产地']) if record['产地'] else '',
                    '基本描述': record['基本描述'][:100] + '...' if record['基本描述'] and len(
                        record['基本描述']) > 100 else (record['基本描述'] if record['基本描述'] else '')
                }
                minerals.append(mineral)

            return minerals

    def create_and_get_category_hierarchy(self, system_data, system_key):
        """
        创建分类层级并返回所有有效的分类节点信息

        Args:
            system_data: 分类数据字典
            system_key: 系统标识符，如'system1'

        Returns:
            list: 所有创建的分类节点信息列表
        """
        all_categories = []

        with self.driver.session() as session:
            # 提取当前系统所有有效的分类值
            categories = []
            for level in range(1, 5):
                col_name = f'标本分类{system_key[-1]}-{level}'  # 从system1中提取1
                value = system_data.get(col_name, '')
                if value:  # 只处理非空值
                    categories.append({
                        'level': level,
                        'name': self.clean_string(value),
                        'col_name': col_name
                    })

            if not categories:
                return all_categories

            # 创建分类节点和层级关系
            prev_node = None
            for i, category in enumerate(categories):
                level = category['level']
                name = category['name']

                # 创建当前层级的节点
                create_query = """
                MERGE (c:Category {name: $name, system: $system, level: $level})
                SET c.created_at = timestamp(),
                    c.updated_at = timestamp()
                RETURN c
                """

                result = session.run(
                    create_query,
                    name=name,
                    system=system_key,
                    level=level
                )

                current_node = result.single()[0]
                all_categories.append({
                    'name': name,
                    'system': system_key,
                    'level': level
                })

                # 创建层级关系（如果有上一级）
                if prev_node is not None:
                    hierarchy_query = """
                    MATCH (parent:Category {name: $parent_name, system: $system})
                    MATCH (child:Category {name: $child_name, system: $system})
                    MERGE (parent)-[:HAS_SUBCATEGORY]->(child)
                    """
                    session.run(
                        hierarchy_query,
                        parent_name=prev_node['name'],
                        system=system_key,
                        child_name=name
                    )

                prev_node = category

            return all_categories

    def get_category_hierarchy_for_specimen(self, specimen_name, system_key):
        """
        获取标本在指定分类系统中的所有分类节点

        Args:
            specimen_name: 标本名称
            system_key: 系统标识符

        Returns:
            list: 分类节点列表
        """
        with self.driver.session() as session:
            query = """
            MATCH (s:Specimen {name: $specimen_name})-[:BELONGS_TO]->(c:Category {system: $system})
            RETURN c.name as name, c.level as level
            ORDER BY c.level
            """

            result = session.run(query, specimen_name=specimen_name, system=system_key)
            return [{'name': record['name'], 'level': record['level']} for record in result]

    def connect_specimen_to_all_categories(self, specimen_name, system_data, system_key):
        """
        将标本连接到指定分类系统的所有层级节点

        Args:
            specimen_name: 标本名称
            system_data: 分类数据字典
            system_key: 系统标识符
        """
        with self.driver.session() as session:
            # 获取所有有效的分类
            categories = []
            for level in range(1, 5):
                col_name = f'标本分类{system_key[-1]}-{level}'
                value = system_data.get(col_name, '')
                if value:
                    categories.append({
                        'level': level,
                        'name': self.clean_string(value)
                    })

            # 连接标本到每个分类节点
            for category in categories:
                connect_query = """
                MATCH (s:Specimen {name: $specimen_name})
                MATCH (c:Category {name: $category_name, system: $system})
                MERGE (s)-[:BELONGS_TO]->(c)
                """

                session.run(
                    connect_query,
                    specimen_name=specimen_name,
                    category_name=category['name'],
                    system=system_key
                )
