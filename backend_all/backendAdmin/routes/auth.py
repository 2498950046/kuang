# routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_
from datetime import timedelta, datetime

# 创建蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """登录接口"""
    try:
        # 1. 获取请求数据
        print("=== 收到登录请求 ===")

        # 支持多种传参方式
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        username = data.get('username')
        password = data.get('password')

        print(f"用户名: {username}, 密码: {'*' * len(password) if password else 0}")

        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码是必需的'
            }), 400

        # 2. 导入模型（在视图函数内部导入，避免循环导入）
        # ⚠️ 关键：确保在应用上下文中导入
        from backendAdmin.extensions import db
        from backendAdmin.models.user import User

        # 3. 查询用户
        user = User.query.filter(
            or_(User.username == username, User.email == username)
        ).first()

        print(f"查询结果: {user}")

        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404

        # 4. 验证密码
        if not user.check_password(password):
            return jsonify({
                'success': False,
                'message': '密码错误'
            }), 401

        # 5. 生成JWT令牌
        from backendAdmin.extensions import jwt
        from flask_jwt_extended import create_access_token

        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=1)
        )

        print("✅ 登录成功")

        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': user.to_dict(),
            'access_token': access_token
        }), 200

    except Exception as e:
        print(f"❌ 登录错误: {str(e)}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """注册接口"""
    try:
        data = request.get_json() or request.form

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not all([username, email, password]):
            return jsonify({'success': False, 'message': '请填写完整信息'}), 400

        # 导入模型
        from backendAdmin.extensions import db
        from backendAdmin.models.user import User

        # 检查用户是否已存在
        if User.query.filter((User.username == username) | (User.email == email)).first():
            return jsonify({'success': False, 'message': '用户名或邮箱已存在'}), 400

        # 创建用户
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '注册成功',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()  # 需要用户登录
def change_password():
    """修改密码接口 - 需要验证旧密码"""
    try:
        # 获取当前用户ID
        current_user_id = get_jwt_identity()

        # 获取请求数据
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400

        # 验证必需字段
        required_fields = ['old_password', 'new_password']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必要字段: {field}'
                }), 400

        old_password = data.get('old_password')
        new_password = data.get('new_password')

        # 验证密码强度
        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'message': '新密码长度至少8位'
            }), 400

        # 导入模型
        from backendAdmin.extensions import db
        from backendAdmin.models.user import User

        # 查询当前用户
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404

        # 验证旧密码
        if not user.check_password(old_password):
            return jsonify({
                'success': False,
                'message': '原密码错误'
            }), 401

        # 设置新密码
        user.set_password(new_password)

        # 更新修改时间
        if hasattr(user, 'updated_at'):
            from datetime import datetime
            user.updated_at = datetime.utcnow()

        # 保存到数据库
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '密码修改成功',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"修改密码失败: {e}")
        return jsonify({
            'success': False,
            'message': f'密码修改失败: {str(e)}'
        }), 500

