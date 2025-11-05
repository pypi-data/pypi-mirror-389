""" Run the QuanTI-FRET GUI or CLI application.
"""
from quanti_fret.apps.cli import CliController
from quanti_fret.io import CalibrationConfig, FretConfig

import argparse
import os
import sys


def run_gui():
    """Run the gui application
    """
    from quanti_fret.apps.gui import QtfMainWidget
    from qtpy.QtWidgets import (
        QApplication,
        QMainWindow,
    )

    class QtfWindow(QMainWindow):
        """ Qt Window that host the main QuanTI-FRET widget.
        """
        def __init__(self):
            super().__init__()
            self.setWindowTitle("QuanTI-FRET")
            centralWidget = QtfMainWidget()
            self.setCentralWidget(centralWidget)

    app = QApplication([])
    window = QtfWindow()
    window.show()
    sys.exit(app.exec())


def run_cli(phase: str, config_path: os.PathLike | str):
    """Run the CLI application

    Args:
        phase (str): Phase of the config to run the app on
        config_path (os.PathLike | str): Path to the config file
    """
    if phase == 'calibration':
        controller = CliController(calibration_config_path=config_path)
        controller.run_calibration()
    else:
        controller = CliController(fret_config_path=config_path)
        controller.run_fret()


def parse_args() -> argparse.Namespace:
    """Parse the command line arguments.

    The parser provide an optionnal subcommand `cli` that invoke the CLI
    application of the GUI one.

    Returns:
        argparse.Namespace: populated namespace
    """
    # Parser
    parser = argparse.ArgumentParser(
        description='Run the QuanTI-FRET GUI application')
    subs = parser.add_subparsers(dest='command', required=False)

    # Subcommand for the CLI
    cli = subs.add_parser('cli', description='run the cli mode instead')
    cli.add_argument(
        'phase', type=str, choices=['calibration', 'fret'],
        help='In what phase to run the app.'
    )
    cli.add_argument(
        'config_file', type=str, help='Path to the config file'
    )

    # Subcommand for the config generation
    config = subs.add_parser('generate_config',
                             description='Generate a default config')
    config.add_argument(
        'phase', type=str, choices=['calibration', 'fret'],
        help='For what phase to generate the config.'
    )
    config.add_argument(
        'config_file', type=str,
        help='Path to the file to write the default config in'
    )

    # Parse args
    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == 'generate_config':
        if args.phase == 'calibration':
            config = CalibrationConfig()
        else:
            config = FretConfig()
        config.set_default()
        config.save(args.config_file)
    elif args.command == 'cli':
        run_cli(args.phase, args.config_file)
    else:
        run_gui()


if __name__ == "__main__":
    main()
