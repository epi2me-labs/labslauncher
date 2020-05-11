"""Extras for Qt."""
import argparse
import sys
import threading
import traceback

from PyQt5.QtCore import (
    pyqtSignal as Signal, pyqtSlot as Slot, QObject, QRunnable, QSettings, Qt)
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QLabel


class Property(QObject):
    """A variable which emits its value when changed.

    For example:
        variable = Property("value")
        variable.connect(callback)
    """

    changed = Signal(object)

    def __init__(self, value):
        """Initialize the property."""
        super().__init__()
        self._value = value

    @property
    def value(self):
        """Return the value of the property."""
        return self._value

    @value.setter
    def value(self, new_val):
        """Set the value of the property."""
        self._value = new_val
        self.changed.emit(new_val)

    def __str__(self):
        """Retun string reprepresentation of property value."""
        return str(self._value)


class StringProperty(Property):
    """A Property which emits a string."""

    changed = Signal(str)


class BoolProperty(Property):
    """A Property which emits a bool."""

    changed = Signal(bool)


class FloatProperty(Property):
    """A Property which emits a float."""

    changed = Signal(float)


class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread.

    finished - no data
    error - tuple (exctype, value, traceback.format_exc() )
    result - object data returned from processing, anything
    progress - int indicating % progress
    """

    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(float)


class Worker(QRunnable):
    """A worker thread."""

    def __init__(self, fn, *args, **kwargs):
        """Initialize the worker.

        :param callback: function callback to run on this worker thread.
        :param args: arguments to pass to the callback function.
        :param kwargs: keyword arguments to pass to the callback function.

        To enable progress indicator the worker should accept a Qt Signal
        as a `progress` keyword argument. To enable stopping of the thread
        the function should accept a threading.Event as a `stopped` keyword
        argument.
        """
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['progress'] = self.signals.progress
        self.stopped = threading.Event()
        self.kwargs['stopped'] = self.stopped

    @Slot()
    def run(self):
        """Run the function."""
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

    def stop(self):
        """Signal the worker function to stop."""
        print("closing, setting stop")
        self.stopped.set()


class ClickLabel(QLabel):
    """A Label that can be clicked."""

    clicked = Signal()

    def __init__(self, parent=None):
        """Initialize the widget."""
        super().__init__(parent=parent)
        self.setStyleSheet(
                "color: blue; text-decoration: underline;")
        self.setFocusPolicy(Qt.NoFocus)
        self.setClickable(True)

    def mousePressEvent(self, event):
        """Emit clicked signal when pressed."""
        if self.enabled and event.button() == Qt.LeftButton:
            self.clicked.emit()
        else:
            super().mousePressEvent(event)

    def setClickable(self, enabled):
        """Set whether label is clickable.

        :param enabled: boolean.
        """
        self.enabled = enabled
        if self.enabled:
            self.setCursor(QCursor(Qt.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))


class Settings():
    """Wrapper around QSettings to provide defaults."""

    def __init__(self, specification):
        """Initialize settings.

        :param specification: an item like `labslauncher.Settings`.

        """
        self.qsettings = QSettings("EPIME Labs", "Launcher")
        self.spec = specification

        for item in self.spec:
            key = item["key"]
            if not self.qsettings.contains(key):
                self.qsettings.setValue(key, item["default"])
        self.overrides = None

    def __getitem__(self, key):
        """Get the value of a setting."""
        type = self.spec.get_type(key)
        if self.overrides is not None and self.overrides[key] is not None:
            value = self.overrides[key]
            if type == bool:
                value = bool(value)
        else:
            value = type(self.qsettings.value(key))
        return value

    def __setitem__(self, key, value):
        """Set the value of a setting."""
        self.qsettings.setValue(key, value)

    def override(self):
        """Set command line overrides."""
        self.parser = argparse.ArgumentParser()
        for item in self.spec:
            key = item["key"]
            arg_type = self.spec.get_type(key)
            if arg_type == bool:  # just to help parsing
                arg_type = int
            self.parser.add_argument(
                "--{}".format(key), type=arg_type,
                help=self.spec.get_description(key))
        self.overrides = vars(self.parser.parse_args())

    def clear_override(self):
        """Clear command line overrides."""
        self.overrides = None
