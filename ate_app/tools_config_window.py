from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QFormLayout, QLabel, QPushButton, QVBoxLayout

from ate_app.tools_config import ToolsConfig


class ToolsConfigWindow(QDialog):
    def __init__(self, config_path: Path, parent=None) -> None:
        super().__init__(parent)
        self._config = ToolsConfig.from_ini(config_path)
        self.setWindowTitle("Hardware Resources")
        self.setFixedSize(520, 320)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        title = QLabel("Hardware Resources")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.addRow("PS Main:", QLabel(self._config.ps_main))
        form_layout.addRow("PS Second:", QLabel(self._config.ps_second))
        form_layout.addRow("Serial COM Port:", QLabel(self._config.serial_com_port))
        form_layout.addRow("SSH:", QLabel(self._config.ssh))
        form_layout.addRow("Network Analyzer:", QLabel(self._config.network_analyzer))
        form_layout.addRow("VNA:", QLabel(self._config.vna))

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        layout.addWidget(title)
        layout.addLayout(form_layout)
        layout.addStretch()
        layout.addWidget(close_button)
