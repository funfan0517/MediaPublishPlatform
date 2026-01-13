"""
Facebook平台上传器初始化文件
"""
from pathlib import Path
from conf import BASE_DIR

# 创建cookie存储目录
COOKIE_DIR = Path(BASE_DIR / "cookies" / "fb_uploader")
COOKIE_DIR.mkdir(parents=True, exist_ok=True)
