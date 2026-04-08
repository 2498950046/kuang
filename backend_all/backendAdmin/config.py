# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-dev-key-change'

    # 数据库配置 (请确保你本地 MySQL 的密码是 123456，并且提前建好了名为 mineral_database 的空数据库)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'mysql+pymysql://root:123456@localhost/mineral_database'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True  # 显示SQL语句，调试用

    # JWT配置
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时

    # redis地址 (默认你的本地 Redis 运行在 6379 端口)
    REDIS_URL = 'redis://localhost:6379/0'

    # neo4j 配置 (已将端口修改为刚才新建容器的 7688 端口)
    NEO4J_URI = "bolt://localhost:7688"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "12345678"