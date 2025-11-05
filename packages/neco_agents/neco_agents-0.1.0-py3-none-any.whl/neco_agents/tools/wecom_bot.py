"""企业微信机器人推送工具"""
import requests
from typing import Optional
from agno.tools import Toolkit
from loguru import logger


class WeComBot(Toolkit):
    """企业微信机器人推送工具

    支持发送文本、Markdown等消息到企业微信群聊
    """

    def __init__(self, webhook_token: str):
        """初始化企业微信机器人

        Args:
            webhook_token: 企业微信机器人的 Webhook Token
        """
        super().__init__(name="wecom_bot")
        self.webhook_token = webhook_token
        self.webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={webhook_token}"

        # 注册工具函数
        self.register(self.send_text)
        self.register(self.send_markdown)

    def send_text(self, content: str, mentioned_list: Optional[list[str]] = None) -> str:
        """发送文本消息到企业微信群

        Args:
            content: 文本内容
            mentioned_list: @的用户列表，如 ["user1", "user2"]，@所有人用 ["@all"]

        Returns:
            发送结果信息
        """
        logger.info(f"准备发送文本消息到企业微信，内容长度: {len(content)} 字符")

        payload = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }

        if mentioned_list:
            payload["text"]["mentioned_list"] = mentioned_list

        try:
            logger.debug(f"企业微信 Webhook URL: {self.webhook_url[:50]}...")
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            result = response.json()

            logger.info(
                f"企业微信响应: errcode={result.get('errcode')}, errmsg={result.get('errmsg')}")

            if result.get("errcode") == 0:
                logger.success("文本消息发送成功")
                return "消息发送成功"
            else:
                error_msg = f"消息发送失败: errcode={result.get('errcode')}, errmsg={result.get('errmsg', '未知错误')}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"发送请求失败: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def send_markdown(self, content: str) -> str:
        """发送 Markdown 消息到企业微信群

        Args:
            content: Markdown 格式的内容

        Returns:
            发送结果信息
        """
        logger.info(f"准备发送 Markdown 消息到企业微信，内容长度: {len(content)} 字符")

        # 企业微信 Markdown 换行符处理
        import re

        # 1. 统一换行符为 \n
        content = content.replace('\r\n', '\n')

        # 2. 移除行尾空格
        content = re.sub(r'[ \t]+\n', '\n', content)

        # 3. 将多个连续空行压缩为最多一个空行
        # 这是关键:企业微信不能有太多连续换行,否则会切分消息
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 4. 移除开头和结尾的空白行
        content = content.strip()

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

        try:
            logger.debug(f"企业微信 Webhook URL: {self.webhook_url[:50]}...")
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            result = response.json()

            logger.info(
                f"企业微信响应: errcode={result.get('errcode')}, errmsg={result.get('errmsg')}")

            if result.get("errcode") == 0:
                logger.success("Markdown 消息发送成功")
                return "Markdown消息发送成功"
            else:
                error_msg = f"Markdown消息发送失败: errcode={result.get('errcode')}, errmsg={result.get('errmsg', '未知错误')}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"发送请求失败: {str(e)}"
            logger.error(error_msg)
            return error_msg
