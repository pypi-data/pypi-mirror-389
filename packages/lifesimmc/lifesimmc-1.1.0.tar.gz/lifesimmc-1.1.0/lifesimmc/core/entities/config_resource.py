from lifesimmc.core.entities.base_resource import BaseResource


class ConfigResource(BaseResource):
    def __init__(self, name: str):
        super().__init__(name)
        self.phringe = None
