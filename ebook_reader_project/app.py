from flask import Flask
from flask_mysqldb import MySQL

app = Flask(__name__)

# 配置 MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '159753HuangLan!'
app.config['MYSQL_DB'] = 'ebook_reader'

# 初始化 MySQL
mysql = MySQL(app)

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

# 首页路由
@app.route('/')
def index():
    return "Welcome to the eBook Reader App!"

# 添加用户路由
@app.route('/add_user')
def add_user():
    username = 'john_doe'
    email = 'john@example.com'
    password_hash = 'hashed_password'  # 这里最好使用加密库，如 bcrypt 来加密密码
    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, password_hash))
        mysql.connection.commit()
        print("User added successfully!")  # 打印日志
        return "User added!"
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}"
    finally:
        cur.close()

# 在应用启动时调用 create_tables
if __name__ == "__main__":
    with app.app_context():  # 手动推送应用上下文
        create_tables()  # 创建表
        add_user()
    app.run(debug=True)
