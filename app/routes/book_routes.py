from flask import request, jsonify, current_app, make_response, Blueprint, redirect, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from . import book_bp
from ..file_handlers import epub, mobi, pdf, azw3, djvu
from ..extensions import mysql
from ..utils import allowed_file, get_allowed_extensions
import tempfile
import io
import json
import os
import oss2
import urllib.parse
import datetime
from datetime import datetime

class DatabaseError(Exception):
    """数据库操作异常"""
    pass

class ValidationError(Exception):
    """参数验证异常"""
    pass

def execute_query(cur, query, params=None):
    """执行SQL查询并处理异常"""
    try:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        return cur.fetchall()
    except Exception as e:
        raise ValueError(f"Error executing query: {str(e)}")

def serialize_books(books):
    """序列化书籍查询结果到JSON格式"""
    return [{
        "id": book[0],
        "title": book[1],
        "author": book[2],
        "language": book[3],
        "book_file_url": book[4],
        "description": book[5],
        "uploader_id": book[6],
        "is_public": book[7],
        "category_id": book[8],
        "cover_image_url": book[9],
        "upload_time": book[10]
    } for book in books]

def get_category_list():
    """获取所有可用的分类列表"""
    try:
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT id, name FROM categories ORDER BY id")
            categories = cur.fetchall()
            return [{
                "id": cat[0],
                "name": cat[1]
            } for cat in categories]
    except Exception:
        return []

@book_bp.route('/upload-options', methods=['GET'])
@jwt_required()
def get_upload_options():
    """获取上传书籍时的选项"""
    try:
        categories = get_category_list()
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 100 * 1024 * 1024)
        return jsonify({
            "categories": categories,
            "allowed_extensions": get_allowed_extensions(),
            "max_file_size": max_size
        }), 200
    except Exception as e:
        return jsonify({"message": f"Error getting upload options: {str(e)}"}), 500


