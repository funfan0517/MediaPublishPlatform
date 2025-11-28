# -*- coding: utf-8 -*-
"""
通用多平台视频上传核心实现
"""
import os
import asyncio
from datetime import datetime
from playwright.async_api import Playwright, async_playwright
from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.files_times import get_absolute_path
from utils.log import get_logger

# 平台配置字典
PLATFORM_CONFIGS = {
    "facebook": {
        "name": "Facebook",
        "upload_url": "https://www.facebook.com/",
        "personal_url": "https://www.facebook.com/profile.php",
        "login_url": "https://www.facebook.com/",
        "selectors": {
            "upload_button": ['div[aria-label="照片/视频"]', 'div[aria-label="Photo/Video"]'],
            "publish_button": ['//span[text()="发帖"]', '//span[text()="Post"]', '//span[text()="Schedule"]', '//span[text()="发布"]'],
            "title_editor": [
                '[contenteditable="true"][role="textbox"][data-lexical-editor="true"]',
                '[aria-placeholder*="分享你的新鲜事"][contenteditable="true"]',
                '[aria-label="Add a description"]',
                '[aria-label="Write something..."]'
            ],
            "thumbnail_button": ["//span[contains(text(), 'Add')]", "//span[contains(text(), '添加')]"],
            "schedule_button": ["//span[text()='Schedule']", "//span[text()='定时']"],
            "date_input": '[aria-label="Date"]',
            "time_input": '[aria-label="Time"]',
        },
        "features": {
            "thumbnail": True,
            "schedule": True,
            "tags": True
        }
    },
    "youtube": {
        "name": "YouTube", 
        "upload_url": "https://www.youtube.com/upload",
        "personal_url": "https://www.youtube.com/",
        "login_url": "https://www.youtube.com/",
        "selectors": {
            "upload_button": ['//span[text()="上传视频"]', '//span[text()="Upload videos"]'],
            "publish_button": ['//span[text()="发布"]', '//span[text()="Publish"]'],
            "title_editor": ['#textbox[name="title"]', '//div[@id="textbox" and @name="title"]'],
            "description_input": ['#textbox[name="description"]', '//div[@id="textbox" and @name="description"]'],
            "thumbnail_button": ['//span[text()="上传缩略图"]', '//span[text()="Upload thumbnail"]'],
            "schedule_button": ['//span[text()="定时发布"]', '//span[text()="Schedule"]'],
        },
        "features": {
            "thumbnail": True,
            "schedule": True,
            "tags": False  # YouTube使用描述而不是标签
        }
    },
    "tiktok": {
        "name": "TikTok",
        "upload_url": "https://www.tiktok.com/upload",
        "personal_url": "https://www.tiktok.com/",
        "login_url": "https://www.tiktok.com/login",
        "selectors": {
            "upload_button": ['//div[text()="上传视频"]', '//div[text()="Upload video"]'],
            "publish_button": ['//button[contains(text(),"发布")]', '//button[contains(text(),"Post")]'],
            "title_editor": ['[data-text="true"]', '.public-DraftEditor-content'],
        },
        "features": {
            "thumbnail": False,
            "schedule": False,
            "tags": True
        }
    }
}


