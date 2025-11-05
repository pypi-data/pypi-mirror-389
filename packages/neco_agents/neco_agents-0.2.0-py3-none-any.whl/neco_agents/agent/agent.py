"""
Agent Builder Module
负责构建和初始化 Agent 实例
"""

from loguru import logger
from agno.agent import Agent
from neco_agents.backend.backend_factory import BackendFactory


def build_agent(agent_name, backend="local"):
    """
    构建 agent

    Args:
        agent_name: agent 名称，对应 agents 目录下的文件夹名
        backend: 后端类型，默认为 "local"

    Returns:
        Agent: 构建好的 Agent 实例
    """
    # 使用工厂获取后端实例
    backend_instance = BackendFactory.get_backend(backend)

    # 加载配置
    config = backend_instance.load_agent_config(agent_name)

    llm_configs = config['llm']
    db_configs = config.get('db', {})
    agent_config = config['agent']

    # 准备 agent 参数
    agent_params = backend_instance.prepare_agent_params(
        agent_config, llm_configs, db_configs)

    # 创建 agent
    agent = Agent(**agent_params)
    logger.success(f"Agent '{agent_name}' 创建成功！(backend={backend})")

    return agent
