import os
from dotenv import load_dotenv
import fire
from loguru import logger
from neco_agents.agent.agent import build_agent
from neco_agents.agent.teams import build_team

load_dotenv()


class CLI:
    def run_agent(self, agent_name, message="Start", mode="agent", backend="local"):
        """运行 agent 或 team"""
        logger.info(f"使用 backend: {backend}")

        if mode == "agent":
            agent = build_agent(agent_name, backend=backend)
            agent.print_response(message, stream=True)
        elif mode == "teams":
            team = build_team(agent_name, backend=backend)
            team.print_response(message, stream=True)
        else:
            logger.error(f"不支持的模式: {mode}，请使用 'agent' 或 'teams'")


def main():
    """主入口函数"""
    fire.Fire(CLI)


if __name__ == "__main__":
    main()