# 上传书籍
@book_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_book():
    try:
        # 从应用上下文中获取 OSS 配置信息
        access_key_id = current_app.config['OSS_ACCESS_KEY_ID']
        access_key_secret = current_app.config['OSS_ACCESS_KEY_SECRET']
        bucket_name = current_app.config['OSS_BUCKET_NAME']
        endpoint = current_app.config['OSS_ENDPOINT']

        # 创建 OSS 认证对象
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)

        current_user = get_jwt_identity()
        user_info = json.loads(current_user)

        is_admin = user_info['role'] == 'admin'
        uploader_id = user_info['id']

        if 'file' not in request.files:
            return jsonify({"message": "No file part"}), 400

        file = request.files['file']

        # 如果没有选择文件
        if file.filename == '':
            return jsonify({"message": "No selected file"}), 400

        # 获取表单数据，使用默认值处理可选字段
        title = request.form.get('title') or os.path.splitext(file.filename)[0]  # 如果没有标题，使用文件名
        author = request.form.get('author') or '未知'
        description = request.form.get('description') or ''
        language = request.form.get('language') or '未知'
        category_id = request.form.get('category', 1, type=int)  # 默认使用 "其它" 分类

        # 验证分类是否存在
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        category = cur.fetchone()
        if not category:
            return jsonify({"message": "Invalid category"}), 400

        # 文件类型检查
        if file and allowed_file(file.filename):
            filename = file.filename
            object_name = f"uploads/{filename}"

            try:
                # 从上传的文件对象创建一个BytesIO对象
                file_stream = io.BytesIO(file.read())
                # 上传文件流
                bucket.put_object(object_name, file_stream)
            except Exception as e:
                return jsonify({"message": f"Error saving file: {str(e)}"}), 500

            # 获取文件扩展名
            file_extension = os.path.splitext(filename)[1].lower()
            base_title = os.path.splitext(filename)[0]

            # 处理封面图片
            cover_image_url = None
            custom_cover = request.files.get('cover')  # 获取用户上传的封面

            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                    tmp_file_path = tmp_file.name
                    bucket.get_object_to_file(object_name, tmp_file_path)

                    if custom_cover:
                        # 使用用户上传的封面
                        cover_filename = secure_filename(custom_cover.filename)
                        cover_object_name = f"covers/{os.path.splitext(filename)[0]}_{cover_filename}"
                        bucket.put_object(cover_object_name, custom_cover)
                        cover_image_url = f"/api/cover/covers/{os.path.basename(cover_object_name)}"
                    else:
                        # 尝试从文件中提取封面
                        if file_extension == '.pdf':
                            cover_image_url = pdf.extract_cover(tmp_file_path, bucket, filename)
                        elif file_extension == '.epub':
                            cover_image_url = epub.extract_cover(tmp_file_path, bucket, filename)
                        elif file_extension == '.mobi':
                            cover_image_url = mobi.extract_cover(tmp_file_path, bucket, filename)
                        elif file_extension == '.azw3':
                            cover_image_url = azw3.extract_cover(tmp_file_path, bucket, filename)
                        elif file_extension == '.djvu':
                            cover_image_url = djvu.extract_cover(tmp_file_path, bucket, filename)

                        if not cover_image_url:
                            cover_image_url = 'covers/default_cover.jpg'  # 默认封面

                    # 提取元数据
                    if file_extension == '.pdf':
                        book_metadata = pdf.extract_metadata(tmp_file_path)
                    elif file_extension == '.epub':
                        book_metadata = epub.extract_metadata(tmp_file_path)
                    elif file_extension == '.mobi':
                        book_metadata = mobi.extract_metadata(tmp_file_path)
                    elif file_extension == '.azw3':
                        book_metadata = azw3.extract_metadata(tmp_file_path)
                    elif file_extension == '.djvu':
                        book_metadata = djvu.extract_metadata(tmp_file_path)
                    else:
                        return jsonify({"message": "Unsupported file format"}), 400

                    # 提取元数据（如果没有元数据，使用默认值）
                    title = book_metadata.get('title') if book_metadata and book_metadata.get('title') else base_title
                    author = book_metadata.get('author') if book_metadata and book_metadata.get('author') else 'Unknown Author'
                    description = book_metadata.get('description') if book_metadata and book_metadata.get(
                        'description') else 'No description available'
                    language = book_metadata.get('language') if book_metadata and book_metadata.get('language') else 'Unknown'

            finally:
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)

            # 检查请中是否提供了自定义信息
            custom_title = request.form.get('title')
            custom_author = request.form.get('author')
            custom_description = request.form.get('description')
            custom_language = request.form.get('language')

            # 如果提供了自定义信息，则使用它们
            if custom_title:
                title = custom_title
            if custom_author:
                author = custom_author
            if custom_description:
                description = custom_description
            if custom_language:
                language = custom_language

            is_public = 1 if is_admin else 0
            upload_time = datetime.now()
            # 将书籍元数据保存到数据库
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    INSERT INTO books (
                        title, author, language, book_file_url, 
                        description, uploader_id, is_public, category_id,
                        cover_image_url, upload_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        title, author, language, object_name,
                        description, uploader_id, is_public, category_id,
                        cover_image_url, upload_time
                    ))
                mysql.connection.commit()
                cur.close()

                return jsonify({
                    "message": "Book uploaded successfully!",
                    "book": {
                        "title": title,
                        "author": author,
                        "language": language,
                        "description": description,
                        "category_id": category_id,
                        "cover_image_url": cover_image_url
                    }
                }), 201
            except Exception as e:
                return jsonify({"message": f"Error saving book data to database: {str(e)}"}), 500
        else:
            return jsonify({"message": "Invalid file format"}), 400

    except Exception as e:
        current_app.logger.error(f"Error in upload_book: {str(e)}")
        return jsonify({"message": f"Error uploading book: {str(e)}"}), 500


