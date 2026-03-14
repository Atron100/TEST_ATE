from pathlib import Path

from PySide6.QtCore import QFile, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMainWindow


class MainWindow:
    def __init__(self, username: str, status: int) -> None:
        self._username = username
        self._status = status
    
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

    def show(self) -> None:
        self._window.show()

    def close(self) -> None:
        self._window.close()
