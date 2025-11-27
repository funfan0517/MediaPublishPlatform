# -*- coding: utf-8 -*-
"""
Facebook平台视频上传核心实现
"""
import os
import asyncio
from datetime import datetime
from playwright.async_api import Playwright, async_playwright
from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.files_times import get_absolute_path
from utils.log import facebook_logger as logger


class FacebookVideo(object):
    """
    Facebook视频上传器类
    """
    
    def __init__(self, title, file_path, tags, publish_date, account_file, thumbnail_path=None):
        self.title = title
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.thumbnail_path = thumbnail_path
        self.account_file = account_file
        self.local_executable_path = LOCAL_CHROME_PATH
        self.headless = LOCAL_CHROME_HEADLESS
        self.locator_base = None

    async def main(self):
        """
        主入口函数
        """
        # 验证cookie(可选：如果已登录，可跳过验证)
        #if not await facebook_setup(self.account_file, handle=True):
        #    raise Exception("Cookie验证失败")

        # 执行上传
        async with async_playwright() as playwright:
            await self.upload(playwright)

        logger.info(f"✅ Facebook视频发布成功: {self.title}")
        return True

    async def upload(self, playwright: Playwright) -> None:
        """
        作用：执行视频上传
        """
        logger.info(f'[+]Start Uploading-------{self.title}')
        # step1.创建浏览器实例
        browser = await playwright.chromium.launch(
            headless=self.headless, 
            executable_path=self.local_executable_path
        )
        logger.info("step1：【Facebook】浏览器实例已创建")


        # step2.创建上下文并加载cookie
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)
        logger.info("step2：【Facebook】上下文已创建并加载cookie")


        # step3.创建新页面，导航到上传页面，明确指定等待domcontentloaded状态
        page = await context.new_page()
        facebook_url = "https://www.facebook.com/"
        await page.goto(facebook_url, wait_until='domcontentloaded', timeout=60000)
        logger.info("step3：【Facebook】创作中心页面已加载完成")
        
        # step4.选择基础定位器
        await self.choose_base_locator(page)
        logger.info("step4：【Facebook】基础定位器已选择")

        # step5.上传视频文件
        await self.upload_video_file(page)
        logger.info("step5：【Facebook】视频文件已上传")

        # step6.检测上传状态
        await self.detect_upload_status(page)
        logger.info("step6：【Facebook】视频上传状态检测完成")
        
        # step7.添加标题和标签
        await self.add_title_tags(page)
        logger.info("step7：【Facebook】标题和标签已添加")
        
        # step8.上传缩略图（如果有）
        if self.thumbnail_path:
            logger.info(f'[+] Uploading thumbnail file {self.title}')
            await self.upload_thumbnails(page)
            logger.info("step8：【Facebook】缩略图已上传")

        # step9.设置定时发布（如果需要）
        if self.publish_date != 0:
            await self.set_schedule_time(page, self.publish_date)
            logger.info("step9：【Facebook】定时发布时间已设置")

        # step10.点击发布
        await self.click_publish(page)
        logger.info("step10：【Facebook】视频已发布")   

        # step11.重新保存最新cookie
        await context.storage_state(path=f"{self.account_file}")  
        logger.info("step11：【Facebook】cookie已更新")
        await asyncio.sleep(2)  # close delay for look the video status
        
        # step12.关闭所有页面和浏览器上下文
        await context.close()
        await browser.close()
        logger.info("step12：【Facebook】浏览器实例已关闭")

    async def choose_base_locator(self, page):
        """
        选择基础定位器
        """
        # Facebook通常不需要iframe处理，直接使用page
        self.locator_base = page

    async def upload_video_file(self, page):
        """
        作用：上传视频文件
        网页中相关按钮：上传视频文件的按钮元素为（）
        """
        try:
            # 点击上传按钮（照片/视频），使用指定的选择器
            facebook_upload_selector = 'div[aria-label="照片/视频"]'
            logger.info(f"  [-] 将点击上传视频按钮: {facebook_upload_selector}")
            upload_button = self.locator_base.locator(facebook_upload_selector)
            await upload_button.wait_for(state='visible', timeout=30000)
            
            # 上传按钮，需要点击触发系统文件选择器
            async with page.expect_file_chooser() as fc_info:
                await upload_button.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.file_path)
            logger.info(f"通过系统文件选择器上传文件: {self.file_path}")
        except Exception as e:
            logger.error(f"选择视频文件失败: {str(e)}")
            raise

    async def detect_upload_status(self, page):
        """
        作用：检测上传状态
        网页中相关按钮：发布按钮选择器（）
        """
        while True:
            try:
                # 匹配中文发帖按钮和英文发布按钮，与click_publish方法保持一致
                facebook_publish_button = self.locator_base.locator('//span[text()="发帖"]').or_(
                    self.locator_base.locator('//span[text()="Post"]').or_(
                        self.locator_base.locator('//span[text()="Schedule"]').or_(
                            self.locator_base.locator('//span[text()="发布"]')
                        )
                    )
                )
                
                # 检查发布按钮是否可点击
                if await facebook_publish_button.get_attribute("disabled") is None:
                    logger.info("  [-]video uploaded.")
                    break
                else:
                    logger.info("  [-] video uploading...")
                    await asyncio.sleep(2)
                    # 检查是否有错误需要重试，使用中文和英文选择器
                    facebook_upload_selector = ['div[aria-label="照片/视频"]']
                    for selector in facebook_upload_selector:
                        if await self.locator_base.locator(selector).count():
                            logger.info("  [-] found some error while uploading now retry...")
                            await self.handle_upload_error(page)
                            break
            except Exception as e:
                logger.info(f"  [-] video uploading... Error: {str(e)}")
                await asyncio.sleep(2)

    async def handle_upload_error(self, page):
        """
        作用：处理上传错误，重新上传
        网页中相关按钮：系统文件管理器的上传按钮（input[type="file"]）
        """
        instagram_logger.info("video upload error retrying.")
        try:
            # 重新选择文件
            upload_button = self.locator_base.locator('input[type="file"]')
            await upload_button.set_input_files(self.file_path)
        except Exception as e:
            instagram_logger.error(f"重新上传失败: {str(e)}")
    
    async def add_title_tags(self, page):
        """
        作用：添加标题和标签
        网页中相关按钮：添加标题和标签的按钮选择器（）
        """
        try:
            # 使用更通用的选择器定位标题输入框，支持中文和英文界面
            facebook_editor_locators = [
                # 中文界面选择器
                '[contenteditable="true"][role="textbox"][data-lexical-editor="true"]',
                '[aria-placeholder*="分享你的新鲜事"][contenteditable="true"]',
                # 英文界面选择器
                '[aria-label="Add a description"]',
                '[aria-label="Write something..."]'
            ]

            editor_locator = None
            for selector in facebook_editor_locators:
                if await self.locator_base.locator(selector).count() > 0:
                    editor_locator = self.locator_base.locator(selector)
                    logger.info(f"  [-] 将点击标题输入框: {await editor_locator.text_content()}")
                    break
            if not editor_locator:
                raise Exception("未找到标题输入框")
            await editor_locator.click()
            
            # 清空现有内容
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Delete")         
            await page.wait_for_timeout(500)  # 等待500毫秒
                
            # 输入标题
            await page.keyboard.insert_text(self.title)
            await page.wait_for_timeout(500)  # 等待500毫秒
                
            # 输入标签
            if self.tags:
                await page.keyboard.press("Enter")
                await page.keyboard.press("Enter")
                    
                for index, tag in enumerate(self.tags, start=1):
                    logger.info("Setting the %s tag" % index)
                    await page.keyboard.insert_text(f"#{tag} ")
                    await page.wait_for_timeout(300)
                      # 等待300毫秒
        except Exception as e:
            logger.error(f"添加标题和标签失败: {str(e)}")

    async def upload_thumbnails(self, page):
        """
        作用：上传缩略图
        网页中相关按钮：上传缩略图的按钮选择器（）
        """
        try:
            # 等待并点击缩略图上传按钮
            thumbnail_button = self.locator_base.locator("//span[contains(text(), 'Add')] >> visible=true")
            logger.info(f"  [-] 将点击上传缩略图按钮: {await thumbnail_button.text_content()}")
            await thumbnail_button.click()
            
            # 上传缩略图文件
            async with page.expect_file_chooser() as fc_info:
                await page.locator("//input[@type='file']").click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.thumbnail_path)
            
            logger.info("  [-] Thumbnail uploaded successfully")
        except Exception as e:
            logger.warning(f"  [-] Failed to upload thumbnail: {str(e)}")

    async def set_schedule_time(self, page, publish_date):
        """
        设置定时发布时间
        """
        schedule_button = self.locator_base.locator("//span[text()='Schedule']")
        logger.info(f"  [-] 将点击定时发布按钮: {await schedule_button.text_content()}")
        await schedule_button.wait_for(state='visible')
        await schedule_button.click()

        # 解析时间戳
        publish_datetime = publish_date
        if isinstance(publish_date, int):
            publish_datetime = datetime.fromtimestamp(publish_date)

        # 设置日期和时间
        await page.fill('[aria-label="Date"]', publish_datetime.strftime('%Y-%m-%d'))
        await page.fill('[aria-label="Time"]', publish_datetime.strftime('%H:%M'))
        
        logger.info(f"  [-] Schedule time set: {publish_datetime}")

    async def click_publish(self, page):
        """
        作用：点击发布按钮
        网页中相关按钮：发布按钮选择器（）
        """
        while True:
            try:
                # 匹配中文发帖按钮和英文发布按钮
                publish_button = self.locator_base.locator('//span[text()="发帖"]').or_(
                    self.locator_base.locator('//span[text()="Post"]').or_(
                        self.locator_base.locator('//span[text()="Schedule"]').or_(
                            self.locator_base.locator('//span[text()="发布"]')
                        )
                    )
                )
                
                # 打印publish_button的文本
                button_text = await publish_button.text_content() if await publish_button.count() > 0 else "Not found"
                logger.info(f"  [-] 将点击发布按钮: {button_text}")
                
                if await publish_button.count():
                    await publish_button.click()

                await page.wait_for_url("https://www.facebook.com/",  timeout=60000)
                break
            except Exception as e:
                logger.exception(f"  [-] Exception: {e}")
                logger.info("  [-] video publishing")
                await asyncio.sleep(0.5)


