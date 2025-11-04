import os
import tempfile
import asyncio
import time
import uuid
from contextvars import ContextVar
from typing import Tuple, Optional, List, Dict
from playwright.async_api import async_playwright, Playwright, BrowserContext, Page
from shared.log_util import log_debug, log_info, log_error

# 浏览器路径配置 - 从环境变量读取
CHROME_PATH = os.getenv("chrome_path")  # 如果环境变量中有chrome_path，则使用Chrome，否则使用Chromium
CHROME_USER_DATA_DIR = None


class BrowserSession:
    """浏览器会话，每个会话可以有多个页面"""
    def __init__(self, session_id: str, browser_context: BrowserContext):
        self.session_id = session_id
        self.browser_context = browser_context
        self.pages: List[Page] = []  # 会话中的所有页面
        self.current_page: Optional[Page] = None  # 当前活跃页面
        self.created_at = time.time()

    async def create_page(self) -> Page:
        """在会话中创建新页面"""
        page = await self.browser_context.new_page()
        page.set_default_timeout(5000)
        self.pages.append(page)
        self.current_page = page
        log_info(f"会话 {self.session_id} 创建新页面，当前页面数: {len(self.pages)}")
        return page

    @property
    def page(self) -> Optional[Page]:
        """获取当前页面（兼容性属性）"""
        return self.current_page

    async def close(self):
        """关闭会话的所有页面"""
        for page in self.pages:
            try:
                await page.close()
            except Exception as e:
                log_error(f"关闭页面失败: {e}")
        self.pages.clear()
        self.current_page = None
        log_info(f"已关闭会话 {self.session_id} 的所有页面")


class BrowserManager:
    """浏览器管理器，支持多会话"""
    def __init__(self):
        self._playwright_instance: Optional[Playwright] = None
        self._browser_context: Optional[BrowserContext] = None
        self._sessions: Dict[str, BrowserSession] = {}
        self._lock = asyncio.Lock()

    async def get_or_create_session(self, session_id: Optional[str] = None, create_new_page: bool = True) -> BrowserSession:
        """获取或创建浏览器会话

        Args:
            session_id: 会话ID，如果为None则自动生成
            create_new_page: 是否创建新页面，默认True
        """
        async with self._lock:
            # 如果没有指定session_id，生成一个新的
            if session_id is None:
                session_id = f"session_{uuid.uuid4().hex[:8]}"

            # 检查会话是否已存在
            if session_id in self._sessions:
                session = self._sessions[session_id]
                log_debug(f"复用现有会话组: {session_id}")

                if create_new_page:
                    # 在现有会话中创建新页面
                    await session.create_page()

                return session

            # 确保浏览器上下文存在
            await self._ensure_browser_context()

            # 创建新会话
            session = BrowserSession(session_id, self._browser_context)
            self._sessions[session_id] = session

            if create_new_page:
                # 创建第一个页面
                await session.create_page()

            log_info(f"创建新会话组: {session_id}，当前总会话数: {len(self._sessions)}")
            return session

    async def _ensure_browser_context(self):
        """确保浏览器上下文存在"""
        if self._playwright_instance is None or self._browser_context is None:
            log_debug("创建新的浏览器实例")
            self._playwright_instance, self._browser_context = await create_playwright()
        else:
            try:
                # 验证浏览器上下文是否还可用
                pages = self._browser_context.pages
                log_debug(f"浏览器上下文可用，当前页面数: {len(pages)}")
            except Exception as e:
                log_info(f"浏览器上下文不可用: {e}，重新创建")
                self._playwright_instance, self._browser_context = await create_playwright()

    async def close_session(self, session_id: str):
        """关闭指定会话"""
        async with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                await session.close()
                del self._sessions[session_id]
                log_info(f"已关闭会话 {session_id}，剩余会话数: {len(self._sessions)}")
            else:
                log_info(f"会话 {session_id} 不存在")

    async def close_all_sessions(self):
        """关闭所有会话"""
        async with self._lock:
            for session_id in list(self._sessions.keys()):
                await self._sessions[session_id].close()
            self._sessions.clear()
            log_info("已关闭所有会话")

    async def close_browser(self):
        """关闭浏览器和所有会话"""
        async with self._lock:
            # 关闭所有会话
            await self.close_all_sessions()

            # 关闭浏览器上下文
            if self._browser_context:
                try:
                    await self._browser_context.close()
                    log_info("已关闭浏览器上下文")
                except Exception as e:
                    log_error(f"关闭浏览器上下文失败: {e}")
                finally:
                    self._browser_context = None

            # 停止playwright
            if self._playwright_instance:
                try:
                    await self._playwright_instance.stop()
                    log_info("已停止playwright实例")
                except Exception as e:
                    log_error(f"停止playwright实例失败: {e}")
                finally:
                    self._playwright_instance = None

    def list_sessions(self) -> List[str]:
        """列出所有活跃会话"""
        return list(self._sessions.keys())

    def is_browser_available(self) -> bool:
        """检查浏览器是否可用"""
        if self._browser_context is None or self._playwright_instance is None:
            return False

        try:
            # 尝试获取页面列表来验证浏览器是否可用
            pages = self._browser_context.pages
            return True
        except Exception as e:
            log_info(f"浏览器不可用: {e}")
            return False


