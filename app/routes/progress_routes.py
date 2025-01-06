from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import progress_bp
from app.extensions import mysql
import json

# 更新阅读进度
@progress_bp.route('/update/<int:book_id>', methods=['POST'])
@jwt_required()
def update_progress(book_id):
    try:
        current_user = json.loads(get_jwt_identity())
        user_id = current_user['id']

        data = request.get_json()
        current_page = data.get('current_page', 0)
        total_pages = data.get('total_pages', 0)

        # 计算阅读进度百分比
        progress = (current_page / total_pages * 100) if total_pages > 0 else 0

        with mysql.connection.cursor() as cur:
            # 检查是否存在用户与书籍的记录
            cur.execute("""
                SELECT id FROM reading_progress 
                WHERE user_id = %s AND book_id = %s
            """, (user_id, book_id))
            existing_record = cur.fetchone()

            if existing_record:
                # 如果记录存在，更新当前页和进度
                cur.execute("""
                    UPDATE reading_progress 
                    SET current_page = %s, reading_progress = %s, last_read_time = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (current_page, progress, existing_record['id']))
            else:
                # 如果记录不存在，插入新的记录
                cur.execute("""
                    INSERT INTO reading_progress 
                    (user_id, book_id, current_page, reading_progress) 
                    VALUES (%s, %s, %s, %s)
                """, (user_id, book_id, current_page, progress))

            mysql.connection.commit()

        return jsonify({
            "message": "Progress updated successfully",
            "progress": progress
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error updating progress: {str(e)}")
        return jsonify({"error": str(e)}), 500
