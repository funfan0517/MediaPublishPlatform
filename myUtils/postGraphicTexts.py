import asyncio
import os
import logging
from datetime import datetime
from pathlib import Path
from conf import BASE_DIR
from uploader.baseVideoUploader import FacebookVideo, YouTubeVideo, TikTokVideo
from utils.constant import TencentZoneTypes
from utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags
logger = logging.getLogger(__name__)


#初始化
def __init__(self, platform: str):
    self.platform = platform.lower()
    self.logger = get_logger(f"multi_uploader_{platform}")
    self.uploader_classes = {
        "facebook": FacebookVideo,
        "youtube": YouTubeVideo,
        "tiktok": TikTokVideo,
    }
    if self.platform not in self.uploader_classes:
        raise ValueError(f"不支持的平台: {platform}")


def post_graphic_text_common(platform,title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0, is_draft=False):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            uploader_class = self.uploader_classes[platform]
            app = uploader_class(title, str(file), tags, publish_datetimes[index], cookie, category, is_draft)
            asyncio.run(app.main(), debug=False)