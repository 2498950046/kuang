import pandas as pd
from neo4j import GraphDatabase
import logging
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jCSVImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_constraints(self):
        """创建约束确保数据唯一性"""
        with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT specimen_id IF NOT EXISTS FOR (s:Specimen) REQUIRE s.name IS UNIQUE",
                "CREATE CONSTRAINT category_name IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
                "CREATE CONSTRAINT location_name IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
                "CREATE CONSTRAINT color_name IF NOT EXISTS FOR (c:Color) REQUIRE c.name IS UNIQUE",
                "CREATE CONSTRAINT year_value IF NOT EXISTS FOR (y:Year) REQUIRE y.name IS UNIQUE"
            ]
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"创建约束: {constraint}")
                except Exception as e:
                    logger.warning(f"约束可能已存在: {e}")

    def clean_string(self, input_str):
        """通用清理字符串函数，移除'（来自Deepseek）'等后缀"""
        if not input_str or pd.isna(input_str):
            return ''

        result = str(input_str).strip()

        # 移除各种"来自Deepseek"后缀
        patterns = [
            r'等（来自[^）]+）',
            r'等\(来自[^)]+\)',
            r'等来自[^;，,]*',
            r'（来自[^）]+）',
            r'\(来自[^)]+\)',
            r'来自[^;，,]*$'
        ]

        for pattern in patterns:
            result = re.sub(pattern, '', result)

        return result.strip()

    def clean_location_string(self, location_str):
        """清理产地字符串，移除'等（来自Deepseek）'等后缀"""
        if not location_str or pd.isna(location_str):
            return []

        # 清理字符串
        cleaned_str = self.clean_string(location_str)

        # 分割字符串
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

    def create_category_hierarchy_for_system(self, row_data, system_num):
        """创建指定分类体系的层级关系"""
        category_nodes = {}  # 存储该体系创建的节点

        with self.driver.session() as session:
            # 遍历该体系的所有层级（1-4级）
            for level in range(1, 5):
                col_name = f'标本分类{system_num}-{level}'

                # 检查该层级是否有数据
                if col_name in row_data and pd.notna(row_data[col_name]):
                    category_name = self.clean_string(row_data[col_name])

                    if category_name:
                        # 创建分类节点
                        query = """
                        MERGE (c:Category {name: $name})
                        SET c.level = $level, 
                            c.system = $system,
                            c.full_path = $full_path
                        RETURN c
                        """

                        # 构建完整路径
                        full_path_parts = []
                        for l in range(1, level + 1):
                            part_col = f'标本分类{system_num}-{l}'
                            if part_col in row_data and pd.notna(row_data[part_col]):
                                part_name = self.clean_string(row_data[part_col])
                                if part_name:
                                    full_path_parts.append(part_name)

                        full_path = " > ".join(full_path_parts) if full_path_parts else ""

                        result = session.run(query,
                                             name=category_name,
                                             level=level,
                                             system=f'system{system_num}',
                                             full_path=full_path)

                        # 保存节点引用
                        category_nodes[level] = category_name

                        # 如果存在父分类，创建关系
                        if level > 1 and (level - 1) in category_nodes:
                            parent_name = category_nodes[level - 1]

                            relation_query = """
                            MATCH (parent:Category {name: $parent_name, system: $system})
                            MATCH (child:Category {name: $child_name, system: $system})
                            MERGE (parent)-[r:HAS_SUBCATEGORY]->(child)
                            SET r.system = $system
                            """

                            session.run(relation_query,
                                        parent_name=parent_name,
                                        child_name=category_name,
                                        system=f'system{system_num}')

            # 返回该体系的叶子节点（最细分类）
            for level in range(4, 0, -1):
                if level in category_nodes:
                    return category_nodes[level]

        return None

    def connect_specimen_to_categories(self, specimen_name, row_data):
        """将标本连接到所有分类体系的叶子节点"""
        cleaned_name = self.clean_string(specimen_name)

        with self.driver.session() as session:
            # 遍历所有可能的分类体系（1, 2, 3）
            for system_num in ['1', '2', '3']:
                # 检查该体系是否有数据（至少有一级不为空）
                has_data = False
                leaf_category = None

                # 先找到该体系的叶子节点
                for level in range(4, 0, -1):
                    col_name = f'标本分类{system_num}-{level}'
                    if col_name in row_data and pd.notna(row_data[col_name]):
                        category_name = self.clean_string(row_data[col_name])
                        if category_name:
                            leaf_category = category_name
                            has_data = True
                            break

                if has_data and leaf_category:
                    # 连接到标本
                    query = """
                    MATCH (s:Specimen {name: $specimen_name})
                    MATCH (c:Category {name: $category_name, system: $system})
                    MERGE (s)-[r:BELONGS_TO]->(c)
                    SET r.system = $system,
                        r.connection_type = 'leaf'
                    """

                    try:
                        session.run(query,
                                    specimen_name=cleaned_name,
                                    category_name=leaf_category,
                                    system=f'system{system_num}')

                        logger.info(f"✅ 标本 '{cleaned_name}' 连接到体系{system_num}: {leaf_category}")
                    except Exception as e:
                        logger.warning(f"⚠️  连接体系{system_num}失败: {e}")

                    # 同时连接到该体系的所有层级节点
                    self.connect_to_all_levels(cleaned_name, row_data, system_num)

    def connect_to_all_levels(self, specimen_name, row_data, system_num):
        """将标本连接到指定体系的所有层级节点"""
        with self.driver.session() as session:
            for level in range(1, 5):
                col_name = f'标本分类{system_num}-{level}'
                if col_name in row_data and pd.notna(row_data[col_name]):
                    category_name = self.clean_string(row_data[col_name])

                    if category_name:
                        query = """
                        MATCH (s:Specimen {name: $specimen_name})
                        MATCH (c:Category {name: $category_name, system: $system})
                        MERGE (s)-[r:BELONGS_TO]->(c)
                        SET r.level = $level,
                            r.system = $system,
                            r.connection_type = 'direct'
                        """

                        try:
                            session.run(query,
                                        specimen_name=specimen_name,
                                        category_name=category_name,
                                        system=f'system{system_num}',
                                        level=level)
                        except Exception as e:
                            logger.warning(f"⚠️  连接到层级{level}失败: {e}")

    def process_specimen_categories(self, row_data, specimen_name):
        """处理标本的分类关系（完整流程）"""
        cleaned_name = self.clean_string(specimen_name)

        # 1. 为每个分类体系创建层级关系
        leaf_categories = {}  # 存储各体系的叶子节点

        for system_num in ['1', '2', '3']:
            # 检查该体系是否有数据
            has_data = False
            for level in range(1, 5):
                col_name = f'标本分类{system_num}-{level}'
                if col_name in row_data and pd.notna(row_data[col_name]):
                    category_name = self.clean_string(row_data[col_name])
                    if category_name:
                        has_data = True
                        break

            if has_data:
                # 创建该体系的层级关系
                leaf_category = self.create_category_hierarchy_for_system(row_data, system_num)
                if leaf_category:
                    leaf_categories[system_num] = leaf_category

        # 2. 将标本连接到各体系的叶子节点
        self.connect_specimen_to_categories(specimen_name, row_data)

    def create_year_node_and_relationship(self, specimen_name, year_value):
        """创建年份节点和关系"""
        if not year_value or pd.isna(year_value):
            return

        year_str = self.clean_string(year_value)
        if not year_str or year_str in ['暂无', '未知', '无', '暂无无年份信息']:
            return

        with self.driver.session() as session:
            # 创建年份节点
            year_query = """
            MERGE (y:Year {name: $year_value})
            """
            session.run(year_query, year_value=year_str)

            # 创建标本与年份的关系
            year_relation_query = """
            MATCH (s:Specimen {name: $specimen_name})
            MATCH (y:Year {name: $year_value})
            MERGE (s)-[:DISCOVERED_IN]->(y)
            """
            session.run(year_relation_query,
                        specimen_name=specimen_name,
                        year_value=year_str)

    def create_color_nodes_and_relationships(self, specimen_name, color_str):
        """创建颜色节点和关系"""
        if not color_str or pd.isna(color_str):
            return

        cleaned_color_str = self.clean_string(color_str)
        if not cleaned_color_str or cleaned_color_str in ['暂无', '未知', '无']:
            return

        colors = []

        # 分割颜色字符串
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
                # 创建颜色节点
                color_query = """
                MERGE (c:Color {name: $color_name})
                """
                session.run(color_query, color_name=color)

                # 创建标本与颜色的关系
                color_relation_query = """
                MATCH (s:Specimen {name: $specimen_name})
                MATCH (c:Color {name: $color_name})
                MERGE (s)-[:HAS_COLOR]->(c)
                """
                session.run(color_relation_query,
                            specimen_name=specimen_name,
                            color_name=color)

    def import_specimen_data(self, csv_file_path):
        """导入标本数据"""
        # 读取CSV文件
        df = pd.read_csv(csv_file_path, encoding='utf-8')
        logger.info(f"成功读取CSV文件，共{len(df)}条记录")

        # 显示列名
        logger.info(f"列名: {df.columns.tolist()}")
        logger.info(f"前3行数据:\n{df.head(3)}")

        # 创建约束
        self.create_constraints()

        with self.driver.session() as session:
            for index, row in df.iterrows():
                try:
                    specimen_name = row['中文名称'] if '中文名称' in row else f"标本_{index}"
                    logger.info(f"正在处理标本: {specimen_name}")

                    # 清理标本名称
                    cleaned_name = self.clean_string(specimen_name)

                    # 创建标本节点
                    specimen_query = """
                    MERGE (s:Specimen {name: $name})
                    SET s.english_name = $english_name,
                        s.chemical_formula = $chemical_formula,
                        s.description = $description
                    """

                    session.run(
                        specimen_query,
                        name=cleaned_name,
                        english_name=self.clean_string(row.get('英文名称', '')) if '英文名称' in row else '',
                        chemical_formula=self.clean_string(row.get('化学式', '')) if '化学式' in row else '',
                        description=self.clean_string(row.get('基本描述', '')) if '基本描述' in row else ''
                    )

                    # 处理标本的分类关系（支持多体系）
                    self.process_specimen_categories(row, cleaned_name)

                    # 创建产地节点和关系
                    if '产地' in row and pd.notna(row['产地']):
                        locations = self.clean_location_string(row['产地'])
                        logger.info(f"产地解析结果: {cleaned_name} -> {locations}")

                        for location in locations:
                            cleaned_location = self.clean_string(location)
                            if cleaned_location:
                                location_query = """
                                MERGE (l:Location {name: $location_name})
                                WITH l
                                MATCH (s:Specimen {name: $name})
                                MERGE (s)-[:FROM_LOCATION]->(l)
                                """
                                session.run(location_query,
                                            location_name=cleaned_location,
                                            name=cleaned_name)

                    # 创建颜色节点和关系
                    if '颜色' in row:
                        self.create_color_nodes_and_relationships(cleaned_name, row['颜色'])

                    # 创建年份节点和关系
                    if '发现年份' in row:
                        self.create_year_node_and_relationship(cleaned_name, row['发现年份'])

                    logger.info(f"成功导入标本: {cleaned_name}")

                except Exception as e:
                    logger.error(
                        f"导入标本 {specimen_name if 'specimen_name' in locals() else f'标本_{index}'} 时出错: {e}",
                        exc_info=True)
                    continue

def main():
    # Neo4j连接配置
    NEO4J_URI = "bolt://localhost:7688"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "12345678"

    # 初始化导入器
    importer = Neo4jCSVImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        csv_file = './mineral_data_test/矿物基本信息.csv'

        # 测试清理函数
        test_strings = [
            "德国、美国等（来自Deepseek）",
            "铁黑、暗灰色等（来自Deepseek）",
            "美国；印度（来自Deepseek）",
            "缅甸、斯里兰卡、泰国等（来自Deepseek）"
        ]

        for test_str in test_strings:
            cleaned = importer.clean_string(test_str)
            print(f"原始: '{test_str}' -> 清理后: '{cleaned}'")

        # 导入数据
        importer.import_specimen_data(csv_file)
        logger.info("数据导入完成！")

    except Exception as e:
        logger.error(f"导入过程中发生错误: {e}", exc_info=True)
    finally:
        importer.close()


if __name__ == "__main__":
    main()