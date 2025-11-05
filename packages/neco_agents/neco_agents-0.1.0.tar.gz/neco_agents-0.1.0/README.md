# NecoAgents

智能体构建工具

## Backend
* LocalBackend: 本地存储后端
* NotionBackend: Notion 存储后端

## Usage

### Agent
```
uv run neco_agents/cli/bootstrap.py run_agent "react_agent" --message "hi"
```

### Team
```
uv run neco_agents/cli/bootstrap.py run_agent "react_agent" --message "hi" --mode "team"
```