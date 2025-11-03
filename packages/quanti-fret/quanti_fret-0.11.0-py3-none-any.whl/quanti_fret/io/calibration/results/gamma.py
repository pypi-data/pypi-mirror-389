from quanti_fret.core import QtfSeries
from quanti_fret.io.base.results import StageResults
from quanti_fret.io.base.validate import (
    BackgroundEngineValidator, BooleanValidator, FloatValidator,
    IntValidator, StringValidator, Validator
)

from typing import Any
from pathlib import Path


class GammaResults(StageResults):
    """ Manage the saving of the settings and results of the Gamma stages
    (BT and DE)

    The value expected as input are:
        * settings:
            * series name (str)
            * series used (QtfSeries): transformed in size of the series (int)
            * background of the gamma channel (float)
            * background to the DA channel (float)
            * discard low percentile (float)
            * plot sequence details (bool)
        * results:
            * gamma (float)
            * standard deviation (float)
            * Number of pixels used for gamma (float)
            * figures created (dict)
    """

    VALIDATORS: dict[str, dict[str, Validator]] = {
        'settings': {
            'series': StringValidator(),
            'nb_seq': IntValidator(min=0),
            'background': BackgroundEngineValidator(),
            'discard_low_percentile': FloatValidator(min=0.0, max=100.0),
            'plot_seq_details': BooleanValidator(),
        },
        'results': {
            'gamma': FloatValidator(),
            'std': FloatValidator(),
            'nb_pix': IntValidator(min=0)
        }
    }

    def __init__(
        self, output_dir: Path, gamma_name: str, std_name: str
    ) -> None:
        """Constructor

        This will duplicate the `self.VALIDATORS` and change the keys
        `gamma`, and `std` to their name in the BT or DE results.

        Args:
            output_dir (Path): Path to the output directory
            gamma_name (str): Name of the gamma computed
            std_name (str): Name of the std computed
            std_name (str): Name of channel used for the gamma computation
        """
        self._gamma_name = gamma_name
        self._std_name = std_name

        # Create the new validators
        # (We can't modify self.VALIDATORS as it will be modify for all
        # instances. And we can't just pop out values as we want to keep order)
        val_settings = self.VALIDATORS['settings']
        val_results = self.VALIDATORS['results']
        validators: dict[str, dict[str, Validator]] = {
            'settings': {
                'series': val_settings['series'],
                'nb_seq': val_settings['nb_seq'],
                'background': val_settings['background'],
                'discard_low_percentile':
                    val_settings['discard_low_percentile'],
                'plot_seq_details': val_settings['plot_seq_details'],
            },
            'results': {
                self._gamma_name: val_results['gamma'],
                self._std_name: val_results['std'],
                'nb_pix': val_results['nb_pix']
            }
        }
        super().__init__(output_dir, validators)

    def _get_json_results(self, results: tuple[Any, ...]) -> tuple[Any, ...]:
        """ Return all the results that are supposed to be in the json file.

        Remove the last settings element that is a figure

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
        figures: dict[str, Any] = results[-1]

        # Box plot
        figures['boxplot'].savefig(self._output_dir / 'boxplot.png')

        # Scatter plot
        figures['scatter'].savefig(self._output_dir / 'scatter.png')

        # Sequences plot
        if 'sequences' in figures:
            for seq in figures['sequences']:
                index = seq['index']
                folder = self._output_dir / 'Details'
                folder.mkdir(parents=True, exist_ok=True)
                hist_2d_path = folder / f'{index:02d}_hist2d.png'
                gamma_path = folder / f'{index:02d}_{self._gamma_name}.png'
                seq['hist_2d'].savefig(hist_2d_path)
                seq['gamma'].savefig(gamma_path)

        # Save sequences indices
        if 'boxplot' in figures:
            series: QtfSeries = settings[1]
            self._save_sequences_index(series)
