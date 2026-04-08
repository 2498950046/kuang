# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from neo4j import GraphDatabase
import logging
from config import Config

# 创建全局唯一的扩展实例
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
cors = CORS()

# Neo4j配置
NEO4J_URI = Config.NEO4J_URI
NEO4J_USER = Config.NEO4J_USER
NEO4J_PASSWORD = Config.NEO4J_PASSWORD


# 创建Neo4j连接
def create_neo4j_driver():
    """创建Neo4j数据库连接"""
    try:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        # 测试连接
        with driver.session() as session:
            session.run("RETURN 1")
        print("✅ Neo4j连接成功")
        return driver
    except Exception as e:
        print(f"❌ Neo4j连接失败: {e}")
        return None


neo4j_driver = create_neo4j_driver()


def get_neo4j_driver():
    """获取Neo4j驱动实例"""
    return neo4j_driver
