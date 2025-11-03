"""
API v1 路由模块集合

路由结构：
- /api/v1/namespaces - 命名空间列表和创建（全局）
- /api/v1/{namespace} - 命名空间详情、更新、删除（命名空间下）
- /api/v1/{namespace}/statistics - 命名空间统计（命名空间下）
- /api/v1/{namespace}/queues - 队列管理（命名空间下的资源）
- /api/v1/{namespace}/queues/send - 任务发送（命名空间下的资源，已合并到 queues）
- /api/v1/{namespace}/scheduled - 定时任务（命名空间下的资源）
- /api/v1/{namespace}/workers - Worker 监控（命名空间下的资源）
- /api/v1/{namespace}/settings - 设置（命名空间下的资源）
- /api/v1/{namespace}/alerts - 告警规则（命名空间下的资源）
"""
from fastapi import APIRouter

# 导入主要模块的路由
from .overview import router as overview_router                           # 概览
from .namespaces import global_router as namespaces_global_router         # 命名空间（全局路由）
from .namespaces import namespace_router as namespaces_namespace_router   # 命名空间（命名空间路由）
from .queues import router as queues_router                               # 队列（包含任务发送）
from .scheduled import router as scheduled_router                         # 定时任务
from .alerts import router as alerts_router                               # 告警
from .settings import router as settings_router                           # 设置
from .workers import router as workers_router                             # Worker 监控

# 创建 v1 总路由，添加统一的 /api/v1 前缀
api_router = APIRouter(prefix="/api/task/v1")

# 1. 注册全局路由（不需要 namespace 的路由）
api_router.include_router(namespaces_global_router)  # 命名空间管理（列表和创建）
api_router.include_router(alerts_router)             # 告警规则管理（支持可选 namespace）

# 2. 创建命名空间路由（所有需要 namespace 的资源）
namespace_router = APIRouter(prefix="/{namespace}")

# 3. 注册命名空间下的资源路由
namespace_router.include_router(namespaces_namespace_router)  # 命名空间详情、更新、删除、统计
namespace_router.include_router(overview_router)              # 系统概览、健康检查
namespace_router.include_router(queues_router)                # 队列管理、任务处理、任务发送
namespace_router.include_router(scheduled_router)             # 定时任务管理
namespace_router.include_router(workers_router)               # Worker 监控
namespace_router.include_router(settings_router)              # 系统配置

# 4. 将命名空间路由注册到总路由
api_router.include_router(namespace_router)

__all__ = ['api_router']


