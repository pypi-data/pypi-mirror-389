"""
Base Backend Module
定义后端的抽象接口和公共方法
"""

import os
import re
import importlib
from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path
from loguru import logger
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb


class BaseBackend(ABC):
    """后端抽象基类，定义配置管理的标准接口"""

    @abstractmethod
    def load_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        加载 agent 的配置

        Args:
            agent_name: agent 名称或标识符

        Returns:
            agent 配置字典
        """
        pass

    @abstractmethod
    def load_team_config(self, team_name: str) -> Dict[str, Any]:
        """
        加载 team 的配置

        Args:
            team_name: team 名称或标识符

        Returns:
            team 配置字典
        """
        pass

    @staticmethod
    def resolve_env_vars(value):
        """
        解析环境变量，支持 ${VAR_NAME} 格式

        Args:
            value: 待解析的值

        Returns:
            解析后的值
        """
        if isinstance(value, str) and "${" in value:
            pattern = r'\$\{([^}]+)\}'
            return re.sub(pattern, lambda m: os.environ.get(m.group(1), ''), value)
        return value

    def create_llm_model(self, model_id: str, model_config: Dict[str, Any]) -> OpenAIChat:
        """
        根据配置创建 LLM 模型实例

        Args:
            model_id: 模型 ID
            model_config: 模型配置

        Returns:
            OpenAIChat 实例
        """
        return OpenAIChat(
            id=model_id,
            api_key=self.resolve_env_vars(model_config['api_key']),
            base_url=self.resolve_env_vars(model_config['base_url'])
        )

    def create_db_storage(self, db_id: str, db_config: Dict[str, Any]) -> SqliteDb:
        """
        根据配置创建数据库存储实例

        Args:
            db_id: 数据库 ID
            db_config: 数据库配置

        Returns:
            SqliteDb 实例
        """
        db_path = Path(self.resolve_env_vars(db_config['database']))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return SqliteDb(db_file=str(db_path))

    def create_tool(self, tool_config: Dict[str, Any]):
        """
        根据配置创建工具实例

        Args:
            tool_config: 工具配置

        Returns:
            工具实例
        """
        tool_type = tool_config['type']
        module_path, class_or_func_name = tool_type.rsplit('.', 1)
        module = importlib.import_module(module_path)
        tool_item = getattr(module, class_or_func_name)

        # 获取工具参数（排除 id 和 type）
        tool_params = {k: self.resolve_env_vars(v) for k, v in tool_config.items() if k not in [
            'id', 'type']}

        # 判断是类还是函数
        if callable(tool_item) and not isinstance(tool_item, type):
            # 是函数，直接返回
            return tool_item
        else:
            # 是类，实例化
            return tool_item(**tool_params) if tool_params else tool_item()

    def prepare_agent_params(self, agent_config: Dict[str, Any], llm_configs: Dict[str, Any], db_configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据配置准备 Agent 初始化参数

        Args:
            agent_config: agent 配置字典
            llm_configs: LLM 配置字典
            db_configs: DB 配置字典

        Returns:
            Agent 初始化参数字典
        """
        # 创建模型
        model_id = agent_config['model']
        model = self.create_llm_model(model_id, llm_configs[model_id])
        logger.info(f"使用模型: {model_id}")

        # 创建数据库（可选）
        agent_params = {'model': model}
        db_id = agent_config.get('db')
        if db_id and db_id in db_configs:
            agent_params['db'] = self.create_db_storage(
                db_id, db_configs[db_id])
            logger.info(f"使用数据库: {db_id}")

        # 创建工具（可选）
        tools_config = agent_config.get('tools', [])
        if tools_config:
            tools = [self.create_tool(tool_config)
                     for tool_config in tools_config]
            agent_params['tools'] = tools
            logger.info(f"加载 {len(tools)} 个工具")

        # 透传其他参数
        for key, value in agent_config.items():
            if key not in ['model', 'db', 'tools']:
                agent_params[key] = value

        # 处理 instructions
        if 'instructions' in agent_params and isinstance(agent_params['instructions'], str):
            agent_params['instructions'] = [agent_params['instructions']]

        return agent_params
