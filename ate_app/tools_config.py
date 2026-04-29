from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path


class ToolsConfigError(RuntimeError):
    """Raised when the tools configuration cannot be loaded."""


@dataclass(frozen=True)
class ToolsConfig:
    ps_main: str
    ps_second: str
    serial_com_port: str
    ssh: str
    network_analyzer: str
    vna: str

    @classmethod
    def from_ini(cls, config_path: Path) -> "ToolsConfig":
        parser = configparser.ConfigParser()
        files_read = parser.read(config_path, encoding="utf-8")
        if not files_read:
            raise ToolsConfigError(f"Tools config file was not found: {config_path}")

        section = "HARDWARE_RESOURCES"
        if section not in parser:
            raise ToolsConfigError(
                f"Tools config is missing the [{section}] section."
            )

        resource_section = parser[section]
        required_keys = (
            "PS_MAIN",
            "PS_SECOND",
            "SERIAL_COM_PORT",
            "SSH",
            "NETWORK_ANALYZER",
            "VNA",
        )
        missing_keys = [key for key in required_keys if not resource_section.get(key)]
        if missing_keys:
            missing = ", ".join(missing_keys)
            raise ToolsConfigError(
                f"Tools config is missing required keys: {missing}"
            )

        return cls(
            ps_main=resource_section["PS_MAIN"],
            ps_second=resource_section["PS_SECOND"],
            serial_com_port=resource_section["SERIAL_COM_PORT"],
            ssh=resource_section["SSH"],
            network_analyzer=resource_section["NETWORK_ANALYZER"],
            vna=resource_section["VNA"],
        )
