from neo4j import GraphDatabase, basic_auth
import logging
import time

from config import config

logger = logging.getLogger(__name__)


def initialize_neo4j_driver():
    """Initialize and return the Neo4j driver with enhanced connection handling."""
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        print("用户:", config.NEO4J_USER, "密码:", config.NEO4J_PASSWORD)
        try:
            driver = GraphDatabase.driver(
                config.NEO4J_URI,
                auth=basic_auth(config.NEO4J_USER, config.NEO4J_PASSWORD),
                max_connection_lifetime=300,  # 5分钟后回收连接（缩短以避免超时）
                max_connection_pool_size=50,  # 连接池大小
                connection_acquisition_timeout=60,  # 获取连接超时时间（秒）
                keep_alive=True  # 启用TCP Keep-Alive
            )

            # 验证连接
            with driver.session() as session:
                session.run("RETURN 1").single()

            logger.info(f"Neo4j connection established successfully: URI={config.NEO4J_URI}")
            return driver

        except Exception as e:
            logger.warning(f"Neo4j connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                logger.error(f"Failed to connect to Neo4j after {max_retries} attempts: {e}")
                raise


driver = initialize_neo4j_driver()
