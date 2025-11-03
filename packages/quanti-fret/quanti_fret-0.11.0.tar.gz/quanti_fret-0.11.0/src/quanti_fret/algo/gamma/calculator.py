from quanti_fret.algo.background import BackgroundEngine, substract_background
from quanti_fret.algo.plot import PlotGenerator
import quanti_fret.algo.matrix_functions as mfunc
from quanti_fret.core import QtfSeries, TripletSequence

import abc
from typing import Any

from matplotlib.figure import Figure
import numpy as np


class GammaCalculator(abc.ABC):
    """ Abstract class that compute the gamma value from a given series.

    A gamma value is the matrix obtained by dividing the DA channel image by
    either the DD or the AA channel image.

    This class then add multiple operation allowing to compute the gamma on
    relevant values (taking only values from the object analysed, discarding
    useless values, ...) and returns the median values of all gammas.

    This class is intended to be inherited. You have to pass the gamma name to
    this class constructor (can be for example 'alpha_BT' or 'delta_DE' and you
    must define the following:
        * `self._get_gamma_channels`: returns all the gamma channel from a
            given sequence (must be DD or AA channel)
    """
    def __init__(self, gamma_name: str, channel_name) -> None:
        """ Constructor

        Args:
            gamma_name (str): Name of the gamma value to compute
            channel_name (str): Name of the channel used to compute gamma
        """
        self._plot = PlotGenerator()
        self._gamma_name = gamma_name
        self._channel_name = channel_name

    def run(
        self, series: QtfSeries, background: BackgroundEngine,
        discard_low_percentile: float = 0., plot_sequence_details: bool = False
    ) -> tuple[float, float, int, dict[str, Any]]:
        """ Compute the Gamma value and the standard deviation of the
        given series.

        Args:
            series (QtfSeries): Series to use to compute the gamma
            bckg_gamma (float): backgroung of the gamma channel
            bckg_da (float): backgroung of the da channel
            discard_low_percentile (float): percentile of pixels to discard
                under this value, after applying the mask.
            plot_sequence_details (float): True to plot the hist2d and gamma
                figures for each dequences

        Returns:
            tuple[float, float, float]:
                The median of all Gamma value computed
                The Standard Deviation
                The Number of pixels used to compute the median gamma
        """
        # Get gammas and median intensities for each sequence
        seq_gammas, seq_intensities_median, seq_figures = \
            self._compute_and_extract_gammas(
                series, background, discard_low_percentile,
                plot_sequence_details
            )

        # Compute gamma_median, gamma_std and gamma_nb_pix
        seq_gammas_array = np.concatenate([np.array(i) for i in seq_gammas])
        gamma_median = np.round(np.median(seq_gammas_array), 3)
        # Compute the standard deviation of gamma over all pixels
        # We get rid of zero values coming from NaN
        # TODO: check wether we also need to get rid of those values for the
        # median?? Median is less sensitive to outliers
        gamma_std = np.round(np.std(seq_gammas_array > 0.0), 3)
        gamma_nb_pix = len(seq_gammas_array)

        # Create plots
        figures: dict[str, Any] = {'sequences': seq_figures}
        boxplot, scatter = self._summary_plots(seq_gammas,
                                               seq_intensities_median)
        figures['boxplot'] = boxplot
        figures['scatter'] = scatter

        return float(gamma_median), float(gamma_std), gamma_nb_pix, figures

    def _compute_and_extract_gammas(
        self, series: QtfSeries, background: BackgroundEngine,
        discard_low_percentile: float = 0., plot_sequence_details: bool = False
    ) -> tuple[list[np.ndarray], list[float], list[dict[str, Figure | int]]]:
        """ Compute the gamma value for one triplet of each sequence. The gamma
        returned represent only the values within a mask. Return also the
        median intensities within the same mask.

        The mask is created from the triplet mask. It is then improved removing
        some irrelevant values and discarding the given low percentile pixels.

        Args:
            series (QtfSeries): Series to use to compute the gamma
            bckg_gamma (float): backgroung of the gamma channel
            bckg_da (float): backgroung of the da channel
            discard_low_percentile (float): percentile of pixels to discard
                under this value, after applying the mask.
            plot_sequence_details (float): True to plot the hist2d and gamma
                figures for each dequences

        Returns:
            tuple[list[np.ndarray], list[float],
            list[dict[str, Figure | Path]]]:
               Tuple value with:
                    * Gammas values for each sequence within the computed mask.
                        Array is dimension 1
                    * The median intensity for each sequence whithin the mask.
                        Array is dimension 1
                    * The figures associated to each sequence. The keys are
                        * 'subfolder': Path to the sequence subfolder relative
                            to the series folder
                        * 'hist_2d': figure plotting the 2d histogram
                        * 'gamma': figure containing the gamma image
        """
        seq_gammas: list[np.ndarray] = []
        seq_median_intensities: list[float] = []
        figures: list[dict[str, Figure | int]] = []
        # For each image
        for seq in series:
            # Get the first triplet of each sequence
            # TODO: let the user decide the triplet
            triplet = seq.triplets[0]
            mask = triplet.mask_cell

            # substract background
            triplet_np = substract_background(triplet, background)

            # select channels
            channel = triplet_np[self._get_gamma_channels_index()]
            da = triplet_np[1]

            # Compute Gamma
            gamma = mfunc.gamma(channel, da)

            # Compute Mask
            new_mask = mfunc.clean_mask(mask, channel, gamma,
                                        discard_low_percentile)

            # Extract data from mask
            masked_gamma = gamma[new_mask]
            masked_intensity = channel[new_mask]

            # Plot histogram (itensity / gamme) and gamma
            if plot_sequence_details:
                figures.append(self._detail_seq_plot(
                    seq, len(seq_gammas), gamma, masked_gamma, masked_intensity
                ))

            # Append all_gamma and all_Intensity
            seq_gammas.append(masked_gamma)
            seq_median_intensities.append(float(np.median(masked_intensity)))

        return seq_gammas, seq_median_intensities, figures

    def _summary_plots(
        self, seq_gammas: list[np.ndarray], seq_intensities_median: list[float]
    ) -> tuple[Figure, Figure]:
        """ Plot the summary figures.

        The summary figures are:
            * the Boxplot of gammas per sequence
            * The scatter plot of median gamma per sequence with regards to
                medium intensity per sequence

        Args:
            seq_gammas (list[np.ndarray]): the gamma computed per sequence
            seq_intensities_median (list[float]): the median intensity on the
                gamma channel per sequence

        Returns:
            tuple[Figure, Figure]: The two figures created
        """
        seq_gamma_median = [float(np.median(g)) for g in seq_gammas]
        mean_seq_gamma_median = np.mean(seq_gamma_median)
        std_seq_gamma_median = np.std(seq_gamma_median)
        boxplot_subtitle = f"Median's mean = {mean_seq_gamma_median:.3f} / " \
                           f"Median's std = {std_seq_gamma_median:.3f}"
        fig_boxplot = self._plot.boxplot_seq_overview(
            self._gamma_name, seq_gammas, boxplot_subtitle
        )
        fig_scatter = self._plot.scatterplot_signal_intensity(
            'median intensity', seq_intensities_median,
            f'median {self._gamma_name[0].upper() + self._gamma_name[1:]}',
            seq_gamma_median
        )
        return fig_boxplot, fig_scatter

    def _detail_seq_plot(
        self, seq: TripletSequence, index: int, gamma: np.ndarray,
        masked_gamma: np.ndarray, seq_intensity: np.ndarray
    ) -> dict[str, int | Figure]:
        """ Plot the figure representing the details of the specific sequence.

        Args:
            seq (TripletSequence): The sequence to plot
            index (int): index of the sequence in the process
            gamma (np.ndarray): The gamma computed
            masked_gamma (np.ndarray): The gamma values extracted from the mask
            seq_intensity (np.ndarray): The intensity values extracted from
                the mask

        Returns:
            dict[str, str | Figure]: The plot in the form of a dict with:
                * 'index': index of the sequence
                * 'hist_2d': 2d histogram figure
                * ''gamma'': gamma image figure
        """
        hist_2d_subtitle = f'Sequence: {index} - ' \
                           f'Folder: {seq.subfolder_crop(40)} - ' \
                           f'median({self._gamma_name}): ' \
                           f'{np.median(masked_gamma):.3f}'
        hist_2d_fig = self._plot.hist2d_signal_intensity(
            seq_intensity, masked_gamma,
            f'I_{self._channel_name}', self._gamma_name,
            range='minimaxi',
            title=f'Dependence of {self._gamma_name} on intensity '
                  f'I_{self._channel_name}',
            subtitle=hist_2d_subtitle
        )
        range, nticks = self._get_gamma_plot_params()
        gamma_fig = self._plot.image_with_colorbar(
            gamma,
            title=self._gamma_name.title(),
            subtitle=f'Sequence: {index} - Folder: {seq.subfolder_crop(40)}',
            range=range, nticks=nticks
        )
        figures: dict[str, int | Figure] = {
            'index': index,
            'hist_2d': hist_2d_fig,
            'gamma': gamma_fig
        }
        return figures

    @abc.abstractmethod
    def _get_gamma_channels_index(self) -> int:
        """ Return the gama channels index associated with the given sequence.

        Returns:
            int: The gamma channels index
        """
        pass

    @abc.abstractmethod
    def _get_gamma_plot_params(self) -> tuple[tuple[float, float], int]:
        """ Get the range and nticks params to give to the mfunction to plot
        the gamma image

        Args:
            seq (TripletSequence): The associated sequence

        Returns:
            tuple[tuple[float, float], int]: range, nticks
        """
        pass
