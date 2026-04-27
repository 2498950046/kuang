from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from neo4j import GraphDatabase

from backendAdmin.config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
cors = CORS()

NEO4J_URI = Config.NEO4J_URI
NEO4J_USER = Config.NEO4J_USER
NEO4J_PASSWORD = Config.NEO4J_PASSWORD


def create_neo4j_driver():
    try:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )
        with driver.session() as session:
            session.run("RETURN 1")
        return driver
    except Exception as exc:
        print(f"neo4j connection failed: {exc}")
        return None


neo4j_driver = create_neo4j_driver()


def get_neo4j_driver():
    return neo4j_driver
