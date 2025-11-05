import os
from datetime import datetime
import uvicorn
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from pymicrosvc.service_registry import ServiceRegistry
from pymicrosvc.logger import PyMicroSvcLogger
from pymicrosvc.nacos_config.nacos_config import (
    NACOS_NAMESPACE, NACOS_GROUP, THIS_SERVICE_NAME)

pylogger = PyMicroSvcLogger.get_logger()
listen_port = int(os.getenv("PY_MICRO_SVC_LISTEN_PORT", "7001"))
listen_IP = os.getenv("PY_MICRO_SVC_LISTEN_IP", "0.0.0.0")
nacos_server_addresses = os.getenv("NACOS_SERVER_ADDRESSES", "127.0.0.1:8848")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """生命周期管理"""
    try:
        # 初始化服务注册
        service_registry = ServiceRegistry(ip=listen_IP, port=listen_port,
                                           namespace=NACOS_NAMESPACE, group=NACOS_GROUP, service_name=THIS_SERVICE_NAME,
                                           registry_server_address=nacos_server_addresses,
                                           ephemeral=True, heartbeat_seconds=4)
        app.state.service_registry = service_registry
        # 注册服务和获取配置
        service_registry.register_service()
        config = service_registry.get_config()
        app.state.config = config or {
            "greeting": "Hello {name}! Today is {date}",
            "other_config": "value"
        }
    except Exception as e:
        pylogger.error(f"Initialization failed: ", exc_info=True)
        raise

    yield  # 应用运行期间

    # 清理阶段
    try:
        service_registry.deregister_service()
    except Exception as e:
        pylogger.error(f"shutdown failed: ", exc_info=True)

app = FastAPI(lifespan=lifespan)

@app.get("/hello/{name}")
async def greet(name: str, request: Request):
    """
    返回个性化问候
    - **name**: 用户名
    - 返回示例: {"message": "Hello John! Today is 2023-11-15"}
    """
    today = datetime.now().strftime("%Y-%m-%d")
    template = request.app.state.config["greeting"]
    return {
        "message": template.format(name=name, date=today),
        "received_at": datetime.now().isoformat()
    }

@app.get("/config")
async def show_config(request: Request):
    """查看当前配置（调试用）"""
    return {"config": request.app.state.config}

def main():
   uvicorn.run(app, host=listen_IP, port=listen_port)


