import fitz
from langdetect import detect, LangDetectException
import os
import subprocess
import chardet
import re

def extract_metadata(file_path):
    """提取 DjVu 文件的元数据，使用 djvutxt 命令"""
    command = ['djvutxt', file_path]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Error extracting metadata: {result.stderr}")

    metadata = {}

    # 检查 result.stdout 是否为 None
    if result.stdout:
        # 假设元数据以文本格式输出，进行简单的解析
        for line in result.stdout.splitlines():
            if line.startswith("Title:"):
                metadata['title'] = line[len("Title:"):].strip()
            elif line.startswith("Creator:"):
                metadata['author'] = line[len("Creator:"):].strip()
            elif line.startswith("Language:"):
                metadata['language'] = line[len("Language:"):].strip()
            elif line.startswith("Description:"):  # 假设描述字段是 "Description:"
                metadata['description'] = line[len("Description:"):].strip()
            elif line.startswith("Summary:"):  # 如果是 "Summary:"，替代描述字段
                metadata['description'] = line[len("Summary:"):].strip()

    # 如果没有从元数据中获得语言信息，则使用 langdetect 检测描述的语言
    if 'language' not in metadata and 'description' in metadata:
        try:
            metadata['language'] = detect(metadata['description'])
        except LangDetectException:
            metadata['language'] = 'unknown'
    return metadata


def clean_text(text):
    """
    清理 DjVu 提取出的文本，去除控制字符，处理乱码，保留必要的换行符和段落间的空行，
    以及在句号后面跟着空格和大写字母时插入换行符。
    """
    text = re.sub(r'[\x00-\x1F\x7F]+', ' ', text)  # 替换控制字符

    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    text = text.strip()

    text = re.sub(r'(\.)(\s)([A-Z])', r'\1\n\3', text)
    return text




def extract_text(file_path):
    """从 DjVu 文件中提取 HTML 格式的内容"""
    try:
        # 使用 djvutxt 命令提取文本
        command = ['djvutxt', file_path]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8'  # 假设编码是 UTF-8，但后面会处理乱码
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise Exception(f"Error extracting text: {stderr}")

        # 2. 动态检测编码格式，避免乱码
        detected_encoding = chardet.detect(stdout.encode())['encoding']
        if detected_encoding and detected_encoding != 'utf-8':
            stdout = stdout.encode(detected_encoding).decode(detected_encoding)

        # 3. 清理提取的文本，去除控制字符，保留段落和换行符
        cleaned_text = clean_text(stdout)

        # 4. 将文本按页分割（假设页面之间有特定的分隔符）
        pages_html = []
        current_page = []
        lines = cleaned_text.split('\n')

        for line in lines:
            # 假设 PAGE 或 --- 是页面分隔符，具体可以根据文件的实际内容调整
            if 'PAGE' in line or '---' in line:
                if current_page:
                    # 将当前页面的内容包装成 HTML 格式
                    page_html = "<html><body><p>" + "</p><p>".join(current_page) + "</p></body></html>"
                    pages_html.append(page_html)
                    current_page = []
            else:
                # 继续添加当前页面内容，保持段落之间的换行符
                current_page.append(line.strip())

        # 添加最后一页
        if current_page:
            page_html = "<html><body><p>" + "</p><p>".join(current_page) + "</p></body></html>"
            pages_html.append(page_html)

        # 如果没有找到分页符，按固定长度分页
        if not pages_html:
            chars_per_page = 3000  # 每页大约 3000 个字符
            pages = [cleaned_text[i:i + chars_per_page] for i in range(0, len(cleaned_text), chars_per_page)]
            pages_html = ["<html><body><p>" + page.replace("\n", "</p><p>") + "</p></body></html>" for page in pages]

        print(f"Extracted {len(pages_html)} pages from DjVu file")
        return pages_html

    except Exception as e:
        print(f"Error extracting HTML from DjVu: {str(e)}")
        raise


def extract_cover(file_path, bucket, filename):
    """从 DjVu 文件中提取封面并上传到OSS"""
    try:
        # 使用 PyMuPDF 打开文件
        doc = fitz.open(file_path)
        
        if doc.page_count > 0:
            # 获取第一页作为封面
            page = doc[0]
            
            # 将页面渲染为图片
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x缩放以获得更好的质量
            
            # 将图片保存为 JPEG 格式
            img_data = pix.tobytes("jpeg")
            
            # 生成封面图片的 OSS 路径
            cover_object_name = f"covers/{os.path.splitext(filename)[0]}_cover.jpg"

            bucket.put_object(cover_object_name, img_data)
            
            doc.close()
            print(f"Successfully extracted and uploaded cover image")
            return cover_object_name
        
        doc.close()
        print("No pages found in DjVu file")
        return None

    except Exception as e:
        print(f"Error extracting cover from DjVu: {str(e)}")
        return None