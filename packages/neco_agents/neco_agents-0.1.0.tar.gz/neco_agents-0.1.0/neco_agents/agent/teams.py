"""
Team Builder Module
负责构建和初始化 Team 实例
"""

from loguru import logger
from agno.agent import Agent
from agno.team.team import Team
from neco_agents.backend.backend_factory import BackendFactory


def build_member_agent(member_config, llm_configs, db_configs, backend="local"):
    """
    根据配置创建成员 agent

    Args:
        member_config: 成员配置字典
        llm_configs: LLM 配置字典
        db_configs: DB 配置字典
        backend: 后端类型

    Returns:
        Agent: 构建好的成员 Agent 实例
    """
    # 使用工厂获取后端实例
    backend_instance = BackendFactory.get_backend(backend)

    # 使用统一的参数准备函数
    member_params = backend_instance.prepare_agent_params(
        member_config, llm_configs, db_configs)

    return Agent(**member_params)


def build_team(team_name, backend="local"):
    """
    构建 team

    Args:
        team_name: team 名称，对应 agents 目录下的文件夹名
        backend: 后端类型，默认为 "local"

    Returns:
        Team: 构建好的 Team 实例
    """
    # 使用工厂获取后端实例
    backend_instance = BackendFactory.get_backend(backend)

    # 加载配置
    config = backend_instance.load_team_config(team_name)

    llm_configs = config['llm']
    db_configs = config.get('db', {})
    team_config = config['team']

    # 创建团队领导的模型
    model_id = team_config['model']
    model = backend_instance.create_llm_model(model_id, llm_configs[model_id])
    logger.info(f"团队领导使用模型: {model_id}")

    # 创建数据库（可选）
    team_params = {'model': model}
    db_id = team_config.get('db')
    if db_id and db_id in db_configs:
        team_params['db'] = backend_instance.create_db_storage(
            db_id, db_configs[db_id])
        logger.info(f"使用数据库: {db_id}")

    # 创建成员 agents
    members_config = team_config.get('members', [])
    if members_config:
        members = []
        for member_config in members_config:
            member_agent = build_member_agent(
                member_config, llm_configs, db_configs, backend)
            members.append(member_agent)
            logger.info(f"创建成员: {member_config.get('name', 'Unnamed')}")
        team_params['members'] = members
        logger.info(f"共创建 {len(members)} 个成员")

    # 透传其他参数
    for key, value in team_config.items():
        if key not in ['model', 'db', 'members']:
            team_params[key] = value

    # 处理 instructions
    if 'instructions' in team_params and isinstance(team_params['instructions'], str):
        team_params['instructions'] = [team_params['instructions']]

    team = Team(**team_params)
    logger.success(f"Team '{team_name}' 创建成功！(backend={backend})")

    return team
