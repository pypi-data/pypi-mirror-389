"""
Execute Tool for running shell commands.
提供执行 Shell 命令的能力，根据配置动态生成工具。
"""
import subprocess
from typing import Dict, List
from agno.tools import Toolkit
from loguru import logger


class BashTool(Toolkit):
    """
    Shell 命令执行工具，根据配置动态生成多个子工具。

    每个子工具对应一个预定义的 shell 脚本，用户可通过 parameters 配置
    允许执行的命令及其用途描述。
    """

    # 配置常量
    DEFAULT_TIMEOUT = 30  # 默认超时时间（秒）
    MAX_OUTPUT_LENGTH = 10000  # 最大输出长度

    def __init__(self, parameters: List[Dict[str, str]] = None, timeout: int = None):
        """
        初始化 BashTool。

        Args:
            parameters: 工具参数列表，每个参数包含:
                - id: 工具唯一标识符
                - script: 要执行的 shell 脚本
                - description: 工具描述
            timeout: 命令执行超时时间（秒），默认为 DEFAULT_TIMEOUT
        """
        super().__init__(name="bash_tool")
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.parameters = parameters or []

        # 验证参数
        self._validate_parameters()

        # 动态注册工具
        self._register_tools()

        logger.info(f"BashTool 初始化完成，注册了 {len(self.parameters)} 个命令工具")

    def _validate_parameters(self):
        """
        验证参数配置的合法性。

        Raises:
            ValueError: 参数配置不合法时抛出
        """
        if not self.parameters:
            logger.warning("BashTool 未配置任何命令参数")
            return

        seen_ids = set()
        for idx, param in enumerate(self.parameters):
            # 检查必需字段
            if 'id' not in param:
                raise ValueError(f"参数配置[{idx}]缺少必需字段: id")
            if 'script' not in param:
                raise ValueError(f"参数配置[{idx}]缺少必需字段: script")
            if 'description' not in param:
                raise ValueError(f"参数配置[{idx}]缺少必需字段: description")

            # 检查 id 唯一性
            tool_id = param['id']
            if tool_id in seen_ids:
                raise ValueError(f"工具 ID 重复: {tool_id}")
            seen_ids.add(tool_id)

            # 检查字段类型
            if not isinstance(param['id'], str) or not param['id'].strip():
                raise ValueError(f"参数配置[{idx}]的 id 必须是非空字符串")
            if not isinstance(param['script'], str) or not param['script'].strip():
                raise ValueError(f"参数配置[{idx}]的 script 必须是非空字符串")
            if not isinstance(param['description'], str):
                raise ValueError(f"参数配置[{idx}]的 description 必须是字符串")

    def _register_tools(self):
        """动态注册工具到 Toolkit。"""
        for param in self.parameters:
            tool_id = param['id']
            script = param['script']
            description = param['description']

            # 创建工具函数
            tool_func = self._create_tool_function(
                tool_id, script, description)

            # 注册到 Toolkit
            self.register(tool_func)
            logger.debug(f"已注册工具: {tool_id} - {description}")

    def _create_tool_function(self, tool_id: str, script: str, description: str):
        """
        创建工具函数。

        Args:
            tool_id: 工具 ID
            script: 要执行的脚本
            description: 工具描述

        Returns:
            可调用的工具函数
        """
        def tool_function() -> str:
            f"""
            {description}

            Returns:
                str: 命令执行结果
            """
            return self._execute_command(tool_id, script)

        # 设置函数元数据
        tool_function.__name__ = tool_id
        tool_function.__doc__ = description

        return tool_function

    def _execute_command(self, tool_id: str, script: str) -> str:
        """
        执行 shell 命令。

        Args:
            tool_id: 工具 ID（用于日志记录）
            script: 要执行的脚本

        Returns:
            str: 命令执行结果

        Raises:
            RuntimeError: 命令执行失败时抛出
        """
        logger.info(f"开始执行工具 [{tool_id}]: {script[:100]}")

        try:
            # 执行命令（使用 bash）
            result = subprocess.run(
                script,
                shell=True,
                executable='/bin/bash',  # 显式使用 bash 而非 sh
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False  # 不自动抛出异常，手动处理返回码
            )

            # 构建输出
            output_parts = []

            if result.stdout:
                stdout = result.stdout.strip()
                if len(stdout) > self.MAX_OUTPUT_LENGTH:
                    stdout = stdout[:self.MAX_OUTPUT_LENGTH] + \
                        f"\n...(输出过长，已截断，共 {len(result.stdout)} 字符)"
                output_parts.append(f"标准输出:\n{stdout}")

            if result.stderr:
                stderr = result.stderr.strip()
                if len(stderr) > self.MAX_OUTPUT_LENGTH:
                    stderr = stderr[:self.MAX_OUTPUT_LENGTH] + \
                        f"\n...(输出过长，已截断，共 {len(result.stderr)} 字符)"
                output_parts.append(f"标准错误:\n{stderr}")

            # 添加返回码信息
            output_parts.append(f"返回码: {result.returncode}")

            output = "\n\n".join(output_parts)

            # 记录执行结果
            if result.returncode == 0:
                logger.info(f"工具 [{tool_id}] 执行成功")
            else:
                logger.warning(f"工具 [{tool_id}] 执行失败，返回码: {result.returncode}")

            return output

        except subprocess.TimeoutExpired:
            error_msg = f"命令执行超时（{self.timeout}秒）"
            logger.error(f"工具 [{tool_id}] {error_msg}")
            raise RuntimeError(f"[{tool_id}] {error_msg}")

        except Exception as e:
            error_msg = f"命令执行异常: {e}"
            logger.error(f"工具 [{tool_id}] {error_msg}")
            raise RuntimeError(f"[{tool_id}] {error_msg}")
