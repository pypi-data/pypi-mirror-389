from quanti_fret.core.exception import QtfException

import os
from pathlib import Path
from typing import Iterator

import numpy as np
import tifffile


class Triplet:
    """ Class representing a triplet image.

    A triplet is a collection of the 3 (+2) of the following images, called
    channels, and representing a single acquisition of two snapshots:
    - DD: Donor-Direct channel
    - DA: Donor-Acceptor channel
    - AA: Acceptor-Acceptor channel
    - (MaskCell: Cell mask)
    - (MaskBckg: Background mask) -> Optional

    All images can be accessed as properties, which will load the images
    from disk only once, and then cache them for future access.
    The images are expected to be in TIFF format, and the paths to the images
    are provided at initialization.
    """

    def __init__(self,
                 dd_path: os.PathLike | str,
                 da_path: os.PathLike | str,
                 aa_path: os.PathLike | str,
                 mask_cell_path: os.PathLike | str,
                 mask_bckg_path: os.PathLike | str = '',
                 img_type: np.typing.DTypeLike | None = np.float32):
        """ Constructor

        Initializes the Triplet with the paths to the channels images.

        Args:
            dd_path (os.PathLike | str): Path to the DD image.
            da_path (os.PathLike | str): Path to the DA image.
            aa_path (os.PathLike | str): Path to the AA image.
            mask_cell_path (os.PathLike | str): Path to the cell mask image.
            mask_bckg_path (os.PathLike | str, optional): Path to the
                background mask image. If set to "''", consider the Triplet do
                not have background Mask. Default to ''
            img_type (np.dtype | None): Force the type of the dd/da/aa images.
        """
        self._dd_path = Path(dd_path)
        self._dd: np.ndarray | None = None
        self._da_path = Path(da_path)
        self._da: np.ndarray | None = None
        self._aa_path = Path(aa_path)
        self._aa: np.ndarray | None = None
        self._mask_cell_path = Path(mask_cell_path)
        self._mask_cell: np.ndarray | None = None

        self._mask_bckg_path: Path | None = None
        if mask_bckg_path != '':
            self._mask_bckg_path = Path(mask_bckg_path)
        self._mask_bckg: np.ndarray | None = None

        self._img_type = img_type

    @property
    def dd(self) -> np.ndarray:
        """ Returns the DD channel. Loads it from disk if not already loaded.

        Returns:
            np.ndarray: the DD channel as a NumPy array.
        """
        if self._dd is None:
            self._dd = tifffile.imread(self._dd_path)
            if self._img_type is not None:
                self._dd.astype(self._img_type)
        return self._dd

    @property
    def da(self) -> np.ndarray:
        """ Returns the DA channel. Loads it from disk if not already loaded.

        Returns:
            np.ndarray: the DA channel as a NumPy array.
        """
        if self._da is None:
            self._da = tifffile.imread(self._da_path)
            if self._img_type is not None:
                self._da.astype(self._img_type)
        return self._da

    @property
    def aa(self) -> np.ndarray:
        """ Returns the AA channel. Loads it from disk if not already loaded.

        Returns:
            np.ndarray: the AA channel as a NumPy array.
        """
        if self._aa is None:
            self._aa = tifffile.imread(self._aa_path)
            if self._img_type is not None:
                self._aa.astype(self._img_type)
        return self._aa

    @property
    def stacked(self) -> np.ndarray:
        """ Return the DD/DA/AA channels stacked in a numpy array.

        Returns:
            np.ndarray: the triplet stacked
        """
        return np.stack((self.dd, self.da, self.aa), axis=0)

    @property
    def mask_bckg(self) -> np.ndarray:
        """ Returns the background mask channel. Loads it from disk if not
        already loaded.

        Returns:
            np.ndarray: the background mask channel as a NumPy array.
        """
        if self._mask_bckg is None:
            if self._mask_bckg_path is None:
                raise QtfException('Triplet does not have a mask_bckg')
            self._mask_bckg = \
                tifffile.imread(self._mask_bckg_path).astype(bool)
        return self._mask_bckg

    @property
    def mask_cell(self) -> np.ndarray:
        """ Returns the cell mask channel. Loads it from disk if not already
        loaded.

        Returns:
            np.ndarray: the cell mask channel as a NumPy array.
        """
        if self._mask_cell is None:
            self._mask_cell = \
                tifffile.imread(self._mask_cell_path).astype(bool)
        return self._mask_cell

    def has_mask_bckg(self) -> bool:
        """ Check if the Triplet have a background mask

        Returns:
            bool: True if triplet have a background mask
        """
        return self._mask_bckg_path is not None


