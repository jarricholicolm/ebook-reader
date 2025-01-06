from flask import current_app
import os
import tempfile
from lxml import etree
import subprocess

def extract_metadata(file_path):
    # 确认 KindleUnpack 工具路径
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
            universal_newlines=True,
            encoding='utf-8'
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"Error unpacking MOBI file: {stdout}\n{stderr}")
    except Exception as e:
        print(f"Exception: {e}")
        raise

    # 解包后的 metadata.opf 文件路径
    metadata_file = os.path.join(output_dir, 'mobi7', 'content.opf')

    if not os.path.exists(metadata_file):
        raise Exception(f"未找到 metadata 文件: {metadata_file}")

    # 使用 lxml 解析 OPF 文件
    try:
        tree = etree.parse(metadata_file)
        root = tree.getroot()
    except Exception as e:
        raise Exception(f"解析 metadata.opf 文件时出错: {e}")

    # 提取元数据
    try:
        metadata = {
            'title': root.find('.//dc:title', namespaces={'dc': 'http://purl.org/dc/elements/1.1/'}).text,
            'author': root.find('.//dc:creator', namespaces={'dc': 'http://purl.org/dc/elements/1.1/'}).text,
            'language': root.find('.//dc:language', namespaces={'dc': 'http://purl.org/dc/elements/1.1/'}).text,
            'description': root.find('.//dc:description',
                                     namespaces={'dc': 'http://purl.org/dc/elements/1.1/'}).text if root.find(
                './/dc:description', namespaces={'dc': 'http://purl.org/dc/elements/1.1/'}) is not None else None,
        }
    except AttributeError as e:
        raise Exception(f"提取元数据时发生错误: {e}")

    return metadata

def extract_text(file_path):
    """从MOBI文件中提取HTML内容"""
    kindle_unpack_path = current_app.config['KINDLE_UNPACK_PATH']
    output_dir = os.path.join(tempfile.gettempdir(), os.path.basename(os.path.splitext(file_path)[0]))

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # 解包MOBI文件
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
            raise Exception(f"Error unpacking MOBI file: {stdout}\n{stderr}")

        # 查找所有可能包含HTML文件的路径
        html_files = []
        possible_paths = [
            os.path.join(output_dir, 'mobi7', 'OEBPS', 'Text'),
            os.path.join(output_dir, 'mobi7', 'Text'),
            os.path.join(output_dir, 'mobi8', 'OEBPS', 'Text'),
            os.path.join(output_dir, 'mobi8', 'Text'),
            os.path.join(output_dir, 'mobi7'),
            os.path.join(output_dir, 'mobi8')
        ]

        for path in possible_paths:
            if os.path.exists(path):
                # 递归查找所有HTML文件
                for root, dirs, files in os.walk(path):
                    for file in sorted(files):
                        if file.endswith(('.html', '.xhtml', '.htm')):
                            html_files.append(os.path.join(root, file))

        # 按文件名排序，确保正确的阅读顺序
        html_files.sort()

        # 读取所有HTML文件并合并它们的内容
        html_content = []
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    html_content.append(content)
                    print(f"Extracted HTML content from {os.path.basename(html_file)}")  # 调试信息
            except Exception as e:
                print(f"Error processing {html_file}: {str(e)}")
                continue

        if not html_content:
            print("No HTML content found in the MOBI file")
            return ["No content found in the book"]

        # 将所有HTML内容合并为一个字符串，并返回
        return html_content

    except Exception as e:
        print(f"Error extracting HTML: {str(e)}")
        raise
    finally:
        # 清理临时文件
        try:
            if os.path.exists(output_dir):
                import shutil
                shutil.rmtree(output_dir)
        except Exception as e:
            print(f"Error cleaning up: {str(e)}")

def extract_cover(file_path, bucket, filename):
    """从MOBI文件中提取封面并上传到OSS"""
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
            raise Exception(f"Error unpacking MOBI file: {stdout}\n{stderr}")

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
