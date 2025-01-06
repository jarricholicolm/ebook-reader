from flask import Flask, render_template, redirect, url_for, request
from .extensions import mysql, jwt, cache, configure_jwt
from .models import create_tables
from .routes import user_bp, book_bp, progress_bp
import os
from dotenv import load_dotenv
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
import json
import logging

# 加载环境变量
load_dotenv()


def create_app():
    app = Flask(
        __name__,
        template_folder='../templates',  # 指定模板文件夹路径
        static_folder='../static'  # 指定静态文件夹路径
    )

    # 配置日志
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)

    # # 添加静态文件加载日志
    # @app.before_request
    # def log_request_info():
    #     app.logger.debug('Headers: %s', request.headers)
    #     app.logger.debug('Path: %s', request.path)
    #     if request.path.startswith('/static/'):
    #         app.logger.debug('Static file requested: %s', request.path)

    # 加载配置
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        app.config.from_object('app.config.ProductionConfig')
    else:
        app.config.from_object('app.config.DevelopmentConfig')


    # 初始化扩展
    mysql.init_app(app)
    jwt.init_app(app)
    configure_jwt(app)  # 配置JWT
    cache.init_app(app)

    # 在应用上下文中创建数据库表
    with app.app_context():
        create_tables(mysql)

    # 注册蓝图
    app.register_blueprint(user_bp)
    app.register_blueprint(book_bp)
    app.register_blueprint(progress_bp)

    # 页面路由
    @app.route('/')
    def home():
        try:
            # 检查是否存在有效的 JWT
            verify_jwt_in_request(optional=True)
            username = json.loads(get_jwt_identity()).get('username', None)
            if username:
                # 如果用户已登录，渲染个人首页
                return redirect(url_for('index'))
            else:
                # 如果未登录，渲染登录页面
                return render_template('login.html')
        except Exception:
            # 出现异常（如未登录）时，显示登录页面
            return render_template('login.html')

    @app.route('/index')
    @jwt_required()  # 添加JWT保护
    def index():
        try:
            # 获取查询参数
            category = request.args.get('category', 'all')
            sort_by = request.args.get('sort', 'recent')
            search = request.args.get('search', '')

            return render_template(
                'index.html',
                category=category,
                sort_by=sort_by,
                search=search,
                username=json.loads(get_jwt_identity())['username']
            )
        except Exception as e:
            print(f"Error in index route: {str(e)}")
            return redirect(url_for('login_page'))

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/register')
    def register_page():
        return render_template('register.html')

    # 注册阅读器路由
    @app.route('/reader/<int:book_id>')
    @jwt_required()
    def reader_page(book_id):
        try:
            # app.logger.debug('Loading reader page for book_id: %s', book_id)
            # app.logger.debug('Template folder: %s', app.template_folder)
            # app.logger.debug('Static folder: %s', app.static_folder)
            
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
            book = cur.fetchone()
            cur.close()
            
            if not book:
                app.logger.error('Book not found: %s', book_id)
                return "Book not found", 404
                
            # app.logger.debug('Book found: %s', book)
            # app.logger.debug('Rendering template with static files:')
            # app.logger.debug('- CSS: %s', url_for('static', filename='css/reader.css'))
            # app.logger.debug('- JS: %s', url_for('static', filename='js/reader.js'))
            
            return render_template('reader.html', book={
                'id': book[0],
                'title': book[1],
                'author': book[2]
            })
        except Exception as e:
            app.logger.error('Error in reader_page: %s', str(e))
            return str(e), 500

    @app.route('/admin/register')
    def admin_register_page():
        return render_template('admin_register.html')

    return app
