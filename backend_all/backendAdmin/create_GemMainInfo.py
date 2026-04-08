# 1.宝石基本信息建表与导入(csv文件导入)
''''

USE mineral_database;

CREATE TABLE IF NOT EXISTS gems (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    type VARCHAR(100),
    image_url VARCHAR(500),
    color VARCHAR(20),
    info TEXT
);

-- 启用本地文件加载
SET GLOBAL local_infile=1;

LOAD DATA LOCAL INFILE 'D:/chrome_download/KGraphVis-main/backendAdmin/mineral_data_test/gemsBasicInfo.csv'
INTO TABLE gems
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

'''

# 2.宝石详细信息建表
"""
CREATE
TABLE
IF
NOT
EXISTS
gems_info(
    id
VARCHAR(50)
PRIMARY
KEY,
gem_name
VARCHAR(100)
NOT
NULL,
basic_info
JSON
COMMENT
'基本信息JSON',
material_properties
JSON
COMMENT
'材料性质JSON',
treatments
JSON
COMMENT
'优化处理JSON',
created_at
TIMESTAMP
DEFAULT
CURRENT_TIMESTAMP,
updated_at
TIMESTAMP
DEFAULT
CURRENT_TIMESTAMP
ON
UPDATE
CURRENT_TIMESTAMP
) ENGINE = InnoDB
DEFAULT
CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci;
"""

import json
import csv
import mysql.connector
import os


def create_gems_table():
    """创建 gems 表"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='123456',
            database='mineral_database',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # 创建 gems 表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS gems (
            id INT PRIMARY KEY,
            name VARCHAR(100),
            type VARCHAR(100),
            image_url VARCHAR(500),
            color VARCHAR(20),
            info TEXT
        ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        print("✅ gems 表创建成功")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 创建 gems 表出错: {e}")


def import_csv_to_gems_table(csv_file_path):
    """从 CSV 文件导入数据到 gems 表"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='123456',
            database='mineral_database',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # 检查文件是否存在
        if not os.path.exists(csv_file_path):
            print(f"❌ CSV 文件不存在: {csv_file_path}")
            return
        
        # 读取 CSV 文件
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            insert_sql = """
                INSERT INTO gems (id, name, type, image_url, color, info)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    type = VALUES(type),
                    image_url = VALUES(image_url),
                    color = VALUES(color),
                    info = VALUES(info)
            """
            
            count = 0
            for row in csv_reader:
                cursor.execute(insert_sql, (
                    int(row['id']),
                    row['name'],
                    row['type'],
                    row['image_url'],
                    row['color'],
                    row.get('info', '')
                ))
                count += 1
            
            conn.commit()
            print(f"✅ 成功导入 {count} 条记录到 gems 表")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 导入 CSV 数据出错: {e}")


def import_json_to_simple_table(json_file_path):
    """将JSON导入简化表"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='123456',
            database='mineral_database',
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        for gem in data:
            gem_id = gem.get('_id', {}).get('$oid', '')

            # 分离数据
            basic_info = {
                '标本名': gem.get('标本名', ''),
                '矿物名称': gem.get('矿物名称', ''),
                '英文名': gem.get('英文名', ''),
                '晶体化学式': gem.get('晶体化学式', ''),
                '标本分类': gem.get('标本分类', []),
                '产地': gem.get('产地', ''),
                '年代': gem.get('年代', ''),
                '编号': gem.get('编号', ''),
                '捐赠人': gem.get('捐赠人', ''),
                '标本描述': gem.get('标本描述', '')
            }

            sql = """
                INSERT INTO gems_info (id, gem_name, basic_info, material_properties, treatments)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    gem_name = VALUES(gem_name),
                    basic_info = VALUES(basic_info),
                    material_properties = VALUES(material_properties),
                    treatments = VALUES(treatments)
            """

            cursor.execute(sql, (
                gem_id,
                gem.get('标本名', ''),
                json.dumps(basic_info, ensure_ascii=False),
                json.dumps(gem.get('材料性质', {}), ensure_ascii=False),
                json.dumps(gem.get('优化处理', {}), ensure_ascii=False)
            ))

        conn.commit()
        print(f"成功导入 {len(data)} 条记录到简化表")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"导入出错: {e}")

if __name__ == '__main__':
    # 1.创建 gems 表
    print("=" * 60)
    print("开始创建 gems 表...")
    create_gems_table()
    
    # 2.导入 CSV 数据到 gems 表
    print("\n开始导入 CSV 数据到 gems 表...")
    csv_path = './mineral_data_test/gemsBasicInfo.csv'
    import_csv_to_gems_table(csv_path)
    
    # 3.导入宝玉石详细信息到mysql表 gems_info
    print("\n开始导入宝玉石详细信息到 gems_info 表...")
    import_json_to_simple_table('./mineral_data_test/mydb.baoshi.json')
    
    print("\n" + "=" * 60)
    print("✅ 所有操作完成！")
