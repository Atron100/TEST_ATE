from pathlib import Path

from PySide6.QtCore import QObject

from ate_app.database import AuthenticationServiceError, LoginRepository
from ate_app.main_window import MainWindow
from ate_app.login_window import LoginWindow


class ATEApplication(QObject):
    def __init__(self) -> None:
        super().__init__()
        config_path = Path(__file__).resolve().parent.parent / "db_config.ini"
        self._login_repository = LoginRepository(config_path)
        self._login_window = LoginWindow()
        self._main_window: MainWindow | None = None

        self._login_window.login_requested.connect(self._handle_login)

    def start(self) -> None:
        self._login_window.show()

    def _handle_login(self, username: str, password: str) -> None:
        if not username.strip() or not password.strip():
            self._login_window.show_error("Please enter both username and password.")
            return

        try:
            is_valid_login = self._login_repository.validate_credentials(username=username, password=password)

            if is_valid_login:
                status_query = self._login_repository.return_status(username=username)
                print(f"User {username} status: {status_query}")
            else:
                print(f"User {username} failed to log in.")
                
        except AuthenticationServiceError as exc:
            self._login_window.show_error(str(exc))
            return

        if not is_valid_login:
            self._login_window.show_error("Invalid username or password.")
            return

        self._main_window = MainWindow(username=username, status=int(status_query))
        self._main_window.show()
        self._login_window.close()