class TripletSequence:
    """ Class representing a TripletSequence, which is a sequence of triplet
    representing either an acquisition of a single triplet, or of a video.
    """
    def __init__(self, triplets: list[Triplet], folder:  os.PathLike | str,
                 series_folder: os.PathLike | str | None = None):
        self.triplets = triplets

        self._folder = Path(folder)
        if series_folder is None:
            self._series_folder = None
        else:
            self._series_folder = Path(series_folder)
        self._ignore_file = self._folder / '.qtf_ignore.txt'

        self._dds: list[np.ndarray] | None = None
        self._das: list[np.ndarray] | None = None
        self._aas: list[np.ndarray] | None = None
        self._stacked: np.ndarray | None = None
        self._mask_bckgs: list[np.ndarray] | None = None
        self._mask_cells: list[np.ndarray] | None = None

    @property
    def folder(self) -> Path:
        """ Returns the folder where the sequence is stored.
        """
        return self._folder

    def folder_crop(self, max_length: int, prefix='[...]') -> str:
        """ Utility to get the folder Path as a string cropped to a given
        max length.

        Args:
            max_length (int): max string length (prefix included)
            prefix (str, optional): prefix to put in front of the cropped path

        Returns:
            str: the string representation of the path cropped
        """
        return self._crop_path(self._folder, max_length, prefix)

    @property
    def subfolder(self) -> Path:
        """ Returns the subfolder compared to the series folder if any.
        """
        if self._series_folder is None:
            return self._folder
        else:
            return self._folder.relative_to(self._series_folder)

    def subfolder_crop(self, max_length: int, prefix='[...]') -> str:
        """ Utility to get the subfolder Path as a string cropped to a given
        max length.

        Args:
            max_length (int): max string length (prefix included)
            prefix (str, optional): prefix to put in front of the cropped path

        Returns:
            str: the string representation of the path cropped
        """
        return self._crop_path(self.subfolder, max_length, prefix)

    @property
    def dds(self) -> list[np.ndarray]:
        if self._dds is None:
            self._dds = [t.dd for t in self.triplets]
        return self._dds

    @property
    def das(self) -> list[np.ndarray]:
        if self._das is None:
            self._das = [t.da for t in self.triplets]
        return self._das

    @property
    def aas(self) -> list[np.ndarray]:
        if self._aas is None:
            self._aas = [t.aa for t in self.triplets]
        return self._aas

    @property
    def stacked(self) -> np.ndarray:
        if self._stacked is None:
            self._stacked = np.array(
                [t.stacked for t in self.triplets]
            )
        return self._stacked

    @property
    def mask_bckgs(self) -> list[np.ndarray]:
        if self._mask_bckgs is None:
            self._mask_bckgs = [t.mask_bckg for t in self.triplets]
        return self._mask_bckgs

    @property
    def mask_cells(self) -> list[np.ndarray]:
        if self._mask_cells is None:
            self._mask_cells = [t.mask_cell for t in self.triplets]
        return self._mask_cells

    def have_all_mask_bckg(self) -> bool:
        """ Check if all the Triplet have a background mask

        Returns:
            bool: True if all triplet have a background mask
        """
        return all([t.has_mask_bckg() for t in self.triplets])

    def is_enabled(self) -> bool:
        """ Returns True if the sequence is enabled. False otherwise
        """
        return not self._ignore_file.is_file()

    def set_enabled(self, val: bool) -> None:
        """ Set the enabled state of the sequence

        I the sequence goes from disabled to enabled, it deletes the ignore
        file in the sequence's folder. In the other way arround, it creates
        the file.

        Args:
            val (bool): Value to set
        """
        if val:
            self._ignore_file.unlink(missing_ok=True)
        else:
            self._ignore_file.touch(exist_ok=True)

    def __getitem__(self, index: int) -> Triplet:
        if index > len(self.triplets):
            raise QtfException('Index out of range')
        return self.triplets[index]

    def __iter__(self) -> Iterator[Triplet]:
        for triplet in self.triplets:
            yield triplet

    def _crop_path(self, path: Path, max_length: int, prefix='[...]') -> str:
        """ Utility to get the a Path as a string cropped to a given max
        length.

        Args:
            path (Path): path to crop
            max_length (int): max string length (prefix included)
            prefix (str, optional): prefix to put in front of the cropped path

        Returns:
            str: the string representation of the path cropped
        """
        path_s = str(path)
        if len(path_s) > max_length:
            new_path_len = max_length - len(prefix)
            path_s = path_s[-new_path_len:]
            path_s = f'{prefix}{path_s}'
        return path_s


