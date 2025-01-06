from langdetect import detect
import os
import fitz  # PyMuPDF

def extract_metadata(file_path):
    # 打开 PDF 文件
    doc = fitz.open(file_path)
    # 尝试获取文档的元数据
    metadata = {
        'title': doc.metadata.get('title', 'Unknown'),
        'author': doc.metadata.get('author', 'Unknown'),
        'language': doc.metadata.get('language', None),  # 获取元数据中的语言
        'description': doc.metadata.get('description', 'Unknown'),
    }
    # 如果元数据中没有语言信息，则从文本内容中检测语言
    if not metadata['language']:
        try:
            # 提取 PDF 文件的文本内容
            text = ""
            for page in doc:
                text += page.get_text()
            # 如果文本内容过少，检测结果可能不准确
            if len(text.strip()) > 20:  # 设定一个合理的文本长度阈值
                metadata['language'] = detect(text)
            else:
                metadata['language'] = "Unknown"
        except Exception as e:
            metadata['language'] = f"Error: {str(e)}"

    # 关闭 PDF 文档
    doc.close()
    return metadata


def extract_text(file_path):
    """提取 PDF 文档中的所有页面内容，返回 HTML 格式"""
    doc = fitz.open(file_path)
    pages_html = []

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        # 提取该页内容为 HTML 格式
        html_content = page.get_text("html")
        pages_html.append(html_content)

    doc.close()
    return pages_html

def extract_cover(file_path, bucket, filename):
    """从PDF文件中提取封面图片并上传到OSS"""
    try:
        doc = fitz.open(file_path)
        # 获取第一页
        page = doc[0]
        # 获取页面上的图片
        images = page.get_images()
        
        if images:
            # 获取第一张图片作为封面
            img_index = 0
            base_image = doc.extract_image(images[img_index][0])
            image_data = base_image["image"]
            
            # 生成封面图片的OSS路径
            cover_object_name = f"covers/{os.path.splitext(filename)[0]}_cover.jpg"
            
            # 上传图片到OSS
            bucket.put_object(cover_object_name, image_data)
            
            return cover_object_name
            
        return None
    except Exception as e:
        print(f"Error extracting cover: {str(e)}")
        return None

