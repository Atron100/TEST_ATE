from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LoginWindow(QWidget):
    login_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ATE Login")
        self.setFixedSize(480, 320)

        self._username_input = QLineEdit()
        self._password_input = QLineEdit()
        self._login_button = QPushButton("Login")
        self._login_button.setAutoDefault(True)
        self._login_button.setDefault(True)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #f4f7fb;
                color: #1f2933;
                font-size: 14px;
            }
            QFrame#card {
                background-color: white;
                border: 1px solid #d9e2ec;
                border-radius: 16px;
            }
            QLineEdit {
                min-height: 40px;
                border: 1px solid #bcccdc;
                border-radius: 8px;
                padding: 0 12px;
                background-color: #fdfefe;
            }
            QLineEdit:focus {
                border: 1px solid #486581;
            }
            QPushButton {
                min-height: 42px;
                border: none;
                border-radius: 8px;
                background-color: #0f4c81;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1363a2;
            }
            """
        )

        title = QLabel("LSBB ATE TEST STATION")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Sign in to continue to the test dashboard")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #52606d;")

        self._username_input.setPlaceholderText("Username")
        self._username_input.returnPressed.connect(self._password_input.setFocus)

        self._password_input.setPlaceholderText("Password")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.returnPressed.connect(self._login_button.setFocus)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setVerticalSpacing(14)
        form_layout.addRow("Username", self._username_input)
        form_layout.addRow("Password", self._password_input)

        self._login_button.clicked.connect(self._submit_login)
        

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(18)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(8)
        card_layout.addLayout(form_layout)
        card_layout.addSpacing(6)
        card_layout.addWidget(self._login_button)

        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(24, 24, 24, 24)
        outer_layout.addWidget(card)

    def _submit_login(self) -> None:
        self.login_requested.emit(
            self._username_input.text(),
            self._password_input.text(),
        )

    def show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Login Error", message)


