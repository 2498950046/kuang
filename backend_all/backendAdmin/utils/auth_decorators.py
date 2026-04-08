from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from backendAdmin.models.user import User


def token_required(f):
    """JWT Token 验证装饰器"""

    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # 验证 JWT
            verify_jwt_in_request()

            # 获取当前用户
            current_user_id = get_jwt_identity()

            # 验证用户是否存在且活跃
            user = User.query.get(current_user_id)
            if not user:
                return jsonify({
                    'success': False,
                    'message': '非管理员账户'
                }), 404

            if not user.is_active:
                return jsonify({
                    'success': False,
                    'message': '管理员账户已被禁用'
                }), 403

            # 将用户对象添加到请求上下文
            request.current_user = user

            return f(*args, **kwargs)

        except Exception as e:
            return jsonify({
                'success': False,
                'message': '身份验证失败',
                'error': str(e)
            }), 401

    return decorated
