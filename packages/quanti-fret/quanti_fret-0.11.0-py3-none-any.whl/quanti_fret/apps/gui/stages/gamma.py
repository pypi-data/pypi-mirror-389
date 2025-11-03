from quanti_fret.apps.gui.io_gui_manager import IOGuiManager
from quanti_fret.apps.gui.stages.stage_calculation import StageCalculatorWidget
from quanti_fret.apps.gui.utils import BackgroundEngineLabel, PercentileSpinBox
from quanti_fret.core import QtfException

from qtpy.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QVBoxLayout,
)


class StageGammaWidget(StageCalculatorWidget):
    """ Handle the stage that computes the BT or DE stages.
    """

    def __init__(self, mode: str, *args, **kwargs) -> None:
        """ Constructor

        Args:
            mode (str): Weather this widget is in BT or DE mode
        """
        self._mode = mode
        if mode == 'BT':
            self._gamma_type = 'bt'
            self._series_name = 'donors'
            self._gamma_channel = 'DD'
            self._gamma_background_index = 0
            self._gamma_name = 'Alpha BT'
        elif mode == 'DE':
            self._gamma_type = 'de'
            self._series_name = 'acceptors'
            self._gamma_channel = 'AA'
            self._gamma_background_index = 2
            self._gamma_name = 'Delta DE'
        else:
            QtfException(
                'Invalid StageGammaWidget type. Must be in ["BT", "DE"]'
            )

        super().__init__(self._gamma_type, IOGuiManager().cali, *args,
                         **kwargs)

    def _buildSettings(self) -> QLayout:
        """ Create the settings QLayout that will be added to the top of the
        widget layout.

        Returns:
            QLayout: Settings layout created
        """
        settingsLayout = QVBoxLayout()

        # Series
        self._sSeriesLabel = QLabel()
        settingsLayout.addWidget(self._sSeriesLabel)

        # Background
        self._backgroundLabel = BackgroundEngineLabel(self)
        settingsLayout.addWidget(self._backgroundLabel)

        # percentile
        percentileLayout = QHBoxLayout()
        settingsLayout.addLayout(percentileLayout)
        sPercentilelabel = QLabel('Discard Low Percentile:')
        percentileLayout.addWidget(sPercentilelabel)
        self._sPercentileBox = PercentileSpinBox()
        self._sPercentileBox.valueChanged.connect(self._set_percentile)
        percentileLayout.addWidget(self._sPercentileBox)

        # Details
        self._sPlotDetailsBox = QCheckBox('Plot Sequences Details')
        settingsLayout.addWidget(self._sPlotDetailsBox)
        self._sPlotDetailsBox.stateChanged.connect(self._set_plot_details)

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
        self._rSeriesLabel = QLabel()
        self._rNbSeqLabel = QLabel()
        self._rBckgLabel = BackgroundEngineLabel()
        self._rPercentileLabel = QLabel()
        self._rPlotDetailsLabel = QLabel()
        resultSettingsLayout.addWidget(self._rSeriesLabel)
        resultSettingsLayout.addWidget(self._rNbSeqLabel)
        resultSettingsLayout.addWidget(self._rBckgLabel)
        resultSettingsLayout.addWidget(self._rPercentileLabel)
        resultSettingsLayout.addWidget(self._rPlotDetailsLabel)

        # Result backgrounds labels
        resultBckgBox = QGroupBox(f'{self._gamma_type.upper()}')
        resultLayout.addWidget(resultBckgBox)
        resultGamma = QVBoxLayout()
        resultBckgBox.setLayout(resultGamma)
        self._rGammaLabel = QLabel()
        self._rStdLabel = QLabel()
        self._rNbPixLabel = QLabel()
        resultGamma.addWidget(self._rGammaLabel)
        resultGamma.addWidget(self._rStdLabel)
        resultGamma.addWidget(self._rNbPixLabel)

        return resultLayout

    def _blockAllSignals(self, val: bool) -> None:
        """ Call the `blockSignal` method of all widget whose signal is
        connected to a slot.

        The purpose of this method is to prevent slots to call config save
        while being updated by it.

        Args:
            val (bool): The value to pass to the `blockSignal` method
        """
        self._sPercentileBox.blockSignals(val)
        self._sPlotDetailsBox.blockSignals(val)

    def _updateSettings(self) -> None:
        """ Update the number of sequences for each series
        """
        # Retrieve params
        params = self._iopm.params.get(self._gamma_type, True)
        _, series, background, percentile, plotDetails = params

        # Series
        text = f'{self._series_name.capitalize()}: {series.size()}'
        self._sSeriesLabel.setText(text)

        # Background
        self._backgroundLabel.setBackgroundEngine(background)

        # percentile
        percentile = self._iopm.config.get(self._mode,
                                           'discard_low_percentile')
        self._sPercentileBox.setValue(percentile)

        # Plot details
        plotDetails = self._iopm.config.get(self._mode,
                                            'plot_sequence_details')
        self._sPlotDetailsBox.setChecked(plotDetails)

    def _loadResults(self) -> bool:
        """ Load the results, update the results widget. and inform if results
        were found.

        Returns:
            bool: True if results were loaded, False otherwise
        """
        # Retrieve results
        results = self._iopm.results.get(f'{self._gamma_type}')
        if results is None:
            return False
        series, nb_seq, background, percentile, plotDetails = \
            results[0]
        gamma, std_dev, nb_pix = results[1]

        # Update settings
        self._rSeriesLabel.setText(f'Series Name: {series}')
        self._rNbSeqLabel.setText(f' Number of sequences used: {nb_seq}')
        self._rBckgLabel.setBackgroundEngine(background)
        self._rPercentileLabel.setText(f'Discard Low Percentile: {percentile}')
        self._rPlotDetailsLabel.setText(
            f'Plot sequence Details: {plotDetails}'
        )

        # Update results
        self._rGammaLabel.setText(f'{self._gamma_name}: {gamma}')
        self._rStdLabel.setText(f'Standard Deviation: {std_dev}')
        self._rNbPixLabel.setText(f'Number of Pixels: {nb_pix}')

        return True

    def _set_percentile(self, val: float) -> None:
        """ Set the percentile value in the config

        Args:
            val (float): Value to set
        """
        self._iopm.config.set(self._mode, 'discard_low_percentile', val)

    def _set_plot_details(self, _: bool) -> None:
        """Set the plot sequence details value in the config

        Args:
            _ (bool): Not used, we get the checked directly from widget
        """
        checked = self._sPlotDetailsBox.isChecked()
        self._iopm.config.set(self._mode, 'plot_sequence_details', checked)
