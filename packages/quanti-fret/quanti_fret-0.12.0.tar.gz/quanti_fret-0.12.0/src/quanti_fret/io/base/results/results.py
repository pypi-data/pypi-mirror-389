from quanti_fret.core import QtfException
from quanti_fret.io.base.results.stage import StageResults

from typing import Any
from pathlib import Path


class ResultsManager:
    """ Manage the saving of the different stages settings and results.
    """
    def __init__(self, stages_managers: dict[str, StageResults]) -> None:
        """Constructor

        Args:
            stages_managers (dict[str, StageResults]): Dictionary containing
                all the stages available to store the results, with their
                StageResults associated.
        """
        self._managers = stages_managers

    def save(
        self, stage: str, settings: tuple[Any, ...], results: tuple[Any, ...],
    ) -> None:
        """ Save the stage settings and results.

        Values saved and their order are described in each stage results
        implementation class. For the settings, we expect them to be the same
        as the ones returned by StageParams. For the results we expect the
        first elements to be the one to put in the Json files (also described
        in the stage's self._validators), in the same order. Trailing values
        will be for specific savings.

        Args:
            stage (str): Stage name. Must be a key from `self._managers`
            settings (tuple[Any, ...]): Settings to save
            results (tuple[Any, ...]): Results to save

        Raises:
            QtfException: If the stage is unknown.
        """
        if stage not in self._managers:
            err = f'No StageManager exists for stage "{stage}"'
            raise QtfException(err)
        self._managers[stage].save(settings, results)

    def save_index(
        self, stage: str, index: int, results: tuple[Any, ...],
    ) -> None:
        """ Save the stage results for a computation on a single index of the
        series.

        Values saved and their order are described in each stage results
        implementation class. For the results we expect them to be in the same
        order than the one returned by the function computing one index at a
        time.

        Args:
            stage (str): Stage name. Must be a key from `self._managers`
            index (int): Index of the element to save
            results (tuple[Any, ...]): Results to save
        """
        if stage not in self._managers:
            err = f'No StageManager exists for stage "{stage}"'
            raise QtfException(err)
        self._managers[stage].save_index(index, results)

    def get(
        self, stage: str
    ) -> tuple[tuple[Any, ...], tuple[Any, ...]] | None:
        """ Get the settings and results of the given stage

        Values returned are the one from the Json files, in the same order.
        They are also the one described in the stage's self._validators and
        class comments.

        Args:
            stage (str): Stage name in ['background', 'bt', 'de', 'xm']

        Raises:
            QtfException: If the stage is unknown.

        Returns:
            tuple[tuple[Any, ...], tuple[Any, ...]] | None:
                ((settings), (results)) or None if no results found
        """
        if stage not in self._managers:
            err = f'No StageManager exists for stage "{stage}"'
            raise QtfException(err)
        return self._managers[stage].get()

    def _check_output_dir(self, output_dir: Path) -> None:
        """ Check if the output dir is valid

        Args:
            output_dir (Path): path to test

        Raises:
            QtfException: If the output dir is invalid
        """
        if not isinstance(output_dir, Path):
            err = 'Output path is not an instance of Path'
            raise QtfException(err)
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        if not output_dir.is_dir():
            err = f'Output path {output_dir} exists and is not a directory'
            raise QtfException(err)
