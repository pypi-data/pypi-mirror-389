from quanti_fret.apps.gui.stages.background.mode import BackgroundModeBox
from quanti_fret.apps.gui.stages.background.floating import (
    FloatingBackgroundBox
)
from quanti_fret.apps.gui.io_gui_manager import IOGuiManager
from quanti_fret.apps.gui.stages.stage_calculation import StageCalculatorWidget

from quanti_fret.algo import BackgroundMode

from qtpy.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QLayout,
    QVBoxLayout,
)


class StageBackgroundWidget(StageCalculatorWidget):
    """ Handle the stage that computes the background for the calibration phase
    """

    def __init__(self, *args, **kwargs) -> None:
        """Constructor

        Args:
            phase (str): Phase of the widget
        """
        # Must be instanciated before super init
        self._seriesCheckBox: dict[str, QCheckBox] = {}
        self._phase = 'calibration'

        super().__init__('background', IOGuiManager().cali, *args, **kwargs)

        # Must be done after super init to avoid useless signal emission
        for name in self._seriesCheckBox:
            self._seriesCheckBox[name].stateChanged.connect(
                lambda val, name=name: self._select_series(name, val)
            )

    def _buildSettings(self) -> QLayout:
        """ Create the settings QLayout that will be added to the top of the
        widget layout.

        Returns:
            QLayout: Settings layout created
        """
        settingsLayout = QVBoxLayout()

        # Floating Box
        floatingBox = FloatingBackgroundBox(self._phase, self)
        settingsLayout.addWidget(floatingBox)

        # Mode Box
        self._modeBox = BackgroundModeBox(self._phase, self)
        settingsLayout.addWidget(self._modeBox)

        # Series Button
        self._seriesBox = QGroupBox('Series', self)
        settingsLayout.addWidget(self._seriesBox)
        seriesLayout = QVBoxLayout()
        self._seriesBox.setLayout(seriesLayout)
        for name in self._iopm.series._series:
            self._seriesCheckBox[name] = QCheckBox(name, self._seriesBox)
            seriesLayout.addWidget(self._seriesCheckBox[name])

        return settingsLayout

    def _buildResults(self) -> QLayout:
        """ Create the results QLayout that will be added to the bottom of
        the widget layout.

        Returns:
            QLayout: Results layout created
        """
        # Result layout
        resultLayout = QVBoxLayout()

        # Result settings box
        resultSettingsBox = QGroupBox('Settings')
        resultLayout.addWidget(resultSettingsBox)
        resultSettingsLayout = QVBoxLayout()
        resultSettingsBox.setLayout(resultSettingsLayout)
        self._seriesResultLabel = QLabel()
        self._seqCountResultLabel = QLabel()
        self._modeResultLabel = QLabel()
        self._extraInfoResultLabel = QLabel()
        resultSettingsLayout.addWidget(self._seriesResultLabel)
        resultSettingsLayout.addWidget(self._seqCountResultLabel)
        resultSettingsLayout.addWidget(self._modeResultLabel)
        resultSettingsLayout.addWidget(self._extraInfoResultLabel)

        # Result backgrounds labels
        resultBckgBox = QGroupBox('Backgrounds')
        resultLayout.addWidget(resultBckgBox)
        resultBckgLayout = QVBoxLayout()
        resultBckgBox.setLayout(resultBckgLayout)
        self._ddResultLabel = QLabel()
        self._daResultLabel = QLabel()
        self._aaResultLabel = QLabel()
        self._disabledResultLabel = QLabel('Disabled')
        resultBckgLayout.addWidget(self._ddResultLabel)
        resultBckgLayout.addWidget(self._daResultLabel)
        resultBckgLayout.addWidget(self._aaResultLabel)
        resultBckgLayout.addWidget(self._disabledResultLabel)

        return resultLayout

    def _blockAllSignals(self, val: bool) -> None:
        """ Call the `blockSignal` method of all widget whose signal is
        connected to a slot.

        The purpose of this method is to prevent slots to call config save
        while being updated by it.

        Args:
            val (bool): The value to pass to the `blockSignal` method
        """
        for name in self._seriesCheckBox:
            self._seriesCheckBox[name].blockSignals(val)

    def _updateSettings(self) -> None:
        """ Update the number of sequences for each series
        """
        # Series
        for name in self._seriesCheckBox:
            checked = self._iopm.config.get('Background', f'use_{name}')
            self._seriesCheckBox[name].setChecked(checked)
            nb_elements = self._iopm.series.get(name).size()
            self._seriesCheckBox[name].setText(f'{name} ({nb_elements})')

        # Disabled what is needed
        floating = self._iopm.config.get('Background', 'floating')
        if floating:
            self._seriesBox.setEnabled(False)
        else:
            self._seriesBox.setEnabled(True)

    def _loadResults(self) -> bool:
        """ Load the results, update the results widget. and inform if results
        were found.

        Returns:
            bool: True if results were loaded, False otherwise
        """
        # Retrieve results
        results = self._iopm.results.get('background')
        if results is None:
            return False
        (series, nbSequences, engine), (background,) = results

        # Update settings results
        self._seriesResultLabel.setText(f'Series: "{series}"')
        self._seqCountResultLabel.setText(
            f'Number of Sequences: {nbSequences}')
        self._modeResultLabel.setText(f'Mode: {engine.mode}')
        if engine.mode == BackgroundMode.PERCENTILE:
            self._extraInfoResultLabel.setText(
                f'Percentile: {engine._percentile}'
            )
            self._extraInfoResultLabel.show()
        elif engine.mode == BackgroundMode.FIXED:
            self._extraInfoResultLabel.setText(
                f'Fixed Value: {engine.background}'
            )
            self._extraInfoResultLabel.show()
        else:
            self._extraInfoResultLabel.hide()

        # Update background results
        if background.mode == BackgroundMode.DISABLED:
            self._ddResultLabel.hide()
            self._daResultLabel.hide()
            self._aaResultLabel.hide()
            self._disabledResultLabel.show()
        else:
            self._ddResultLabel.show()
            self._daResultLabel.show()
            self._aaResultLabel.show()
            self._disabledResultLabel.hide()
            self._ddResultLabel.setText(f'DD: {background.background[0]}')
            self._daResultLabel.setText(f'DA: {background.background[1]}')
            self._aaResultLabel.setText(f'AA: {background.background[2]}')

        return True

    def _select_series(self, name: str, _: int) -> None:
        """ Select or unselect the series for background computation

        Args:
            name (str): name of the series to set
        """
        checked = self._seriesCheckBox[name].isChecked()
        self._iopm.config.set('Background', f'use_{name}', checked)
