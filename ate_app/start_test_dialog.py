from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class StartTestDialog(QDialog):
    def __init__(self, board_pn: str, description: str, parent=None) -> None:
        super().__init__(parent)
        self._board_pn = board_pn or "N/A"
        self._description = description or "N/A"

        self._sn_input = QLineEdit()
        self._pn_label = QLabel(self._board_pn)
        self._desc_label = QLabel(self._description)
        self._test_type_combo = QComboBox()

        self.setWindowTitle("Start Test")
        self.setFixedSize(430, 220)
        self._build_ui()

    def _build_ui(self) -> None:
        self._sn_input.setPlaceholderText("Enter serial number")
        self._test_type_combo.addItems(["FPY", "MRB", "RMA", "INV"])

        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.addRow("SN:", self._sn_input)
        form_layout.addRow("PN:", self._pn_label)
        form_layout.addRow("DESC:", self._desc_label)
        form_layout.addRow("Test Type:", self._test_type_combo)

        start_button = QPushButton("Start")
        start_button.clicked.connect(self._handle_start)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(start_button)
        buttons_layout.addWidget(cancel_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        layout.addLayout(form_layout)
        layout.addStretch()
        layout.addLayout(buttons_layout)

    def _handle_start(self) -> None:
        if not self.serial_number:
            QMessageBox.warning(self, "Start Test", "Please enter a serial number.")
            return
        self.accept()

    @property
    def serial_number(self) -> str:
        return self._sn_input.text().strip()

    @property
    def test_type(self) -> str:
        return self._test_type_combo.currentText()
