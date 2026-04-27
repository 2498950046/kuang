#!/bin/sh
set -eu

cd /app/backend_all

echo "Waiting for MySQL..."
python - <<'PY'
import os
import time

import mysql.connector

config = {
    "host": os.getenv("DB_HOST", "mysql"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "mineral_database"),
    "charset": os.getenv("DB_CHARSET", "utf8mb4"),
}

last_error = None
for _ in range(60):
    try:
        conn = mysql.connector.connect(**config)
        conn.close()
        print("MySQL is ready.")
        break
    except Exception as exc:
        last_error = exc
        time.sleep(5)
else:
    raise SystemExit(f"MySQL did not become ready: {last_error}")
PY

echo "Waiting for Neo4j..."
python - <<'PY'
import os
import time

from neo4j import GraphDatabase

uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "12345678")

last_error = None
for _ in range(60):
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        print("Neo4j is ready.")
        break
    except Exception as exc:
        last_error = exc
        time.sleep(5)
else:
    raise SystemExit(f"Neo4j did not become ready: {last_error}")
PY

echo "[1/2] Importing MySQL seed data..."
python backendAdmin/create_GemMainInfo.py

echo "[2/2] Importing Neo4j graph data..."
python backendAdmin/create_neo4j_fromMysql.py

echo "Data initialization completed."