class BaseVideoUploader(object):
    """
    通用视频上传器基类
    """
    
    def __init__(self, platform, title, file_path, tags, publish_date, account_file, thumbnail_path=None):
        self.platform = platform.lower()
        self.title = title
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.thumbnail_path = thumbnail_path
        self.account_file = account_file
        self.local_executable_path = LOCAL_CHROME_PATH
        self.headless = LOCAL_CHROME_HEADLESS
        self.locator_base = None
        
        # 获取平台配置
        self.config = PLATFORM_CONFIGS.get(self.platform)
        if not self.config:
            raise ValueError(f"不支持的平台: {platform}")
        
        # 获取平台特定的日志器
        self.logger = get_logger(f"{self.platform}_uploader")
        
    async def main(self):
        """
        主入口函数
        """
        # 验证平台cookie是否有效
        if not await self.platform_setup(handle=True):
            raise Exception(f"{self.config['name']} Cookie验证失败")

        # 执行平台上传视频
        async with async_playwright() as playwright:
            await self.upload(playwright)

        self.logger.info(f"✅ 【{self.config['name']}】视频发布成功: {self.title}")
        return True

    async def upload(self, playwright: Playwright) -> None:
        """
        执行视频上传
        """
        self.logger.info(f'[+]开始上传-------{self.title}')
        
        # step1.创建浏览器实例
        browser = await playwright.chromium.launch(
            headless=self.headless, 
            executable_path=self.local_executable_path
        )
        self.logger.info(f"step1：【{self.config['name']}】浏览器实例已创建")

        # step2.创建上下文并加载cookie
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)
        self.logger.info(f"step2：【{self.config['name']}】上下文已创建并加载cookie")

        # step3.创建新页面，导航到上传页面
        page = await context.new_page()
        await page.goto(self.config['upload_url'], wait_until='domcontentloaded', timeout=60000)
        self.logger.info(f"step3：【{self.config['name']}】创作中心页面已加载完成")
        
        # step4.选择基础定位器
        await self.choose_base_locator(page)
        self.logger.info(f"step4：【{self.config['name']}】基础定位器已选择")

        # step5.上传视频文件
        await self.upload_video_file(page)
        self.logger.info(f"step5：【{self.config['name']}】视频文件已上传")

        # step6.检测上传状态
        await self.detect_upload_status(page)
        self.logger.info(f"step6：【{self.config['name']}】视频上传状态检测完成")
        
        # step7.添加标题和标签
        await self.add_title_tags(page)
        self.logger.info(f"step7：【{self.config['name']}】标题和标签已添加")
        
        # step8.上传缩略图（如果有）
        if self.config['features']['thumbnail'] and self.thumbnail_path:
            self.logger.info(f'[+] Uploading thumbnail file {self.title}')
            await self.upload_thumbnails(page)
            self.logger.info(f"step8：【{self.config['name']}】缩略图已上传")

        # step9.设置定时发布（如果需要）
        if self.config['features']['schedule'] and self.publish_date != 0:
            await self.set_schedule_time(page, self.publish_date)
            self.logger.info(f"step9：【{self.config['name']}】定时发布时间已设置")

        # step10.点击发布
        await self.click_publish(page)
        self.logger.info(f"step10：【{self.config['name']}】视频已发布")   

        # step11.重新保存最新cookie
        await context.storage_state(path=f"{self.account_file}")  
        self.logger.info(f"step11：【{self.config['name']}】cookie已更新")

        await asyncio.sleep(2)  # close delay for look the video status
        
        # step12.关闭所有页面和浏览器上下文
        await context.close()
        await browser.close()
        self.logger.info(f"step12：【{self.config['name']}】浏览器实例已关闭")

    async def choose_base_locator(self, page):
        """
        选择基础定位器
        """
        # 通用平台不需要处理iframe，直接使用page即可
        self.locator_base = page

    async def find_button(self, selector_list):
        """
        通用的按钮查找方法
        Args:
            selector_list: 所有可能的按钮选择器列表
        Returns:
            找到的按钮定位器对象，如果没找到则返回None
        """
        for selector in selector_list:
            # 检查当前选择器是否在页面上存在匹配的元素
            count = await self.locator_base.locator(selector).count()
            if count > 0:
                # 异步等待元素可交互（避免元素未加载完成）
                await self.locator_base.locator(selector).wait_for(state="visible", timeout=30000)
                # 返回找到的按钮定位器
                return self.locator_base.locator(selector)

        # 如果所有选择器都没找到，返回None
        self.logger.info("未找到任何按钮定位器")
        return None

    async def upload_video_file(self, page):
        """
        上传视频文件
        """
        try:
            upload_button = await self.find_button(self.config['selectors']['upload_button'])
            if not upload_button:
                raise Exception("未找到上传视频按钮")
            self.logger.info(f"  [-] 将点击上传视频按钮")
            await upload_button.wait_for(state='visible', timeout=30000)
            
            # 上传按钮，需要点击触发系统文件选择器
            async with page.expect_file_chooser() as fc_info:
                await upload_button.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.file_path)
            self.logger.info(f"通过系统文件选择器上传文件: {self.file_path}")
        except Exception as e:
            self.logger.error(f"选择视频文件失败: {str(e)}")
            raise

    async def detect_upload_status(self, page):
        """
        检测上传状态
        """
        while True:
            try:
                publish_button = await self.find_button(self.config['selectors']['publish_button'])
                
                # 检查发布按钮是否可点击
                if publish_button and await publish_button.get_attribute("disabled") is None:
                    self.logger.info("  [-]video uploaded.")
                    break
                else:
                    self.logger.info("  [-] video uploading...")
                    await asyncio.sleep(2)
                    # 检查是否有错误需要重试
                    error_selectors = [
                        'div:has-text("error"):visible',
                        'div:has-text("Error"):visible',
                        'div[class*="error"]:visible'
                    ]
                    error_element = await self.find_button(error_selectors)
                    if error_element:
                        self.logger.info("  [-] found error while uploading now retry...")
                        await self.handle_upload_error(page)
            except Exception as e:
                self.logger.info(f"  [-] video uploading... Error: {str(e)}")
                await asyncio.sleep(2)

    async def handle_upload_error(self, page):
        """
        处理上传错误，重新上传
        """
        self.logger.info("video upload error retrying.")
        try:
            file_input_selectors = ['input[type="file"]']
            file_input_button = await self.find_button(file_input_selectors)
            if file_input_button:
                await file_input_button.set_input_files(self.file_path)
        except Exception as e:
            self.logger.error(f"重新上传失败: {str(e)}")
    
    async def add_title_tags(self, page):
        """
        添加标题和标签
        """
        try:
            editor_button = await self.find_button(self.config['selectors']['title_editor'])
            if not editor_button:
                raise Exception("未找到标题输入框")
            self.logger.info(f"  [-] 将点击标题输入框")
            await editor_button.click()
            
            # 清空现有内容
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Delete")
            await page.wait_for_timeout(500)  # 等待500毫秒
                
            # 输入标题
            await page.keyboard.insert_text(self.title)
            await page.wait_for_timeout(500)  # 等待500毫秒
                
            # 输入标签（如果平台支持）
            if self.config['features']['tags'] and self.tags:
                await page.keyboard.press("Enter")
                await page.keyboard.press("Enter")
                    
                for index, tag in enumerate(self.tags, start=1):
                    self.logger.info("Setting the %s tag" % index)
                    await page.keyboard.insert_text(f"#{tag} ")
                    # 等待300毫秒
                    await page.wait_for_timeout(300)
        except Exception as e:
            self.logger.error(f"添加标题和标签失败: {str(e)}")

    async def upload_thumbnails(self, page):
        """
        上传缩略图
        """
        try:
            thumbnail_button = await self.find_button(self.config['selectors']['thumbnail_button'])
            if not thumbnail_button:
                raise Exception("未找到缩略图上传按钮")
            self.logger.info(f"  [-] 将点击上传缩略图按钮")
            await thumbnail_button.click()
            
            # 上传缩略图文件
            async with page.expect_file_chooser() as fc_info:
                await page.locator("//input[@type='file']").click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.thumbnail_path)
            
            self.logger.info("  [-] Thumbnail uploaded successfully")
        except Exception as e:
            self.logger.warning(f"  [-] Failed to upload thumbnail: {str(e)}")

    async def set_schedule_time(self, page, publish_date):
        """
        设置定时发布时间
        """
        schedule_button = await self.find_button(self.config['selectors']['schedule_button'])
        if not schedule_button:
            raise Exception("未找到定时发布按钮")
        self.logger.info(f"  [-] 将点击定时发布按钮")
        await schedule_button.wait_for(state='visible')
        await schedule_button.click()

        # 解析时间戳
        publish_datetime = publish_date
        if isinstance(publish_date, int):
            publish_datetime = datetime.fromtimestamp(publish_date)

        # 设置日期和时间
        date_input = self.config['selectors'].get('date_input')
        time_input = self.config['selectors'].get('time_input')
        
        if date_input:
            await page.fill(date_input, publish_datetime.strftime('%Y-%m-%d'))
        if time_input:
            await page.fill(time_input, publish_datetime.strftime('%H:%M'))
        
        self.logger.info(f"  [-] Schedule time set: {publish_datetime}")

    async def click_publish(self, page):
        """
        点击发布按钮并等待发布完成
        """
        max_attempts = 3  # 最大尝试次数
        attempt = 0
        publish_success = False
        
        while attempt < max_attempts and not publish_success:
            attempt += 1
            try:
                # 步骤1: 查找并点击发布按钮
                publish_button = await self.find_button(self.config['selectors']['publish_button'])
                if publish_button:
                    await publish_button.click()

                # 步骤2: 等待视频处理完成（通过检查上传按钮重新出现）
                self.logger.info("  [-] 等待视频处理和发布完成...")
                # 尝试查找上传按钮
                upload_button = await self.find_button(self.config['selectors']['upload_button'])
                self.logger.info(f"  [-] 第 {attempt} 次上传按钮状态: {await upload_button.is_visible()}")

                if upload_button:
                    await upload_button.wait_for(state='visible', timeout=30000)
                    publish_success = True
                    break
            except Exception:
                # 等待后重试
                self.logger.warning(f"  [-] 第 {attempt} 次点击发布按钮失败，等待后重试")
                await asyncio.sleep(min(attempt * 2, 10))
        
        # 最终状态检查
        if publish_success:
            self.logger.info("  [-] 视频发布流程已完成")
        else:
            self.logger.error(f"  [-] 在{max_attempts}次尝试后仍未能成功发布视频")
        return publish_success

    async def platform_setup(self, handle=False):
        """
        设置平台账户cookie
        """
        account_file = get_absolute_path(self.account_file, "cookiesFile")
        if not os.path.exists(account_file) or not await self.cookie_auth():
            if not handle:
                return False
            self.logger.info('[+] cookie file is not existed or expired. Now open the browser auto. Please login.')
            await self.get_platform_cookie(account_file)
        return True

    async def cookie_auth(self):
        """
        验证平台的cookie是否有效
        """
        async with async_playwright() as playwright:
            # 设置本地Chrome浏览器路径
            browser = await playwright.chromium.launch(headless=True, executable_path=LOCAL_CHROME_PATH)
            context = await browser.new_context(storage_state=self.account_file)
            context = await set_init_script(context)
            # 创建一个新的页面
            page = await context.new_page()
            # 访问平台个人中心页面url验证cookie，明确指定等待domcontentloaded状态
            personal_url = self.config['personal_url']
            await page.goto(personal_url, wait_until='domcontentloaded', timeout=60000)
            self.logger.info(f"【{self.config['name']}】个人中心页面DOM加载完成")
            
            try:
                # 检查是否登录成功（如果成功跳转到个人中心页面的url）
                current_url = page.url
                self.logger.info(f"当前页面URL: {current_url}")
                if personal_url in current_url:
                    self.logger.info("[+] cookie valid")
                    return True
                else:
                    self.logger.error("[+] cookie expired - not redirect to personal center")
                    return False
    
            except Exception as e:
                self.logger.error(f"[+] cookie validation error: {str(e)}")
                return False
            finally:
                await browser.close()

    async def get_platform_cookie(self, account_file):
        """
        获取平台登录cookie
        """
        async with async_playwright() as playwright:
            options = {
                'args': [
                    '--lang en-US',
                ],
                'headless': False,  # 登录时需要可视化
                'executable_path': LOCAL_CHROME_PATH,
            }
            # Make sure to run headed.
            browser = await playwright.chromium.launch(**options)
            # Setup context however you like.
            context = await browser.new_context()  # Pass any options
            context = await set_init_script(context)
            # Pause the page, and start recording manually.
            page = await context.new_page()
            url = self.config['login_url']
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await page.pause()
            # 点击调试器的继续，保存cookie
            await context.storage_state(path=account_file)
            await browser.close()


