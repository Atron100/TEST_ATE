from pathlib import Path

from PySide6.QtCore import QFile, QIODevice, QDateTime, QTimer
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton

from ate_app.db_config_window import DBConfigWindow


class MainWindow:
    def __init__(self, username: str, status: int) -> None:
        self._username = username
        self._status = status
        self._db_config_window: DBConfigWindow | None = None
        self._date_time_label: QLabel | None = None
        self._date_time_timer: QTimer | None = None

        self._window = self._load_ui()
        self._configure_window()

    def _load_ui(self) -> QMainWindow:
        ui_path = Path(__file__).resolve().parent.parent / "MAIN_ATE.ui"
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError(f"Could not open UI file: {ui_path}")

        loader = QUiLoader()
        loaded_window = loader.load(ui_file)
        ui_file.close()

        if loaded_window is None:
            raise RuntimeError(f"Could not load UI file: {ui_path}")

        if not isinstance(loaded_window, QMainWindow):
            raise RuntimeError("MAIN_ATE.ui must have a QMainWindow as its top-level widget.")

        return loaded_window

    def _configure_window(self) -> None:
        self._window.setWindowTitle(self._window.windowTitle() or "LSBB ATE Test SW ver1.0")
        self._window.setFixedSize(1150, 900)

        status_bar = self._window.statusBar()
        if status_bar is not None:
            status_bar.showMessage(f"Logged as {self._username}")

        db_button = self._window.findChild(QPushButton, "DB_Button")
        if db_button is not None:
            db_button.clicked.connect(self._show_db_config)
            self._add_date_time_label(db_button)

        exit_button = self._window.findChild(QPushButton, "Exit_Button")
        if exit_button is not None:
            exit_button.clicked.connect(self.close)

    def _add_date_time_label(self, db_button: QPushButton) -> None:
        parent = db_button.parentWidget()
        if parent is None:
            return

        self._date_time_label = QLabel(parent)
        self._date_time_label.setObjectName("DateTimeLabel")
        self._date_time_label.setGeometry(
            db_button.x(),
            max(0, db_button.y() - 20),
            db_button.width() + 40,
            20,
        )

        self._date_time_timer = QTimer(parent)
        self._date_time_timer.timeout.connect(self._update_date_time)
        self._update_date_time()
        self._date_time_timer.start(1000)

    def _update_date_time(self) -> None:
        if self._date_time_label is None:
            return

        current_text = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss")
        self._date_time_label.setText(current_text)

    def _show_db_config(self) -> None:
        config_path = Path(__file__).resolve().parent.parent / "db_config.ini"
        self._db_config_window = DBConfigWindow(config_path, self._window)
        self._db_config_window.show()
        self._db_config_window.raise_()
        self._db_config_window.activateWindow()

    def show(self) -> None:
        self._window.show()

    def close(self) -> None:
        self._window.close()

