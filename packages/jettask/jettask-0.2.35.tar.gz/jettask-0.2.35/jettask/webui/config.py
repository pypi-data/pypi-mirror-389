#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebUI配置管理模块
提供统一的配置管理，所有配置的环境变量读取都在此处集中处理
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class WebUIConfig:
    """
    WebUI配置管理类（单例模式）

    所有配置的环境变量读取都在初始化时完成，
    后续使用配置直接从实例属性获取，不再重复读取环境变量。

    使用方式:
        from jettask.webui.config import webui_config

        # 获取配置
        redis_url = webui_config.redis_url
        pg_url = webui_config.pg_url
    """

    _instance: Optional['WebUIConfig'] = None
    _initialized: bool = False

    def __new__(cls):
        """单例模式：确保全局只有一个配置实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置（只执行一次）"""
        # 防止重复初始化
        if self._initialized:
            return

        logger.info("正在初始化 WebUI 配置...")

        # 读取所有环境变量
        self._load_env_vars()

        # 验证必需的配置
        self._validate_required_configs()

        # 标记已初始化
        self._initialized = True

        logger.info("WebUI 配置初始化完成")
        self._log_config_summary()

    def _load_env_vars(self):
        """从环境变量中加载所有配置"""
        # ==================== 必需配置 ====================
        self.redis_url: Optional[str] = os.getenv('JETTASK_REDIS_URL')
        self.pg_url: Optional[str] = os.getenv('JETTASK_PG_URL')

        # ==================== 可选配置（有合理默认值）====================
        # Redis键前缀，默认为'jettask'
        self.redis_prefix: str = os.getenv('JETTASK_REDIS_PREFIX', 'jettask')

        # 是否使用Nacos配置，默认为false
        use_nacos_str = os.getenv('USE_NACOS', 'false')
        self.use_nacos: bool = use_nacos_str.lower() == 'true'

        # Nacos配置（仅在使用Nacos时需要）
        if self.use_nacos:
            self.nacos_server: Optional[str] = os.getenv('NACOS_SERVER')
            self.nacos_namespace: Optional[str] = os.getenv('NACOS_NAMESPACE')
            self.nacos_data_id: Optional[str] = os.getenv('NACOS_DATA_ID')
            self.nacos_group: Optional[str] = os.getenv('NACOS_GROUP')
        else:
            self.nacos_server = None
            self.nacos_namespace = None
            self.nacos_data_id = None
            self.nacos_group = None

        # API服务配置（用于任务中心）
        # 优先使用 JETTASK_API_HOST/PORT，兼容旧的 TASK_CENTER_API_HOST/PORT
        self.api_host: str = os.getenv('JETTASK_API_HOST') or os.getenv('TASK_CENTER_API_HOST', '0.0.0.0')
        self.api_port: int = int(os.getenv('JETTASK_API_PORT') or os.getenv('TASK_CENTER_API_PORT', '8001'))

        # 基础URL配置（用于生成connection_url）
        # 优先使用环境变量，否则根据 api_host 和 api_port 构建
        self.base_url: str = os.getenv('TASK_CENTER_BASE_URL') or f"http://{self.api_host}:{self.api_port}"

        # 日志级别
        self.log_level: str = os.getenv('JETTASK_LOG_LEVEL', 'INFO').upper()

    def _validate_required_configs(self):
        """验证必需的配置是否存在"""
        missing_configs = []

        # 检查必需的配置
        if not self.redis_url:
            missing_configs.append('JETTASK_REDIS_URL')
        if not self.pg_url:
            missing_configs.append('JETTASK_PG_URL')


        if missing_configs:
            error_msg = f"缺少必需的环境变量: {', '.join(missing_configs)}"
            logger.error(error_msg)
            logger.error("=" * 60)
            logger.error("请通过以下方式之一提供配置:")
            logger.error("  1. 在 .env 文件中设置环境变量")
            logger.error("  2. 使用命令行: jettask api --use-nacos")
            logger.error("  3. 手动设置环境变量")
            logger.error("=" * 60)
            logger.error("示例 .env 文件:")
            logger.error("  JETTASK_REDIS_URL=redis://localhost:6379/0")
            logger.error("  JETTASK_PG_URL=postgresql://user:pass@localhost:5432/db")
            logger.error("=" * 60)
            raise ValueError(error_msg)

    def _log_config_summary(self):
        """记录配置摘要（用于调试）"""
        logger.info("=" * 60)
        logger.info("WebUI 配置摘要:")
        logger.info(f"  配置模式: {'Nacos' if self.use_nacos else '环境变量'}")
        logger.info(f"  Redis URL: {self._mask_url(self.redis_url)}")
        logger.info(f"  PostgreSQL URL: {self._mask_url(self.pg_url)}")
        logger.info(f"  Redis Prefix: {self.redis_prefix}")
        logger.info(f"  API Host: {self.api_host}")
        logger.info(f"  API Port: {self.api_port}")
        logger.info(f"  Log Level: {self.log_level}")

        if self.use_nacos:
            logger.info(f"  Nacos Server: {self.nacos_server}")
            logger.info(f"  Nacos Namespace: {self.nacos_namespace}")
            logger.info(f"  Nacos Data ID: {self.nacos_data_id}")
            logger.info(f"  Nacos Group: {self.nacos_group}")

        logger.info("=" * 60)

    @staticmethod
    def _mask_url(url: Optional[str]) -> str:
        """隐藏URL中的密码信息"""
        if not url:
            return "未配置"

        import re
        # 隐藏密码部分: user:password@host -> user:****@host
        masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', url)
        return masked

    def reload(self):
        """重新加载配置（用于配置变更后刷新）"""
        logger.info("重新加载 WebUI 配置...")
        self._initialized = False
        self.__init__()

    @property
    def meta_database_url(self) -> str:
        """
        获取元数据库连接URL（确保使用 asyncpg 驱动）

        Returns:
            PostgreSQL 连接URL字符串
        """
        if not self.pg_url:
            raise ValueError("PostgreSQL URL未配置")

        # 确保使用 asyncpg 驱动
        if 'postgresql://' in self.pg_url and '+asyncpg' not in self.pg_url:
            return self.pg_url.replace('postgresql://', 'postgresql+asyncpg://')

        return self.pg_url

    @property
    def sync_meta_database_url(self) -> str:
        """
        获取同步元数据库连接URL（用于初始化等同步操作）

        Returns:
            同步 PostgreSQL 连接URL字符串
        """
        if not self.pg_url:
            raise ValueError("PostgreSQL URL未配置")

        # 移除 asyncpg 驱动标识
        url = self.pg_url.replace('+asyncpg', '')
        return url

    def get_database_info(self) -> dict:
        """
        获取数据库连接信息（解析后的）

        Returns:
            包含数据库连接信息的字典
        """
        import re

        result = {
            'raw_url': self.pg_url,
            'host': None,
            'port': None,
            'database': None,
            'username': None
        }

        if self.pg_url:
            # 解析PostgreSQL URL
            # 支持格式: postgresql://user:pass@host:port/db 或 postgresql+asyncpg://user:pass@host:port/db
            match = re.match(
                r'postgresql(?:\+asyncpg)?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)',
                self.pg_url
            )
            if match:
                username, _, host, port, database = match.groups()
                result.update({
                    'username': username,
                    'host': host,
                    'port': port or '5432',
                    'database': database
                })

        return result

    def __repr__(self) -> str:
        """配置对象的字符串表示"""
        return (
            f"<WebUIConfig("
            f"redis_url={self._mask_url(self.redis_url)}, "
            f"pg_url={self._mask_url(self.pg_url)}, "
            f"use_nacos={self.use_nacos}"
            f")>"
        )


# 创建全局单例实例
# 其他模块通过导入此实例来使用配置
webui_config = WebUIConfig()
