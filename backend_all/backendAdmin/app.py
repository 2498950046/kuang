# app.py
from flask import Flask
from config import Config
from backendAdmin.extensions import db, bcrypt, jwt, cors
import routes.auth  # 导入路由
import routes.mineral  # 导入矿物管理路由


def create_app(config_class=Config):
    """创建Flask应用"""
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config_class)

    # 初始化扩展（只在这里初始化一次！）
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, supports_credentials=True)

    # 注册蓝图
    from routes.auth import auth_bp
    from routes.mineral import mineral_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(mineral_bp, url_prefix='/manage')

    # 使用标志位确保只初始化一次
    _database_initialized = False

    @app.before_request
    def initialize_database_once():
        """应用启动时初始化数据库（只执行一次）"""
        nonlocal _database_initialized
        if not _database_initialized:
            with app.app_context():
                try:
                    from sqlalchemy import text, inspect

                    # 检查连接
                    db.session.execute(text('SELECT 1'))
                    print("✅ 数据库连接正常")

                    # 检查 users 表是否存在
                    inspector = inspect(db.engine)
                    tables = inspector.get_table_names()

                    if 'users' not in tables:
                        print("🔄 users 表不存在，正在创建...")

                        # 使用原生 SQL 创建表
                        create_table_sql = """
                           CREATE TABLE users (
                               id INT AUTO_INCREMENT PRIMARY KEY,
                               username VARCHAR(80) UNIQUE NOT NULL,
                               email VARCHAR(120) UNIQUE NOT NULL,
                               password_hash VARCHAR(255) NOT NULL,
                               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                               is_active BOOLEAN DEFAULT TRUE
                           )
                           """

                        db.session.execute(text(create_table_sql))
                        db.session.commit()
                        print("✅ users 表创建完成")

                        # 创建测试用户
                        from extensions import bcrypt
                        from models.user import User

                        admin = User(
                            username='admin',
                            email='admin@example.com',
                            password='Admin@123456'
                        )

                        db.session.add(admin)
                        db.session.commit()
                        print("✅ 测试用户创建完成")

                    else:
                        print("✅ users 表已存在")

                    _database_initialized = True

                except Exception as e:
                    print(f"❌ 数据库初始化失败: {e}")
                    import traceback
                    traceback.print_exc()

    return app