import os
import subprocess
import tempfile
from flask import current_app
from lxml import etree
from bs4 import BeautifulSoup

def extract_metadata(file_path):
    """使用 KindleUnpack 解包 AZW3 文件并提取元数据"""
    kindle_unpack_path = current_app.config['KINDLE_UNPACK_PATH']

    # 自动生成解包输出目录（以文件名为基础的临时路径）
    output_dir = os.path.join(tempfile.gettempdir(), os.path.basename(os.path.splitext(file_path)[0]))

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 调用 KindleUnpack 工具进行解包，设置环境变量以处理编码问题
    command = ['python', kindle_unpack_path, '-r', file_path, output_dir]
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            env=env,
            universal_newlines=True,  # 使用文本模式
            encoding='utf-8'
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"Error unpacking AZW3 file: {stdout}\n{stderr}")
    except Exception as e:
        print(f"Exception: {e}")
        raise

    # 解包后的 metadata.opf 文件路径
    metadata_file = os.path.join(output_dir, 'mobi8', 'OEBPS', 'content.opf')

    if not os.path.exists(metadata_file):
        raise Exception(f"未找到 metadata 文件: {metadata_file}")

    # 使用 lxml 解析 OPF 文件（同样处理 AZW3 的元数据）
    try:
        tree = etree.parse(metadata_file)
        root = tree.getroot()
    except Exception as e:
        raise Exception(f"Error parsing metadata.opf file: {e}")

    # 提取元数据
    try:
        metadata = {
            'title': root.find('.//dc:title', namespaces={'dc': 'http://purl.org/dc/elements/1.1/'}).text,
            'author': root.find('.//dc:creator', namespaces={'dc': 'http://purl.org/dc/elements/1.1/'}).text,
            'language': root.find('.//dc:language', namespaces={'dc': 'http://purl.org/dc/elements/1.1/'}).text,
            'description': root.find('.//dc:description', namespaces={'dc': 'http://purl.org/dc/elements/1.1/'}).text
            if root.find('.//dc:description',
                         namespaces={'dc': 'http://purl.org/dc/elements/1.1/'}) is not None else None,
        }
    except AttributeError as e:
        raise Exception(f"Error extracting metadata: {e}")

    return metadata

import shutil


def extract_text(file_path):
    """从AZW3文件中提取HTML格式的文本内容，并确保返回完整的HTML内容"""
    kindle_unpack_path = current_app.config['KINDLE_UNPACK_PATH']
    output_dir = os.path.join(tempfile.gettempdir(), os.path.basename(os.path.splitext(file_path)[0]))

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # 调用 KindleUnpack 工具进行解包
        command = ['python', kindle_unpack_path, '-r', file_path, output_dir]
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            universal_newlines=True,
            encoding='utf-8'
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"Error unpacking AZW3 file: {stdout}\n{stderr}")

        # 查找所有可能包含文本内容的HTML文件
        html_files = []
        possible_paths = [
            os.path.join(output_dir, 'mobi8', 'OEBPS', 'Text'),
            os.path.join(output_dir, 'mobi8', 'Text'),
            os.path.join(output_dir, 'mobi8')
        ]

        # 递归查找所有HTML文件
        for path in possible_paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in sorted(files):
                        if file.endswith(('.html', '.xhtml', '.htm')):
                            html_files.append(os.path.join(root, file))

        html_files.sort()

        all_html_content = []
        seen_html = set()  # 用来去重内容，确保不重复

        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    soup = BeautifulSoup(content, 'html.parser')

                    # 移除脚本和样式标签
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # 获取完整的 HTML 内容
                    html_content = str(soup)

                    # 去除重复的内容
                    if html_content.strip() and html_content not in seen_html:
                        seen_html.add(html_content)  # 标记为已添加
                        all_html_content.append(html_content)

            except Exception as e:
                print(f"Error processing {html_file}: {str(e)}")
                continue

        if not all_html_content:
            print("No HTML content found in the AZW3 file")
            return ["No content found in the book"]

        # 将所有内容合并为一个单一的HTML页面
        combined_html = "\n".join(all_html_content)

        lst = []
        pages = ""

        for content in combined_html:
            soup = BeautifulSoup(content, 'html.parser')

            # 遍历每个元素，按字数限制进行分页
            for element in soup.recursiveChildGenerator():
                pages += str(element)
        lst.append(pages)
        # 返回合并后的单个 HTML 页面
        return lst

    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        raise
    finally:
        # 清理临时文件
        try:
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
        except Exception as e:
            print(f"Error cleaning up: {str(e)}")


def extract_cover(file_path, bucket, filename):
    """从AZW3文件中提取封面并上传到OSS"""
    kindle_unpack_path = current_app.config['KINDLE_UNPACK_PATH']
    output_dir = os.path.join(tempfile.gettempdir(), os.path.basename(os.path.splitext(filename)[0]))

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # 解包文件
        command = ['python', kindle_unpack_path, '-r', file_path, output_dir]
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            env=env,
            universal_newlines=True,
            encoding='utf-8'
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"Error unpacking AZW3 file: {stdout}\n{stderr}")

        # 查找封面图片
        cover_path = None
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.lower() in ['cover.jpg', 'cover.jpeg', 'cover.png']:
                    cover_path = os.path.join(root, file)
                    break

        if cover_path and os.path.exists(cover_path):
            with open(cover_path, 'rb') as f:
                cover_data = f.read()
                
            # 生成封面图片的OSS路径
            cover_object_name = f"covers/{os.path.splitext(filename)[0]}_cover.jpg"
            
            # 上传图片到OSS
            bucket.put_object(cover_object_name, cover_data)
            return cover_object_name
            
        return None

    except Exception as e:
        print(f"Error extracting cover: {str(e)}")
        return None
    finally:
        # 清理临时文件
        try:
            if os.path.exists(output_dir):
                import shutil
                shutil.rmtree(output_dir)
        except Exception as e:
            print(f"Error cleaning up: {str(e)}")