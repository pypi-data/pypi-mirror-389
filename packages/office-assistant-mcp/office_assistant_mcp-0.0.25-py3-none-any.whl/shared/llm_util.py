import os
import asyncio
import time
import json
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from shared.log_util import log_info, log_error, log_debug

load_dotenv()

class AzureOpenAIClient:
    """Azure OpenAI客户端，用于测试框架中的AI代理调用"""

    def __init__(self):
        self.endpoint = os.getenv("ENDPOINT_URL", "https://openaiyj.openai.azure.com/")
        self.deployment = os.getenv("DEPLOYMENT_NAME", "gpt-5")
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY_JP')
        if not self.api_key:
            raise ValueError("Azure OpenAI API key not found. Please set AZURE_OPENAI_API_KEY_JP environment variable.")

        # Azure OpenAI配置
        self.client = AsyncAzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version="2025-01-01-preview"
        )

    async def chat_completion(
        self,
        messages: list,
        model: str = None,
        max_tokens: int = 4000,
        tools: list = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> Optional[Dict]:
        """
        调用Azure OpenAI进行对话完成

        Args:
            messages: 对话消息列表
            model: 模型名称
            max_tokens: 最大token数
            tools: 工具定义列表
            tool_choice: 工具选择策略
            **kwargs: 其他参数

        Returns:
            完整的响应对象，失败时返回None
        """
        try:
            # log_info(f"正在调用Azure OpenAI，模型: {model}, 工具数: {len(tools) if tools else 0}")

            # 使用部署名称而不是模型名称
            model_name = model if model else self.deployment

            # 构建请求参数
            request_params = {
                "model": model_name,
                "messages": messages,
                "max_completion_tokens": max_tokens,
                **kwargs
            }

            # 添加工具相关参数
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = tool_choice

            response = await self.client.chat.completions.create(**request_params)
            # log_debug(f"Azure OpenAI响应: {response}")

            if response.choices and len(response.choices) > 0:
                # log_info(f"Azure OpenAI调用成功")
                return response
            else:
                log_error("Azure OpenAI返回空响应")
                return None

        except Exception as e:
            log_error(f"Azure OpenAI调用失败: {str(e)}")
            return None


# 全局客户端实例
_azure_client: Optional[AzureOpenAIClient] = None


def get_azure_client() -> AzureOpenAIClient:
    """获取Azure OpenAI客户端实例（单例模式）"""
    global _azure_client
    if _azure_client is None:
        _azure_client = AzureOpenAIClient()
    return _azure_client


async def call_azure_openai(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = "gpt-5",
    max_tokens: int = 4000,
    tools: list = None,
    tool_choice: str = "auto"
) -> Optional[str]:
    """
    便捷的Azure OpenAI调用函数

    Args:
        prompt: 用户提示
        system_prompt: 系统提示（可选）
        model: 模型名称
        max_tokens: 最大token数
        tools: 工具定义列表
        tool_choice: 工具选择策略

    Returns:
        回复内容，失败时返回None
    """
    try:
        client = get_azure_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat_completion(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice=tool_choice
        )

        if response and response.choices:
            choice = response.choices[0]
            if choice.message.content:
                return choice.message.content
            elif choice.message.tool_calls:
                # 如果有工具调用，返回完整的响应对象
                return response

        return None

    except Exception as e:
        log_error(f"Azure OpenAI调用失败: {str(e)}")
        return None


async def call_azure_openai_with_tools(
    prompt: str,
    system_prompt: Optional[str] = None,
    tools: list = None,
    tool_handler=None,
    model: str = "gpt-5",
    max_tokens: int = 4000,
    max_iterations: int = 10
) -> str:
    """
    支持工具调用的Azure OpenAI调用函数

    Args:
        prompt: 用户提示
        system_prompt: 系统提示
        tools: 工具定义列表
        tool_handler: 工具处理函数，接收(tool_name, arguments)参数
        model: 模型名称
        max_tokens: 最大token数
        max_iterations: 最大迭代次数

    Returns:
        最终的响应内容
    """
    try:
        client = get_azure_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for iteration in range(max_iterations):
            log_debug(f"工具调用迭代 {iteration + 1}")

            response = await client.chat_completion(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                tools=tools,
                tool_choice="auto"
            )

            if not response or not response.choices:
                return "Azure OpenAI调用失败"

            choice = response.choices[0]

            # 如果有文本内容，直接返回
            if choice.message.content:
                return choice.message.content

            # 如果有工具调用
            if choice.message.tool_calls:
                # 添加助手消息
                messages.append({
                    "role": "assistant",
                    "content": choice.message.content,
                    "tool_calls": [tc.dict() for tc in choice.message.tool_calls]
                })

                # 处理每个工具调用
                for tool_call in choice.message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    log_info(f"调用工具: {tool_name}, 参数: {arguments}")

                    # 调用工具处理函数
                    if tool_handler:
                        tool_result = await tool_handler(tool_name, arguments)
                    else:
                        tool_result = f"工具 {tool_name} 调用成功，参数: {arguments}"

                    # 添加工具结果消息
                    messages.append({
                        "role": "tool",
                        "content": str(tool_result),
                        "tool_call_id": tool_call.id
                    })

                # 继续下一轮对话
                continue
            else:
                # 没有内容也没有工具调用
                return "AI没有提供有效响应"

        return "达到最大迭代次数，对话结束"

    except Exception as e:
        log_error(f"Azure OpenAI工具调用失败: {str(e)}")
        return f"工具调用过程出错: {str(e)}"


async def call_azure_openai_test() -> bool:
    """测试Azure OpenAI连接是否正常"""
    try:
        response = await call_azure_openai(
            prompt="你是什么版本？",
            system_prompt="你是一个测试助手，请按照用户要求简短回复。"
        )
        log_info(f"响应: {response}")
        return True
    except Exception as e:
        log_error(f"Azure OpenAI连接测试异常: {str(e)}")
        return False


# 测试代码
async def main():
    print("正在测试Azure OpenAI连接...")
    start_time = time.time()
    success = await call_azure_openai_test()
    end_time = time.time()
    print(f"测试耗时: {end_time - start_time:.2f} 秒")
    if success:
        print("✅ Azure OpenAI连接正常")
    else:
        print("❌ Azure OpenAI连接失败")

if __name__ == "__main__":
    asyncio.run(main())