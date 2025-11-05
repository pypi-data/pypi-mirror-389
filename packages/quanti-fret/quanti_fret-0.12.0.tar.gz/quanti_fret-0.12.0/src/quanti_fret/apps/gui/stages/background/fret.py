from quanti_fret.apps.gui.stages.background.mode import BackgroundModeBox
from quanti_fret.apps.gui.stages.background.floating import (
    FloatingBackgroundBox
)
from quanti_fret.apps.gui.io_gui_manager import IOGuiManager

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QVBoxLayout,
    QWidget
)


class BackgroundFretWidget(QWidget):
    """ Handle the background settings for the Fret
    """

    def __init__(self, *args, **kwargs) -> None:
        """Constructor
        """
        super().__init__(*args, **kwargs)
        self._phase = 'fret'
        self._iopm = IOGuiManager().fret
        self._buildGui()
        self._iopm.stateChanged.connect(self._updateSettings)
        self._updateSettings()

    def _buildGui(self) -> None:
        """ Create the GUI
        """
        # Layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

        # Floating Box
        floatingBox = FloatingBackgroundBox(self._phase, self)
        layout.addWidget(floatingBox)

        # Mode Box
        self._modeBox = BackgroundModeBox(self._phase, self)
        layout.addWidget(self._modeBox)

    def _updateSettings(self) -> None:
        """ Enable or Disable the mode box
        """
        # Disabled what is needed
        floating = self._iopm.config.get('Background', 'floating')
        if floating:
            self._modeBox.setEnabled(True)
        else:
            self._modeBox.setEnabled(False)
