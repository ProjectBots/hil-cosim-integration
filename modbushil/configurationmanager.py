from modbushil.modbusintegrationsettings import ModbusIntegrationSettings
from typing import Any


class ConfigurationManager:
    configs: dict[str, ModbusIntegrationSettings] = {}

    def __init__(self):
        pass

    @classmethod
    def registerModel(cls, modelname: str, config: dict[str, Any]):
        if modelname in cls.configs:
            raise ValueError(f"Model {modelname} is already registered")
        cls.configs[modelname] = ModbusIntegrationSettings(config)
