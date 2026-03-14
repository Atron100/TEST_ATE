import sys

from PySide6.QtWidgets import QApplication

from ate_app.application import ATEApplication


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("LSBB ATE Test SW ver1.0")

    ate_application = ATEApplication()
    ate_application.start()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