async def cookie_auth(account_file):
    """
    验证cookie是否有效
    """
    async with async_playwright() as playwright:
        # 设置本地Chrome浏览器路径
        browser = await playwright.chromium.launch(headless= LOCAL_CHROME_HEADLESS, executable_path=self.local_executable_path)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问Facebook上传页面验证cookie，明确指定等待domcontentloaded状态
        await page.goto("https://www.facebook.com/", wait_until='domcontentloaded', timeout=60000)
        logger.info("Facebook页面DOM加载完成")
        
        try:
            # 检查是否登录成功
            login_indicators = [
                'div[aria-label="照片/视频"]',
                'div[aria-label="Photo/Video"]'
            ]
            
            for indicator in login_indicators:
                if await page.locator(indicator).count() > 0:
                    logger.info("[+] cookie valid")
                    return True
            
            # 如果所有选择器都失败，记录页面内容以便调试
            logger.error("[+] cookie expired - no login indicators found")
            return False
        except Exception as e:
            logger.error(f"[+] cookie validation error: {str(e)}")
            return False
        finally:
            await browser.close()


async def facebook_setup(account_file, handle=False):
    """
    设置Facebook账户cookie
    """
    account_file = get_absolute_path(account_file, "fb_uploader")
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        logger.info('[+] cookie file is not existed or expired. Now open the browser auto. Please login.')
        await get_facebook_cookie(account_file)
    return True


