from fileinput import filename

from flask import Flask, request, jsonify, send_from_directory
from flask_mysqldb import MySQL
from sqlalchemy.sql.functions import current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# 配置文件上传
app.config['UPLOAD_FOLDER'] = 'D:/uploads/' #文件保存路径
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'epub'}

# 配置 MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '159753HuangLan!'
app.config['MYSQL_DB'] = 'ebook_reader'


# 初始化 MySQL
mysql = MySQL(app)

# 配置JWT
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
jwt = JWTManager(app)

# 创建数据库表的函数
def create_tables():
    cur = mysql.connection.cursor()

    # 创建用户表
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL
                )''')

    # 创建书籍表
    cur.execute('''CREATE TABLE IF NOT EXISTS books (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(100) NOT NULL,
                    cover_url VARCHAR(255),
                    description TEXT
                )''')

    # 创建阅读进度表
    cur.execute('''CREATE TABLE IF NOT EXISTS reading_progress (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    book_id INT NOT NULL,
                    progress FLOAT NOT NULL,
                    current_page INT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (book_id) REFERENCES books(id)
                )''')

    # 创建评论表
    cur.execute('''CREATE TABLE IF NOT EXISTS comments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    book_id INT NOT NULL,
                    content TEXT NOT NULL,
                    rating INT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (book_id) REFERENCES books(id)
                )''')

    # 提交事务
    mysql.connection.commit()
    cur.close()

# 用户注册接口
@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')

    #判断用户是否已经存在
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    if user:
        return jsonify({"message": "Duplicate username, please re-enter username!"}), 401
    else:
        # 对密码进行加密
        hashed_password = generate_password_hash(password)

        # 创建用户并保存到数据库
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, hashed_password))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "User created successfully!"}), 201

# 用户登录接口
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    # 查找用户
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    print(user[1], user[3])
    if user and check_password_hash(user[3], password):  # user[3]是存储密码的字段
        # 生成 JWT token
        access_token = create_access_token(identity=username)
        return jsonify({"access_token": access_token}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# 登录用户个人页面接口
@app.route('/profile',methods=['GET'])
@jwt_required()
def profile():
    # 获取当前用户的身份信息
    current_user = get_jwt_identity()
    return jsonify({"message": f"hello, {current_user}! This is your profile."}), 200

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# 书籍上传接口
@app.route('/upload_book', methods=['POST'])
def upload_book():
    # 检查请求中是否有文件
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']

    # 如果没有选择文件
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    # 文件类型检查
    if file and allowed_file(file.filename):
        # 使用 secure_filename 确保文件名安全
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # 保存文件
        try:
            file.save(filepath)
        except Exception as e:
            return jsonify({"message": f"Error saving file: {str(e)}"}), 500

        # 获取表单数据
        title = request.form.get('title')
        author = request.form.get('author')
        description = request.form.get('description')

        # 检查必要字段是否为空
        if not title or not author:
            return jsonify({"message": "Title and author are required!"}), 400

        # 将书籍元数据保存到数据库
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO books (title, author, cover_url, description) VALUES (%s, %s, %s, %s)",
                        (title, author, filepath, description))
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            return jsonify({"message": f"Error saving book data to database: {str(e)}"}), 500

        return jsonify({"message": "Book uploaded successfully!"}), 201
    else:
        return jsonify({"message": "Invalid file format"}), 400

# 书籍下载接口
@app.route('/download_book/<int:book_id>', methods=['GET'])
def download_book(book_id):
    # 查找书籍元数据
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cur.fetchone()
    cur.close()

    if book:
        filepath = book[3]
        filename = os.path.basename(filepath)
        return send_from_directory(app.config["UPLOAD_FOLDER"],filename)
    else:
        return jsonify({"message:", "Book not found"}), 404


# 获取书籍列表
@app.route('/books', methods=['GET'])
def get_books():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, title, author, cover_url FROM books")
    books = cur.fetchall()
    cur.close()

    book_list = []
    for book in books:
        book_data = {
            "id": book[0],
            "title": book[1],
            "author": book[2],
            "cover_url": book[3]
        }
        book_list.append(book_data)

    return jsonify(book_list), 200

# 更新保存阅读进度接口
@app.route('/update_progress', methods=['POST'])
@jwt_required()
def upate_progress():
    username = get_jwt_identity()
    book_id = request.json.get('book_id')
    progress = request.json.get('progress')
    current_page = request.json.get('current_page')

    if not book_id or progress is None or current_page is None:
        return jsonify({"message": "Missing required fields!"}), 400

    # 检查是否已有进度记录
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s ", (username,))
    user_id = cur.fetchone()[0]
    cur.execute("SELECT * FROM reading_progress WHERE user_id = %s AND book_id = %s", (user_id, book_id))
    existing_progress = cur.fetchone()

    if existing_progress:
        # 更新现有进度
        cur.execute('''UPDATE reading_progress 
                           SET progress = %s, current_page = %s 
                           WHERE user_id = %s AND book_id = %s''',
                    (progress, current_page, user_id, book_id))
    else:
        # 插入新进度
        cur.execute('''INSERT INTO reading_progress (user_id, book_id, progress, current_page) 
                           VALUES (%s, %s, %s, %s)''',
                    (user_id, book_id, progress, current_page))

    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Reading progress updated successfully!"}), 200



# 获取历史阅读进度接口
# 获取用户的阅读历史（包括书籍进度）
@app.route('/reading_history', methods=['GET'])
@jwt_required()  # 确保用户已登录
def reading_history():
    username = get_jwt_identity()  # 获取当前用户的身份信息
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s ", (username,))
    user_id = cur.fetchone()[0]

    # 获取该用户的所有阅读进度记录
    cur.execute('''SELECT b.id, b.title, b.author, rp.progress, rp.current_page 
                   FROM reading_progress rp
                   JOIN books b ON rp.book_id = b.id
                   WHERE rp.user_id = %s''', (user_id,))
    history = cur.fetchall()
    cur.close()

    # 格式化输出
    reading_history = []
    for record in history:
        book_data = {
            "book_id": record[0],
            "title": record[1],
            "author": record[2],
            "progress": record[3],
            "current_page": record[4]
        }
        reading_history.append(book_data)

    return jsonify({"reading_history": reading_history}), 200


# 首页路由
@app.route('/')
def index():
    return "Welcome to the eBook Reader App!"

# # 添加用户路由
# @app.route('/add_user')
# def add_user():
#     username = 'john_doe'
#     email = 'john@example.com'
#     password_hash = 'hashed_password'  # 这里最好使用加密库，如 bcrypt 来加密密码
#     cur = mysql.connection.cursor()
#     try:
#         cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
#                     (username, email, password_hash))
#         mysql.connection.commit()
#         print("User added successfully!")  # 打印日志
#         return "User added!"
#     except Exception as e:
#         print(f"Error: {e}")
#         return f"Error: {e}"
#     finally:
#         cur.close()

# 在应用启动时调用 create_tables
if __name__ == "__main__":
    with app.app_context():  # 手动推送应用上下文
        create_tables()  # 创建表
        #add_user()
    app.run(debug=True)
