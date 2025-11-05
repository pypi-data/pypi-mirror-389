from quanti_fret.core import QtfException, QtfSeries
from quanti_fret.io.base.results.json import JsonResultsManager
from quanti_fret.io.base.validate import Validator

import abc
from pathlib import Path
from typing import Any

import pandas as pd


class StageResults(abc.ABC):
    """ Handle the results management of a specific stage.

    It is expected to be inherited. The child class must provide:
        * a `validators` parameter to create a proper JsonResultsManager.
        * `_get_json_results` if that filter out results not supposed to
            be set in the result json.
        * `save_extra` that handle the specific saving of everything that
            is not in the json.
        * `save_index` that handle the saving of the results for a single
            step of the computation at the given index position.
    """

    def __init__(
        self, output_dir: Path, validators: dict[str, dict[str, Validator]],
        json_name: str = 'results.json'
    ) -> None:
        """_summary_

        Args:
            output_dir (Path): Path to the output directory
            validators (dict[str, dict[str, Validator]]): Validators to
                validate, get and save json data
            json_name (str): To set the name of the json file to create
        """
        self._output_dir = output_dir
        self._check_dir()
        json_path = self._output_dir / json_name
        self._validators = validators
        self._json_res_manager = JsonResultsManager(json_path, validators)

    def save(
        self, settings: tuple[Any, ...], results: tuple[Any, ...]
    ) -> None:
        """ Save the stage settings and results, after creating the output dir.

        Values saved and their order are described in each stage results
        implementation class. For the settings, we expect them to be the same
        as the ones returned by StageParams. For the results we expect the
        first elements to be the one to put in the Json files (also described
        in the stage's self._validators), in the same order. Trailing values
        will be for specific savings.

        Args:
            settings (tuple[Any, ...]): Settings to save
            results (tuple[Any, ...]): Results to save
        """
        # Create output dir
        self._check_dir()
        self._output_dir.mkdir(exist_ok=True)
        # Generate and save json
        json_settings = self._get_json_settings(settings)
        json_results = self._get_json_results(results)
        json_data = self._generate_json(json_settings, json_results)
        self._json_res_manager.save(json_data)
        # Save extra data
        self._save_extra(settings, results)

    def save_index(self, index: int, results: tuple[Any, ...]) -> None:
        """ Save the stage results for a computation on a single index of the
        series.

        Values saved and their order are described in each stage results
        implementation class. For the results we expect them to be in the same
        order than the one returned by the function computing one index at a
        time.

        By default, is not implemented

        Args:
            index (int): Index of the element to save
            results (tuple[Any, ...]): Results to save
        """
        raise QtfException('`save_index` was not implemented for this stage')

    def get(self) -> tuple[tuple[Any, ...], tuple[Any, ...]] | None:
        """ Get the settings and results of the given stage

        Values returned are the one from the Json files, in the same order.
        They are also the one described in the stage's self._validators and
        class comments.

        Returns:
            tuple[tuple[Any, ...], tuple[Any, ...]] | None:
                ((settings), (results)) or None if no results found
        """
        # Check dir
        self._check_dir()
        if not self._output_dir.is_dir():
            return None

        # Load data
        data = self._json_res_manager.get()
        if data is None:
            return None
        if 'settings' in data:
            settings = tuple(data['settings'].values())
        else:
            settings = ()
        if 'results' in data:
            results = tuple(data['results'].values())
        else:
            results = ()
        return (settings, results)

    def _get_json_settings(self, settings: tuple[Any, ...]) -> tuple[Any, ...]:
        """ Return all the settings that are supposed to be in the json file.

        By default, turn every `QtfSeries` elements to an integer representing
        the size of the series. Override this to change the behavior.

        Args:
            settings (tuple[Any, ...]): Settings to save

        Results:
            tuple[Any, ...]: Settings to put in the JSON
        """
        return tuple(
            [s.size() if type(s) is QtfSeries else s for s in settings]
        )

    def _get_json_results(self, results: tuple[Any, ...]) -> tuple[Any, ...]:
        """ Return all the results that are supposed to be in the json file.

        Overwritte this if you want to filter out results

        Args:
            results (tuple[Any, ...]): results to save

        Results:
            tuple[Any, ...]: Results to put in the JSON
        """
        return results

    def _save_extra(
        self, settings: tuple[Any, ...], results: tuple[Any, ...]
    ) -> None:
        """ Write every results that are not in the JSON.

        Overwritte this if you want to save something outside the JSON

        Args:
            settings (tuple[Any, ...]): Settings to save
            results (tuple[Any, ...]): All the results to save, included the
                one already saved in the JSON.
        """
        pass

    def _check_dir(self):
        """ Check if the directory is Valid

        Raises:
            QtfException: Check failed
        """
        if not isinstance(self._output_dir, Path):
            err = f'Output dir "{self._output_dir}" is not an instance of Path'
            raise QtfException(err)
        if self._output_dir.exists() and not self._output_dir.is_dir():
            err = f'Output dir {self._output_dir} exists and is not a dir'
            raise QtfException(err)

    def _generate_json(
        self, settings: tuple[Any, ...], results: tuple[Any, ...]
    ) -> dict[str, dict[str, Any]]:
        """ Generate the JSON file to dump.

        About the parameters: Settings and results are supposed to have the
        same elements in the same order than the validators keys

        Args:
            settings (tuple[Any, ...]): Settings to save
            results (tuple[Any, ...]): Results to save
        """
        ret: dict[str, dict[str, Any]] = {}
        if len(settings) > 0:
            ret['settings'] = self._generate_json_section('settings', settings)
        if len(results) > 0:
            ret['results'] = self._generate_json_section('results', results)
        return ret

    def _generate_json_section(
        self, section: str, values: tuple[Any, ...]
    ) -> dict[str, Any]:
        """ Generate the JSON file to dump.

        About the parameters: value is supposed to have the same elements in
        the same order than the validators[section] keys

        Args:
            values (tuple[Any, ...]): values used to put in the section
        """
        ret: dict[str, Validator] = {}
        validator_keys = list(self._validators[section].keys())
        if len(values) != len(validator_keys):
            err = f'Incorrect number of values for section {values}. '
            err += f'Got {len(values)}, expected {len(validator_keys)} ('
            err += f'{validator_keys})'
            raise QtfException(err)
        for i in range(len(values)):
            ret[validator_keys[i]] = values[i]
        return ret

    def _save_sequences_index(self, series: QtfSeries) -> None:
        """ Save a sequences_indices.csv file containing the path of the
        sequence associated with their index used in the results saved.

        Args:
            series (QtfSeries): Series used to compute the results
        """
        indices = pd.DataFrame({'Path': [seq.subfolder for seq in series]})
        indices.index += 1
        path = self._output_dir / 'sequences_indices.csv'
        indices.to_csv(path, index=True, index_label='Index')
