#!/usr/bin/env python3
"""
MCP会话管理器 - 解决MCP工具调用间session连续性问题

MCP特性：每个工具调用都是独立的请求，无法直接共享状态
解决方案：全局session管理，支持自动创建、复用、清理
"""
import time
from typing import Optional, Dict
from shared.log_util import log_info, log_debug
from shared.browser_manager import (
    get_browser_session,
    create_new_page_in_session,
    get_or_create_browser_session_with_page,
    set_current_session,
    get_current_session_id
)

class MCPSessionManager:
    """MCP会话管理器 - 确保工具调用间的session连续性"""

    def __init__(self):
        self._active_session_id: Optional[str] = None

    def get_active_session_id(self) -> Optional[str]:
        """获取当前活跃的session ID"""
        return self._active_session_id

    def set_active_session_id(self, session_id: str):
        """设置活跃的session ID"""
        self._active_session_id = session_id
        log_debug(f"设置活跃session: {session_id}")

        # 同时设置到ContextVar中
        set_current_session(session_id)

    def clear_active_session(self):
        """清除活跃session"""
        if self._active_session_id:
            log_info(f"清除活跃session: {self._active_session_id}")
            self._active_session_id = None

# 全局session管理器实例
_mcp_session_manager = MCPSessionManager()

async def get_mcp_session(create_page: bool = True, session_hint: str = "mcp"):
    """
    获取MCP工具使用的session

    Args:
        create_page: 是否需要创建页面（如果session没有页面的话）
        session_hint: session提示名称，用于生成新session时的标识

    Returns:
        BrowserSession: 浏览器会话实例
    """
    global _mcp_session_manager

    # 首先检查ContextVar中是否已有session（测试场景）
    from shared.browser_manager import get_current_session_id
    context_session_id = get_current_session_id()

    if context_session_id:
        # 使用ContextVar中的session，不要覆盖
        log_debug(f"使用ContextVar中的session: {context_session_id}")
        if create_page:
            session = await get_or_create_browser_session_with_page(context_session_id)
        else:
            session = await get_browser_session(context_session_id)
        return session

    # 获取当前活跃的session
    active_session_id = _mcp_session_manager.get_active_session_id()

    if active_session_id:
        # 复用现有session
        if create_page:
            session = await get_or_create_browser_session_with_page(active_session_id)
        else:
            session = await get_browser_session(active_session_id)

        return session
    else:
        # 创建新session
        session_id = f"{session_hint}_{int(time.time())}"

        if create_page:
            session = await get_or_create_browser_session_with_page(session_id)
        else:
            session = await get_browser_session(session_id)

        # 设置为活跃session
        _mcp_session_manager.set_active_session_id(session_id)

        return session

async def get_mcp_session_with_new_page(session_hint: str = "mcp"):
    """
    获取MCP session并在其中创建新页面

    Args:
        session_hint: session提示名称

    Returns:
        BrowserSession: 包含新页面的浏览器会话实例
    """
    global _mcp_session_manager

    # 首先检查ContextVar中是否已有session（测试场景）
    from shared.browser_manager import get_current_session_id
    context_session_id = get_current_session_id()

    if context_session_id:
        # 使用ContextVar中的session
        log_debug(f"在ContextVar session {context_session_id} 中创建新页面")
        session = await create_new_page_in_session(context_session_id)
        return session

    # 获取当前活跃的session
    active_session_id = _mcp_session_manager.get_active_session_id()

    if active_session_id:
        # 在现有session中创建新页面
        log_debug(f"在活跃session {active_session_id} 中创建新页面")
        session = await create_new_page_in_session(active_session_id)
        return session
    else:
        # 创建新session和页面
        session_id = f"{session_hint}_{int(time.time())}"
        log_info(f"创建新的MCP session: {session_id}")

        session = await create_new_page_in_session(session_id)

        # 设置为活跃session
        _mcp_session_manager.set_active_session_id(session_id)

        return session

def reset_mcp_session():
    """重置MCP session（用于开始新的工作流程）"""
    global _mcp_session_manager
    log_info("重置MCP session管理器")
    _mcp_session_manager.clear_active_session()

def get_mcp_session_info() -> Dict[str, any]:
    """获取当前MCP session信息（用于调试）"""
    global _mcp_session_manager
    return {
        "active_session_id": _mcp_session_manager.get_active_session_id()
    }
