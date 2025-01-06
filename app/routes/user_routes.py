import json
from flask import request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from . import user_bp
from app.extensions import mysql

# 用户注册
@user_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = request.json.get('role', 'user')  # 默认注册为普通用户

        # 输入验证
        errors = []
        if not username or len(username) < 3:
            errors.append({"field": "username", "message": "Username must be at least 3 characters long."})
        if not email or "@" not in email:
            errors.append({"field": "email", "message": "Invalid email format."})
        if not password or len(password) < 8:
            errors.append({"field": "password", "message": "Password must be at least 8 characters long."})

        # 如果有错误，返回错误信息
        if errors:
            return jsonify({"error": "Validation Error", "details": errors}), 400

        # 判断用户是否已经存在
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if user:
            cur.close()
            return jsonify({"error": "Duplicate Error", "message": "用户名已存在，请重新输入！"}), 409

        # 对密码进行加密
        hashed_password = generate_password_hash(password)

        # 创建用户并保存到数据库
        cur.execute("INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                    (username, email, hashed_password, role))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "注册成功！", "role": role}), 201

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

# 管理员注册（专用接口）
@user_bp.route('/register/admin', methods=['POST'])
def register_admin():
    try:

        # 验证管理员密钥
        secret_key = request.headers.get('Admin-Secret-Key')
        if not secret_key:
            current_app.logger.warning("Missing admin secret key in request headers")
            return jsonify({"error": "Missing admin secret key"}), 400
            
        expected_key = current_app.config.get('ADMIN_SECRET_KEY')
        
        if secret_key != expected_key:
            return jsonify({"error": "Invalid admin secret key"}), 403

        # 获取注册信息
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # 验证必填字段
        if not all([username, email, password]):
            return jsonify({"error": "Missing required fields"}), 400

        # 检查用户名是否已存在
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            return jsonify({"error": "Username already exists"}), 409

        # 检查邮箱是否已存在
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({"error": "Email already exists"}), 409

        # 创建管理员用户
        hashed_password = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (username, email, hashed_password, 'admin')
        )
        mysql.connection.commit()
        cur.close()

        return jsonify({
            "message": "Admin registered successfully",
            "username": username
        }), 201

    except Exception as e:
        # current_app.logger.error(f"Error in admin registration: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/login', methods=['POST'])
def login():
    try:
        username = request.json.get('username')
        password = request.json.get('password')

        # 查找用户
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[3], password):  # 确保索引正确
            # 创建访问令牌（Access Token）
            access_token = create_access_token(
                identity=json.dumps({
                    'id': user[0],
                    'username': user[1],
                    'role': user[4] if len(user) > 4 else 'user'  # 添加默认角色
                })
            )

            # 创建刷新令牌（Refresh Token）
            refresh_token = create_refresh_token(
                identity=json.dumps({
                    'id': user[0],
                    'username': user[1],
                    'role': user[4] if len(user) > 4 else 'user'
                })
            )

            return jsonify({
                "message": "登录成功",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user[0],
                    "username": user[1],
                    "role": user[4] if len(user) > 4 else 'user'
                }
            }), 200
        else:
            if not user:
                current_app.logger.info("User not found")
            else:
                current_app.logger.info("Password incorrect")
            return jsonify({"message": "用户名或密码错误"}), 401

    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({"message": str(e)}), 500


@user_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        identity = get_jwt_identity()
        access_token = create_access_token(identity=identity)
        
        response = jsonify({"message": "Token refreshed successfully"})
        response.set_cookie(
            'access_token_cookie',
            access_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=24 * 60 * 60  # 24小时
        )
        
        return response, 200
    except Exception as e:
        return jsonify({"message": "Token refresh failed"}), 401