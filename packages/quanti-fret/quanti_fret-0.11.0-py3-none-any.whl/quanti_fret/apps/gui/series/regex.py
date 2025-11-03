from quanti_fret.apps.gui.io_gui_manager import IOGuiManager
from quanti_fret.io import TripletSequenceLoader

from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class RegexBox(QFrame):
    """ Widget allowing you to set the regex for all the triplets' files path

    It has a title that you can click to show or hide the regex settings.

    I comes with a reload button allowing the user to reload all the series
    once all the regexes have been set

    Can emit the following signals:
        * reloadTriggered: The reload series button have been triggered
    """
    reloadTriggered = Signal()

    def __init__(self, phase: str, *args, **kwargs) -> None:
        """ Constructor

        Args:
            phase (str): phase associated with the regexes
        """
        super().__init__(*args, **kwargs)

        self._phase = phase

        # Build GUI
        self._mainLayout = QVBoxLayout()
        self._mainLayout.setContentsMargins(0, 7, 0, 7)
        self._mainLayout.setSpacing(0)
        self.setLayout(self._mainLayout)
        self._buildTitle()
        self._buildContent()

        # Connect Slots
        self._arrow.clicked.connect(
            lambda: self._swapContentVisibility(self._arrow)
        )
        self._title.clicked.connect(
            lambda: self._swapContentVisibility(self._title)
        )

    def _buildTitle(self) -> None:
        """ Build the title / button of the widget
        """
        # Title Layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._mainLayout.addLayout(layout)

        # Arrow button
        # (This could have been in the self._title but I didn't manage to
        # reduce the size of just the arrow so I'm making two QToolButton)
        self._arrow = QToolButton(self)
        self._arrow.setArrowType(Qt.ArrowType.RightArrow)
        self._arrow.setCheckable(True)
        self._arrow.setChecked(False)
        self._arrow.setStyleSheet("QToolButton { border: none; }")
        layout.addWidget(self._arrow)

        # Title
        self._title = QToolButton(self)
        self._title.setText('Regexes')
        self._title.setCheckable(True)
        self._title.setChecked(False)
        self._title.setStyleSheet("QToolButton { border: none; }")
        layout.addWidget(self._title)

        # Adjust arrow size
        self._arrow.setMaximumHeight(int(self._title.height()/2.5))

    def _buildContent(self) -> None:
        """ Build the content of the widget
        """
        # Create content widget
        self._content = QWidget(self)
        self._content.hide()
        self._mainLayout.addWidget(self._content)

        # Content layout
        layout = QVBoxLayout()
        layout.setSpacing(2)
        self._content.setLayout(layout)

        # Regex widgets
        widgets = [
            RegexWidget(self._phase, 'dd', self._content),
            RegexWidget(self._phase, 'da', self._content),
            RegexWidget(self._phase, 'aa', self._content),
            RegexWidget(self._phase, 'mask_cell', self._content),
            RegexWidget(self._phase, 'mask_bckg', self._content),
        ]
        width = max([w.getTitleWidth() for w in widgets])
        for w in widgets:
            w.setTitleWidth(width)
            layout.addWidget(w)

        # Reload button
        buttonLayout = QHBoxLayout()
        buttonLayout.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addLayout(buttonLayout)
        reloadButton = QPushButton('Reload Series', self._content)
        buttonLayout.addWidget(reloadButton)
        reloadButton.clicked.connect(lambda: self.reloadTriggered.emit())

    def _swapContentVisibility(self, button: QToolButton) -> None:
        """ Swap visibility of the widget's content

        Args:
            button (QToolButton): Button that was clicked
        """
        visible = button.isChecked()
        self._arrow.setChecked(visible)
        self._title.setChecked(visible)
        if visible:
            self._content.show()
            self._arrow.setArrowType(Qt.ArrowType.DownArrow)
            self.setStyleSheet("RegexBox {border :1px solid gray;}")
        else:
            self._content.hide()
            self._arrow.setArrowType(Qt.ArrowType.RightArrow)
            self.setStyleSheet("RegexBox {border :0px;}")


class RegexWidget(QWidget):
    """ Handle the setting of a regex

    Will display a title alongside with a line edit that will update the config
    on change.
    """

    def __init__(
        self, phase: str, config_key: str, *args, **kwargs
    ) -> None:
        """ Constructor

        Args:
            phase (str): Phase linked with the scanner.
            config_key (str): Key associated in the config.
        """
        super().__init__(*args, **kwargs)

        self._phase = phase
        self._config_key = config_key
        self._iopm = IOGuiManager().get_iopm(phase)

        self._buildGui()

        self._iopm.stateChanged.connect(self._updatedConfig)
        self._updatedConfig()

    def setTitleWidth(self, width: int) -> None:
        """ Set the width of the title

        This function helps having all regex title sharing the same width

        Args:
            width (int): width to set
        """
        self._title.setMinimumWidth(width)
        self._title.setMaximumWidth(width)

    def getTitleWidth(self) -> int:
        """ Get the current width of the title

        This function helps having all regex title sharing the same width

        Returns:
            int: The width of the title
        """
        return self._title.minimumSizeHint().width()

    def _buildGui(self) -> None:
        """ Build the GUI
        """
        # Layout
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        self._title = QLabel(f'{self._config_key.upper()}:', self)
        layout.addWidget(self._title)

        # Line Edit
        self._lineEdit = QLineEdit(self)
        self._lineEdit.setPlaceholderText(
            TripletSequenceLoader.DEFAULT_REGEX_PATTERNS[
                f'{self._config_key}_path'
            ]
        )
        self._lineEdit.setMaxLength(100)
        layout.addWidget(self._lineEdit)
        self._lineEdit.editingFinished.connect(self._updateRegex)

    def _updatedConfig(self) -> None:
        """ Update the line edit with the value from the config
        """
        self._lineEdit.blockSignals(True)
        val = self._iopm.config.get('Regex', self._config_key)
        self._lineEdit.setText(val)
        self._lineEdit.blockSignals(False)

    def _updateRegex(self) -> None:
        """ Update the config with the value from the widget
        """
        val = self._lineEdit.text()
        self._iopm.config.set('Regex', self._config_key, val)
