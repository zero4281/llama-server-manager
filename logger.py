import logging
from typing import Dict, Any

class LoggerSetup:
    """
    Configures the root logger based on the logging section of the provided configuration.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def setup(self) -> None:
        logging_config = self.config.get("logging", {})
        enabled = logging_config.get("enabled", True)
        
        if not enabled:
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)
            return

        level_str = logging_config.get("level", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)
        logging.root.setLevel(level)

        log_file = logging_config.get("file")
        if log_file is None:
            log_file = "llama-server-manager.log"
        
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        file_handler = logging.FileHandler(log_file, mode="a")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logging.root.addHandler(file_handler)
