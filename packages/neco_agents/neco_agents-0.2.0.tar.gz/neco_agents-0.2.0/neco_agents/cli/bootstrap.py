import os
from dotenv import load_dotenv
import fire
from loguru import logger
from neco_agents.agent.agent import build_agent
from neco_agents.agent.teams import build_team
from agno.os import AgentOS

load_dotenv()


class CLI:
    def run_os(self, agents="", backend="local"):
        agents_list = agents.split(",")

        teams = []
        agents = []

        for agent_config in agents_list:
            agent_name = agent_config.split(":")[0]
            mode = agent_config.split(":")[1]

            if mode not in ["agent", "teams"]:
                logger.error(f"不支持的模式: {mode}，请使用 'agent' 或 'teams'")
                continue

            if mode == "agent":
                agent = build_agent(agent_name, backend=backend)
                agents.append(agent)
            if mode == "teams":
                agent = build_team(agent_name, backend=backend)
                teams.append(agent)

        agent_os = AgentOS(
            id="neco-agents",
            description="Neco Agents OS",
            agents=agents,
            teams=teams,
        )
        app = agent_os.get_app()
        agent_os.serve(app=app, access_log=True,
                       host="0.0.0.0", port=7110)

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
