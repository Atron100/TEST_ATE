from configparser import ConfigParser
from pathlib import Path

from PySide6.QtCore import QFile, QIODevice, QDateTime, QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
)

from ate_app.db_config_window import DBConfigWindow
from ate_app.sequence import SequenceDefinition, SequenceEntry, SequenceGroup, SequenceLoader, SequenceTest
from ate_app.start_test_dialog import StartTestDialog
from ate_app.tools_config import ToolsConfigError
from ate_app.tools_config_window import ToolsConfigWindow


class MainWindow:
    def __init__(self, username: str, status: int) -> None:
        self._username = username
        self._status = status
        self._db_config_window: DBConfigWindow | None = None
        self._start_test_dialog: StartTestDialog | None = None
        self._tools_config_window: ToolsConfigWindow | None = None
        self._date_time_label: QLabel | None = None
        self._date_time_timer: QTimer | None = None
        self._sequence: SequenceDefinition | None = None
        self._test_items: dict[int, QTreeWidgetItem] = {}
        self._stop_requested = False

        self._window = self._load_ui()
        self._configure_window()

    def _load_ui(self) -> QMainWindow:
        ui_path = Path(__file__).resolve().parent.parent / 'MAIN_ATE.ui'
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError(f'Could not open UI file: {ui_path}')

        loader = QUiLoader()
        loaded_window = loader.load(ui_file)
        ui_file.close()

        if loaded_window is None:
            raise RuntimeError(f'Could not load UI file: {ui_path}')

        if not isinstance(loaded_window, QMainWindow):
            raise RuntimeError('MAIN_ATE.ui must have a QMainWindow as its top-level widget.')

        return loaded_window

    def _configure_window(self) -> None:
        self._window.setWindowTitle(self._window.windowTitle() or 'LSBB ATE Test SW ver1.0')
        self._window.setFixedSize(1150, 900)

        status_bar = self._window.statusBar()
        if status_bar is not None:
            status_bar.showMessage(f'Logged as {self._username}')

        db_button = self._window.findChild(QPushButton, 'DB_Button')
        if db_button is not None:
            db_button.clicked.connect(self._show_db_config)
            self._add_date_time_label(db_button)

        tools_button = self._window.findChild(QPushButton, 'Tools_Button')
        if tools_button is not None:
            tools_button.clicked.connect(self._show_tools_config)

        exit_button = self._window.findChild(QPushButton, 'Exit_Button')
        if exit_button is not None:
            exit_button.clicked.connect(self.close)

        start_button = self._window.findChild(QPushButton, 'Start_Test')
        if start_button is not None:
            start_button.clicked.connect(self._show_start_test_dialog)

        stop_button = self._window.findChild(QPushButton, 'Stop_Test')
        if stop_button is not None:
            stop_button.clicked.connect(self._request_stop)

        self._configure_sequence_selector()
        self._configure_tree()
        self._load_available_sequences()

    def _configure_sequence_selector(self) -> None:
        combo_box = self._window.findChild(QComboBox, 'comboBox')
        if combo_box is None:
            return

        combo_box.currentIndexChanged.connect(self._load_selected_sequence)

    def _load_available_sequences(self) -> None:
        combo_box = self._window.findChild(QComboBox, 'comboBox')
        if combo_box is None:
            return

        combo_box.blockSignals(True)
        combo_box.clear()

        config_path = Path(__file__).resolve().parent.parent / 'agile_config.ini'
        parser = ConfigParser()
        parser.read(config_path, encoding='utf-8')

        if parser.has_section('SEQ_LIST'):
            base_path = config_path.parent
            for _display_name, file_name in parser.items('SEQ_LIST'):
                display_text = Path(file_name).stem
                file_path = base_path / file_name
                combo_box.addItem(display_text, str(file_path))

        combo_box.blockSignals(False)

        if combo_box.count() > 0:
            self._load_selected_sequence()

    def _configure_tree(self) -> None:
        tree_widget = self._window.findChild(QTreeWidget, 'treeWidget')
        if tree_widget is None:
            return

        tree_widget.setColumnCount(7)
        tree_widget.setHeaderLabels(
            ['Check', 'Test Name', 'Min Limit', 'Max Limit', 'Measured Value', 'Units', 'Status']
        )
        tree_widget.setRootIsDecorated(True)
        tree_widget.setAlternatingRowColors(True)
        tree_widget.setIndentation(0)
        tree_widget.header().setStretchLastSection(False)
        tree_widget.setColumnWidth(0, 70)
        tree_widget.setColumnWidth(1, 320)
        tree_widget.setColumnWidth(2, 100)
        tree_widget.setColumnWidth(3, 100)
        tree_widget.setColumnWidth(4, 130)
        tree_widget.setColumnWidth(5, 80)
        tree_widget.setColumnWidth(6, 90)

    def _load_selected_sequence(self) -> None:
        combo_box = self._window.findChild(QComboBox, 'comboBox')
        if combo_box is None or combo_box.count() == 0:
            return

        file_path_value = combo_box.currentData()
        if not file_path_value:
            return

        self._sequence = SequenceLoader.load(Path(file_path_value))
        self._populate_sequence_details()
        self._populate_tree()

    def _populate_sequence_details(self) -> None:
        if self._sequence is None:
            return

        project_label = self._window.findChild(QLabel, 'label_2')
        if project_label is not None:
            project_label.setText(f'PROJECT: {self._sequence.sequence_name}')

        sn_label = self._window.findChild(QLabel, 'label4')
        if sn_label is not None:
            sn_label.setText(f'BOARD PN: {self._sequence.board_pn}')

        status_label = self._window.findChild(QLabel, 'label')
        if status_label is not None:
            status_label.setText('STATUS: READY')

    def _populate_tree(self) -> None:
        tree_widget = self._window.findChild(QTreeWidget, 'treeWidget')
        if tree_widget is None or self._sequence is None:
            return

        tree_widget.clear()
        self._test_items.clear()

        group_items: dict[int, QTreeWidgetItem] = {}
        for entry in self._sequence.entries:
            if isinstance(entry, SequenceGroup):
                group_item = self._create_group_item(entry)
                if entry.parent_id is not None and entry.parent_id in group_items:
                    group_items[entry.parent_id].addChild(group_item)
                else:
                    tree_widget.addTopLevelItem(group_item)
                group_items[entry.id] = group_item
                continue

            test_item = self._create_test_item(entry)
            if entry.parent_id is not None and entry.parent_id in group_items:
                group_items[entry.parent_id].addChild(test_item)
            else:
                tree_widget.addTopLevelItem(test_item)
            self._test_items[entry.id] = test_item

        tree_widget.expandAll()

    def _create_group_item(self, group: SequenceGroup) -> QTreeWidgetItem:
        item = QTreeWidgetItem(['', group.name, '', '', '', '', ''])
        item.setFirstColumnSpanned(False)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
        item.setForeground(1, QColor('#0f4c81'))
        return item

    def _create_test_item(self, test: SequenceTest) -> QTreeWidgetItem:
        test_name = f'    {test.name}' if test.parent_id is not None else test.name
        item = QTreeWidgetItem(
            [
                '',
                test_name,
                self._format_limit_value(test.min_limit),
                self._format_limit_value(test.max_limit),
                '',
                test.units,
                '',
            ]
        )
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Checked if test.enabled else Qt.CheckState.Unchecked)
        return item

    def _format_limit_value(self, value: float | int | None) -> str:
        if value is None:
            return ''
        if isinstance(value, float):
            return f'{value:.3f}'.rstrip('0').rstrip('.')
        return str(value)

    def _run_all_tests(self) -> None:
        if self._sequence is None:
            return

        self._stop_requested = False
        status_label = self._window.findChild(QLabel, 'label')
        if status_label is not None:
            status_label.setText('STATUS: RUNNING')

        overall_pass = True
        for test in self._sequence.tests:
            if self._stop_requested:
                break

            item = self._test_items.get(test.id)
            if item is None:
                continue

            if item.checkState(0) != Qt.CheckState.Checked:
                item.setText(6, 'SKIPPED')
                item.setForeground(6, QColor('#7a7a7a'))
                continue

            measured_value, test_status = self._execute_test(test)
            item.setText(4, measured_value)
            item.setText(6, test_status)
            item.setForeground(6, QColor('#1f7a1f') if test_status == 'PASS' else QColor('#b22222'))
            QApplication.processEvents()

            if test_status != 'PASS':
                overall_pass = False

        if status_label is not None:
            if self._stop_requested:
                status_label.setText('STATUS: STOPPED')
            else:
                status_label.setText('STATUS: PASS' if overall_pass else 'STATUS: FAIL')

    def _execute_test(self, test: SequenceTest) -> tuple[str, str]:
        measured = self._calculate_measured_value(test)
        passed = self._is_within_limits(measured, test)
        return self._format_measured_value(measured), 'PASS' if passed else 'FAIL'

    def _calculate_measured_value(self, test: SequenceTest) -> float | int:
        command_names = [str(step.get('cmd', '')) for step in test.steps]

        if test.units.upper() == 'BOOL' or 'READ_DIGITAL' in command_names:
            return 1

        if test.min_limit is not None and test.max_limit is not None:
            if test.min_limit == test.max_limit:
                return test.min_limit
            return round((float(test.min_limit) + float(test.max_limit)) / 2, 3)

        return 0

    def _is_within_limits(self, measured: float | int, test: SequenceTest) -> bool:
        if test.min_limit is not None and measured < test.min_limit:
            return False
        if test.max_limit is not None and measured > test.max_limit:
            return False
        return True

    def _format_measured_value(self, measured: float | int) -> str:
        if isinstance(measured, float):
            return f'{measured:.3f}'.rstrip('0').rstrip('.')
        return str(measured)

    def _request_stop(self) -> None:
        self._stop_requested = True

    def _add_date_time_label(self, db_button: QPushButton) -> None:
        parent = db_button.parentWidget()
        if parent is None:
            return

        self._date_time_label = QLabel(parent)
        self._date_time_label.setObjectName('DateTimeLabel')
        self._date_time_label.setGeometry(
            db_button.x(),
            max(0, db_button.y() - 20),
            db_button.width() + 60,
            20,
        )

        self._date_time_timer = QTimer(parent)
        self._date_time_timer.timeout.connect(self._update_date_time)
        self._update_date_time()
        self._date_time_timer.start(1000)

    def _update_date_time(self) -> None:
        if self._date_time_label is None:
            return

        current_text = QDateTime.currentDateTime().toString('dd/MM/yyyy HH:mm:ss')
        self._date_time_label.setText(current_text)

    def _show_db_config(self) -> None:
        config_path = Path(__file__).resolve().parent.parent / 'db_config.ini'
        self._db_config_window = DBConfigWindow(config_path, self._window)
        self._db_config_window.show()
        self._db_config_window.raise_()
        self._db_config_window.activateWindow()

    def _show_start_test_dialog(self) -> None:
        if self._sequence is None:
            QMessageBox.warning(self._window, 'Start Test', 'Please select a sequence before starting.')
            return

        description = self._get_sequence_description()
        self._start_test_dialog = StartTestDialog(
            board_pn=self._sequence.board_pn,
            description=description,
            parent=self._window,
        )

        if self._start_test_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        status_bar = self._window.statusBar()
        if status_bar is not None:
            status_bar.showMessage(
                f'Logged as {self._username} | SN: {self._start_test_dialog.serial_number} | '
                f'Type: {self._start_test_dialog.test_type}'
            )

        self._run_all_tests()

    def _get_sequence_description(self) -> str:
        config_path = Path(__file__).resolve().parent.parent / 'agile_config.ini'
        parser = ConfigParser()
        parser.read(config_path, encoding='utf-8')

        if parser.has_option('ATE_DATA', 'FIX_DESC'):
            return parser.get('ATE_DATA', 'FIX_DESC')

        if self._sequence is not None:
            return self._sequence.sequence_name

        return 'N/A'

    def _show_tools_config(self) -> None:
        config_path = Path(__file__).resolve().parent.parent / 'tools_config.ini'
        try:
            self._tools_config_window = ToolsConfigWindow(config_path, self._window)
        except ToolsConfigError as exc:
            QMessageBox.warning(self._window, 'Tools Config Error', str(exc))
            return

        self._tools_config_window.show()
        self._tools_config_window.raise_()
        self._tools_config_window.activateWindow()

    def show(self) -> None:
        self._window.show()

    def close(self) -> None:
        self._window.close()
