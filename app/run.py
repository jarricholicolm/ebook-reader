import os
import sys

# 将项目根目录添加到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app import create_app
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
    #  app.run(host="0.0.0.0", port=5000) #局域网内（如校园网）可以运行
