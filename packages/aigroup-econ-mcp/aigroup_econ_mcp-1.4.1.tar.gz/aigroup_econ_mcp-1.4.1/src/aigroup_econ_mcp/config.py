"""


"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging
from dotenv import load_dotenv


class ConfigSource(Enum):
    """"""
    ENV = "environment"
    FILE = "file"
    DEFAULT = "default"


@dataclass
class ConfigValue:
    """"""
    value: Any
    source: ConfigSource
    key: str
    description: str = ""
    required: bool = False
    validated: bool = False


class ConfigurationError(Exception):
    """"""
    pass


class ConfigManager:
    """
    
    
    """
    
    def __init__(self, config_dir: Optional[str] = None, env_file: Optional[str] = None):
        """
        
        
        Args:
            config_dir: 
            env_file: 
        """
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "config"
        self.env_file = Path(env_file) if env_file else Path.cwd() / ".env"
        
        # 
        self.config_dir.mkdir(exist_ok=True)
        
        # 
        self._load_environment_variables()
        
        # 
        self._config: Dict[str, ConfigValue] = {}
        self._defaults: Dict[str, Any] = {}
        self._validators: Dict[str, callable] = {}
        
        # 
        self._setup_logging()
    
    def _load_environment_variables(self) -> None:
        """"""
        if self.env_file.exists():
            load_dotenv(self.env_file)
        else:
            load_dotenv()
    
    def _setup_logging(self) -> None:
        """"""
        logging.basicConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger("aigroup_econ_mcp")
    
    def set_default(self, key: str, value: Any, description: str = "", required: bool = False) -> None:
        """
        
        
        Args:
            key: 
            value: 
            description: 
            required: 
        """
        self._defaults[key] = {
            "value": value,
            "description": description,
            "required": required
        }
    
    def add_validator(self, key: str, validator: callable) -> None:
        """
        
        
        Args:
            key: 
            validator: 
        """
        self._validators[key] = validator
    
    def load_from_file(self, filename: str, file_type: str = "auto") -> None:
        """
        
        
        Args:
            filename: 
            file_type:  (json, yaml, auto)
        """
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            self.logger.warning(f": {file_path}")
            return
        
        try:
            if file_type == "auto":
                if filename.endswith(".json"):
                    file_type = "json"
                elif filename.endswith((".yaml", ".yml")):
                    file_type = "yaml"
                else:
                    raise ConfigurationError(f": {filename}")
            
            if file_type == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            elif file_type == "yaml":
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            else:
                raise ConfigurationError(f": {file_type}")
            
            # 
            self._update_config_from_dict(config_data, ConfigSource.FILE)
            
            self.logger.info(f": {file_path}")
            
        except Exception as e:
            raise ConfigurationError(f": {file_path}, : {e}")
    
    def load_from_environment(self, prefix: str = "AIGROUP_ECON_") -> None:
        """
        
        
        Args:
            prefix: 
        """
        env_config = {}
        
        for env_key, env_value in os.environ.items():
            if env_key.startswith(prefix):
                # 
                config_key = env_key[len(prefix):].lower()
                
                # 
                try:
                    # JSON
                    parsed_value = json.loads(env_value)
                except (json.JSONDecodeError, ValueError):
                    # JSON
                    parsed_value = env_value
                
                env_config[config_key] = parsed_value
        
        self._update_config_from_dict(env_config, ConfigSource.ENV)
        self.logger.info(f": {prefix}")
    
    def _update_config_from_dict(self, config_dict: Dict[str, Any], source: ConfigSource) -> None:
        """
        
        
        Args:
            config_dict: 
            source: 
        """
        for key, value in config_dict.items():
            description = self._defaults.get(key, {}).get("description", "")
            required = self._defaults.get(key, {}).get("required", False)
            
            # 
            if key in self._validators:
                try:
                    value = self._validators[key](value)
                    validated = True
                except Exception as e:
                    if required:
                        raise ConfigurationError(f": {key}={value}, : {e}")
                    else:
                        self.logger.warning(f": {key}={value}, : {e}")
                        validated = False
            else:
                validated = False
            
            self._config[key] = ConfigValue(
                value=value,
                source=source,
                key=key,
                description=description,
                required=required,
                validated=validated
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        
        
        Args:
            key: 
            default: 
            
        Returns:
            Any: 
        """
        if key in self._config:
            return self._config[key].value
        
        # 
        if key in self._defaults:
            default_value = self._defaults[key]["value"]
            self._config[key] = ConfigValue(
                value=default_value,
                source=ConfigSource.DEFAULT,
                key=key,
                description=self._defaults[key]["description"],
                required=self._defaults[key]["required"],
                validated=False
            )
            return default_value
        
        # 
        if default is not None:
            return default
        
        # 
        if key in self._defaults and self._defaults[key]["required"]:
            raise ConfigurationError(f": {key}")
        
        return None
    
    def set(self, key: str, value: Any, description: str = "") -> None:
        """
        
        
        Args:
            key: 
            value: 
            description: 
        """
        # 
        validated = False
        if key in self._validators:
            try:
                value = self._validators[key](value)
                validated = True
            except Exception as e:
                raise ConfigurationError(f": {key}={value}, : {e}")
        
        required = self._defaults.get(key, {}).get("required", False)
        
        self._config[key] = ConfigValue(
            value=value,
            source=ConfigSource.FILE,  # 
            key=key,
            description=description,
            required=required,
            validated=validated
        )
    
    def save_to_file(self, filename: str, file_type: str = "json") -> None:
        """
        
        
        Args:
            filename: 
            file_type:  (json, yaml)
        """
        file_path = self.config_dir / filename
        
        try:
            config_dict = {}
            for key, config_value in self._config.items():
                if config_value.source != ConfigSource.ENV:  # 
                    config_dict[key] = config_value.value
            
            if file_type == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
            elif file_type == "yaml":
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ConfigurationError(f": {file_type}")
            
            self.logger.info(f": {file_path}")
            
        except Exception as e:
            raise ConfigurationError(f": {file_path}, : {e}")
    
    def validate(self) -> List[str]:
        """
        
        
        Returns:
            List[str]: 
        """
        errors = []
        
        # 
        for key, default_info in self._defaults.items():
            if default_info["required"] and key not in self._config:
                errors.append(f": {key}")
        
        # 
        for key, config_value in self._config.items():
            if key in self._validators and not config_value.validated:
                try:
                    self._validators[key](config_value.value)
                    config_value.validated = True
                except Exception as e:
                    errors.append(f": {key}={config_value.value}, : {e}")
        
        return errors
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        
        
        Returns:
            Dict[str, Any]: 
        """
        config_info = {}
        
        for key, config_value in self._config.items():
            config_info[key] = {
                "value": config_value.value,
                "source": config_value.source.value,
                "description": config_value.description,
                "required": config_value.required,
                "validated": config_value.validated
            }
        
        return config_info
    
    def reload(self) -> None:
        """"""
        self._config.clear()
        self._load_environment_variables()
        self.load_from_environment()


# 
class ConfigValidators:
    """"""
    
    @staticmethod
    def validate_positive_int(value: Any) -> int:
        """"""
        try:
            int_value = int(value)
            if int_value <= 0:
                raise ValueError("")
            return int_value
        except (ValueError, TypeError):
            raise ValueError("")
    
    @staticmethod
    def validate_positive_float(value: Any) -> float:
        """"""
        try:
            float_value = float(value)
            if float_value <= 0:
                raise ValueError("")
            return float_value
        except (ValueError, TypeError):
            raise ValueError("")
    
    @staticmethod
    def validate_boolean(value: Any) -> bool:
        """"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ("true", "1", "yes", "on"):
                return True
            elif value.lower() in ("false", "0", "no", "off"):
                return False
        raise ValueError(" (true/false, 1/0, yes/no)")
    
    @staticmethod
    def validate_list(value: Any) -> list:
        """"""
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [item.strip() for item in value.split(",")]
        raise ValueError("")
    
    @staticmethod
    def validate_file_path(value: Any) -> str:
        """"""
        path = Path(str(value))
        if not path.exists():
            raise ValueError(f": {path}")
        return str(path.absolute())


