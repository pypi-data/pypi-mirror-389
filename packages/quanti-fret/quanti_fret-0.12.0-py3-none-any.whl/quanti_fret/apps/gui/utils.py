""" Module for utility widgets that can be reused for the application.

It contains:
    * class LoadingAnimationLayout
        A layout containing a widget that can show a loading animation
"""

from qtpy.QtCore import Qt, QTimer
from qtpy.QtGui import QPainter, QPaintEvent
from qtpy.QtWidgets import (
    QDoubleSpinBox,
    QLabel,
    QVBoxLayout,
    QWidget
)

from quanti_fret.algo import (
    BackgroundEngine, BackgroundEnginePercentile, BackgroundEngineFixed
)


class PercentileSpinBox(QDoubleSpinBox):
    """ SpinBox for percentile
    """
    def __init__(self, *args, **kwargs):
        """ Constructor
        """
        super().__init__(*args, **kwargs)
        self.setRange(0.0, 100.0)
        self.setSingleStep(0.1)


class BackgroundEngineLabel(QLabel):
    """ Label whose purpose is to display a Background engine.

    It will display: "Background: {mode} ({Extra})" or "Background: -" is no
    background.
    """
    def __init__(
        self, *args, preText: str = 'Background: ', postText: str = '',
        **kwargs
    ):
        """ Constructor

        Args:
            pre_text (str): Text to display before the background
            post_text (str): Text to display after the background
        """
        super().__init__(*args, **kwargs)
        self._preText = preText
        self._postText = postText

    def setBackgroundEngine(self, engine: BackgroundEngine | None) -> None:
        """ Display the given background engine

        Args:
            engine (BackgroundEngine | None): Engine to display. If None,
                display (-) instead
        """
        text = self._preText
        if engine is None:
            text += ' - '
        else:
            text += f' {engine.mode}'
            if isinstance(engine, BackgroundEnginePercentile):
                text += f' ({engine._percentile})'
            elif isinstance(engine, BackgroundEngineFixed):
                text += f' {engine.background}'
        text += self._postText
        self.setText(text)


class PathLabel(QLabel):
    """ Label whose purpose is to display a Path.

    When `setText` is called, it:
        - It will crop (on the left) the text passed to the given width
        - Add the string "Path: " in front of it
        - Add as a hovering tooltip the whole path
    """
    def __init__(self, *args, max_len: int = 250, **kwargs):
        """ Constructor

        Args:
            max_len (int, optional): max len of the path. Defaults to 250.
        """
        super().__init__(*args, **kwargs)
        self._max_width = max_len

    def setText(self, a0: str | None) -> None:
        self.setToolTip(a0)
        font = self.fontMetrics()
        cropped = font.elidedText(a0, Qt.TextElideMode.ElideLeft,
                                  self._max_width)
        super().setText(f"Path: {cropped}")


class EyeWidget(QWidget):
    """ Widget with a Eye drawn on top of it to represent the idea of
    viewing an object
    """

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """ Paint the button

        Args:
            a0 (QPaintEvent | None): Associated QPaintEvent
        """
        def round_to_even(val: float | int) -> int:
            return int(val / 2.) * 2

        super().paintEvent(a0)

        # Prepare coordinates
        frame_w = self.width()
        frame_h = self.height()
        center_x = int(frame_w / 2.)
        center_y = int(frame_h / 2.)
        pupil_size = round_to_even(frame_h * 0.3)
        border_height = round_to_even(frame_h * 0.4)
        border_width = round_to_even(frame_w * 0.4)
        border_width = min(border_width, border_height * 2)

        # Setup the painter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = painter.pen().color()
        painter.setBrush(color)
        pen = painter.pen()
        pen.setWidth(1)
        painter.setPen(pen)

        # Draw eye pupil
        painter.save()
        width = pupil_size
        height = pupil_size
        x = int(center_x - (width / 2))
        y = int(center_y - (height / 2))
        painter.drawEllipse(x, y, width, height)
        painter.restore()

        # Draw eye border
        painter.save()
        height = border_height
        width = border_width
        x = int(center_x - (width / 2))
        y = int(center_y - (height / 2))
        painter.drawArc(x, y, width, height, 0, 360*16)
        painter.restore()


