import logging
from pathlib import Path
import yaml


class Exporter:
    def __init__(self, config_file: Path) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_file = config_file

    from pathlib import Path

    def export(self) -> None:
        self.logger.info("Starting exporting…")
        self.logger.info(f"Using config: {self.config_file}")

        if not self.config_file.exists():
            msg = f"Config file does not exist: {self.config_file}"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        try:
            with self.config_file.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            msg = f"Failed to parse YAML: {e}"
            self.logger.error(msg)
            raise

        if not isinstance(config_data, dict):
            msg = "Config YAML is not a valid mapping."
            self.logger.error(msg)
            raise ValueError(msg)

        for report_id, config in config_data.items():
            self.logger.info(f"Report ID: {report_id}")
            for key, value in config.items():
                self.logger.info(f"  {key}: {value}")

        self.logger.info("Exporting finished.")

    def add(self, a: int, b: int) -> int:
        return a + b
