"""Kivy Screens for the labslauncher application."""

from threading import Thread
import time
import webbrowser

from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
import pyperclip


class HomeScreen(Screen):
    """Home screen for application."""

    cstatus = StringProperty('unknown')
    address = StringProperty('')
    address_fmt = StringProperty('')

    def __init__(self, **kwargs):
        """Initialize the home screen."""
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def on_cstatus(self, *args):
        """Set state when container status changes."""
        self.containerlbl.text = "Server status: {}.".format(self.cstatus)

        self.startbtn.text = "Start"
        if self.cstatus in "running":
            self.startbtn.disabled = True
            self.stopbtn.disabled = False
        elif self.cstatus in (
                "created", "exited", "paused", "dead", "inactive"):
            self.startbtn.disabled = False
            self.stopbtn.disabled = True
            if self.cstatus != "inactive":
                self.startbtn.text = "Restart"

    def on_address(self, *args):
        """Set state when address changes."""
        if "unavailable" in self.address:
            self.address_fmt = self.address
        else:
            self.address_fmt = \
                "[color=2a7cdf][ref=click]{}[/ref][/color]".format(
                    self.address)

    def copy_address_to_clip(self, *args):
        """Copy server address to clipboard."""
        pyperclip.copy(self.address)

    def open_colab(self, *args):
        """Open our Google Colab landing page."""
        webbrowser.open(self.app.conf.COLABLINK)

    def goto_start_settings(self, *args):
        """Move GUI to start container screen."""
        self.manager.transition.direction = 'left'
        self.manager.current = 'start'


class LoadDialog(FloatLayout):
    """Layout to contain a filebrowser."""

    load = ObjectProperty()
    cancel = ObjectProperty()


class StartScreen(Screen):
    """Screen for starting and updating the server."""

    cstatus = StringProperty('unknown')
    data_mount = StringProperty('')
    token = StringProperty('')
    port = StringProperty('')

    def __init__(self, **kwargs):
        """Initialize start screen."""
        super().__init__(**kwargs)

        self.app = App.get_running_app()
        self.data_mount = self.app.get_config("data_mount")
        self.token = self.app.get_config("token")
        self.port = self.app.get_config("port")
        self.image = None

    def on_cstatus(self, *args):
        """Set state when container status changes."""
        msg = ""
        start_text = "Start"
        if self.cstatus == "inactive":
            pass
        elif self.cstatus in ("created", "exited"):
            msg = " (last attempt failed)"
            start_text = "Restart"

        self.startbtn.text = start_text
        self.containerlbl.text = 'Start server{}'.format(msg)

    def on_data_mount(self, *args):
        """Set config on data_mount property change."""
        self.app.set_config("data_mount", self.data_mount)

    def on_token(self, *args):
        """Set config on token property change."""
        self.app.set_config("token", self.token)

    def on_port(self, *args):
        """Set config on port property change."""
        self.app.set_config("port", self.port)

    def show_load(self):
        """Show the directory browser."""
        content = LoadDialog(load=self.load)
        self._popup = Popup(
            title="Select a data folder for server.",
            content=content, size_hint=(0.9, 0.9))
        content.cancel = self._popup.dismiss
        self._popup.open()

    def load(self, path, filename):
        """Set the data path."""
        self.data_mount = path
        self._popup.dismiss()

    def goto_home(self, *args):
        """Move GUI back to home screen."""
        self.manager.transition.direction = 'right'
        self.manager.current = 'home'

    def start_server(self, *args):
        """Start the server container."""
        self.data_mount = self.ids.datamount_input.text
        self.token = self.ids.token_input.text
        self.port = self.ids.port_input.text
        thread = Thread(target=self._start)
        thread.daemon = True
        thread.start()

    def update_server(self, *args):
        """Update the server container."""
        thread = Thread(target=self._pull_image, kwargs={'update': True})
        thread.daemon = True
        thread.start()

    def _start(self):
        """Worker for starting container and providing on screen feedback.

        Will trigger an image pull if the requested image tag is not
        available.
        """
        if self.app.image is None:
            # we don't have an image to run
            self._pull_image()

        self.app.start_container(
            self.data_mount, self.token, self.port)
        if self.cstatus == "running":
            self.goto_home()

    def _pull_image(self, update=False):
        # TODO: could use a kivy property and use callback to manage state
        self.startbtn.disabled = True
        self.updatebtn.disabled = True
        self.backbtn.disabled = True
        self.containerlbl.text = "Start server (downloading)"
        # Run pull in a thread to provide feedback
        func = self.app.ensure_image
        if update:
            self.app.image = None  # bit of a hack
            func = self.app.update_image
        thread = Thread(target=func)
        thread.daemon = True
        thread.start()
        # ...wait for pull to finish
        while self.app.image is None:
            time.sleep(1)
            self.containerlbl.text = \
                "Start server (downloading...{})".format(self.app.download)
        # pull finished
        self.containerlbl.text = "Start server"
        self.startbtn.disabled = False
        self.updatebtn.disabled = not self.app.can_update
        self.backbtn.disabled = False
