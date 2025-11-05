"""
Notion Backend for Configuration Loading
负责从 Notion 数据库加载配置并创建相应的资源实例（LLM、DB、Tools）
"""

import os
import json
from typing import Dict, Any, List, Optional
from loguru import logger
from notion_client import Client
from neco_agents.backend.base_backend import BaseBackend


class NotionBackend(BaseBackend):
    """Notion 后端配置管理器"""

    def __init__(self, notion_token: Optional[str] = None):
        """
        初始化 Notion 后端

        Args:
            notion_token: Notion API token，如果不提供则从环境变量获取
        """
        self.token = notion_token or os.environ.get("NOTION_TOKEN")
        if not self.token:
            raise ValueError(
                "Notion token 未提供，请设置 NOTION_TOKEN 环境变量或传入 notion_token 参数")

        self.client = Client(auth=self.token)
        logger.info("Notion 客户端初始化完成")

    def normalize_block_id(self, block_id: str) -> str:
        """
        标准化 block ID 为 UUID 格式（带连字符）

        Args:
            block_id: 原始 block ID

        Returns:
            标准 UUID 格式的 block ID
        """
        block_id = block_id.replace("-", "")
        if len(block_id) != 32:
            raise ValueError(f"无效的 block ID: {block_id}")

        return f"{block_id[:8]}-{block_id[8:12]}-{block_id[12:16]}-{block_id[16:20]}-{block_id[20:]}"

    def extract_property_value(self, prop_value: dict):
        """
        提取 Notion 属性值

        Args:
            prop_value: Notion 属性值字典

        Returns:
            提取的值
        """
        prop_type = prop_value["type"]

        if prop_type == "title":
            texts = prop_value.get("title", [])
            return "".join([t["plain_text"] for t in texts])
        elif prop_type == "rich_text":
            texts = prop_value.get("rich_text", [])
            return "".join([t["plain_text"] for t in texts])
        elif prop_type == "number":
            return prop_value.get("number")
        elif prop_type == "select":
            select = prop_value.get("select")
            return select["name"] if select else None
        elif prop_type == "multi_select":
            multi_select = prop_value.get("multi_select", [])
            return [item["name"] for item in multi_select]
        elif prop_type == "checkbox":
            return prop_value.get("checkbox", False)
        elif prop_type == "url":
            return prop_value.get("url")
        elif prop_type == "email":
            return prop_value.get("email")
        elif prop_type == "phone_number":
            return prop_value.get("phone_number")
        elif prop_type == "date":
            date_obj = prop_value.get("date")
            return date_obj["start"] if date_obj else None

        return None

    def get_block_content(self, block_id: str) -> Dict[str, Any]:
        """
        获取 Notion block 的内容

        Args:
            block_id: block ID (作为 agent_name)

        Returns:
            block 的配置信息
        """
        block_id = self.normalize_block_id(block_id)

        try:
            # 获取 block 信息
            block = self.client.blocks.retrieve(block_id=block_id)

            # 如果是页面类型，获取页面属性
            if block["object"] == "page":
                page = self.client.pages.retrieve(page_id=block_id)
                return self._parse_page_to_config(page)
            else:
                # 如果是代码块，直接解析代码内容
                if block["type"] == "code":
                    code_content = block["code"]["rich_text"]
                    if code_content:
                        code_text = "".join([t["plain_text"]
                                            for t in code_content])
                        logger.debug(f"代码块内容长度: {len(code_text)}")

                        # 尝试解析为 JSON
                        if code_text.strip().startswith("{") or code_text.strip().startswith("["):
                            try:
                                config = json.loads(code_text)
                                logger.debug(f"成功解析 JSON 配置")
                                return config
                            except json.JSONDecodeError:
                                logger.warning("代码块不是有效的 JSON 格式")

                        # 尝试解析为 YAML
                        try:
                            import yaml
                            config = yaml.safe_load(code_text)
                            logger.debug(f"成功解析 YAML 配置")
                            return config
                        except Exception as e:
                            logger.warning(f"无法解析代码块为 YAML: {e}")

                # 如果不是代码块或解析失败，获取其子 blocks
                children = self.client.blocks.children.list(block_id=block_id)
                logger.debug(f"子 blocks 数量: {len(children['results'])}")
                config = self._parse_blocks_to_config(children["results"])
                logger.debug(f"解析后的配置: {config}")
                return config

        except Exception as e:
            raise RuntimeError(f"获取 Notion block 失败: {e}")

    def _parse_page_to_config(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 Notion 页面解析为配置格式

        Args:
            page: Notion 页面对象

        Returns:
            解析后的配置字典
        """
        config = {}

        # 解析页面属性
        for prop_name, prop_value in page["properties"].items():
            value = self.extract_property_value(prop_value)
            if value is not None:
                # 尝试解析 JSON 格式的配置
                if isinstance(value, str) and (value.startswith("{") or value.startswith("[")):
                    try:
                        config[prop_name] = json.loads(value)
                    except json.JSONDecodeError:
                        config[prop_name] = value
                else:
                    config[prop_name] = value

        # 获取页面内容块
        try:
            children = self.client.blocks.children.list(block_id=page["id"])
            content_config = self._parse_blocks_to_config(children["results"])
            config.update(content_config)
        except Exception as e:
            logger.warning(f"获取页面内容失败: {e}")

        return config

    def _parse_blocks_to_config(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        将 Notion blocks 解析为配置格式

        Args:
            blocks: Notion blocks 列表

        Returns:
            解析后的配置字典
        """
        config = {}

        for block in blocks:
            block_type = block["type"]

            if block_type == "code":
                # 代码块，尝试解析为 JSON 配置
                code_content = block["code"]["rich_text"]
                if code_content:
                    code_text = "".join([t["plain_text"]
                                        for t in code_content])
                    try:
                        parsed_config = json.loads(code_text)
                        config.update(parsed_config)
                    except json.JSONDecodeError:
                        logger.warning(f"无法解析代码块为 JSON: {code_text[:100]}...")

    def load_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        加载 agent 的配置（agent_name 作为 block ID）

        Args:
            agent_name: block ID

        Returns:
            agent 配置字典
        """
        config = self.get_block_content(agent_name)
        logger.debug(f"已加载 agent 配置: {agent_name}")
        return config

    def load_team_config(self, team_name: str) -> Dict[str, Any]:
        """
        加载 team 的配置（team_name 作为 block ID）

        Args:
            team_name: block ID

        Returns:
            team 配置字典
        """
        config = self.get_block_content(team_name)
        logger.debug(f"已加载 team 配置: {team_name}")
        return config
