from quanti_fret.io.base.results import StageResults
from quanti_fret.io.base.validate import (
    BackgroundEngineValidator, BooleanValidator, FloatValidator, IntValidator,
    StringValidator, Validator
)
from quanti_fret.core import QtfException

from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np
import tifffile


class FretResults(StageResults):
    """ Manage the saving of the settings and results of the Fret Stage

    The value expected as input are:
        * settings:
            * series name (str)
            * series used (QtfSeries): transformed in size of the series (int)
            * alpha_bt (float)
            * delta_de (float)
            * beta_x (float)
            * gamma_m (float)
            * background for the 3 channels (tuple[float, float, float])
            * sigma_s (float)
            * target_s (float)
            * sigma_gauss (float)
            * weights_threshold (float)
            * Save analysis details (bool)
            * Sampling (int)
    """

    VALIDATORS: dict[str, dict[str, Validator]] = {
        'settings': {
            'series': StringValidator(),
            'nb_seq': IntValidator(min=0),
            'alpha_bt': FloatValidator(),
            'delta_de': FloatValidator(),
            'beta_x': FloatValidator(),
            'gamma_m': FloatValidator(),
            'background': BackgroundEngineValidator(),
            'sigma_s': FloatValidator(),
            'target_s': FloatValidator(),
            'sigma_gauss': FloatValidator(),
            'weights_threshold': FloatValidator(),
            'save_analysis_details': BooleanValidator(),
            'analysis_sampling': IntValidator(min=1, max=10000)
        },
    }

    def __init__(self, output_dir: Path):
        """Constructor

        Args:
            output_dir (Path): Path to the output directory
        """
        super().__init__(output_dir, self.VALIDATORS, 'settings.json')

    def _get_json_results(self, results: tuple[Any, ...]) -> tuple[Any, ...]:
        """ Return all the results that are supposed to be in the json file.

        No results on this stage

        Args:
            results (tuple[Any, ...]): results to save

        Results:
            tuple[Any, ...]: Results to put in the JSON
        """
        return ()

    def save_index(self, index: int, results: tuple[Any, ...]) -> None:
        """ Save the stage results for a computation on a single index of the
        series.

        Values saved and their order are described in each stage results
        implementation class. For the results we expect them to be in the same
        order than the one returned by the function computing one index at a
        time.

        Args:
            index (int): Index of the element to save
            results (tuple[Any, ...]): Results to save
        """
        def save_fig_if_key(key: str, filename: str) -> None:
            if key in plots:
                path = results_dir / f'{filename}.png'
                plots[key].savefig(path)

        results_dir = self._output_dir / 'Results' / f'{index:04}'
        results_dir.mkdir(parents=True, exist_ok=True)

        E, Ew, S, plots, sampled = results
        self._write_tiff(E, results_dir / 'E.tif')
        self._write_tiff(S, results_dir / 'S.tif')
        self._write_tiff(Ew, results_dir / 'E_filtered.tif')

        save_fig_if_key('hist2d_s_vs_e', 'S_vs_E')
        save_fig_if_key('hist2d_e_vs_iaa', 'E_vs_IAA')
        save_fig_if_key('hist2d_s_vs_iaa', 'S_vs_IAA')

        if sampled is not None:
            df = pd.DataFrame(sampled.T,
                              columns=['DD', 'DA', 'AA', 'E', 'Ew', 'S'])
            path = results_dir / 'sampled.csv'
            df.to_csv(path, index=False, index_label='Index')
            path = results_dir / 'sampled.npy'
            sampled.dump(path)

    def _write_tiff(self, img: np.ndarray, path: Path):
        data_tif = np.copy(img)
        mask = np.logical_or(data_tif < 0, data_tif > 100)
        data_tif[mask] = np.nan
        tifffile.imwrite(path, data_tif.astype(np.float32))

    def _save_extra(
        self, settings: tuple[Any, ...], results: tuple[Any, ...]
    ) -> None:
        """ Write every results that are not in the JSON.

        Save the figures and the CSVs

        Args:
            settings (tuple[Any, ...]): Settings to save
            results (tuple[Any, ...]): All the results to save, included the
                one already saved in the JSON.
        """
        series = settings[1]
        self._save_sequences_index(series)

        if len(results) == 0:
            return
        elif len(results) == 3:
            boxplots, hist2d, median_sampled = results

            # boxplot
            path = self._output_dir / 'E_boxplot.png'
            boxplots['e_boxplot'].savefig(path)
            path = self._output_dir / 'S_boxplot.png'
            boxplots['s_boxplot'].savefig(path)

            # Hist 2d
            path = self._output_dir / 'S_vs_E.png'
            hist2d.savefig(path)

            # Median sampled
            df = pd.DataFrame(median_sampled,
                              columns=['DD', 'DA', 'AA', 'E', 'Ew', 'S'])
            path = self._output_dir / 'median_sampled.csv'
            df.to_csv(path, index=True, index_label='Index')
            path = self._output_dir / 'median_sampled.npy'
            median_sampled.dump(path)
        else:
            raise QtfException('Bad Fret results length')
