from quanti_fret.apps.gui.io_gui_manager import IOGuiManager
from quanti_fret.apps.gui.stages.stage_calculation import StageCalculatorWidget
from quanti_fret.apps.gui.utils import BackgroundEngineLabel, PercentileSpinBox

from qtpy.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QSpinBox,
    QLabel,
    QLayout,
    QVBoxLayout,
)


class StageXmWidget(StageCalculatorWidget):
    """ Handle the stage that computes the BT or DE stages.
    """

    def __init__(self, *args, **kwargs) -> None:
        """ Constructor
        """
        # Mandatory in order to prevent saving config even if value didn't
        # change
        self._sPercentileLowValue = 0.0
        self._sPercentileHighValue = 0.0
        self._sAnalysisSamplingValue = 0

        super().__init__('xm', IOGuiManager().cali, *args, **kwargs)

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

        # Alpha BT
        self._sAlphaBtLabel = QLabel()
        settingsLayout.addWidget(self._sAlphaBtLabel)

        # Delta DE
        self._sDeltaDeLabel = QLabel()
        settingsLayout.addWidget(self._sDeltaDeLabel)

        # Background
        self._sBckgLabel = BackgroundEngineLabel(self._sDeltaDeLabel)
        settingsLayout.addWidget(self._sBckgLabel)

        # percentile
        percentileBox = QGroupBox('Percentile Range')
        settingsLayout.addWidget(percentileBox)
        percentileLayout = QHBoxLayout()
        percentileBox.setLayout(percentileLayout)
        percentileLowLayout = QHBoxLayout()
        percentileLayout.addLayout(percentileLowLayout)
        sPercentileLowlabel = QLabel('Low:')
        self._sPercentileLowBox = PercentileSpinBox()
        percentileLowLayout.addWidget(sPercentileLowlabel)
        percentileLowLayout.addWidget(self._sPercentileLowBox)
        percentileHighLayout = QHBoxLayout()
        percentileLayout.addLayout(percentileHighLayout)
        sPercentileHighlabel = QLabel('High:')
        self._sPercentileHighBox = PercentileSpinBox()
        percentileHighLayout.addWidget(sPercentileHighlabel)
        percentileHighLayout.addWidget(self._sPercentileHighBox)
        self._sPercentileLowBox.editingFinished.connect(self._setPercentileLow)
        self._sPercentileHighBox.editingFinished.connect(
            self._setPercentileHigh)

        # analysis
        analysisBox = QGroupBox('Analysis Details')
        settingsLayout.addWidget(analysisBox)
        analysisLayout = QHBoxLayout()
        analysisBox.setLayout(analysisLayout)
        self._sAnalysisDetailsCheckBox = QCheckBox('Save Details')
        self._sAnalysisDetailsCheckBox.stateChanged.connect(
            self._setAnalysisDetails)
        analysisLayout.addWidget(self._sAnalysisDetailsCheckBox)
        samplingLayout = QHBoxLayout()
        analysisLayout.addLayout(samplingLayout)
        samplingLabel = QLabel('Sampling')
        samplingLayout.addWidget(samplingLabel)
        self._sAnalysisSamplingBox = QSpinBox()
        self._sAnalysisSamplingBox.setRange(1, 10000)
        self._sAnalysisSamplingBox.setSingleStep(1)
        samplingLayout.addWidget(self._sAnalysisSamplingBox)
        self._sAnalysisSamplingBox.editingFinished.connect(self._setSampling)

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
        self._rAlphaBt = QLabel()
        self._rDeltaDe = QLabel()
        self._rBackgroundLabel = BackgroundEngineLabel()
        self._rPercentileRangeLabel = QLabel()
        self._rAnalysisDetailsLabel = QLabel()
        self._rSamplingLabel = QLabel()
        resultSettingsLayout.addWidget(self._rSeriesLabel)
        resultSettingsLayout.addWidget(self._rNbSeqLabel)
        resultSettingsLayout.addWidget(self._rAlphaBt)
        resultSettingsLayout.addWidget(self._rDeltaDe)
        resultSettingsLayout.addWidget(self._rBackgroundLabel)
        resultSettingsLayout.addWidget(self._rPercentileRangeLabel)
        resultSettingsLayout.addWidget(self._rAnalysisDetailsLabel)
        resultSettingsLayout.addWidget(self._rSamplingLabel)

        # Result backgrounds labels
        resultXmBox = QGroupBox('XM')
        resultLayout.addWidget(resultXmBox)
        resultXmLayout = QVBoxLayout()
        resultXmBox.setLayout(resultXmLayout)
        self._rBetaXLabel = QLabel()
        self._rGammaMLabel = QLabel()
        self._rRedChi2Label = QLabel()
        self._rR2Label = QLabel()
        self._rQLabel = QLabel()
        resultXmLayout.addWidget(self._rBetaXLabel)
        resultXmLayout.addWidget(self._rGammaMLabel)
        resultXmLayout.addWidget(self._rRedChi2Label)
        resultXmLayout.addWidget(self._rR2Label)
        resultXmLayout.addWidget(self._rQLabel)

        return resultLayout

    def _blockAllSignals(self, val: bool) -> None:
        """ Call the `blockSignal` method of all widget whose signal is
        connected to a slot.

        The purpose of this method is to prevent slots to call config save
        while being updated by it.

        Args:
            val (bool): The value to pass to the `blockSignal` method
        """
        self._sPercentileLowBox.blockSignals(val)
        self._sPercentileHighBox.blockSignals(val)
        self._sAnalysisDetailsCheckBox.blockSignals(val)
        self._sAnalysisSamplingBox.blockSignals(val)

    def _updateSettings(self) -> None:
        """ Update the number of sequences for each series
        """
        params = self._iopm.params.get('xm', True)
        _, series, alphaBt, deltaDe, background, percentile, \
            analysis_details, sampling = params

        self._sPercentileLowValue = percentile[0]
        self._sPercentileHighValue = percentile[1]
        self._sAnalysisSamplingValue = sampling

        self._sSeriesLabel.setText(f'Standards: {series.size()}')
        self._sAlphaBtLabel.setText(f'Alpha BT: {self._str_val(alphaBt)}')
        self._sDeltaDeLabel.setText(f'Delta DE: {self._str_val(deltaDe)}')
        self._sBckgLabel.setBackgroundEngine(background)
        self._sPercentileLowBox.setValue(percentile[0])
        self._sPercentileHighBox.setValue(percentile[1])
        self._sAnalysisDetailsCheckBox.setChecked(analysis_details)
        self._sAnalysisSamplingBox.setValue(sampling)

    def _loadResults(self) -> bool:
        """ Load the results, update the results widget. and inform if results
        were found.

        Returns:
            bool: True if results were loaded, False otherwise
        """
        # Retrieve results
        results = self._iopm.results.get('xm')
        if results is None:
            return False
        series, nb_seq, alphaBt, deltaDe, background, percentile, \
            analysis_details, sampling = results[0]
        betaX, gammaM, redChi2, r2, q = results[1]

        # Update settings
        self._rSeriesLabel.setText(f'Series Name: {series}')
        self._rNbSeqLabel.setText(f'Number of sequences used: {nb_seq}')
        self._rAlphaBt.setText(f'Alpha BT: {alphaBt}')
        self._rDeltaDe.setText(f'Delta DE: {deltaDe}')
        self._rBackgroundLabel.setBackgroundEngine(background)
        self._rPercentileRangeLabel.setText(f'Percentile Range: {percentile}')
        self._rAnalysisDetailsLabel.setText(
            f'Save Analysis Details: {analysis_details}')
        self._rSamplingLabel.setText(
            f'Sampling for Analysis: {sampling}')

        # Update results
        self._rBetaXLabel.setText(f'BetaX: {betaX}')
        self._rGammaMLabel.setText(f'GammaM: {gammaM}')
        self._rRedChi2Label.setText(f'RedChi2: {redChi2}')
        self._rR2Label.setText(f'R2: {r2}')
        self._rQLabel.setText(f'Q: {q}')

        return True

    def _setPercentileLow(self) -> None:
        """ Set the percentile value in the config

        Make sure it doesn't go above percentile high.
        """
        lowPercentile = self._sPercentileLowBox.value()
        highPercentile = self._sPercentileHighBox.value()
        if lowPercentile > 100:
            lowPercentile = 100
        elif lowPercentile < 0:
            lowPercentile = 0
        elif lowPercentile > highPercentile:
            lowPercentile = highPercentile
        self._sPercentileLowBox.setValue(lowPercentile)

        # Prevent useless savings
        if lowPercentile != self._sPercentileLowValue:
            self._sPercentileLowValue = lowPercentile
            self._iopm.config.set('XM', 'discard_low_percentile',
                                  lowPercentile)

    def _setPercentileHigh(self) -> None:
        """ Set the percentile value in the config

        Make sure it doesn't go above percentile high.
        """
        highPercentile = self._sPercentileHighBox.value()
        lowPercentile = self._sPercentileLowBox.value()
        if highPercentile > 100:
            highPercentile = 100
        elif highPercentile < 0:
            highPercentile = 0
        elif highPercentile < lowPercentile:
            highPercentile = lowPercentile
        self._sPercentileHighBox.setValue(highPercentile)

        # Prevent useless savings
        if highPercentile != self._sPercentileHighValue:
            self._sPercentileHighValue = highPercentile
            self._iopm.config.set('XM', 'discard_high_percentile',
                                  highPercentile)

    def _setAnalysisDetails(self, _: bool) -> None:
        """Set the analysis details value in the config

        Args:
            _ (bool): Not used, we get the checked directly from widget
        """
        checked = self._sAnalysisDetailsCheckBox.isChecked()
        self._iopm.config.set('XM', 'save_analysis_details', checked)

    def _setSampling(self) -> None:
        """ Set the analysis sampling value in the config
        """
        sampling = self._sAnalysisSamplingBox.value()
        if sampling != self._sAnalysisSamplingValue:
            self._sAnalysisSamplingValue = sampling
            self._iopm.config.set('XM', 'analysis_sampling', sampling)
