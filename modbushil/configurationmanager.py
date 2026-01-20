from typing import Any

from .modbusintegrationsettings import ModbusIntegrationSettings


class ConfigurationManager:
    configs: dict[str, ModbusIntegrationSettings] = {}

    def __init__(self):
        pass

    @classmethod
    def register_model(cls, modelname: str, config: dict[str, Any]):
        if modelname in cls.configs:
            raise ValueError(f"Model {modelname} is already registered")
        cls.configs[modelname] = ModbusIntegrationSettings(config)
    
    @classmethod
    def get_model_config(cls, modelname: str) -> ModbusIntegrationSettings:
        if modelname not in cls.configs:
            raise ValueError(f"Model {modelname} is not registered")
        return cls.configs[modelname]
    
    @classmethod
    def get_registered_models(cls) -> list[str]:
        return list(cls.configs.keys())
