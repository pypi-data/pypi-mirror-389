"""
Backend Factory Module
负责管理和创建后端实例
"""

from typing import Dict, Optional
from loguru import logger
from neco_agents.backend.base_backend import BaseBackend


class BackendFactory:
    """后端工厂类，负责创建和管理后端实例"""

    _backends: Dict[str, BaseBackend] = {}

    @classmethod
    def get_backend(cls, backend_type: str = "local", **kwargs) -> BaseBackend:
        """
        获取后端实例（使用单例模式，每种类型的后端只创建一次）

        Args:
            backend_type: 后端类型 ("local" 或 "notion")
            **kwargs: 后端初始化参数

        Returns:
            后端实例

        Raises:
            ValueError: 不支持的后端类型
        """
        # 如果该类型的后端已经创建过，直接返回
        if backend_type in cls._backends:
            return cls._backends[backend_type]

        # 根据类型创建对应的后端实例
        if backend_type == "local":
            from neco_agents.backend.local_backend import LocalBackend
            backend = LocalBackend(**kwargs)
        elif backend_type == "notion":
            from neco_agents.backend.notion_backend import NotionBackend
            backend = NotionBackend(**kwargs)
        else:
            raise ValueError(f"不支持的 backend 类型: {backend_type}")

        # 缓存实例
        cls._backends[backend_type] = backend
        logger.debug(f"创建并缓存了 {backend_type} 后端实例")

        return backend

    @classmethod
    def clear_cache(cls):
        """清空后端缓存（主要用于测试）"""
        cls._backends.clear()
        logger.debug("已清空后端缓存")
