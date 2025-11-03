from quanti_fret.core import TripletSequence

from typing import TYPE_CHECKING

import numpy as np


if TYPE_CHECKING:
    import napari  # type: ignore


class NapariPopUpManager:
    """ Popup manager for the Napari mode
    """

    def __init__(self, viewer: "napari.viewer.Viewer") -> None:
        """ Constructor

        Args:
            viewer (napari.viewer.Viewer): Napari viewer linked with the plugin
        """
        self._viewer = viewer

    def openSequence(self, seq: TripletSequence) -> None:
        """ Open the given Triplet sequence

        This will add the sequence to the viewer

        Args:
            seq (TripletSequence): sequence to open
        """
        array = seq.stacked
        masks = np.expand_dims(seq.mask_cells, axis=1)
        array = np.append(array, masks, axis=1)
        if seq.have_all_mask_bckg():
            bckgs = np.expand_dims(seq.mask_bckgs, axis=1)
            array = np.append(array, bckgs, axis=1)

        self._viewer.add_image(array, name=seq.subfolder)
        self._viewer.dims.axis_labels = ['triplet', 'channel', 'y', 'x']
