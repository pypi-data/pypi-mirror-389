from quanti_fret.apps.gui.stages.background.mode_radio_button import (
    BckgModeRadioButton
)
from quanti_fret.apps.gui.io_gui_manager import IOGuiManager
from quanti_fret.apps.gui.utils import BackgroundEngineLabel

from quanti_fret.algo import BackgroundMode

from qtpy.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QVBoxLayout,
)


class FloatingBackgroundBox(QGroupBox):
    """ Group Box for Background floating selection

    Disaplay a checkbox to activate or deactivate the floating background.

    In Fret mode, it also display the results of the calibration background
    results.
    """

    def __init__(self, phase: str, *args, **kwargs) -> None:
        """ Constructor

        Args:
            phase (str): Phase associated with the widget
        """
        super().__init__('Floating Background', *args, **kwargs)

        self._phase = phase
        self._iopm = IOGuiManager().get_iopm(phase)
        self._modeButtons: dict[BackgroundMode, BckgModeRadioButton] = {}

        self._buildGui()

        if phase == 'fret':
            IOGuiManager().cali.stateChanged.connect(self._updateSettings)
        self._iopm.stateChanged.connect(self._updateSettings)
        self._updateSettings()

    def _buildGui(self) -> None:
        """ Build the GUI interface
        """
        # Layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Checkbox
        self._checkBox = QCheckBox('Activate', self)
        self._checkBox.stateChanged.connect(self._select_floating_background)
        layout.addWidget(self._checkBox)

        # Calibration Value
        if self._phase == 'fret':
            self._caliBckgLabel = BackgroundEngineLabel(
                self,
                preText='(Calibration Value:',
                postText=')'
            )
            layout.addWidget(self._caliBckgLabel)

    def _updateSettings(self) -> None:
        """ Update the checkbox and background results
        """
        # Floating state
        self._checkBox.blockSignals(True)
        # Checkbox
        floating = self._iopm.config.get('Background', 'floating')
        self._checkBox.setChecked(floating)

        # Calibration Background
        if self._phase == 'fret':
            (engine,) = self._iopm.params.get('cali_background',
                                              allow_none_values=True)
            self._caliBckgLabel.setBackgroundEngine(engine)
            f = self._caliBckgLabel.font()
            f.setStrikeOut(floating)
            self._caliBckgLabel.setFont(f)

        self._checkBox.blockSignals(False)

    def _select_floating_background(self, _: int) -> None:
        """ Select the floating background to the given value
        """
        checked = self._checkBox.isChecked()
        self._iopm.config.set('Background', 'floating', checked)