async def get_facebook_cookie(account_file):
    """
    获取Facebook登录cookie
    """
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-US',
            ],
            'headless': False,  # 登录时需要可视化
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://www.facebook.com/login")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)
        await browser.close()


async def setup_upload_browser(account_file, playwright):
    """
    设置上传浏览器
    """
    # 创建浏览器实例
    browser = await playwright.chromium.launch(
        headless=LOCAL_CHROME_HEADLESS,
        executable_path=LOCAL_CHROME_PATH,
        args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--ignore-certificate-errors',
            '--start-maximized',
            '--disable-blink-features=AutomationControlled',
        ],
        slow_mo=50
    )
    
    # 创建上下文并加载cookie
    if os.path.exists(account_file):
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        return browser, context
    else:
        raise FileNotFoundError(f"Cookie文件不存在: {account_file}")


def get_video_info(file_path):
    """
    获取视频信息
    """
    import json
    from utils.media_info import get_media_info
    
    media_info = get_media_info(file_path)
    logger.info(f"[+]Video info: {json.dumps(media_info, ensure_ascii=False)}")
    return media_info


async def run_upload(title, file_path, tags, publish_date, account_file, **kwargs):
    """
    运行上传任务
    
    Args:
        title (str): 视频标题
        file_path (str): 视频文件路径
        tags (str): 标签
        publish_date (int): 发布时间戳
        account_file (str): Cookie文件路径
        **kwargs: 额外参数
    """
    uploader = FacebookVideo(title, file_path, tags, publish_date, account_file, **kwargs)
    return await uploader.main()


if __name__ == "__main__":
    # 示例运行代码
    asyncio.run(run_upload(
        "测试视频",
        "videos/demo.mp4",
        "测试 标签",
        0,  # 立即发布
        "cookies/fb_cookie.json"
    ))