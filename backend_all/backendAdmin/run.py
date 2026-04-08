# run.py
import os
from dotenv import load_dotenv
from app import create_app

# 加载环境变量
load_dotenv()

# 创建应用
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))

    print("=" * 50)
    print(f"🚀 Flask 应用启动")
    print(f"📍 地址: http://localhost:{port}")
    print(f"📁 数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("=" * 50)

    app.run(host='0.0.0.0', port=port, debug=True,use_reloader=False)