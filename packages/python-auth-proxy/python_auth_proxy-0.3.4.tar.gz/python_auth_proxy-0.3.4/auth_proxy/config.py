import logging
import os
from typing import Any, Dict, List, Optional, Union

import yaml

logger = logging.getLogger(__name__)


class ProxyConfig:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            logger.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            try:
                return yaml.safe_load(f)  # type: ignore
            except yaml.YAMLError as e:
                logger.error(f"Error parsing config file: {e}")
                raise

    @property
    def listen(self) -> Dict[str, Union[str, int]]:
        """Get listener configuration."""
        return self.config.get("listen", {})  # type: ignore

    @property
    def backend(self) -> Dict[str, Union[str, int]]:
        """Get backend configuration."""
        return self.config.get("backend", {})  # type: ignore

    @property
    def auth(self) -> Dict[str, Any]:
        """Get authentication configuration."""
        return self.config.get("auth", {})  # type: ignore

    @property
    def auth_plugins(self) -> Dict[str, Any]:
        """Get authentication plugins configuration."""
        return self.config.get("auth_plugins", {})  # type: ignore

    @property
    def paths(self) -> List[Dict[str, Any]]:
        """Get path rules configuration."""
        return self.config.get("paths", [])  # type: ignore
