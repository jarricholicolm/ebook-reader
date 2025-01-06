import ebooklib
from ebooklib import epub
import os


def extract_metadata(file_path):
    # 打开 EPUB 文件
    book = epub.read_epub(file_path)

    def extract_text(metadata_field):
        """提取元数据中的纯文本部分"""
        if not metadata_field:
            return None
        if isinstance(metadata_field, list) and isinstance(metadata_field[0], tuple):
            return metadata_field[0][0]  # 提取元组中的第一个元素（文本部分）
        return metadata_field[0] if isinstance(metadata_field, list) else metadata_field

    # 提取元数据
    metadata = {
        'title': extract_text(book.get_metadata('DC', 'title')),
        'author': extract_text(book.get_metadata('DC', 'creator')),
        'language': extract_text(book.get_metadata('DC', 'language')),
        'description': extract_text(book.get_metadata('DC', 'description'))
    }

    return metadata


def extract_text(file_path):
    """从EPUB文件中提取HTML格式的内容"""
    # 读取 EPUB 文件
    book = epub.read_epub(file_path)
    html_contents = []

    # 遍历书籍中的每个条目
    for item in book.get_items():
        # 如果是 HTML 文档类型
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            # 获取 HTML 内容并解码为 UTF-8 格式
            html_content = item.get_body_content().decode('utf-8')
            html_contents.append(html_content)

    # 返回包含所有 HTML 内容的列表
    return html_contents

def extract_cover(file_path, bucket, filename):
    """从EPUB文件中提取封面并上传到OSS"""
    try:
        book = epub.read_epub(file_path)
        
        # 尝试获取封面
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_COVER or \
               item.get_name().lower().endswith(('cover.jpg', 'cover.jpeg', 'cover.png')):
                cover_data = item.get_content()
                
                # 生成封面图片的OSS路径
                cover_object_name = f"covers/{os.path.splitext(filename)[0]}_cover.jpg"
                
                # 上传图片到OSS
                bucket.put_object(cover_object_name, cover_data)
                return cover_object_name
                
        return None
    except Exception as e:
        print(f"Error extracting cover from EPUB: {str(e)}")
        return None
