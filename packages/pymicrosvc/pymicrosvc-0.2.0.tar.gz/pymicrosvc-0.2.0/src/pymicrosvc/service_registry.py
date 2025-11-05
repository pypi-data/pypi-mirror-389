from pymicrosvc.nacos_client import NacosService
from pymicrosvc.logger import PyMicroSvcLogger

class ServiceRegistry:
    def __init__(self, ip="0.0.0.0", port = None, namespace= None, group=None, service_name=None, registry_server_address=None, ephemeral=True, heartbeat_seconds=5):
        # service's location':  bottom layer + upper layer
        self.ip = ip
        self.port = port
        self.namespace = namespace
        self.group = group
        self.service_name = service_name

        #service's characteristics: ephemeral, heartbeat to be needed!
        self.ephemeral = ephemeral
        self.heartbeat_seconds = heartbeat_seconds

        self.nacos_service = NacosService(namespace, service_name, registry_server_address)

    def register_service(self):
        self.nacos_service.add_naming_instance(
            group= self.group,
            service_name=self.service_name,
            ip=self.ip,
            port=self.port
        )
        PyMicroSvcLogger.get_logger().info(f"Service {self.service_name} registered to Nacos")

    def deregister_service(self):
        self.nacos_service.remove_naming_instance(
            group=self.group,
            service_name=self.service_name,
            ip=self.ip,
            port=self.port
        )
        PyMicroSvcLogger.get_logger().info(f"Service {self.service_name} unregistered from Nacos")

    def get_config(self):
        config = self.nacos_service.get_config()
        return config
