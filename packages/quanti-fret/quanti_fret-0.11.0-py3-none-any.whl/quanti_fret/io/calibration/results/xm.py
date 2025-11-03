from quanti_fret.core import QtfSeries
from quanti_fret.io.base.results import StageResults
from quanti_fret.io.base.validate import (
    BackgroundEngineValidator, BooleanValidator, FloatValidator, IntValidator,
    StringValidator, TupleValidator, Validator
)

from pathlib import Path
from typing import Any

import pandas as pd


class XMResults(StageResults):
    """ Manage the saving of the settings and results of the XM Stage

    The value expected as input are:
        * settings:
            * series name (str)
            * series used (QtfSeries): transformed in size of the series (int)
            * alpha_bt (float)
            * delta_de (float)
            * background for the 3 channels (tuple[float, float, float])
            * percentile rang (tuple[float, float])
            * Save analysis details (bool)
            * Sampling (int)
        * results:
            * beta_x (float)
            * gamma_m (float)
            * redchi_2 (float)
            * r2 (float)
            * q (float)
    """

    VALIDATORS: dict[str, dict[str, Validator]] = {
        'settings': {
            'series': StringValidator(),
            'nb_seq': IntValidator(min=0),
            'alpha_bt': FloatValidator(),
            'delta_de': FloatValidator(),
            'background': BackgroundEngineValidator(),
            'percentile_range': TupleValidator(
                FloatValidator(min=0.0, max=100.0), 2
            ),
            'save_analysis_details': BooleanValidator(),
            'analysis_sampling': IntValidator(min=1, max=10000)
        },
        'results': {
            'beta_x': FloatValidator(),
            'gamma_m': FloatValidator(),
            'redchi_2': FloatValidator(),
            'r2': FloatValidator(),
            'q': FloatValidator(),
        }
    }

    def __init__(self, output_dir: Path):
        """Constructor

        Args:
            output_dir (Path): Path to the output directory
        """
        super().__init__(output_dir, self.VALIDATORS)

    def _get_json_results(self, results: tuple[Any, ...]) -> tuple[Any, ...]:
        """ Return all the results that are supposed to be in the json file.

        Remove the last settings element that are analysis data

        Args:
            results (tuple[Any, ...]): results to save

        Results:
            tuple[Any, ...]: Results to put in the JSON
        """
        return results[:-1]

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
        analysis_data: dict[str, Any] = results[-1]

        def save_fig_if_key(key: str, filename: str) -> None:
            """ Check if a key exists in the dict, if so, save the figure

            Args:
                key (str): key to check
                filename (str): filename to save (without png extension)
            """
            if key in analysis_data:
                path = self._output_dir / f'{filename}.png'
                analysis_data[key].savefig(path)

        # plots
        save_fig_if_key('hist2d_s_vs_e', 'S_vs_E_for_all_cells')
        save_fig_if_key('hist2d_e_vs_iaa', 'E_vs_IAA_intensity_for_all_cells')
        save_fig_if_key('hist2d_s_vs_iaa', 'S_vs_IAA_intensity_for_all_cells')
        save_fig_if_key('e_boxplot', 'E_boxplot')
        save_fig_if_key('s_boxplot', 'S_boxplot')

        # Save indices
        if 'e_boxplot' in analysis_data or 's_boxplot' in analysis_data:
            series: QtfSeries = settings[1]
            self._save_sequences_index(series)

        # Median sampled
        if 'median_sampled' in analysis_data:
            df = pd.DataFrame(analysis_data['median_sampled'],
                              columns=['DD', 'DA', 'AA', 'E', 'S'])
            path = self._output_dir / 'median_sampled.csv'
            df.to_csv(path, index=True, index_label='Index')
            path = self._output_dir / 'median_sampled.npy'
            analysis_data['median_sampled'].dump(path)

        # sequences sampled
        if 'sampled_list' in analysis_data:
            sampled_dir = self._output_dir / 'sampled'
            sampled_dir.mkdir(parents=True, exist_ok=True)
            index = 0
            for sampled in analysis_data['sampled_list']:
                df = pd.DataFrame(sampled.T,
                                  columns=['DD', 'DA', 'AA', 'E', 'S'])
                path = sampled_dir / f'{index}.csv'
                df.to_csv(path, index=False)
                path = sampled_dir / f'{index}.npy'
                sampled.dump(path)
                index += 1

        # inspection
        if 'inspection' in analysis_data:
            inspection_dir = self._output_dir / 'inspection'
            inspection_dir.mkdir(parents=True, exist_ok=True)

            def save_insp_if_key(key: str, filename: str) -> None:
                if key in analysis_data['inspection']:
                    path = inspection_dir / f'{filename}.png'
                    analysis_data['inspection'][key].savefig(path)

            save_insp_if_key('triplets_per_seq', 'triplets_per_seq')
            save_insp_if_key('s_per_seq', 'S_per_seq')
            save_insp_if_key('s_vs_e', 'S_vs_E')
            save_insp_if_key('scatter_3d', 'scatter_3d')