# 全局浏览器管理器实例
_browser_manager = BrowserManager()

# 使用ContextVar替代全局变量，支持并发执行
_current_session_context: ContextVar[Optional[str]] = ContextVar('current_session_context', default=None)

# 默认会话ID生成器
def generate_default_session_id() -> str:
    """生成默认的会话ID"""
    return f"session_{uuid.uuid4().hex[:8]}"

# 保持向后兼容的全局变量（已废弃，建议使用会话管理）
_playwright_instance: Optional[Playwright] = None
_browser_instance: Optional[BrowserContext] = None
_page_instance: Optional[Page] = None
_all_pages: List[Page] = []


class BrowserSessionContext:
    """浏览器会话上下文管理器 - 基于ContextVar实现并发安全"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.token = None

    async def __aenter__(self):
        self.token = _current_session_context.set(self.session_id)
        log_debug(f"切换到会话上下文: {self.session_id}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            _current_session_context.reset(self.token)
        log_debug(f"恢复会话上下文")


def set_current_session(session_id: str):
    """设置当前活跃会话ID"""
    _current_session_context.set(session_id)
    log_debug(f"设置当前会话: {session_id}")


def get_current_session_id() -> Optional[str]:
    """获取当前活跃会话ID"""
    return _current_session_context.get()


def with_session(session_id: str) -> BrowserSessionContext:
    """创建会话上下文管理器

    用法：
    async with with_session("my_session"):
        # 在这个代码块中，所有playwright_util函数都会使用my_session
        await click_add_behavior_tag_button()
    """
    return BrowserSessionContext(session_id)


def reset_playwright_cache():
    """重置playwright缓存，以便创建新的浏览器和页面实例"""
    log_info("reset playwright cache")
    global _playwright_instance, _browser_instance, _page_instance
    _playwright_instance = None
    _browser_instance = None
    _page_instance = None


async def remove_lock_files():
    """删除浏览器用户数据目录下的锁文件，防止浏览器打不开"""
    if not CHROME_USER_DATA_DIR:
        log_info("使用默认chromium浏览器，无需清理缓存")
        return
        
    lock_files_to_remove = ["SingletonLock", "SingletonCookie", "SingletonSocket"]
    if os.path.exists(CHROME_USER_DATA_DIR):
        for file_name in lock_files_to_remove:
            file_path = os.path.join(CHROME_USER_DATA_DIR, file_name)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    log_info(f"Successfully removed lock file: {file_path}")
                except OSError as e:
                    log_info(f"Error removing lock file {file_path}: {e}")
    else:
        log_info(f"User data directory not found, skipping lock file cleanup: {CHROME_USER_DATA_DIR}")


async def create_playwright(user_data_dir_name: str = "office_assistant_mcp_chrome_user_data") -> Tuple[Playwright, BrowserContext]:
    """创建playwright实例
    
    Args:
        user_data_dir_name: 用户数据目录名称，不同业务可以使用不同的目录
    """
    global CHROME_USER_DATA_DIR
    
    # 如果CHROME_USER_DATA_DIR为空，则在临时目录下创建一个固定的用户数据目录
    if CHROME_USER_DATA_DIR is None:
        temp_dir = os.path.join(tempfile.gettempdir(), user_data_dir_name)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        CHROME_USER_DATA_DIR = temp_dir
        log_info(f"使用Chrome临时用户数据目录: {CHROME_USER_DATA_DIR}")
        
    await remove_lock_files()
    p = await async_playwright().start()
    
    # 浏览器启动参数
    launch_options = {
        'user_data_dir': CHROME_USER_DATA_DIR,
        'headless': os.getenv('HEADLESS_MODE', 'false').lower() == 'true',  # headless模式可通过环境变量控制
        'args': ['--window-size=1920,900', '--ignore-certificate-errors']  # 设置窗口大小为1920x900
    }
    
    # 如果CHROME_PATH不为空，则使用指定的浏览器路径
    if CHROME_PATH:
        launch_options['executable_path'] = CHROME_PATH
        log_info(f"使用Chrome浏览器，路径: {CHROME_PATH}")
    else:
        log_info("使用默认Chromium浏览器")
    log_info(f"launch_options: {launch_options}")
    browser = await p.chromium.launch_persistent_context(**launch_options)
    return p, browser


async def get_playwright() -> Tuple[Playwright, BrowserContext, Page]:
    """获取playwright对象,如果没有则新建，有则返回全局缓存的对象

    注意：此函数已废弃，建议使用 get_browser_session() 获取会话

    新增功能：支持会话上下文，优先使用当前活跃会话
    """
    # 确定使用的会话ID优先级：当前上下文 > 生成新ID
    current_session_id = get_current_session_id()
    if current_session_id:
        session_id = current_session_id
    else:
        session_id = generate_default_session_id()
        log_info(f"生成新的会话ID: {session_id}")

    # 使用新的会话管理器，不创建新页面（向后兼容）
    session = await _browser_manager.get_or_create_session(session_id, create_new_page=False)

    # 如果会话没有页面，创建一个
    if not session.pages:
        await session.create_page()

    # 保持向后兼容
    global _playwright_instance, _browser_instance, _page_instance
    _playwright_instance = _browser_manager._playwright_instance
    _browser_instance = session.browser_context
    _page_instance = session.current_page

    return _playwright_instance, _browser_instance, _page_instance


async def get_browser_session(session_id: Optional[str] = None) -> BrowserSession:
    """获取浏览器会话（不创建新页面）

    Args:
        session_id: 会话ID，如果为None则自动生成

    Returns:
        BrowserSession: 浏览器会话对象
    """
    # 获取会话但不创建新页面
    return await _browser_manager.get_or_create_session(session_id, create_new_page=False)


async def get_or_create_browser_session_with_page(session_id: Optional[str] = None) -> BrowserSession:
    """获取或创建浏览器会话并确保有至少一个页面

    Args:
        session_id: 会话ID，如果为None则自动生成

    Returns:
        BrowserSession: 浏览器会话对象（确保至少有一个页面）
    """
    session = await _browser_manager.get_or_create_session(session_id, create_new_page=False)

    # 如果会话没有页面，创建一个
    if not session.pages:
        await session.create_page()

    return session


async def create_new_page_in_session(session_id: Optional[str] = None) -> BrowserSession:
    """在指定会话中创建新页面

    Args:
        session_id: 会话ID，如果为None则自动生成

    Returns:
        BrowserSession: 浏览器会话对象（已创建新页面）
    """
    # 总是创建新页面
    return await _browser_manager.get_or_create_session(session_id, create_new_page=True)


async def close_browser_session(session_id: str):
    """关闭指定的浏览器会话"""
    await _browser_manager.close_session(session_id)


async def list_browser_sessions() -> List[str]:
    """列出所有活跃的浏览器会话"""
    return _browser_manager.list_sessions()


async def create_new_tab() -> Page:
    """创建新的标签页（已废弃，建议使用 get_browser_session 获取新会话）

    Returns:
        Page: 新创建的页面实例
    """
    # 为了向后兼容，创建一个新会话
    session = await get_browser_session()

    # 兼容旧的全局页面列表
    global _all_pages
    _all_pages.append(session.page)

    log_info(f"创建新标签页，当前总标签页数量: {len(_all_pages)}")
    return session.page


async def close_tab(page: Page):
    """关闭指定的标签页

    Args:
        page: 要关闭的页面实例
    """
    global _all_pages

    try:
        await page.close()
        if page in _all_pages:
            _all_pages.remove(page)
        log_info(f"已关闭标签页，剩余标签页数量: {len(_all_pages)}")
    except Exception as e:
        log_error(f"关闭标签页失败: {e}")


async def close_all_tabs():
    """关闭所有标签页（已废弃，建议使用 close_all_browser_sessions）"""
    global _all_pages

    for page in _all_pages.copy():
        try:
            await page.close()
        except Exception as e:
            log_error(f"关闭标签页失败: {e}")

    _all_pages.clear()
    log_info("已关闭所有标签页")


async def close_all_browser_sessions():
    """关闭所有浏览器会话"""
    await _browser_manager.close_all_sessions()


async def close_playwright():
    """关闭并清除缓存的playwright和browser实例"""
    log_debug("关闭playwright")

    # 关闭新的浏览器管理器
    await _browser_manager.close_browser()

    # 清理向后兼容的全局变量
    global _playwright_instance, _browser_instance, _page_instance, _all_pages
    await close_all_tabs()
    _playwright_instance = None
    _browser_instance = None
    _page_instance = None
    _all_pages = []


def update_global_page(page: Page):
    """更新全局页面实例
    
    Args:
        page: 新的页面实例
    """
    global _page_instance
    _page_instance = page
    log_info(f"已更新全局页面实例")


def is_browser_available() -> bool:
    """检查浏览器是否已经启动并可用

    Returns:
        bool: 浏览器可用返回True，否则返回False
    """
    return _browser_manager.is_browser_available()