# 
class EconometricConfig:
    """"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        
        
        Args:
            config_manager: 
        """
        self.config = config_manager
        
        # 
        self._set_defaults()
        
        # 
        self._add_validators()
    
    def _set_defaults(self) -> None:
        """"""
        defaults = {
            # 
            "cache_enabled": (True, "", False),
            "cache_ttl": (3600, "", False),
            "cache_max_size": (1000, "", False),
            
            # 
            "monitoring_enabled": (True, "", False),
            "memory_monitoring_interval": (1.0, "", False),
            
            # 
            "default_n_estimators": (100, "", False),
            "default_max_depth": (None, "", False),
            "default_learning_rate": (0.1, "", False),
            "default_alpha": (1.0, "", False),
            
            # 
            "min_sample_size": (10, "", False),
            "max_feature_count": (100, "", False),
            "data_validation_strict": (True, "", False),
            
            # 
            "log_level": ("INFO", "", False),
            "log_file": (None, "", False),
            
            # 
            "parallel_processing": (False, "", False),
            "max_workers": (None, "", False),
        }
        
        for key, (value, description, required) in defaults.items():
            self.config.set_default(key, value, description, required)
    
    def _add_validators(self) -> None:
        """"""
        validators = {
            "cache_enabled": ConfigValidators.validate_boolean,
            "cache_ttl": ConfigValidators.validate_positive_int,
            "cache_max_size": ConfigValidators.validate_positive_int,
            "monitoring_enabled": ConfigValidators.validate_boolean,
            "memory_monitoring_interval": ConfigValidators.validate_positive_float,
            "default_n_estimators": ConfigValidators.validate_positive_int,
            "default_learning_rate": ConfigValidators.validate_positive_float,
            "default_alpha": ConfigValidators.validate_positive_float,
            "min_sample_size": ConfigValidators.validate_positive_int,
            "max_feature_count": ConfigValidators.validate_positive_int,
            "data_validation_strict": ConfigValidators.validate_boolean,
            "parallel_processing": ConfigValidators.validate_boolean,
        }
        
        for key, validator in validators.items():
            self.config.add_validator(key, validator)
    
    def get_model_config(self) -> Dict[str, Any]:
        """"""
        return {
            "n_estimators": self.config.get("default_n_estimators"),
            "max_depth": self.config.get("default_max_depth"),
            "learning_rate": self.config.get("default_learning_rate"),
            "alpha": self.config.get("default_alpha"),
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """"""
        return {
            "enabled": self.config.get("cache_enabled"),
            "ttl": self.config.get("cache_ttl"),
            "max_size": self.config.get("cache_max_size"),
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """"""
        return {
            "enabled": self.config.get("monitoring_enabled"),
            "memory_interval": self.config.get("memory_monitoring_interval"),
        }


# 
global_config_manager = ConfigManager()
econometric_config = EconometricConfig(global_config_manager)

# 
def get_config(key: str, default: Any = None) -> Any:
    """"""
    return global_config_manager.get(key, default)

def set_config(key: str, value: Any, description: str = "") -> None:
    """"""
    global_config_manager.set(key, value, description)

def load_config_files() -> None:
    """"""
    # 
    global_config_manager.load_from_environment()
    
    # 
    config_files = ["config.json", "config.yaml", "config.yml"]
    for config_file in config_files:
        if (global_config_manager.config_dir / config_file).exists():
            global_config_manager.load_from_file(config_file)
            break

# 
load_config_files()

# 
__all__ = [
    "ConfigSource",
    "ConfigValue",
    "ConfigurationError",
    "ConfigManager",
    "ConfigValidators",
    "EconometricConfig",
    "global_config_manager",
    "econometric_config",
    "get_config",
    "set_config",
    "load_config_files"
]