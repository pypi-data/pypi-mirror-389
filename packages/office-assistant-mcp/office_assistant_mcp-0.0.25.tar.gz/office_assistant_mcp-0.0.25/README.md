# MCP自动化工具集合

本项目包含两个独立的MCP工具包：
- **office-assistant-mcp**: 客群管理和短信营销自动化
- **commission-setting-mcp**: 佣金设置自动化

## 项目架构

```
office_assistant_mcp/
├── src/
│   ├── office_assistant_mcp/          # 客群短信业务
│   ├── commission_setting_mcp/        # 佣金设置业务  
│   └── shared/                        # 共享基础组件
├── pyproject.toml                     # office-assistant-mcp配置
├── pyproject_commission.toml          # commission-setting-mcp配置
├── build_and_upload_pypi.sh          # office包构建脚本
└── build_and_upload_commission.sh    # 佣金包构建脚本
```

## 包管理
使用uv

## 安装依赖
clone项目后，使用uv安装依赖：
```bash
uv sync
```

执行代码前激活虚拟环境：
```bash
source .venv/bin/activate
```

安装三方包:
```bash
uv add playwright==1.51.0
```

## Tools调试

### 客群短信业务调试
启动office-assistant-mcp调试工具：
```bash
uv run mcp dev src/office_assistant_mcp/mcp_server.py
```

### 佣金设置业务调试
启动commission-setting-mcp调试工具：
```bash
uv run mcp dev src/commission_setting_mcp/mcp_server.py
```

调试界面自动打开
页面配置：STDIO
uv
run --with mcp mcp run src/office_assistant_mcp/mcp_server.py

## 开发

为了能执行examples/下的文件，需要在根目录下安装office_assistant_mcp包：
```bash
uv pip install -e .
```

## 构建和发布

### Office Assistant MCP包

**手动构建：**
```bash
uv build
```

**自动构建和发布：**
```bash
./build_and_upload_pypi.sh
```
- 自动递增版本号
- 构建包文件
- 可选择上传到PyPI

### Commission Setting MCP包

**自动构建和发布：**
```bash
./build_and_upload_commission.sh
```
- 自动递增版本号
- 切换配置文件进行构建
- 恢复原配置文件
- 可选择上传到PyPI

### 包文件位置
构建的包文件存放在 `dist/` 目录下：
- office-assistant-mcp-x.x.x.tar.gz
- office-assistant-mcp-x.x.x-py3-none-any.whl
- commission-setting-mcp-x.x.x.tar.gz  
- commission-setting-mcp-x.x.x-py3-none-any.whl

## Session管理机制

### Session_ID的作用

**核心问题**：MCP工具调用是无状态的 - 每个工具调用都是独立请求，无法共享浏览器页面，导致打开多个标签页

**解决方案**：统一的Session管理机制确保多个MCP工具在同一浏览器会话中串行执行

### Session管理架构

```
MCP工具调用 → ensure_mcp_session_context() → 获取/创建Session → 操作同一页面
     ↓                        ↓                       ↓
  独立请求              ContextVar管理           BrowserSession实例
```

#### 关键组件

1. **MCPSessionManager** (`src/shared/mcp_session_manager.py`)
   - 全局session状态管理
   - session复用和连续性保证

2. **BrowserSession** (`src/shared/browser_manager.py`)
   - 浏览器会话封装：`session_id`, `browser_context`, `current_page`
   - 支持多页面管理：`pages[]`
   - 兼容性属性：`page` → `current_page`

3. **ContextVar机制**
   - 线程安全的session传递
   - 支持测试场景并发执行
   - 自动上下文管理

### 使用方式

#### MCP工具中（自动）
每个MCP工具自动调用`ensure_mcp_session_context()`：
```python
@mcp.tool()
async def fill_customer_group_info(group_name: str) -> str:
    try:
        await ensure_mcp_session_context()  # 自动session管理
        result = await playwright_util.fill_customer_group_info(group_name)
        return f"成功: {result}"
    except Exception as e:
        return format_exception_message("填写客群信息时出错", e)
```

#### 测试场景中（手动）
```python
# 方式1：ContextVar设置（推荐）
from shared.browser_manager import set_current_session
set_current_session("test_session_123")
await fill_customer_group_info("测试客群")

# 方式2：上下文管理器
from shared.browser_manager import with_session
async with with_session("test_session_123"):
    await fill_customer_group_info("测试客群")
```

### Session生命周期

1. **创建**：首次MCP工具调用时自动创建
2. **复用**：后续工具调用复用同一session
3. **重置**：`reset_mcp_session()` 手动清理

### 最佳实践

- ✅ **MCP工具**：依赖自动session管理，无需手动处理
- ✅ **测试用例**：使用`set_current_session()`设置固定session
- ✅ **并发测试**：不同测试使用不同session_id避免冲突
- ❌ **避免**：直接操作`_current_session_context`
- ❌ **避免**：跨session共享页面对象

## 功能模块

### Office Assistant MCP
- 客群创建和管理
- 用户行为标签设置
- 短信营销计划创建
- 飞书SSO登录
- **Session连续性保证**：串行工具调用在同一页面执行，session持续有效直到手动重置

### Commission Setting MCP
- 佣金设置管理
- 更多功能开发中...




