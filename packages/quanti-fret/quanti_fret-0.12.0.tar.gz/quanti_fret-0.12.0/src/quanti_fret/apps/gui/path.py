from quanti_fret.core import QtfException
from quanti_fret.apps.gui.io_gui_manager import IOGuiManager
from quanti_fret.apps.gui.utils import PathLabel

from pathlib import Path
import traceback

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PathWidget(QWidget):
    """ Handle the selection of a file or folder path.
    """

    def __init__(
        self, phase: str, config_key: tuple[str, str], type: str,
        dialog_title: str, *args, dialog_file_filter: str = '', **kwargs
    ) -> None:
        """ Constructor

        Args:
            phase (str): Phase of the widget
            config_key (tuple[str, str]): Config's section and key associated
                with the option
            type (str): Type of path to look for. Either 'file' or 'folder'
            dialog_title (str): Title to put on the dialog selection window
            dialog_file_filter (str): Filter to select pecific file type
        """
        super().__init__(*args, **kwargs)

        if type not in ['file', 'folder']:
            err = f'Unknow type {type}. Must be in ["file", "folder"]'
            raise QtfException(err)

        self._iopm = IOGuiManager().get_iopm(phase)
        self._config_key = config_key
        self._type = type
        self._dialog_title = dialog_title
        self._dialog_file_filter = dialog_file_filter

        # GUI
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignmentFlag.AlignTop)  # type: ignore
        self._buildPathSelection()

        # Populate with previous value
        self._updateDisplay()
        self._iopm.stateChanged.connect(self._updateDisplay)

    def _buildPathSelection(self) -> None:
        """ Build the folder selection GUI
        """
        fSelectBox = QGroupBox(f'Select {self._type.capitalize()}')
        self.layout().addWidget(fSelectBox)  # type: ignore
        fSelectLayout = QHBoxLayout()
        fSelectBox.setLayout(fSelectLayout)
        self._fSelectLabel = PathLabel("Path:")
        fSelectLayout.addWidget(self._fSelectLabel)

        # Folder select Button
        self._buttonLayout = QVBoxLayout()
        fSelectLayout.addLayout(self._buttonLayout)
        self._fSelectButton = QPushButton("Select")
        self._buttonLayout.addWidget(self._fSelectButton)
        self._fSelectButton.setMinimumSize(50, 25)
        self._fSelectButton.setMaximumSize(100, 50)
        self._fSelectButton.clicked.connect(self._openPath)

    def _openPath(self) -> None:
        """ Let the user choose a directory with a directory selection window,
        and update the output folder.
        """
        current_path = self._iopm.config.get(*self._config_key)
        if current_path is not None:
            parent = str(current_path.parent)
        else:
            parent = ""

        # Select user's path
        if self._type == 'file':
            path_str, _ = QFileDialog.getOpenFileName(
                self, self._dialog_title, parent, self._dialog_file_filter
            )
        else:
            path_str = QFileDialog.getExistingDirectory(
                self, self._dialog_title, parent
            )

        # Manage results
        if path_str:
            self._updatePath(Path(path_str))

    def _updatePath(self, path: Path | None) -> None:
        """ Update the path with the one chosen

        Args:
            path (Path | None): Path to set
        """
        current_path = self._iopm.config.get(*self._config_key)
        if path != current_path:
            try:
                self._iopm.config.set(*self._config_key, path)
            except Exception:
                msgBox = QMessageBox()
                msgBox.setText('Error while loading the file...')
                msgBox.setInformativeText(traceback.format_exc())
                msgBox.setStandardButtons(
                    QMessageBox.StandardButton.Close
                )
                msgBox.setIcon(QMessageBox.Icon.Critical)
                self._iopm.config.set(*self._config_key, current_path)
                msgBox.exec()

    def _updateDisplay(self) -> None:
        """ Update the current output folder value
        """
        current_path = self._iopm.config.get(*self._config_key)
        if current_path is None:
            current_path_str = ''
        else:
            current_path_str = str(current_path)
        self._fSelectLabel.setText(current_path_str)
        self._fSelectButton.setText("Change")


class FretCaliConfigFileWidget(PathWidget):
    """ Widget handling the Calibration config file selection for the Fret
    phase.
    """
    def __init__(self, *args, **kwargs) -> None:
        """ Constructor
        """
        super().__init__(
            'fret', ('Calibration', 'config_file'), 'file',
            'Select Calibration Results folder', *args,
            dialog_file_filter='Config (*.ini)', **kwargs)

        self._iopm_cali = IOGuiManager().cali

        # Add Button to set to the current calibrations
        self._toCurrentButton = QPushButton('Active Config')
        self._buttonLayout.addWidget(self._toCurrentButton)
        self._toCurrentButton.clicked.connect(self._setToCurrentCaliConfig)
        self._toCurrentButton.setMaximumSize(self._fSelectButton.size())

        self._updateButton()
        self._iopm.stateChanged.connect(self._updateButton)
        self._iopm_cali.stateChanged.connect(self._updateButton)
        self._iopm_cali.noConfig.connect(self._remove_config_if_non_existing)
        self._iopm_cali.errorConfig.connect(
            self._remove_config_if_non_existing)

    def _setToCurrentCaliConfig(self):
        new_path = self._iopm_cali.get_active_config_path()
        assert new_path is not None
        self._updatePath(new_path)
        self._updateButton()

    def _updateButton(self) -> None:
        """ Update the current output folder value
        """
        active_cali_path = self._iopm_cali.get_active_config_path()
        fret_cali_path = self._iopm.config.get(*self._config_key)

        if active_cali_path is None:
            self._toCurrentButton.setEnabled(False)
            self._iopm_cali.link_iopm(None)
        else:
            if active_cali_path == fret_cali_path:
                self._toCurrentButton.setEnabled(False)
                self._iopm_cali.link_iopm(self._iopm)
            else:
                self._toCurrentButton.setEnabled(True)
                self._iopm_cali.link_iopm(None)
        self._remove_config_if_non_existing()

    def _remove_config_if_non_existing(self) -> None:
        """ Remove the calibration config file if the file doesn't exists
        anymore
        """
        fret_cali_path: Path | None = self._iopm.config.get(*self._config_key)
        if fret_cali_path is not None:
            if not fret_cali_path.exists():
                self._updatePath(None)
                self._updateButton()
