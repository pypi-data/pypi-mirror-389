from quanti_fret.apps.gui.runner import CalculatorRunner
from quanti_fret.apps.gui.io_gui_manager import IOPhaseGuiManager
from quanti_fret.apps.gui.utils import (
    LoadingAnimationLayout, LoadingProgressLayout
)

from quanti_fret.core import QtfException

import abc
from typing import Any

from qtpy.QtCore import Qt, QObject
from qtpy.QtWidgets import (
    QGroupBox,
    QLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class QABCMeta(abc.ABCMeta, type(QObject)):  # type: ignore
    """ Metaclass to allow a QObject to have an abc.ABCMeta metaclass
    """
    pass


class StageCalculatorWidget(QWidget, metaclass=QABCMeta):
    """ Generic class to handle a stage that perform a computation.

    This widget is composed of 3 different sections:
        * One Box for the settings
        * One Button to trigger the run
        * One Box that displays the results

    The run is handled by the singleton `CalculatorRunner` that allows one
    access at the time to it's run method.

    To create a child class, you need to:
        * Override `_buildSettings` to create the settings box
        * Override `_buildResults` to create the results box
        * Override `_updateSettings` to update the settings widgets
        * Override `_loadResults` to update the results widgets, and inform if
            the results should be displayed or not.
    """

    def __init__(
        self, stage: str, iopm: IOPhaseGuiManager, *args,
        showProgress: bool = False, **kwargs
    ) -> None:
        """ Constructor

        Args:
            stage (str): Name of the stage. Used to retrieve stage parameters
            iopm (IOPhaseGuiManager): IOPhaseGuiManager to use
            showProgress (bool): Weather or not to connect to the progress
                signal of the runner to display progress
        """
        super().__init__(*args, **kwargs)
        self._iopm = iopm
        self._stage = stage
        self._showProgress = showProgress

        # Setup the calculator runner
        self._runner = CalculatorRunner()
        self._runner.finished.connect(self._stopCompute)
        self._runner.runAvailable.connect(self._setCalculatorAvailable)
        self._runner.runDisabled.connect(self._setCalculatorDisabled)
        self._calculatorAvailable = True
        self._buttonLoading = False

        # Build the Gui
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        mainLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        settingsLayout = self._buildSettings()
        mainLayout.addLayout(settingsLayout)
        self._buildRunButton()
        resultsLayout = self._buildResults()
        self._resultsBox = QGroupBox('Results', self)
        self._resultsBox.setLayout(resultsLayout)
        mainLayout.addWidget(self._resultsBox)

        # Populate settings and load previous results
        self._safeUpdateSettings()
        self._updateRunButton()
        self._updateResults()
        self._iopm.stateChanged.connect(self._safeUpdateSettings)
        self._iopm.stateChanged.connect(self._updateRunButton)
        self._iopm.stateChanged.connect(self._updateResults)

    @abc.abstractmethod
    def _buildSettings(self) -> QLayout:
        """ Create the settings QLayout that will be added to the top of the
        widget layout.

        Returns:
            QLayout: Settings layout created
        """
        pass

    def _buildRunButton(self) -> None:
        """ Build the button that trigger the run of the computation
        """
        # Run Button
        self._runButton = QPushButton()
        self._runButton.clicked.connect(self._startCompute)
        self.layout().addWidget(self._runButton)  # type: ignore

        self._loadingLayout: LoadingAnimationLayout | LoadingProgressLayout
        if not self._showProgress:
            # LoadingAnimationLayout
            self._loadingLayout = LoadingAnimationLayout()
            self._runButton.setLayout(self._loadingLayout)
        else:
            # LoadingProgressLayout
            self._loadingLayout = LoadingProgressLayout()
            self._runButton.setLayout(self._loadingLayout)
            self._runner.progress.connect(self._loadingLayout.setProgress)

    @abc.abstractmethod
    def _buildResults(self) -> QLayout:
        """ Create the results QLayout that will be added to the bottom of
        the widget layout.

        Returns:
            QLayout: Results layout created
        """
        pass

    def _safeUpdateSettings(self) -> None:
        """ Update the settings widgets while preventing the signals to be
        raised by them for value changed.

        Will be called on IOGuiManager `stateChanged` Signal
        """
        self._blockAllSignals(True)
        self._updateSettings()
        self._blockAllSignals(False)

    def _blockAllSignals(self, val: bool) -> None:
        """ Call the `blockSignal` method of all widget whose signal is
        connected to a slot.

        The purpose of this method is to prevent slots to call config save
        while being updated by it.

        This is expected to be override.

        Args:
            val (bool): The value to pass to the `blockSignal` method
        """
        pass

    @abc.abstractmethod
    def _updateSettings(self) -> None:
        """ Update the settings widgets.

        Will be called on IOGuiManager `stateChanged` Signal
        """
        pass

    def _updateRunButton(self) -> None:
        """ Update the Run button widget.
        """
        if not self._buttonLoading:
            try:
                series = self._iopm.params.get(self._stage)[1]
                text = f'Run on {series.size()} sequences'
                enable = True
            except QtfException as e:
                text = f'Impossible to run: {e}'
                enable = False
            self._runButton.setEnabled(enable)
            self._runButton.setText(text)

            if not self._calculatorAvailable:
                self._runButton.setEnabled(False)

    def _updateResults(self) -> None:
        """ Update the results widgets
        """
        if self._loadResults():
            self._resultsBox.show()
        else:
            self._resultsBox.hide()

    @abc.abstractmethod
    def _loadResults(self) -> bool:
        """ Load the results, update the results widget. and inform if results
        were found.

        Returns:
            bool: True if results were loaded, False otherwise
        """
        pass

    def _startCompute(self) -> None:
        """ Start the worker that will perdorm the computation, disable the
        button and starts the loading animation.
        """
        # Disable the button
        self._buttonLoading = True
        self._runButton.setEnabled(False)

        # Hide previous results
        self._resultsBox.hide()

        # Start loading animation
        self._runButton.setText("")
        self._loadingLayout.start()

        # Run computation
        self._runner.run(self._stage)

    def _stopCompute(self, stage: str) -> None:
        """ If the stage match the one of the widget, stops the loading
        animation, and restores the button.

        Args:
            stage (str): Stage that finished the run
        """
        if stage == self._stage:
            # Stop loading animation
            self._loadingLayout.stop()

            # Restore button
            self._buttonLoading = False
            self._updateRunButton()

    def _setCalculatorAvailable(self) -> None:
        """ Set the calculator to available state
        """
        self._calculatorAvailable = True
        self._updateRunButton()

    def _setCalculatorDisabled(self) -> None:
        """ Set the calculator to disabled state
        """
        self._calculatorAvailable = False
        self._updateRunButton()

    def _str_val(self, value: Any) -> str:
        """ Return the str representation of a value or '' if None
        """
        return str(value) if value is not None else ' -'
