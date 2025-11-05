
from quanti_fret.apps.gui import QtfMainWidget
from quanti_fret.apps.gui.popup import PopUpManager

from qtpy.QtWidgets import QHBoxLayout, QWidget

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import napari   # type: ignore


class QtfNapariWidget(QWidget):
    """ Entry point widget for the Napari plugin
    """
    def __init__(
            self, viewer: "napari.viewer.Viewer"
    ):
        super().__init__()

        PopUpManager().setNapariMode(viewer)

        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QtfMainWidget())
