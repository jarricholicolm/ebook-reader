# 电子书阅读器项目

## 项目简介
这是一个基于 Flask 的电子书阅读器系统，支持多种电子书格式的上传、管理和在线阅读。用户可以通过个人书架管理电子书，管理员可以上传公共图书库资源。

## 功能特性
- **用户认证**：
  - 支持普通用户和管理员用户。
  - 用户可以注册、登录、退出。
- **电子书上传与下载**：
  - 支持多种电子书格式：PDF、EPUB、MOBI、AZW3、DJVU。
  - 上传的书籍文件存储在阿里云OSS。
  - 书籍元数据（如书名、作者、封面图片）存储在RDS云数据库。
  - 用户可以通过链接下载公共书籍。
- **在线阅读与记录**：
  - 支持在线阅读 PDF、EPUB、MOBI、AZW3、DJVU格式的电子书。
  - 提供阅读时间和进度的后端实时记录。
- **个人书架**：
  - 普通用户可以查看公共书库（管理员上传）以及个人上传图书，管理员仅支持查看公共书库。
  - 支持分类检索（如小说、科技、历史、技术等进行筛选）和模糊检索（根据书名、作者等关键词进行搜索）。
- **前端支持**：
  - 响应式设计，适配桌面端和移动端。
  - 提供用户友好的界面（基于 HTML、CSS 和 JavaScript）。

---

## 技术栈
- **后端**：Flask (Python Web 框架)
- **数据库**：阿里云 RDS (MySQL)
- **文件存储**：阿里云 OSS
- **认证**：JWT (JSON Web Token)
- **前端**：HTML, CSS, JavaScript (Jinja2 模板渲染)
- **其他依赖**：PDF、EPUB 格式解析库（用于解析和处理电子书的 PDF 和 EPUB 格式），KindleUnpack 工具（用于解包 MOBI、AZW3 格式，以提取其中的内容和元数据），djvutxt 命令（用于将 DJVU 格式的电子书转换为文本格式，便于在线阅读）

---

## 项目目录结构
```
ebook_reader/
├── app/                        # 应用主目录
│   ├── __init__.py             # 初始化 Flask 应用，提供页面接口
│   ├── config.py               # 配置文件
│   ├── models.py               # 数据库模型
│   ├── extensions.py           # JWT配置文件
│   ├── routes/                 # 路由和 API
│   │   ├── __init__.py         # 路由初始化
│   │   ├── book_routes.py      # 图书相关接口
│   │   ├── user_routes.py      # 用户相关接口
│   │   └── progress_routes.py  # 阅读进度接口
│   ├── file_handlers/          # 文件处理模块
│   │   ├── __init__.py         # 初始化
│   │   ├── azw3.py             # 处理 AZW3 格式
│   │   ├── djvu.py             # 处理 DJVU 格式
│   │   ├── epub.py             # 处理 EPUB 格式
│   │   ├── mobi.py             # 处理 MOBI 格式
│   │   └── pdf.py              # 处理 PDF 格式
│   ├── logs/                   # 日志目录
│   │   └── app.log             # 日志文件
│   ├── docs/                   # 接口目录
│   │   ├── eBook_reader API.postman_collection  # postman测试文档
│   │   └── eBook_reader API.md # API接口文档          
│   ├── utils.py                # 工具函数
│   └── run.py                  # 项目入口文件
├── static/                     # 静态资源文件
│   ├── css/                    # 样式表
│   │   ├── index.css           # 处理书架样式
│   │   ├── reader.css          # 处理阅读样式
│   │   └── style.css           # 处理整体样式
│   ├── js/                     # 前端脚本
│   │   ├── index.js            # 页面脚本
│   │   ├── login.js            # 登录脚本
│   │   ├── reader.js           # 阅读脚本
│   │   └── register.js         # 注册脚本
│   └── images/                 # 图像资源
│      
├── templates/                  # 前端 HTML 模板
│   ├── admin_register.html     # 管理员登录页面
│   ├── error.html              # 错误模板
│   ├── index.html              # 书架页面
│   ├── base.html               # 基础模板
│   ├── login.html              # 登录页面
│   ├── register.html           # 注册页面
│   └── reader.html             # 在线阅读页面
├── .env                        # 环境变量配置文件
├── .env.example                # 环境变量示例配置文件
├── requirements.txt            # 项目依赖列表
├── .gitgnore                   # 忽略文件
└── README.md                   # 项目文档
```

---

## 安装和运行

### 环境要求
- Python 版本 >= 3.10
- MySQL 版本 >= 8.0
- 阿里云 OSS 账号（需开通存储服务）
- 配置 **KindleUnpack** 和 **djvulibre**：
  - **KindleUnpack**：用于解析 Kindle 格式电子书（MOBI 文件）。请参考 [KindleUnpack 安装文档](https://github.com/kevinhendricks/KindleUnpack) 进行安装。
  - **djvulibre**：用于支持处理 DjVu 格式电子书。请参考 [djvulibre 安装指南](https://sourceforge.net/projects/djvulibre/) 进行配置。

### 安装步骤
1. **克隆代码仓库或下载代码**：
   ```bash
   git clone https://github.com/jarricholicolm/ebook-reader.git
   cd ebook_reader
   ```
   或者你可以直接下载代码。

2. **创建虚拟环境**：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**：
   - 将 `.env.example` 重命名为 `.env`：
     ```bash
     cp .env.example .env
     ```
   - 修改 `.env` 文件中的内容以匹配你的实际环境，包括数据库配置、阿里云 OSS 的 AccessKey，以及 KindleUnpack 和 djvulibre 的配置。

5. **运行应用**：
   ```bash
   python app/run.py
   ```
   默认服务运行在 `http://127.0.0.1:5000/`。

---

## 使用说明
1. **登录和注册**：
   - 注册普通用户或管理员账户。
   - 登录后进入主界面。

2. **上传电子书**：
   - 上传本地电子书文件。
   - 系统会自动提取书籍元数据和封面。

3. **管理书架**：
   - 普通用户可以管理个人书架。
   - 管理员可以上传公共书籍到系统书库。

4. **在线阅读**：
   - 点击电子书封面直接打开阅读器。
   - 阅读进度会自动保存。

---

## API 文档
接口详情请参考 [API 文档](app/docs/eBook_reader API.md)。

---

## 注意事项
1. 请确保阿里云 OSS 配置正确，包括 `bucket` 名称和访问权限。
2. 日志文件存储在 `logs/` 目录中，便于调试和错误定位。

---

## 贡献
欢迎提出 Issue 或提交 Pull Request！

---

## 许可证
本项目遵循 MIT 许可证。
