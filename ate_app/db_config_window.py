from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QFormLayout, QLabel, QPushButton, QVBoxLayout

from ate_app.database import DatabaseConfig


class DBConfigWindow(QDialog):
    def __init__(self, config_path: Path, parent=None) -> None:
        super().__init__(parent)
        self._config = DatabaseConfig.from_ini(config_path)
        self.setWindowTitle("Database Configuration")
        self.setFixedSize(420, 220)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        title = QLabel("DB Configuration")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.addRow("DB Name:", QLabel(self._config.database))
        form_layout.addRow("Login:", QLabel(self._config.username))
        form_layout.addRow("Server:", QLabel(self._config.server))

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        layout.addWidget(title)
        layout.addLayout(form_layout)
        layout.addStretch()
        layout.addWidget(close_button)
