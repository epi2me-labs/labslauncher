"""Kivy Screens for the labslauncher application."""

from threading import Thread
import time
import webbrowser

from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
import pyperclip


class BoxRows(list):
    """Helper to generate a boxy kivy layout."""

    def new_row(self):
        """Add and return a new row."""
        r = BoxLayout()
        self.append(r)
        return r

    @property
    def layout(self):
        """Generate the layout."""
        layout = BoxLayout(orientation='vertical')
        for r in self:
            layout.add_widget(r)
        return layout


class HomeScreen(Screen):
    """Home screen for application."""

    cstatus = StringProperty('unknown')

    def __init__(self, **kwargs):
        """Initialize the home screen."""
        super().__init__(**kwargs)

        self.app = App.get_running_app()

        rows = BoxRows()

        row = rows.new_row()
        self.containerlbl = Label()
        row.add_widget(self.containerlbl)

        row = rows.new_row()
        self.startbtn = Button(text='Start', width=50)
        self.startbtn.bind(on_press=self.goto_start_settings)
        row.add_widget(self.startbtn)

        self.stopbtn = Button(text='Stop', width=50)
        self.stopbtn.bind(on_release=self.app.clear_container)
        row.add_widget(self.stopbtn)

        row = rows.new_row()
        helptext = Label(
            text="Navigate to the [color=2a7cdf][ref=click]"
                 "Welcome page[/ref][/color] to get started.",
            markup=True)
        helptext.bind(on_ref_press=self.open_colab)
        row.add_widget(helptext)

        def copy_button_press(button):
            button.text = button.text.replace("Copy", "Copied")

        row = rows.new_row()
        self.copy_button = Button(text=self.app.local_address, width=50)
        self.copy_button.bind(on_press=self.copy_local_address_to_clipboard)
        self.copy_button.bind(on_release=copy_button_press)
        row.add_widget(self.copy_button)

        self.add_widget(rows.layout)
        self.height = 100

    def copy_local_address_to_clipboard(self, *args):
        """Copy server address to clipboard."""
        pyperclip.copy(self.app.local_address)

    def open_colab(self, *args):
        """Open our Google Colab landing page."""
        webbrowser.open(self.app.conf.COLABLINK)

    def goto_start_settings(self, *args):
        """Move GUI to start container screen."""
        self.manager.transition.direction = 'left'
        self.manager.current = 'start'

    def on_cstatus(self, *args):
        """Set state when container status changes."""
        self.containerlbl.text = "Server status: {}.".format(self.cstatus)

        self.startbtn.text = "Start"
        if self.cstatus in "running":
            self.startbtn.disabled = True
            self.stopbtn.disabled = False
            if self.app.local_address == "Local address unavailable":
                self.copy_button.disabled = True
                self.copy_button.text = self.app.local_address
            else:
                self.copy_button.disabled = False
                self.copy_button.text = "Copy \"{}\" to clipboard".format(
                    self.app.local_address)
        elif self.cstatus in (
                "created", "exited", "paused", "dead", "inactive"):
            self.startbtn.disabled = False
            self.stopbtn.disabled = True
            self.copy_button.disabled = True
            if self.cstatus != "inactive":
                self.startbtn.text = "Restart"


class StartScreen(Screen):
    """Screen for starting and updating the server."""

    cstatus = StringProperty('unknown')
    start_status = StringProperty('Start server')

    def __init__(self, **kwargs):
        """Initialize start screen."""
        super().__init__(**kwargs)

        self.app = App.get_running_app()
        self.image = None

        rows = BoxRows()

        row = rows.new_row()
        self.containerlbl = Label(text=self.start_status)
        self.bind(start_status=self.containerlbl.setter('text'))
        row.add_widget(self.containerlbl)

        row = rows.new_row()
        row.add_widget(Label(text='data location'))
        self.datamount_input = TextInput(
            text=self.app.conf.DATAMOUNT)
        row.add_widget(self.datamount_input)

        row = rows.new_row()
        row.add_widget(Label(text='token'))
        self.token_input = TextInput(
            text=self.app.conf.LABSTOKEN)
        row.add_widget(self.token_input)

        row = rows.new_row()
        row.add_widget(Label(text='port'))
        self.port_input = TextInput(
            text=str(self.app.conf.PORTHOST))
        row.add_widget(self.port_input)

        row = rows.new_row()
        self.startbtn = Button(text='Start')
        self.startbtn.bind(on_release=self.start_server)
        row.add_widget(self.startbtn)

        self.backbtn = Button(text='Back', width=50)
        self.backbtn.bind(on_release=self.goto_home)
        row.add_widget(self.backbtn)

        self.add_widget(rows.layout)

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

    def goto_home(self, *args):
        """Move GUI back to home screen."""
        self.manager.transition.direction = 'right'
        self.manager.current = 'home'

    def start_server(self, *args):
        """Start the server container."""
        # create thread external to GUI loop
        thread = Thread(target=self._start)
        thread.daemon = True
        thread.start()

    def _start(self):
        """Worker for starting container and providing on screen feedback.

        Will trigger an image pull if the requested image tag is not
        available.
        """
        if self.app.image is None:
            # we don't have the required tag
            self.startbtn.disabled = True
            self.backbtn.disabled = True
            self.containerlbl.text = "Start server (downloading)"
            # Run pull in a thread to provide feedback
            thread = Thread(target=self.app.ensure_image)
            thread.daemon = True
            thread.start()
            # ...wait for pull to finish
            prog = r'|/-\|-/-'
            pi = 0
            font = self.startbtn.font_name
            self.startbtn.font_name = "RobotoMono-Regular"
            while self.app.image is None:
                time.sleep(1)
                symbol = prog[pi % len(prog)]
                pi += 1
                self.startbtn.text = "Download...{}".format(symbol)
            # pull finished
            self.startbtn.font_name = font
            self.startbtn.disabled = False
            self.backbtn.disabled = False

        self.app.start_container(
            self.datamount_input.text, self.token_input.text,
            int(self.port_input.text), self.app.im_request)
        if self.cstatus == "running":
            self.goto_home()