class QtfSeries:
    def __init__(self, sequences: list[TripletSequence]) -> None:
        self._sequences = sequences
        self._dds: list[list[np.ndarray]] | None = None
        self._das: list[list[np.ndarray]] | None = None
        self._aas: list[list[np.ndarray]] | None = None
        self._mask_bckgs: list[list[np.ndarray]] | None = None
        self._mask_cells: list[list[np.ndarray]] | None = None
        self._stacked: np.ndarray | None = None

    def size(self):
        return len(self._sequences)

    @property
    def dds(self) -> list[list[np.ndarray]]:
        if self._dds is None:
            self._dds = [ts.dds for ts in self._sequences]
        return self._dds

    @property
    def das(self) -> list[list[np.ndarray]]:
        if self._das is None:
            self._das = [ts.das for ts in self._sequences]
        return self._das

    @property
    def aas(self) -> list[list[np.ndarray]]:
        if self._aas is None:
            self._aas = [ts.aas for ts in self._sequences]
        return self._aas

    @property
    def stacked(self) -> np.ndarray:
        if self._stacked is None:
            self._stacked = np.array(
                [s.stacked for s in self._sequences]
            )
        return self._stacked

    @property
    def mask_bckgs(self) -> list[list[np.ndarray]]:
        if self._mask_bckgs is None:
            self._mask_bckgs = [ts.mask_bckgs for ts in self._sequences]
        return self._mask_bckgs

    @property
    def mask_cells(self) -> list[list[np.ndarray]]:
        if self._mask_cells is None:
            self._mask_cells = [ts.mask_cells for ts in self._sequences]
        return self._mask_cells

    def have_all_mask_bckg(self) -> bool:
        """ Check if all the Triplet have a background mask

        Returns:
            bool: True if all triplet have a background mask
        """
        return all([s.have_all_mask_bckg() for s in self._sequences])

    def get_only_enabled(self) -> 'QtfSeries':
        """ Returns a series containing only sequences that are enabled
        """
        return QtfSeries([s for s in self._sequences if s.is_enabled()])

    def __add__(self, o: 'QtfSeries') -> 'QtfSeries':
        new_list = self._sequences + o._sequences
        return QtfSeries(new_list)

    def __iter__(self) -> Iterator[TripletSequence]:
        for triplet_seq in self._sequences:
            yield triplet_seq

    def __getitem__(self, index: int) -> TripletSequence:
        if index > len(self._sequences):
            raise QtfException('Index out of range')
        return self._sequences[index]
