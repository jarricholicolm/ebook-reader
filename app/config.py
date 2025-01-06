import os
from datetime import timedelta
class Config:
    """基础配置类"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    
    # JWT配置
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    JWT_REFRESH_TOKEN_EXPIRES = 604800
    JWT_ERROR_MESSAGE_KEY = 'message'
    
    # MySQL配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')
    MYSQL_DB = os.getenv('MYSQL_DB', 'ebook_reader')
    
    # 缓存配置
    CACHE_TYPE = 'simple'  # 使用简单的内存缓存
    CACHE_DEFAULT_TIMEOUT = 300  # 缓存默认过期时间（秒）

    # 文件上传配置
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
    ALLOWED_EXTENSIONS = {'pdf', 'epub', 'mobi', 'azw3', 'djvu'}
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB 限制
    
    # 管理员配置
    ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'admin_secret_key')
    
    # OSS配置
    OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
    OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
    OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME')
    OSS_ENDPOINT = os.getenv('OSS_ENDPOINT')

    # 安装包配置
    KINDLE_UNPACK_PATH = os.getenv('KINDLE_UNPACK_PATH')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False