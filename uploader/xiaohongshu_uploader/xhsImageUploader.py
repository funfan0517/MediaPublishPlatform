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


class xhsImageUploader(object):
    """
    小红书图文上传器类
    """
    
    def __init__(self, account_file, file_path, title, text, tags, publish_date):
        self.title = title
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.account_file = account_file
        self.local_executable_path = LOCAL_CHROME_PATH
        self.headless = LOCAL_CHROME_HEADLESS
        self.locator_base = None
        self.text = text
        
        # URL constants
        self.xiaohongshu_url = "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=image&openFilePicker=true"
        self.personal_url = "https://creator.xiaohongshu.com/new/home"
        self.login_url = "https://creator.xiaohongshu.com/login"
        
        # Selector lists
        self.upload_button_selectors = [
            'input.upload-input[type="file"]'
        ]
        self.publish_button_selectors = [
            'div.d-button-content span.d-text:has-text("发布")'
        ]
        self.error_selectors = [
            'div:has-text("error"):visible',
            'div:has-text("Error"):visible',
            'div[class*="error"]:visible'
        ]
        self.editor_button_locators = [
            # 标题输入框选择器
            'div.d-input.\--color-text-title.\--color-bg-fill input.d-text[type="text"]'
        ]
        self.textbox_selectors = [
            # 正文输入框选择器
            'div.tiptap.ProseMirror[contenteditable="true"][role="textbox"]'
        ]
        self.schedule_button_selectors = [
            "//span[text()='Schedule']",
            "//span[text()='定时']"
        ]
        self.file_input_selectors = ['input[type="file"]']
        
        # Timeout and retry constants
        self.timeout_30s = 30000
        self.timeout_60s = 60000
        self.max_publish_attempts = 3
        self.upload_check_interval = 2
        self.wait_timeout_500ms = 500
        self.wait_timeout_300ms = 300
        self.sleep_2s = 2
        self.login_wait_timeout = 10000
        self.max_retry_delay = 10
        self.date_format = '%Y-%m-%d'
        self.time_format = '%H:%M'
        self.file_input_selector = "//input[@type='file']"
        self.browser_lang = 'en-US'
        
        # Logging messages
        self.cookie_valid_msg = "[+] cookie valid"
        self.cookie_expired_msg = "[+] cookie expired - not redirect to personal center"
        self.cookie_validation_error_msg = "[+] cookie validation error"
        self.cookie_file_not_exist_msg = "[+] cookie file is not existed or expired. Now open the browser auto. Please login."
        self.login_prompt_msg = "请登录Facebook账户..."
        self.cookie_saved_msg = "Cookie已保存到"
        
        # Upload process messages
        self.upload_success_msg = "✅ 【Facebook】视频发布成功"
        self.start_upload_msg = "[+]Start Uploading-------"
        self.browser_created_msg = "step1：【Facebook】浏览器实例已创建"
        self.context_created_msg = "step2：【Facebook】上下文已创建并加载cookie"
        self.page_loaded_msg = "step3：【Facebook】创作中心页面已加载完成"
        self.locator_selected_msg = "step4：【Facebook】基础定位器已选择"
        self.video_uploaded_msg = "step5：【Facebook】视频文件已上传"
        self.upload_status_checked_msg = "step6：【Facebook】视频上传状态检测完成"
        self.title_tags_added_msg = "step7：【Facebook】标题和标签已添加"
        self.thumbnail_uploaded_msg = "step8：【Facebook】缩略图已上传"
        self.schedule_set_msg = "step9：【Facebook】定时发布时间已设置"
        self.video_published_msg = "step10：【Facebook】视频已发布"
        self.cookie_updated_msg = "step11：【Facebook】cookie已更新"
        self.browser_closed_msg = "step12：【Facebook】浏览器实例已关闭"
        self.uploading_thumbnail_msg = "[+] Uploading thumbnail file"
        self.button_not_found_msg = "未找到任何按钮定位器"
        self.upload_button_click_msg = "  [-] 将点击上传视频按钮"
        self.file_selector_upload_msg = "通过系统文件选择器上传文件"
        self.upload_failed_msg = "选择视频文件失败"
        self.video_upload_success_msg = "  [-]video uploaded."
        self.video_uploading_msg = "  [-] video uploading..."
        self.upload_error_msg = "  [-] found error while uploading now retry..."
        self.upload_error_retry_msg = "video upload error retrying."
        self.upload_retry_failed_msg = "重新上传失败"
        self.title_input_click_msg = "  [-] 将点击标题输入框"
        self.text_input_click_msg = "  [-] 将点击正文输入框"
        self.tag_setting_msg = "Setting the %s tag"
        self.title_tags_failed_msg = "添加标题和标签失败"
        self.thumbnail_button_click_msg = "  [-] 将点击上传缩略图按钮"
        self.thumbnail_success_msg = "  [-] Thumbnail uploaded successfully"
        self.schedule_button_click_msg = "  [-] 将点击定时发布按钮"
        self.schedule_time_set_msg = "  [-] Schedule time set"
        self.publish_waiting_msg = "  [-] 等待视频处理和发布完成..."
        self.publish_attempt_msg = "  [-] 第 %s 次上传按钮状态"
        self.publish_complete_msg = "  [-] 视频发布流程已完成"
        self.publish_failed_msg = "  [-] 在%s次尝试后仍未能成功发布视频"
        self.personal_page_loaded_msg = "平台个人中心页面DOM加载完成"
        self.current_url_msg = "当前页面URL"
        
        # Browser launch options
        self.browser_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--ignore-certificate-errors',
            '--start-maximized',
            '--disable-blink-features=AutomationControlled'
        ]
        self.slow_mo = 50

    async def main(self):
        """
        主入口函数
        """
        # 验证平台cookie是否有效(可选：如果已登录，可跳过验证)
        if not await platform_setup(self, handle=True):
            raise Exception("Cookie验证失败")

        # 执行平台上传视频
        async with async_playwright() as playwright:
            await self.upload(playwright)

        logger.info(f"{self.upload_success_msg}: {self.title}")
        return True

    async def upload(self, playwright: Playwright) -> None:
        """
        作用：执行视频上传
        """
        logger.info(f'{self.start_upload_msg}{self.title}')
        # step1.创建浏览器实例
        browser = await playwright.chromium.launch(
            headless=self.headless, 
            executable_path=self.local_executable_path
        )
        logger.info(self.browser_created_msg)


        # step2.创建上下文并加载cookie
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)
        logger.info(self.context_created_msg)


        # step3.创建新页面，导航到上传页面，明确指定等待domcontentloaded状态
        page = await context.new_page()
        await page.goto(self.facebook_url, wait_until='domcontentloaded', timeout=self.timeout_60s)
        logger.info(self.page_loaded_msg)
        
        # step4.选择基础定位器
        await self.choose_base_locator(page)
        logger.info(self.locator_selected_msg)

        # step5.上传视频文件
        await self.upload_video_file(page)
        logger.info(self.video_uploaded_msg)

        # step6.检测上传状态
        await self.detect_upload_status(page)
        logger.info(self.upload_status_checked_msg)
        
        # step7.添加标题和标签
        await self.add_title_tags(page)
        logger.info(self.title_tags_added_msg)

        # step9.设置定时发布（如果需要）
        if self.publish_date != 0:
            await self.set_schedule_time(page, self.publish_date)
            logger.info(self.schedule_set_msg)

        # step10.点击发布
        await self.click_publish(page)
        logger.info(self.video_published_msg)   

        # step11.重新保存最新cookie
        await context.storage_state(path=f"{self.account_file}")  
        logger.info(self.cookie_updated_msg)

        await asyncio.sleep(self.sleep_2s)  # close delay for look the video status
        
        # step12.关闭所有页面和浏览器上下文
        await context.close()
        await browser.close()
        logger.info(self.browser_closed_msg)

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
                await self.locator_base.locator(selector).wait_for(state="visible", timeout=self.timeout_30s)
                # logger.info(f"找到按钮定位器: {selector}, 是否可见: {await self.locator_base.locator(selector).is_visible()}")
                # 返回找到的按钮定位器
                return self.locator_base.locator(selector)

        # 如果所有选择器都没找到，返回None
        logger.info(self.button_not_found_msg)
        return None

    async def upload_video_file(self, page):
        """
        作用：上传视频文件
        网页中相关按钮：上传视频文件的按钮元素为（）
        """
        try:
            # 使用find_button方法查找上传按钮，支持中文和英文界面
            upload_button = await self.find_button(self.upload_button_selectors)
            if not upload_button:
                raise Exception("未找到上传视频按钮")
            logger.info(self.upload_button_click_msg)
            await upload_button.wait_for(state='visible', timeout=self.timeout_30s)
            
            # 上传按钮，需要点击触发系统文件选择器
            async with page.expect_file_chooser() as fc_info:
                await upload_button.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.file_path)
            logger.info(f"{self.file_selector_upload_msg}: {self.file_path}")
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
                # 使用find_button方法查找发布按钮
                publish_button = await self.find_button(self.publish_button_selectors)
                
                # 检查发布按钮是否可点击
                if publish_button and await publish_button.get_attribute("disabled") is None:
                    logger.info(self.video_upload_success_msg)
                    break
                else:
                    logger.info(self.video_uploading_msg)
                    await asyncio.sleep(self.upload_check_interval)
                    # 检查是否有错误需要重试，使用中文和英文选择器
                    error_element = await self.find_button(self.error_selectors)
                    if error_element:
                        logger.info(self.upload_error_msg)
                        await self.handle_upload_error(page)
            except Exception as e:
                logger.info(f"  [-] video uploading... Error: {str(e)}")
                await asyncio.sleep(self.upload_check_interval)

    async def handle_upload_error(self, page):
        """
        作用：处理上传错误，重新上传
        网页中相关按钮：系统文件管理器的上传按钮（input[type="file"]）
        """
        logger.info("video upload error retrying.")
        try:
            # 使用find_button方法查找文件上传按钮
            file_input_button = await self.find_button(self.file_input_selectors)
            if file_input_button:
                await file_input_button.set_input_files(self.file_path)
        except Exception as e:
            logger.error(f"{self.upload_retry_failed_msg}: {str(e)}")
    
    async def add_title_tags(self, page):
        """
        作用：添加标题和标签
        网页中相关按钮：添加标题和标签的按钮选择器（）
        """
        try:
            # 输入标题
            if self.title:
                # 使用find_button方法定位标题输入框，支持中文和英文界面
                editor_button = await self.find_button(self.editor_button_locators)
                if not editor_button:
                    raise Exception("未找到标题输入框")
                logger.info(f"{self.title_input_click_msg}: {await editor_button.text_content()}")
                await editor_button.click()
                
                # 清空现有内容
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Delete")
                await page.wait_for_timeout(self.wait_timeout_500ms)  # 等待500毫秒
                    
                # 输入标题
                await page.keyboard.insert_text(self.title)
                await page.wait_for_timeout(self.wait_timeout_500ms)  # 等待500毫秒


            # 输入正文
            if self.text:
                textbox_button = await self.find_button(self.textbox_selectors)
                if textbox_button:
                    logger.info(f"{self.text_input_click_msg}: {await textbox_button.text_content()}")
                    await textbox_button.click()
                    
                    # 清空现有内容（如果有）
                    await page.keyboard.press("Control+A")
                    await page.keyboard.press("Delete")
                    await page.wait_for_timeout(self.wait_timeout_500ms)  # 等待500毫秒
                        
                    # 输入正文
                    await page.keyboard.insert_text(self.text)
                    await page.wait_for_timeout(self.wait_timeout_500ms)  # 等待500毫秒
            
            # 输入标签（跟在正文后面）
            if self.tags:
                await page.keyboard.press("Enter")
                await page.keyboard.press("Enter")
                    
                for index, tag in enumerate(self.tags, start=1):
                    logger.info("Setting the %s tag" % index)
                    await page.keyboard.insert_text(f"#{tag} ")
                    # 等待300毫秒
                    await page.wait_for_timeout(self.wait_timeout_300ms)
        except Exception as e:
            logger.error(f"{self.title_tags_failed_msg}: {str(e)}")

    async def set_schedule_time(self, page, publish_date):
        """
        设置定时发布时间
        """
        # 使用find_button方法查找定时发布按钮
        schedule_button = await self.find_button(self.schedule_button_selectors)
        if not schedule_button:
            raise Exception("未找到定时发布按钮")
        logger.info(f"{self.schedule_button_click_msg}: {await schedule_button.text_content()}")
        await schedule_button.wait_for(state='visible')
        await schedule_button.click()

        # 解析时间戳
        publish_datetime = publish_date
        if isinstance(publish_date, int):
            publish_datetime = datetime.fromtimestamp(publish_date)

        # 设置日期和时间
        await page.fill('[aria-label="Date"]', publish_datetime.strftime(self.date_format))
        await page.fill('[aria-label="Time"]', publish_datetime.strftime(self.time_format))
        
        logger.info(f"{self.schedule_time_set_msg}: {publish_datetime}")

    async def click_publish(self, page):
        """
        作用：点击发布按钮并等待发布完成
        参数：
            page: Playwright页面对象
        返回值：
            bool: 发布是否成功
        """
        max_attempts = self.max_publish_attempts  # 最大尝试次数
        attempt = 0
        publish_success = False
        
        # 上传按钮选择器列表
        
        while attempt < max_attempts and not publish_success:
            attempt += 1
            try:
                # 步骤1: 查找并点击发布按钮
                publish_button = await self.find_button(self.publish_button_selectors)
                if publish_button:
                    await publish_button.click()

                # 步骤2: 等待视频处理完成（通过检查上传按钮重新出现）
                logger.info(self.video_processing_msg)
                # 尝试查找上传按钮
                upload_button = await self.find_button(self.upload_button_selectors)
                logger.info(f"{self.upload_attempt_msg} {attempt} {self.upload_button_status_msg}: {await upload_button.is_visible()}")

                if upload_button:
                    await upload_button.wait_for(state='visible', timeout=self.timeout_30s)
                    publish_success = True
                    break
            except Exception:
                # 等待后重试
                logger.warning(f"{self.publish_retry_msg} {attempt} {self.publish_retry_wait_msg}")
                await asyncio.sleep(min(attempt * 2, self.max_retry_delay))
        
        # 最终状态检查
        if publish_success:
            logger.info(self.publish_complete_msg)
        else:
            logger.error(f"{self.publish_failed_msg} {max_attempts} {self.publish_failed_attempts_msg}")
        return publish_success