# 特定平台上传器类（用于向后兼容和特殊处理）
class FacebookVideo(BaseVideoUploader):
    """Facebook视频上传器"""
    def __init__(self, title, file_path, tags, publish_date, account_file, thumbnail_path=None):
        super().__init__("facebook", title, file_path, tags, publish_date, account_file, thumbnail_path)

class YouTubeVideo(BaseVideoUploader):
    """YouTube视频上传器"""
    def __init__(self, title, file_path, tags, publish_date, account_file, thumbnail_path=None):
        super().__init__("youtube", title, file_path, tags, publish_date, account_file, thumbnail_path)

class TikTokVideo(BaseVideoUploader):
    """TikTok视频上传器"""
    def __init__(self, title, file_path, tags, publish_date, account_file, thumbnail_path=None):
        super().__init__("tiktok", title, file_path, tags, publish_date, account_file, thumbnail_path)


# 工厂函数和便捷函数
async def run_upload(platform, title, file_path, tags, publish_date, account_file, **kwargs):
    """
    运行上传任务
    
    Args:
        platform (str): 平台名称 (facebook, youtube, tiktok等)
        title (str): 视频标题
        file_path (str): 视频文件路径
        tags (str): 标签
        publish_date (int): 发布时间戳
        account_file (str): Cookie文件路径
        **kwargs: 额外参数
    """
    uploader = BaseVideoUploader(platform, title, file_path, tags, publish_date, account_file, **kwargs)
    return await uploader.main()

# 特定平台的便捷函数
async def upload_to_facebook(title, file_path, tags, publish_date, account_file, **kwargs):
    """上传到Facebook的便捷函数"""
    return await run_upload("facebook", title, file_path, tags, publish_date, account_file, **kwargs)

async def upload_to_youtube(title, file_path, tags, publish_date, account_file, **kwargs):
    """上传到YouTube的便捷函数"""
    return await run_upload("youtube", title, file_path, tags, publish_date, account_file, **kwargs)

async def upload_to_tiktok(title, file_path, tags, publish_date, account_file, **kwargs):
    """上传到TikTok的便捷函数"""
    return await run_upload("tiktok", title, file_path, tags, publish_date, account_file, **kwargs)


if __name__ == "__main__":
    # 示例运行代码
    asyncio.run(upload_to_facebook(
        "测试视频",
        "videos/demo.mp4",
        "测试 标签",
        0,  # 立即发布
        "cookies/fb_cookie.json"
    ))
    
    # 或者使用通用函数
    asyncio.run(run_upload(
        "youtube",
        "YouTube测试视频", 
        "videos/demo.mp4",
        "测试 YouTube 标签",
        0,
        "cookies/yt_cookie.json"
    ))