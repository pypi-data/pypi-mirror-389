from quanti_fret.apps.gui.phases import CalibrationWidget
from quanti_fret.apps.gui.phases import FretWidget

from qtpy.QtWidgets import (
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class QtfMainWidget(QWidget):
    """ Top level widget for QuanTI-FRET Gui application.

    Can be called inside a window, or passed to Napari.
    """
    def __init__(self, *args, **kwargs) -> None:
        """Constructor
        """
        super().__init__(*args, **kwargs)

        self.setLayout(QVBoxLayout())
        self._buildStagesTab()

    def _buildStagesTab(self) -> None:
        """Create the tab widget that will host the different stages of the
        QuanTI-FRET process.
        """
        # Create Tab Widget
        operations = QTabWidget(self)
        operations.setDocumentMode(True)
        tabBar = operations.tabBar()
        assert tabBar is not None
        tabBar.setExpanding(True)
        self.layout().addWidget(operations)  # type: ignore

        # Add Calibration Operation tab
        calibrationWidget = CalibrationWidget(operations)
        operations.addTab(calibrationWidget, 'Calibration')

        # Add Fret Operation tab
        fretWidget = FretWidget(operations)
        operations.addTab(fretWidget, 'Fret')
