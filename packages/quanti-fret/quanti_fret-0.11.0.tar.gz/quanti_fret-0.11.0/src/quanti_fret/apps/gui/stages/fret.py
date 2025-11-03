from quanti_fret.apps.gui.io_gui_manager import IOGuiManager
from quanti_fret.apps.gui.stages.stage_calculation import StageCalculatorWidget
from quanti_fret.apps.gui.utils import BackgroundEngineLabel

from qtpy.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QSpinBox,
    QVBoxLayout,
)


class StageFretWidget(StageCalculatorWidget):
    """ Handle the stage that computes the BT or DE stages.
    """

    def __init__(self, *args, **kwargs) -> None:
        """ Constructor
        """
        # Mandatory in order to prevent saving config even if value didn't
        # change
        self._filterSettingsValues = {
            'sigma_s': 0.0,
            'target_s': 0.0,
            'sigma_gauss': 0.0,
            'weights_threshold': 0.0,
        }
        self._sAnalysisSamplingValue = 0

        IOGuiManager().cali.stateChanged.connect(self._updateSettings)

        super().__init__('fret', IOGuiManager().fret, *args, showProgress=True,
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

        # Alpha BT
        self._sAlphaBtLabel = QLabel()
        settingsLayout.addWidget(self._sAlphaBtLabel)

        # Delta DE
        self._sDeltaDeLabel = QLabel()
        settingsLayout.addWidget(self._sDeltaDeLabel)

        # BetaX
        self._sBetaXLabel = QLabel()
        settingsLayout.addWidget(self._sBetaXLabel)

        # GammaM
        self._sGammaMLabel = QLabel()
        settingsLayout.addWidget(self._sGammaMLabel)

        # Background
        self._sBckgLabel = BackgroundEngineLabel()
        settingsLayout.addWidget(self._sBckgLabel)

        # Gaussian filter settings
        gFilterBox = QGroupBox('Gaussian Filter Settings')
        settingsLayout.addWidget(gFilterBox)
        gFilterLayout = QGridLayout()
        gFilterBox.setLayout(gFilterLayout)
        # SigmaS
        sigmaSLayout, self._sSigmaSBox = self._buildGaussianFilterSettings(
            'Sigma S', 'sigma_s'
        )
        gFilterLayout.addLayout(sigmaSLayout, 0, 0)
        # Target S
        targetSLayout, self._sTargetSBox = self._buildGaussianFilterSettings(
            'Target S', 'target_s'
        )
        gFilterLayout.addLayout(targetSLayout, 0, 1)
        # Sigma Gauss
        sigmaGaussLayout, self._sSigmaGaussBox = \
            self._buildGaussianFilterSettings('Sigma Gauss', 'sigma_gauss',
                                              step=1.)
        gFilterLayout.addLayout(sigmaGaussLayout, 1, 0)
        # Weights threshold
        weightsTLayout, self._sWeightsTBox = self._buildGaussianFilterSettings(
            'Weights Threshold', 'weights_threshold'
        )
        gFilterLayout.addLayout(weightsTLayout, 1, 1)

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

    def _buildGaussianFilterSettings(
        self, title: str, key: str, step: float = 0.1
    ) -> tuple[QHBoxLayout, QDoubleSpinBox]:
        """ Build the layout and doublespin box for a single Gaussian Filter
        settings.

        Args:
            title (str): Title to display on the label widget
            key (str): key to save the value in the config
            step (float): Value to add when using the widget + and - arrows

        Returns:
            tuple[QHBoxLayout, QDoubleSpinBox]: the layout and the box created
        """
        layout = QHBoxLayout()
        label = QLabel(title)
        spinBox = QDoubleSpinBox()
        spinBox.setSingleStep(step)
        layout.addWidget(label)
        layout.addWidget(spinBox)
        spinBox.editingFinished.connect(
            lambda: self._setGammaFilterDetails(key, spinBox)
        )

        return layout, spinBox

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
        self._rBetaXLabel = QLabel()
        self._rGammaMLabel = QLabel()
        self._rBackgroundLabel = BackgroundEngineLabel()
        self._rSigmaSLabel = QLabel()
        self._rTargetSLabel = QLabel()
        self._rSigmaGaussLabel = QLabel()
        self._rWeightsTLabel = QLabel()
        self._rAnalysisDetailsLabel = QLabel()
        self._rSamplingLabel = QLabel()
        resultSettingsLayout.addWidget(self._rSeriesLabel)
        resultSettingsLayout.addWidget(self._rNbSeqLabel)
        resultSettingsLayout.addWidget(self._rAlphaBt)
        resultSettingsLayout.addWidget(self._rDeltaDe)
        resultSettingsLayout.addWidget(self._rBetaXLabel)
        resultSettingsLayout.addWidget(self._rGammaMLabel)
        resultSettingsLayout.addWidget(self._rBackgroundLabel)
        resultSettingsLayout.addWidget(self._rSigmaSLabel)
        resultSettingsLayout.addWidget(self._rTargetSLabel)
        resultSettingsLayout.addWidget(self._rSigmaGaussLabel)
        resultSettingsLayout.addWidget(self._rWeightsTLabel)
        resultSettingsLayout.addWidget(self._rAnalysisDetailsLabel)
        resultSettingsLayout.addWidget(self._rSamplingLabel)

        return resultLayout

    def _blockAllSignals(self, val: bool) -> None:
        """ Call the `blockSignal` method of all widget whose signal is
        connected to a slot.

        The purpose of this method is to prevent slots to call config save
        while being updated by it.

        Args:
            val (bool): The value to pass to the `blockSignal` method
        """
        self._sSigmaSBox.blockSignals(val)
        self._sTargetSBox.blockSignals(val)
        self._sSigmaGaussBox.blockSignals(val)
        self._sWeightsTBox.blockSignals(val)
        self._sAnalysisDetailsCheckBox.blockSignals(val)
        self._sAnalysisSamplingBox.blockSignals(val)

    def _updateSettings(self) -> None:
        """ Update the number of sequences for each series
        """
        params = self._iopm.params.get('fret', True)
        _, series, alphaBt, deltaDe, betaX, GammaM, background, SigmaS,  \
            targetS, sigmaGauss, weightsThreshold,  analysisDetails,  \
            analysisSampling = params

        self._filterSettingsValues = {
            'sigma_s': SigmaS,
            'target_s': targetS,
            'sigma_gauss': sigmaGauss,
            'weights_threshold': weightsThreshold,
        }
        self._sAnalysisSamplingValue = analysisSampling

        self._sSeriesLabel.setText(f'Experiments: {series.size()}')
        self._sAlphaBtLabel.setText(f'Alpha BT: {self._str_val(alphaBt)}')
        self._sDeltaDeLabel.setText(f'Delta DE: {self._str_val(deltaDe)}')
        self._sBetaXLabel.setText(f'BetaX: {self._str_val(betaX)}')
        self._sGammaMLabel.setText(f'GammaM: {self._str_val(GammaM)}')
        self._sBckgLabel.setBackgroundEngine(background)
        self._sSigmaSBox.setValue(SigmaS)
        self._sTargetSBox.setValue(targetS)
        self._sSigmaGaussBox.setValue(sigmaGauss)
        self._sWeightsTBox.setValue(weightsThreshold)
        self._sAnalysisDetailsCheckBox.setChecked(analysisDetails)
        self._sAnalysisSamplingBox.setValue(analysisSampling)

    def _loadResults(self) -> bool:
        """ Load the results, update the results widget. and inform if results
        were found.

        Returns:
            bool: True if results were loaded, False otherwise
        """
        # Retrieve results
        results = self._iopm.results.get('fret')
        if results is None:
            return False
        series, nb_seq, alphaBt, deltaDe, betaX, gammaM, background, sigmaS,  \
            targetS, sigmaGauss, weightsThreshold,  analysisDetails,  \
            analysisSampling = results[0]

        # Update settings
        self._rSeriesLabel.setText(f'Series Name: {series}')
        self._rNbSeqLabel.setText(f'Number of sequences used: {nb_seq}')
        self._rAlphaBt.setText(f'Alpha BT: {alphaBt}')
        self._rDeltaDe.setText(f'Delta DE: {deltaDe}')
        self._rBetaXLabel.setText(f'BetaX: {betaX}')
        self._rGammaMLabel.setText(f'GammaM: {gammaM}')
        self._rBackgroundLabel.setBackgroundEngine(background)
        self._rSigmaSLabel.setText(f'Sigma S: {sigmaS}')
        self._rTargetSLabel.setText(f'Target S: {targetS}')
        self._rSigmaGaussLabel.setText(f'Sigma Gauss: {sigmaGauss}')
        self._rWeightsTLabel.setText(f'Weights Threshold: {weightsThreshold}')
        self._rAnalysisDetailsLabel.setText(
            f'Save Analysis Details: {analysisDetails}')
        self._rSamplingLabel.setText(
            f'Sampling for Analysis: {analysisSampling}')

        return True

    def _setGammaFilterDetails(self, key: str, widget: QDoubleSpinBox) -> None:
        """Set the gamma filter value in the config

        Args:
            key (str): Key in the config to set
            widget (QDoubleSpinBox): widget to get the value from
        """
        val = widget.value()
        if self._filterSettingsValues[key] != val:
            self._filterSettingsValues[key] = val
            self._iopm.config.set('Fret', key, val)

    def _setAnalysisDetails(self, _: bool) -> None:
        """Set the analysis details value in the config

        Args:
            _ (bool): Not used, we get the checked directly from widget
        """
        checked = self._sAnalysisDetailsCheckBox.isChecked()
        self._iopm.config.set('Fret', 'save_analysis_details', checked)

    def _setSampling(self) -> None:
        """ Set the analysis sampling value in the config
        """
        sampling = self._sAnalysisSamplingBox.value()
        if sampling != self._sAnalysisSamplingValue:
            self._sAnalysisSamplingValue = sampling
            self._iopm.config.set('Fret', 'analysis_sampling', sampling)
