from flask import Blueprint

# 创建蓝图实例
user_bp = Blueprint('user', __name__, url_prefix='/api')
book_bp = Blueprint('book', __name__, url_prefix='/api')
progress_bp = Blueprint('progress', __name__, url_prefix='/api')
# 导入具体的路由模块
from .user_routes import *  # 用户相关路由
from .book_routes import *  # 书籍相关路由
from .progress_routes import *

# 导出所有蓝图
__all__ = ['user_bp', 'book_bp', 'progress_bp']