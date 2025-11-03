from quanti_fret.algo import (
    compute_background, BTCalculator, DECalculator, XMCalculator,
    FretCalculator
)
from quanti_fret.core import QtfSeries
from quanti_fret.io import IOManager

from typing import Any, Callable


class QtfRunner:
    """ Manage the run of all the differents stages of the QuanTI-FRET
    algorithm.

    It gets its inputs and save its outputs using the IOPhaseManager passed to
    the constructor.
    """
    def __init__(self, iom: IOManager):
        """Constructor

        Args:
            iom (IOPhaseManager): IOManager to get params and retrive the
                results of each stage run for each phase.
        """
        self._iom = iom
        self._bt_calculator = BTCalculator()
        self._de_calculator = DECalculator()
        self._xm_calculator = XMCalculator()
        self._fret_calculator = FretCalculator()

    def run_all(self) -> None:
        """ Run the QuanTI-FRET stages
        """
        self.run_calibration()
        self.run_fret()

    def run_calibration(self) -> None:
        """ Run the QuanTI-FRET calibration stages
        """
        self.run_background()
        self.run_bt()
        self.run_de()
        self.run_xm()

    def run_background(self) -> None:
        """Run the Background computation

        Raises:
            QtfException: If it can't be run.
        """
        params = self._iom.cali.params.get('background')
        result = (compute_background(*params[1:]),)
        self._iom.cali.results.save('background', params, result)

    def run_bt(self) -> None:
        """Run the BT calculation

        Raises:
            QtfException: If it can't be run.
        """
        params = self._iom.cali.params.get('bt')
        result = self._bt_calculator.run(*params[1:])  # type: ignore
        self._iom.cali.results.save('bt', params, result)

    def run_de(self) -> None:
        """Run the DE calculation

        Raises:
            QtfException: If it can't be run.
        """
        params = self._iom.cali.params.get('de')
        result = self._de_calculator.run(*params[1:])  # type: ignore
        self._iom.cali.results.save('de', params, result)

    def run_xm(self) -> None:
        """Run the XM calculation

        Raises:
            QtfException: If it can't be run.
        """
        params = self._iom.cali.params.get('xm')
        result = self._xm_calculator.run(*params[1:])  # type: ignore
        self._iom.cali.results.save('xm', params, result)

    def run_fret(self, callback: Callable[[str], None] | None = None) -> None:
        """Run the Fret calculation on the whole dataset

        Args:
            callback (Callable[[str], None]): Callback that will be called
                between each steps to inform the user of the progress. Please
                note that the run will be paused while the callback is being
                called.

        Raises:
            QtfException: If it can't be run.
        """
        def notify(msg: str):
            if callback is not None:
                callback(msg)
        notify('Initialization')
        params = self._iom.fret.params.get('fret')
        self._fret_calculator.series_reset()
        self._fret_calculator.series_params(*params[2:])  # type: ignore
        series: QtfSeries = params[1]
        index = 1
        max = series.size()
        for seq in series:
            notify(f'Computing Fret ({index}/{max})')
            seq_results = self._fret_calculator.series_next(seq.triplets[0])
            self._iom.fret.results.save_index('fret', index, seq_results)
            index += 1
        notify('Performing analysis')
        results_ = self._fret_calculator.series_analysis()
        results: tuple[Any, ...] = ()
        if results_ is not None:
            results = results_
        notify('Saving results')
        self._iom.fret.results.save('fret', params, results)
        notify('Done')
