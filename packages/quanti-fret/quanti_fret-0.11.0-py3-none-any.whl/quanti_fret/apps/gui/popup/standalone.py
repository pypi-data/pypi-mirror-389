from quanti_fret.core import TripletSequence

from qtpy.QtCore import QUrl
from qtpy.QtGui import QDesktopServices


class StandalonePopUpManager:
    """ PopUp manager for the Standalone Mode
    """

    def openSequence(self, seq: TripletSequence) -> None:
        """ Open the given Triplet sequence

        This will launch the OS's file manager at the sequence's location

        Args:
            seq (TripletSequence): sequence to open
        """
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(seq.folder)))