# 下载书籍
@book_bp.route('/download/<int:book_id>', methods=['GET'])
@jwt_required()
def download_book(book_id):
    try:
        # 获取 OSS 配置
        access_key_id = current_app.config['OSS_ACCESS_KEY_ID']
        access_key_secret = current_app.config['OSS_ACCESS_KEY_SECRET']
        bucket_name = current_app.config['OSS_BUCKET_NAME']
        endpoint = current_app.config['OSS_ENDPOINT']

        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)

        current_user = get_jwt_identity()
        user_info = json.loads(current_user)

        # 查找书籍
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        book = cur.fetchone()
        cur.close()

        if not book:
            return jsonify({"error": "Book not found"}), 404

        # 检查权限
        if not (book[7] == 1 or book[6] == user_info['id']):  # is_public or uploader_id
            return jsonify({"error": "Permission denied"}), 403

        # 获取 OSS 文件路径和文件名
        file_path = book[4]
        filename = os.path.basename(file_path)

        # 从 OSS 下载文件
        file_obj = bucket.get_object(file_path)
        file_data = file_obj.read()

        # 创建响应
        response = make_response(file_data)
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = f'attachment; filename="{urllib.parse.quote(filename)}"'

        return response

    except Exception as e:
        current_app.logger.error(f"Download error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# 获取所有分类及其统计信息
@book_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    try:
        current_user = get_jwt_identity()
        user_info = json.loads(current_user)

        with mysql.connection.cursor() as cur:
            # 只统计用户可见的书籍
            cur.execute("""
                SELECT 
                    c.id,
                    c.name,
                    c.description,
                    COUNT(CASE WHEN b.id IS NOT NULL AND (b.is_public = 1 OR b.uploader_id = %s) THEN 1 END) as book_count
                FROM categories c
                LEFT JOIN books b ON c.id = b.category_id
                GROUP BY c.id, c.name, c.description
                ORDER BY c.id
            """, (user_info['id'],))

            categories = cur.fetchall()

            return jsonify({
                "categories": [{
                    "id": cat[0],
                    "name": cat[1],
                    "description": cat[2],
                    "book_count": cat[3]
                } for cat in categories]
            }), 200

    except Exception as e:
        current_app.logger.error(f"Error in get_categories: {str(e)}")
        return jsonify({"error": str(e)}), 500


# 获取分类的可见书籍
@book_bp.route('/category/<category_id>/books', methods=['GET'])
@jwt_required()
def get_books_by_category(category_id):
    try:
        # 获取当前用户信息
        current_user = get_jwt_identity()
        user_info = json.loads(current_user)

        # 获取分页和排序参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 4))
        sort_by = request.args.get('sort', 'recent')

        offset = (page - 1) * per_page

        with mysql.connection.cursor() as cur:
            # 获取总数的查询
            count_query = """
                SELECT COUNT(*) FROM books b
                LEFT JOIN reading_progress p ON b.id = p.book_id AND p.user_id = %s
                WHERE (b.is_public = 1 OR b.uploader_id = %s)
            """
            params = [user_info['id'], user_info['id']]  # 注意params顺序，用户ID需要两次传递

            if category_id != 'all':
                count_query += " AND b.category_id = %s"
                params.append(int(category_id))

            cur.execute(count_query, params)
            total = cur.fetchone()[0]

            # 获取书籍数据的查询
            query = """
                SELECT 
                    b.id, b.title, b.author, b.language,
                    b.book_file_url, b.description, b.uploader_id,
                    b.is_public, b.category_id, b.cover_image_url,
                    COALESCE(p.reading_progress, 0) as reading_progress,
                    p.last_read_time
                FROM books b
                LEFT JOIN reading_progress p ON b.id = p.book_id AND p.user_id = %s
                WHERE (b.is_public = 1 OR b.uploader_id = %s)
            """

            params = [user_info['id'], user_info['id']]  # 确保params包含正确的user_id

            if category_id != 'all':
                query += " AND b.category_id = %s"
                params.append(int(category_id))

            # 添加排序条件
            if sort_by == 'recent':
                query += " ORDER BY b.upload_time DESC"
            elif sort_by == 'title':
                query += " ORDER BY b.title ASC"
            elif sort_by == 'author':
                query += " ORDER BY b.author ASC"
            elif sort_by == 'progress':
                query += " ORDER BY p.reading_progress DESC, p.last_read_time DESC"  # 按阅读进度降序，若进度相同按时间降序排序

            query += " LIMIT %s OFFSET %s"
            params.extend([per_page, offset])  # 添加分页参数

            # 执行查询
            books = execute_query(cur, query, params)
            serialized_books = serialize_books(books)

            # 返回结果
            return jsonify({
                "books": serialized_books,
                "total": total,
                "page": page,
                "per_page": per_page,
                "sort": sort_by
            }), 200

    except Exception as e:
        current_app.logger.error(f"Error in get_books_by_category: {str(e)}")
        return jsonify({"error": str(e)}), 500



# 分类检索
@book_bp.route('/search_by_category', methods=['GET'])
@jwt_required()
def search_books_by_category():
    try:
        # 获取当前用户信息
        current_user = get_jwt_identity()
        user_info = json.loads(current_user)

        # 获取查询参数
        category = request.args.get('category', 'all')
        sort = request.args.get('sort', 'recent')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 4))  # 确保每页只返回4本书

        # 计算偏移量
        offset = (page - 1) * per_page

        with mysql.connection.cursor() as cur:
            # 先获取总数
            count_query = """
                SELECT COUNT(*) FROM books b
                LEFT JOIN reading_progress p ON b.id = p.book_id AND p.user_id = %s
                WHERE (b.is_public = 1 OR b.uploader_id = %s)
            """
            params = [user_info['id'], user_info['id']]  # 用户ID用于查询

            # 添加搜索条件
            if search:
                count_query += " AND (b.title LIKE %s OR b.author LIKE %s)"
                params.extend([f'%{search}%', f'%{search}%'])

            # 执行总数查询
            cur.execute(count_query, params)
            total = cur.fetchone()[0]

            # 获取分页数据的查询
            query = """
                SELECT 
                    b.id, b.title, b.author, b.language,
                    b.book_file_url, b.description, b.uploader_id,
                    b.is_public, b.category_id, b.cover_image_url,
                    COALESCE(p.reading_progress, 0) as reading_progress,
                    p.last_read_time
                FROM books b
                LEFT JOIN reading_progress p ON b.id = p.book_id AND p.user_id = %s
                WHERE (b.is_public = 1 OR b.uploader_id = %s)
            """
            params = [user_info['id'], user_info['id']]  # 使用用户ID进行查询

            # 添加分类过滤条件
            if category != 'all':
                query += " AND b.category_id = %s"
                params.append(category)

            # 添加搜索条件
            if search:
                query += " AND (b.title LIKE %s OR b.author LIKE %s)"
                params.extend([f'%{search}%', f'%{search}%'])

            # 添加排序条件
            if sort == 'recent':
                query += " ORDER BY b.upload_time DESC"
            elif sort == 'title':
                query += " ORDER BY b.title ASC"
            elif sort == 'author':
                query += " ORDER BY b.author ASC"
            elif sort == 'progress':
                query += " ORDER BY p.reading_progress DESC, p.last_read_time DESC"  # 按阅读进度降序，再按时间降序

            # 添加分页
            query += " LIMIT %s OFFSET %s"
            params.extend([per_page, offset])  # 使用 LIMIT 和 OFFSET 进行分页

            # 执行查询
            books = execute_query(cur, query, params)
            serialized_books = serialize_books(books)

            # 返回结果
            return jsonify({
                "books": serialized_books,
                "total": total,
                "page": page,
                "per_page": per_page,
                "sort": sort
            }), 200

    except Exception as e:
        current_app.logger.error(f"Error in search_books_by_category: {str(e)}")
        return jsonify({"error": str(e)}), 500



