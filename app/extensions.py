from flask_mysqldb import MySQL
from flask_jwt_extended import JWTManager
from flask_caching import Cache

mysql = MySQL()
jwt = JWTManager()
cache = Cache()

# JWT配置
def configure_jwt(app):
    # 配置JWT从cookie中获取token
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # 开发环境关闭CSRF保护
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_COOKIE_SECURE'] = False  # 开发环境设置为False
    app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token_cookie'
    app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token_cookie'
    app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
