# -*- coding: utf-8 -*-
import re
from datetime import datetime

from playwright.async_api import Playwright, async_playwright
import os
import asyncio

from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from uploader.ins_uploader.ins_config import Ins_Locator
from utils.base_social_media import set_init_script
from utils.files_times import get_absolute_path
from utils.log import logger


def instagram_logger():
    """获取Instagram专用日志记录器"""
    return logger.get_logger("instagram_uploader")


async def cookie_auth(account_file):
    """
    验证cookie是否有效
    
    Args:
        account_file: cookie文件路径
        
    Returns:
        bool: cookie是否有效
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问Instagram创作者工作室上传页面
        await page.goto("https://www.instagram.com/direct/inbox/")
        await page.wait_for_load_state('networkidle')
        try:
            # 检查是否需要登录
            if await page.locator('input[name="username"]').count() > 0:
                instagram_logger().error("[+] cookie expired")
                return False
            instagram_logger().success("[+] cookie valid")
            return True
        except Exception as e:
            instagram_logger().error(f"Cookie验证出错: {str(e)}")
            return False


async def instagram_setup(account_file, handle=False):
    """
    检查并设置Instagram登录状态
    
    Args:
        account_file: cookie文件路径
        handle: 如果cookie无效，是否自动处理登录
        
    Returns:
        bool: 设置是否成功
    """
    account_file = get_absolute_path(account_file, "ins_uploader")
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        instagram_logger().info('[+] cookie file is not existed or expired. Now open the browser auto. Please login with your way.')
        await get_instagram_cookie(account_file)
    return True


async def get_instagram_cookie(account_file):
    """
    获取Instagram登录cookie
    
    Args:
        account_file: 保存cookie的文件路径
    """
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB',
            ],
            'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
        }
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # 打开Instagram登录页面
        page = await context.new_page()
        await page.goto("https://www.instagram.com/accounts/login/")
        await page.pause()
        # 等待用户手动登录后保存cookie
        await context.storage_state(path=account_file)


class InstagramVideo(object):
    """
    Instagram视频上传类
    
    Args:
        title: 视频标题
        file_path: 视频文件路径
        tags: 标签列表
        publish_date: 发布日期
        account_file: 账号cookie文件路径
        thumbnail_path: 缩略图路径
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
    
    async def set_schedule_time(self, page, publish_date):
        """
        设置视频发布时间
        
        Args:
            page: playwright页面对象
            publish_date: 发布日期时间对象
        """
        try:
            # 查找并点击发布时间选择按钮
            schedule_button = self.locator_base.locator('button:has-text("Schedule")')
            await schedule_button.wait_for(state='visible')
            await schedule_button.click()
            
            # 设置日期
            date_input = self.locator_base.locator('input[type="date"]')
            await date_input.fill(publish_date.strftime("%Y-%m-%d"))
            
            # 设置时间
            time_input = self.locator_base.locator('input[type="time"]')
            await time_input.fill(publish_date.strftime("%H:%M"))
            
            # 确认设置
            confirm_button = self.locator_base.locator('button:has-text("Confirm")')
            await confirm_button.click()
            
            instagram_logger().info(f"[+] 已设置发布时间: {publish_date}")
        except Exception as e:
            instagram_logger().error(f"设置发布时间失败: {str(e)}")
    
    async def handle_upload_error(self, page):
        """
        处理上传错误，重新上传
        
        Args:
            page: playwright页面对象
        """
        instagram_logger().info("video upload error retrying.")
        try:
            # 重新点击上传按钮
            upload_button = self.locator_base.locator('input[type="file"]')
            await upload_button.set_input_files(self.file_path)
        except Exception as e:
            instagram_logger().error(f"重新上传失败: {str(e)}")
    
    async def upload(self, playwright: Playwright) -> None:
        """
        上传视频到Instagram
        
        Args:
            playwright: playwright实例
        """
        browser = await playwright.chromium.launch(headless=self.headless, executable_path=self.local_executable_path)
        context = await browser.new_context(storage_state=f"{self.account_file}")
        page = await context.new_page()
        
        # 访问Instagram创建页面
        await page.goto("https://www.instagram.com/create/")
        instagram_logger().info(f'[+]Uploading-------{self.title}.mp4')
        
        await page.wait_for_load_state('networkidle')
        
        # 选择基本定位器
        self.locator_base = page.locator(Ins_Locator.default)
        
        # 上传视频文件
        await self.upload_video_file(page)
        
        # 添加标题和标签
        await self.add_title_tags(page)
        
        # 检测上传状态
        await self.detect_upload_status(page)
        
        if self.thumbnail_path:
            instagram_logger().info(f'[+] Uploading thumbnail file {self.title}.png')
            await self.upload_thumbnails(page)
        
        if self.publish_date != 0:
            await self.set_schedule_time(page, self.publish_date)
        
        # 点击发布按钮
        await self.click_publish(page)
        
        # 保存cookie
        await context.storage_state(path=f"{self.account_file}")
        instagram_logger().info('  [instagram] update cookie！')
        
        await asyncio.sleep(2)  # 延迟关闭，观察视频状态
        
        # 关闭浏览器
        await context.close()
        await browser.close()
    
    async def upload_video_file(self, page):
        """
        上传视频文件
        
        Args:
            page: playwright页面对象
        """
        try:
            # 查找文件上传输入框
            file_input = page.locator('input[type="file"]')
            await file_input.wait_for(state='attached')
            
            # 设置文件
            await file_input.set_input_files(self.file_path)
            instagram_logger().info("[+] 视频文件已选择")
        except Exception as e:
            instagram_logger().error(f"选择视频文件失败: {str(e)}")
            raise
    
    async def add_title_tags(self, page):
        """
        添加视频标题和标签
        
        Args:
            page: playwright页面对象
        """
        try:
            # 添加标题
            caption_field = self.locator_base.locator('textarea[placeholder="Write a caption..."]')
            await caption_field.wait_for(state='visible')
            await caption_field.click()
            await page.keyboard.insert_text(self.title)
            
            # 添加标签
            if self.tags:
                await page.keyboard.press("Enter")
                await page.keyboard.press("Enter")
                
                for tag in self.tags:
                    await page.keyboard.insert_text(f"#{tag} ")
                    await page.keyboard.press("Space")
            
            instagram_logger().info("[+] 已添加标题和标签")
        except Exception as e:
            instagram_logger().error(f"添加标题和标签失败: {str(e)}")
    
    async def upload_thumbnails(self, page):
        """
        上传缩略图
        
        Args:
            page: playwright页面对象
        """
        try:
            # 查找缩略图上传区域
            thumbnail_upload = self.locator_base.locator('input[type="file"]:visible').nth(1) if await self.locator_base.locator('input[type="file"]:visible').count() > 1 else None
            
            if thumbnail_upload:
                await thumbnail_upload.set_input_files(self.thumbnail_path)
                instagram_logger().info("[+] 缩略图已上传")
            else:
                instagram_logger().warning("[+] 未找到缩略图上传区域")
        except Exception as e:
            instagram_logger().error(f"上传缩略图失败: {str(e)}")
    
    async def click_publish(self, page):
        """
        点击发布按钮
        
        Args:
            page: playwright页面对象
        """
        success = False
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 查找发布按钮
                publish_button = self.locator_base.locator('button:has-text("Share"):not([disabled])')
                await publish_button.wait_for(state='visible', timeout=10000)
                await publish_button.click()
                
                # 等待发布完成
                await page.wait_for_url("https://www.instagram.com/", timeout=60000)
                instagram_logger().success("  [-] video published success")
                success = True
                break
            except Exception as e:
                retry_count += 1
                instagram_logger().error(f"  [-] 发布失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    await asyncio.sleep(2)
        
        if not success:
            instagram_logger().error("  [-] 多次尝试发布失败")
    
    async def detect_upload_status(self, page):
        """
        检测上传状态
        
        Args:
            page: playwright页面对象
        """
        max_wait_time = 300  # 最大等待时间（秒）
        wait_time = 0
        
        while wait_time < max_wait_time:
            try:
                # 检查是否可以发布
                publish_button = self.locator_base.locator('button:has-text("Share")')
                
                if await publish_button.count() > 0 and await publish_button.get_attribute("disabled") is None:
                    instagram_logger().info("  [-]video uploaded.")
                    break
                else:
                    instagram_logger().info("  [-] video uploading...")
                    await asyncio.sleep(2)
                    wait_time += 2
                    
                    # 检查是否有错误提示
                    error_elements = self.locator_base.locator('div:has-text("error")')
                    if await error_elements.count() > 0:
                        instagram_logger().info("  [-] found error while uploading, retrying...")
                        await self.handle_upload_error(page)
            except Exception as e:
                instagram_logger().info(f"  [-] 上传中，错误: {str(e)}")
                await asyncio.sleep(2)
                wait_time += 2
        
        if wait_time >= max_wait_time:
            instagram_logger().error("  [-] 上传超时")
    
    async def main(self):
        """
        主函数，执行上传过程
        """
        async with async_playwright() as playwright:
            await self.upload(playwright)
