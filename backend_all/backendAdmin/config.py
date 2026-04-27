import os

from dotenv import load_dotenv

load_dotenv()


def _build_database_url():
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return database_url

    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '123456')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '3306')
    db_name = os.environ.get('DB_NAME', 'mineral_database')
    return f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-dev-key-change')
    SQLALCHEMY_DATABASE_URI = _build_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'false').lower() == 'true'
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7688')
    NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', '12345678')
