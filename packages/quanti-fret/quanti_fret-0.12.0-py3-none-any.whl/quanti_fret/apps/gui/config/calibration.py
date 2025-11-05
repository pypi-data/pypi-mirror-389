from quanti_fret.apps.gui.config.config import ConfigManagementWidget
from quanti_fret.apps.gui.utils import BackgroundEngineLabel

from qtpy.QtWidgets import (
    QFrame,
    QGroupBox,
    QLabel,
    QVBoxLayout,
)


class CalibrationConfigManagementWidget(ConfigManagementWidget):
    """ Handle the selection and creation of config files of calibration phase.

    It also display the summary results of the calibration if any.
    """
    def __init__(self, *args, **kwargs) -> None:
        """ Constructor
        """
        super().__init__('calibration', *args, **kwargs)

    def _buildSeparator(self) -> None:
        """ Build the separator line between config management and results
        """
        horizontal_line = QFrame()
        horizontal_line.setFrameShape(QFrame.Shape.HLine)
        horizontal_line.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout().addWidget(horizontal_line)  # type: ignore

    def _buildPhaseSummary(self) -> None:
        """ Build the widgets to show the Calibration results
        """
        # Result layout
        resultLayout = QVBoxLayout()
        self.layout().addLayout(resultLayout)  # type: ignore

        # Result settings box
        resultSettingsBox = QGroupBox('Calibration Results')
        resultLayout.addWidget(resultSettingsBox)
        resultSettingsLayout = QVBoxLayout()
        resultSettingsBox.setLayout(resultSettingsLayout)
        self._rBackgroundLabel = BackgroundEngineLabel()
        self._rAlphaBt = QLabel('Alpha BT: -')
        self._rDeltaDe = QLabel('Delta DE: -')
        self._rBetaXLabel = QLabel('Beta X: -')
        self._rGammaMLabel = QLabel('Gamma M: -')
        resultSettingsLayout.addWidget(self._rBackgroundLabel)
        resultSettingsLayout.addWidget(self._rAlphaBt)
        resultSettingsLayout.addWidget(self._rDeltaDe)
        resultSettingsLayout.addWidget(self._rBetaXLabel)
        resultSettingsLayout.addWidget(self._rGammaMLabel)

    def _updateResults(self) -> None:
        """Update the calibration results
        """
        background = None
        alphaBT = '-'
        deltaDE = '-'
        betaX = '-'
        gammaM = '-'

        res = self._iopm.results.get('background')
        if res is not None:
            background = res[1][0]

        res = self._iopm.results.get('bt')
        if res is not None:
            alphaBT = str(res[1][0])

        res = self._iopm.results.get('de')
        if res is not None:
            deltaDE = str(res[1][0])

        res = self._iopm.results.get('xm')
        if res is not None:
            betaX = res[1][0]
            gammaM = res[1][1]

        self._rBackgroundLabel.setBackgroundEngine(background)
        self._rAlphaBt.setText(f'Alpha BT: {alphaBT}')
        self._rDeltaDe.setText(f'Delta DE: {deltaDE}')
        self._rBetaXLabel.setText(f'Beta X: {betaX}')
        self._rGammaMLabel.setText(f'Gamma M: {gammaM}')
