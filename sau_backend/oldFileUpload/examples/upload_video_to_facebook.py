"""
上传视频到Facebook平台示例
"""
import asyncio
from pathlib import Path
from conf import BASE_DIR

async def upload_to_facebook():
    """
    上传视频到Facebook平台
    """
    try:
        # 导入平台上传器
        from uploader.fb_uploader.main_chrome import FacebookVideo
        
        # 视频文件路径
        video_path = Path(BASE_DIR / "videos/demo.mp4")
        
        # Cookie文件路径
        cookie_path = Path(BASE_DIR / "cookiesFile/facebook_cookie.json")
        
        # 创建上传器实例
        uploader = FacebookVideo(
            title="Facebook测试视频标题",
            video_path=str(video_path),
            tags="测试 标签 Facebook",
            publish_time=0,  # 立即发布
            cookie_path=str(cookie_path)
            # 可以添加Facebook平台特定参数
        )
        
        # 执行上传
        await uploader.main()
        
        print("✅ Facebook视频上传成功")
        
    except Exception as e:
        print(f"❌ Facebook视频上传失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(upload_to_facebook())
