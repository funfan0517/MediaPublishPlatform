# -*- coding: utf-8 -*-
"""
Facebook平台视频上传通用实现（基于基础上传器类）
"""
import asyncio
import os
import time
from ..baseVideoUploader import FacebookVideo as BaseFacebookVideo
from utils.log import facebook_logger as logger

# Facebook平台上传相关配置
FB_CONFIG = {
    # 上传重试次数
    'MAX_RETRY': 3,
    # 上传状态检查间隔（秒）
    'STATUS_CHECK_INTERVAL': 5,
    # 上传超时时间（秒）
    'UPLOAD_TIMEOUT': 3600,
    # 页面加载超时（秒）
    'PAGE_LOAD_TIMEOUT': 30,
    # 操作超时（秒）
    'OPERATION_TIMEOUT': 60
}


class FacebookVideo(BaseFacebookVideo):
    """
    Facebook视频上传器类（基于通用基础上传器）
    继承自基础上传器，并保持与原实现的兼容性
    """
    
    def __init__(self, title, file_path, tags, publish_date, account_file, thumbnail_path=None):
        # 调用父类构造函数，父类会自动处理platform为'facebook'
        super().__init__(title, file_path, tags, publish_date, account_file, thumbnail_path)
        
        # 确保日志器与原实现一致
        self.logger = logger
        
        # 添加原实现中的相关属性
        self.browser = None
        self.context = None
        self.page = None
        self.upload_status = ""
        self.error_message = ""
        self.error_count = 0


async def main(title, file_path, tags, publish_date, account_file, thumbnail_path=None):
    """
    主函数，用于外部调用，与main_chrome.py保持一致
    
    Args:
        title (str): 视频标题
        file_path (str): 视频文件路径
        tags (list): 标签列表
        publish_date (int): 发布时间戳，0表示立即发布
        account_file (str): Cookie文件路径
        thumbnail_path (str, optional): 缩略图文件路径，默认为None
        
    Returns:
        bool: 上传是否成功
    """
    try:
        # 验证参数
        if not os.path.exists(file_path):
            logger.error(f"视频文件不存在: {file_path}")
            return False
            
        if thumbnail_path and not os.path.exists(thumbnail_path):
            logger.error(f"缩略图文件不存在: {thumbnail_path}")
            return False
        
        # 创建上传器实例
        uploader = FacebookVideo(
            title=title,
            file_path=file_path,
            tags=tags,
            publish_date=publish_date,
            account_file=account_file,
            thumbnail_path=thumbnail_path
        )
        
        logger.info(f"开始上传视频到Facebook: {title}")
        # 执行上传
        success = await uploader.main()
        
        if success:
            logger.info(f"视频上传成功: {title}")
        else:
            logger.error(f"视频上传失败: {title}")
            
        return success
    except Exception as e:
        logger.error(f"上传过程中发生错误: {str(e)}")
        raise


# 提供便捷的运行函数，便于测试和调用
def run_facebook_upload(title, file_path, tags, publish_date, account_file, thumbnail_path=None):
    """同步运行Facebook视频上传的便捷函数"""
    return asyncio.run(main(
        title=title,
        file_path=file_path,
        tags=tags,
        publish_date=publish_date,
        account_file=account_file,
        thumbnail_path=thumbnail_path
    ))


if __name__ == "__main__":
    # 示例运行代码
    asyncio.run(main(
        "测试视频",
        "videos/demo.mp4",
        ["测试", "标签"],
        0,  # 立即发布
        "cookies/fb_cookie.json"
    ))
