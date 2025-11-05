"""
Local Backend for YAML Configuration Loading
负责从 YAML 文件加载配置并创建相应的资源实例（LLM、DB、Tools）
"""

import yaml
from typing import Dict, Any
from pathlib import Path
from loguru import logger
from neco_agents.backend.base_backend import BaseBackend


class LocalBackend(BaseBackend):
    """本地 YAML 文件后端"""

    def __init__(self, agents_dir: str = None):
        """
        初始化本地后端

        Args:
            agents_dir: agents 目录路径，默认为项目根目录下的 agents 文件夹
        """
        if agents_dir:
            self.agents_dir = Path(agents_dir)
        else:
            self.agents_dir = Path(__file__).parent.parent.parent / "agents"
        logger.debug(f"本地后端初始化，agents 目录: {self.agents_dir}")

    def load_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        加载 agent 的 YAML 配置文件

        Args:
            agent_name: agent 名称

        Returns:
            agent 配置字典
        """
        agent_dir = self.agents_dir / agent_name
        config_path = agent_dir / "agent.yml"

        if not config_path.exists():
            raise FileNotFoundError(f"Agent 配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        logger.debug(f"已加载 agent 配置: {agent_name}")
        return config

    def load_team_config(self, team_name: str) -> Dict[str, Any]:
        """
        加载 team 的 YAML 配置文件

        Args:
            team_name: team 名称

        Returns:
            team 配置字典
        """
        team_dir = self.agents_dir / team_name
        config_path = team_dir / "teams.yml"

        if not config_path.exists():
            raise FileNotFoundError(f"Team 配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        logger.debug(f"已加载 team 配置: {team_name}")
        return config