class LoadingProgressWidget(QLabel):
    """ Widget that displays a loading animation alongside a a text describing
    the progress.

    The Animation consist of the progress text surrounded with "dots". The
    number of dots change over time to give an idea of something running in
    background.

    By default the widget is hidden. You can call `start()` to show the widget
    and start the animation. And you can call `stop()` to hide the widget and
    stop the animation.

    Call `setProgress()` to change the text to be displayed on the widget
    """
    def __init__(self, interval: int = 1000) -> None:
        """ Constructor

        Args:
            interval (int): interval in ms between two frames
        """
        super().__init__()

        # Animation
        self._interval = interval
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.updateAnimation)
        self._text = ''
        self._min_dots = 0
        self._max_dots = 4
        self._dots = self._min_dots

        # GUI
        self.hide()

    def start(self) -> None:
        """ Shows the widget and starts the animation
        """
        self._text = 'Initializing'
        self._displayProgress()
        self._timer.start(self._interval)
        self.show()

    def stop(self) -> None:
        """ Hides the widget and stops the animation
        """
        self._timer.stop()
        self._text = ''
        self.hide()

    def setProgress(self, progress: str) -> None:
        """ Set The progress message to be displayed alongside the animation

        Args:
            progress (str): Message to display
        """
        self._text = progress
        self._displayProgress()

    def updateAnimation(self) -> None:
        """ Update the animation by adding or removing dots
        """
        self._dots += 1
        if self._dots > self._max_dots:
            self._dots = self._min_dots
        self._displayProgress()

    def _displayProgress(self):
        """ Format the text to be displayed in the label and display it.
        """
        text = f'{'.' * self._dots} {self._text} {'.' * self._dots}'
        self.setText(text)


class LoadingProgressLayout(QVBoxLayout):
    """ Layout containing a LoadingProgressWidget that can display a loading
    animation associated along side with a text indicating a progress.

    This class is just a layout containing the widget. It exists to be prevent
    the user to be forced to create a loayout.

    You can put this layout inside another widget or layout. By default the
    widget is hidden. You can call `start()` to show the widget and start the
    animation. And you can call `stop()` to hide the widget and stop the
    animation. Finally, you can call `setProgress()` to set the progress
    message.
    """
    def __init__(self, interval: int = 1000) -> None:
        """ Constructor

        Args:
            interval (int): interval in ms between two frames
        """
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._widget = LoadingProgressWidget(interval)
        self.addWidget(self._widget)

    def start(self) -> None:
        """ Shows the widget and starts the animation
        """
        self._widget.start()

    def stop(self) -> None:
        """ Hides the widget and stops the animation
        """
        self._widget.stop()

    def setProgress(self, progress: str) -> None:
        """ Set The progress message to be displayed alongside the animation

        Args:
            progress (str): Message to display
        """
        self._widget.setProgress(progress)


class LoadingAnimationWidget(QWidget):
    """ Widget that displays a loading animation

    By default the widget is hidden. You can call `start()` to show the widget
    and start the animation. And you can call `stop()` to hide the widget and
    stop the animation.
    """
    def __init__(self, interval: int = 50) -> None:
        """ Constructor

        Args:
            interval (int): interval in ms between two frames
        """
        super().__init__()

        # Animation
        self._angle = 0
        self._interval = interval
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.updateAnimation)

        # GUI
        self.hide()

    def start(self) -> None:
        """ Shows the widget and starts the animation
        """
        self._timer.start(self._interval)
        self.show()

    def stop(self) -> None:
        """ Hides the widget and stops the animation
        """
        self._timer.stop()
        self.hide()

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """ Paint the animation for a single frame

        Args:
            a0 (QPaintEvent | None): Associated QPaintEvent
        """
        # Compute Geometry
        frame_w = self.width()
        frame_h = self.height()
        square_size = min(frame_w, frame_h)
        circle_size = square_size / 6
        dist = int(square_size / 4)
        max_size = int(circle_size)

        # Setup the painter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(frame_w / 2, frame_h / 2)
        color = painter.pen().color()
        painter.setBrush(color)

        # Draw each circles
        for i in range(4):
            painter.save()
            angle = (self._angle - 40 * i) % 360
            new_size = int(max_size / (2**i))
            painter.rotate(angle)
            painter.drawEllipse(*self._toRectCoordonates(dist, new_size))
            painter.restore()

    def _toRectCoordonates(
        self, dist: int, size: int
    ) -> tuple[int, int, int, int]:
        """Transform coordinates representing the distance to the center of
        the circle and its size to a rect coordinates

        Args:
            dist (int): distance of the center of the circle to the center of
                the frame.
            size (int): size of the circle

        Returns:
            tuple[int, int, int, int]: Rectangle frame in which to draw the
                circle.
        """
        x = int(dist - size / 2)
        y = 0
        w = size
        h = size
        return x, y, w, h

    def updateAnimation(self) -> None:
        """ Update the animation by moving the circles angle
        """
        self._angle = (self._angle + 10) % 360
        self.update()


class LoadingAnimationLayout(QVBoxLayout):
    """ Layout containing a LoadingAnimationWidget that can display a loading
    animation.

    This class is just a layout containing the widget. It exists to be prevent
    the user to be forced to create a loayout.

    You can put this layout inside another widget or layout. By default the
    widget is hidden. You can call `start()` to show the widget and start the
    animation. And you can call `stop()` to hide the widget and stop the
    animation.
    """
    def __init__(self, interval: int = 50) -> None:
        """ Constructor

        Args:
            interval (int): interval in ms between two frames
        """
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self._widget = LoadingAnimationWidget(interval)
        self.addWidget(self._widget)

    def start(self) -> None:
        """ Shows the widget and starts the animation
        """
        self._widget.start()

    def stop(self) -> None:
        """ Hides the widget and stops the animation
        """
        self._widget.stop()
