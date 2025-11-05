from quanti_fret.apps.gui.popup.napari import NapariPopUpManager
from quanti_fret.apps.gui.popup.standalone import StandalonePopUpManager

from quanti_fret.core import Singleton, TripletSequence

from typing import Any


class PopUpManager(metaclass=Singleton):
    """ Manage actions that open QuanTI-FRET elements outside of the main
    GUI.

    There are two modes of the manager:
        * Standalone mode (default): Used as a standalone applcation
        * Napari mode: to be used insde Napari as a plugin and to interract
            with Napari

    This manager is a singleton, which means that if you need to set the
    Napari mode, you have to do it only once.

    This does not handle the files/folders Dialogs popup.
    """

    def __init__(self) -> None:
        self._viewer: StandalonePopUpManager | NapariPopUpManager
        self._viewer = StandalonePopUpManager()

    def setNapariMode(self, viewer: Any) -> None:
        """ Set the Mode to Napari

        Args:
            viewer (napari.viewer.Viewer): Napari Viewer associated with the
                plugin
        """
        self._viewer = NapariPopUpManager(viewer)

    def openSequence(self, seq: TripletSequence) -> None:
        """ Open the given Triplet sequence

        Args:
            seq (TripletSequence): sequence to open
        """
        self._viewer.openSequence(seq)
