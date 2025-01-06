# 创建数据库表的函数
def create_tables(mysql):
    connection = mysql.connection
    cur = connection.cursor()

    # 删除现有的表（如果存在）
    # cur.execute('''DROP TABLE IF EXISTS comments, reading_progress, books, categories, users''')

    # 创建用户表
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role ENUM('user', 'admin') DEFAULT 'user'
                )''')

    # 创建分类表
    cur.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT
        )''')

    # 创建书籍表
    cur.execute('''CREATE TABLE IF NOT EXISTS books (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(100) NOT NULL,
            language VARCHAR(100) NOT NULL,
            book_file_url VARCHAR(255),
            description TEXT,
            uploader_id INT NOT NULL,
            is_public TINYINT(1) DEFAULT 0,
            category_id INT DEFAULT NULL,
            cover_image_url VARCHAR(255),
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uploader_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )''')

    # 创建阅读进度表
    cur.execute('''CREATE TABLE IF NOT EXISTS reading_progress (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            book_id INT NOT NULL,
            current_page INT NOT NULL DEFAULT 0,
            last_read_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            reading_progress FLOAT DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )''')

    # 检查分类表是否为空
    cur.execute('SELECT COUNT(*) FROM categories')
    count = cur.fetchone()[0]

    # 如果分类表为空，则插入数据
    if count == 0:
        cur.execute('''
            INSERT INTO categories (name, description) VALUES
            ('小说类', '小说类图书'),
            ('科幻类', '科幻类图书'),
            ('历史类', '历史类图书'),
            ('技术类', '技术类图书'),
            ('其它', '其它类型图书')
        ''')

    # 提交所有更改
    mysql.connection.commit()
    cur.close()