async def platform_setup(self, handle=False):
    """
    设置平台账户cookie
    """
    account_file = get_absolute_path(self.account_file, "cookiesFile")
    if not os.path.exists(account_file) or not await cookie_auth(self):
        if not handle:
            return False
        logger.info(self.cookie_file_not_exist_msg)
        await get_platform_cookie(account_file, self.local_executable_path, self.timeout_60s, self.facebook_url, self.login_wait_timeout, self.browser_lang)
    return True


async def cookie_auth(self):
    """
    验证平台的cookie是否有效
    """
    async with async_playwright() as playwright:
        # 设置本地Chrome浏览器路径
        browser = await playwright.chromium.launch(headless=self.headless, executable_path=self.local_executable_path)
        context = await browser.new_context(storage_state=self.account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问平台个人中心页面url验证cookie，明确指定等待domcontentloaded状态
        await page.goto(self.personal_url, wait_until='domcontentloaded', timeout=self.timeout_60s)
        logger.info("平台个人中心页面DOM加载完成")
        
        try:
            # 检查是否登录成功（如果成功跳转到个人中心页面的url）
            current_url = page.url
            logger.info(f"当前页面URL: {current_url}")
            if self.personal_url in current_url:
                logger.info(self.cookie_valid_msg)
                return True
            else:
                logger.error(self.cookie_expired_msg)
                return False

        except Exception as e:
            logger.error(f"{self.cookie_validation_error_msg}: {str(e)}")
            return False
        finally:
            await browser.close()


async def get_platform_cookie(account_file, executable_path, timeout, facebook_url, login_wait_timeout, browser_lang):
    """
    获取平台登录cookie
    """
    async with async_playwright() as playwright:
        options = {
            'args': [
                f'--lang {browser_lang}',
            ],
            'headless': False,  # 登录时需要可视化
            'executable_path': executable_path,
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto(facebook_url, wait_until='domcontentloaded', timeout=timeout)
        await page.pause()
        # 等待用户登录完成
        logger.info(self.login_prompt_msg)
        await page.wait_for_timeout(login_wait_timeout)
        # 保存cookie
        await context.storage_state(path=account_file)
        logger.info(f"{self.cookie_saved_msg}: {account_file}")
        await browser.close()


    async def setup_upload_browser(self, playwright):
        """
        设置上传浏览器
        """
        # 创建浏览器实例
        browser = await playwright.chromium.launch(
            headless=self.headless,
            executable_path=self.local_executable_path,
            args=self.browser_args,
            slow_mo=self.slow_mo
        )
        
        # 创建上下文并加载cookie
        account_file = get_absolute_path(self.account_file, "cookiesFile")
        if os.path.exists(account_file):
            context = await browser.new_context(storage_state=account_file)
            context = await set_init_script(context)
            return browser, context
        else:
            raise FileNotFoundError(f"Cookie文件不存在: {account_file}")