# 获取书籍封面
@book_bp.route('/cover/<path:filename>')
def get_cover(filename):
    # print(f"Accessing get_cover with filename: {filename}")
    try:
        # 从应用上下文中获取 OSS 配置信息
        access_key_id = current_app.config['OSS_ACCESS_KEY_ID']
        access_key_secret = current_app.config['OSS_ACCESS_KEY_SECRET']
        bucket_name = current_app.config['OSS_BUCKET_NAME']
        endpoint = current_app.config['OSS_ENDPOINT']

        # 创建 OSS 认证对象
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)

        object_name = filename
        current_app.logger.debug(f"Looking for OSS object: {object_name}")

        # 检查文件是否存在
        exists = bucket.object_exists(object_name)
        current_app.logger.debug(f"Object exists in OSS: {exists}")

        if not exists:
            current_app.logger.error(f"Cover file not found in OSS: {object_name}")
            return '', 404

        # 生成临时访问URL
        url = bucket.sign_url('GET', object_name, 3600)
        current_app.logger.debug(f"Generated OSS URL: {url}")

        return redirect(url)
    except Exception as e:
        current_app.logger.error(f"Error getting cover: {str(e)}")
        return '', 404


# 获取书籍内容
@book_bp.route('/book/<int:book_id>/content')
@jwt_required()
def get_book_content(book_id):
    try:
        current_user = json.loads(get_jwt_identity())

        # 查找书籍
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        book = cur.fetchone()
        cur.close()

        if not book:
            current_app.logger.error(f"Book not found: {book_id}")
            return jsonify({"error": "Book not found"}), 404

        # 检查权限
        if not book[7] and book[6] != current_user['id']:
            current_app.logger.error(f"Permission denied for user {current_user['id']} on book {book_id}")
            return jsonify({"error": "Permission denied"}), 403

        # 获取文件路径
        file_path = book[4]
        file_extension = os.path.splitext(file_path)[1].lower()
        current_app.logger.debug(f"File path: {file_path}, extension: {file_extension}")

        # 从OSS获取文件
        auth = oss2.Auth(
            current_app.config['OSS_ACCESS_KEY_ID'],
            current_app.config['OSS_ACCESS_KEY_SECRET']
        )
        bucket = oss2.Bucket(
            auth,
            current_app.config['OSS_ENDPOINT'],
            current_app.config['OSS_BUCKET_NAME']
        )

        # 检查文件是否存在
        if not bucket.object_exists(file_path):
            current_app.logger.error(f"File not found in OSS: {file_path}")
            return jsonify({"error": "File not found in storage"}), 404

        # 创建临时文件并处理
        tmp_path = None
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as tmp_file:
                bucket.get_object_to_file(file_path, tmp_file.name)
                tmp_path = tmp_file.name

            # 根据文件类型选择相应的解析方法
            if file_extension == '.pdf':
                html_content = pdf.extract_text(tmp_path)
            elif file_extension == '.epub':
                html_content = epub.extract_text(tmp_path)
            elif file_extension == '.mobi':
                html_content = mobi.extract_text(tmp_path)
            elif file_extension == '.azw3':
                html_content  = azw3.extract_text(tmp_path)
            elif file_extension == '.djvu':
                html_content = djvu.extract_text(tmp_path)
            else:
                # current_app.logger.error(f"Unsupported file format: {file_extension}")
                return jsonify({"error": "Unsupported file format"}), 400

            # current_app.logger.debug(f"Successfully extracted HTML content")

            # 返回分页后的 HTML 内容
            return jsonify({
                "content": html_content,
                "total_pages": len(html_content)
            })

        except oss2.exceptions.OssError as e:
            current_app.logger.error(f"OSS error: {str(e)}")
            return jsonify({"error": "Storage service error"}), 500
        except Exception as e:
            current_app.logger.error(f"Error processing file: {str(e)}")
            return jsonify({"error": str(e)}), 500
        finally:
            # 清理临时文件
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    current_app.logger.error(f"Error deleting temp file: {str(e)}")

    except Exception as e:
        current_app.logger.error(f"Unexpected error in get_book_content: {str(e)}")
        return jsonify({"error": str(e)}), 500













