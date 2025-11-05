import yaml
from nacos import NacosClient

class NacosService:
    def __init__(self, namespace=None, service_name=None, nacos_server_address="127.0.0.1:8848"):
        self.client = NacosClient(nacos_server_address, namespace=namespace)
        self.data_id = f"{service_name}.yaml"

    def add_naming_instance(self, group=None, service_name=None, ip="0.0.0.0", port=None, ephemeral=True, heartbeat_seconds=5):
        self.client.add_naming_instance(
            service_name=service_name,
            ip=ip,
            port=port,
            ephemeral = ephemeral,
            group_name=group,
            heartbeat_interval = heartbeat_seconds
        )


    def remove_naming_instance(self, group=None, service_name=None, ip="0.0.0.0", port=None, ephemeral=True):
        self.client.remove_naming_instance(
            service_name=service_name,
            ip=ip,
            port=port,
            ephemeral=ephemeral,
            group_name=group
        )

    def get_config(self):
        config = self.client.get_config(self.data_id, "DEFAULT_GROUP")
        if config:
            return yaml.safe_load(config)
        return None


