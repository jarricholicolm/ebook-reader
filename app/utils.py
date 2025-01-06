ALLOWED_EXTENSIONS = {'pdf', 'epub', 'mobi', 'djvu', 'azw3'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_allowed_extensions():
    """获取允许的文件扩展名列表"""
    return list(ALLOWED_EXTENSIONS)