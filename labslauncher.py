#!/usr/bin/env python
import webbrowser

import docker
from kivy.app import App
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput
import pyperclip

CONTAINER = 'ontresearch/nanolabs-notebook'
SERVER_NAME = 'Epi2Me-Labs-Server'
DATAMOUNT = '/data/'
DATABIND = '/home/jovyan/work'
PORTHOST = 8888
PORTBIND = 8888
LABSTOKEN = 'epi2me'
CONTAINERCMD = [
    "start-notebook.sh",
    "--NotebookApp.allow_origin='https://colab.research.google.com'",
    "--NotebookApp.disable_check_xsrf=True",
    "--NotebookApp.port_retries=0",
    "--ip=0.0.0.0",
    "--no-browser",
    "--notebook-dir=./work"]
COLABLINK = 'https://colab.research.google.com/github/epi2me-labs/resources/blob/master/welcome.ipynb'


Window.size = (400, 200)


class BoxRows(list):
    def new_row(self):
        r = BoxLayout()
        self.append(r)
        return r

    @property
    def layout(self):
        layout = BoxLayout(orientation='vertical')
        for r in self:
            layout.add_widget(r)
        return layout


class HomeScreen(Screen):
    cstatus = StringProperty('unknown')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = App.get_running_app()

        self.bind(cstatus=self.on_status_change)

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
            text="Navigate to the [color=2a7cdf][ref=click]Welcome page[/ref][/color] to get started.",
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
        pyperclip.copy(self.app.local_address)

    def open_colab(self, *args):
        webbrowser.open(COLABLINK)

    def goto_start_settings(self, *args):
        self.manager.transition.direction = 'left'
        self.manager.current = 'start'

    def on_status_change(self, *args):
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
                self.copy_button.text = "Copy \"{}\" to clipboard".format(self.app.local_address)
        elif self.cstatus in ("created", "exited", "paused", "dead", "inactive"):
            self.startbtn.disabled = False
            self.stopbtn.disabled = True
            self.copy_button.disabled = True
            if self.cstatus != "inactive":
                self.startbtn.text = "Restart"


class StartScreen(Screen):
    cstatus = StringProperty('unknown')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = App.get_running_app()
        self.bind(cstatus=self.on_status_change)

        rows = list()

        def new_row():
            r = BoxLayout()
            rows.append(r)
            return r

        row = new_row()
        self.containerlbl = Label(text='Start server.')
        row.add_widget(self.containerlbl)

        row = new_row()
        row.add_widget(Label(text='data location'))
        self.datamount_input = TextInput(text=DATAMOUNT)
        row.add_widget(self.datamount_input)

        row = new_row()
        row.add_widget(Label(text='token'))
        self.token_input = TextInput(text=LABSTOKEN)
        row.add_widget(self.token_input)

        row = new_row()
        row.add_widget(Label(text='port'))
        self.port_input = TextInput(text=str(PORTHOST))
        row.add_widget(self.port_input)

        row = new_row()
        self.startbtn = Button(text='Start')
        self.startbtn.bind(on_release=self.start_server)
        row.add_widget(self.startbtn)

        stopbtn = Button(text='Back', width=50)
        stopbtn.bind(on_release=self.goto_home)
        row.add_widget(stopbtn)

        layout = BoxLayout(orientation='vertical')
        for single_row in rows:
            layout.add_widget(single_row)
        self.add_widget(layout)

    def on_status_change(self, *args):
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
        self.manager.transition.direction = 'right'
        self.manager.current = 'home'

    def start_server(self, *args):
        self.app.start_container(
            self.datamount_input.text, self.token_input.text,
            int(self.port_input.text))
        if self.cstatus == "running":
            self.goto_home()


class LabsLauncherApp(App):

    cstatus = StringProperty('unknown')
    _local_address = "Local address unavailable"

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.docker = docker.from_env()

    @property
    def local_address(self):
        return self._local_address

    def set_local_address(self, port=PORTBIND, token=LABSTOKEN):
        local_address_format = "http://localhost:{}?token={}"
        self._local_address = local_address_format.format(port, token)

    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(HomeScreen(name='home'))
        self.sm.add_widget(StartScreen(name='start'))

        for screen in ('home', 'start'):
            self.bind(cstatus=self.sm.get_screen(screen).setter('cstatus'))
        self.set_status()

        return self.sm

    @property
    def container(self):
        for cont in self.docker.containers.list(True):
            if cont.name == SERVER_NAME:
                return cont
        return None

    def set_status(self):
        c = self.container
        new_status = 'inactive'
        if c is not None:
            new_status = c.status
        if new_status != self.cstatus:
            self.cstatus = new_status

    def clear_container(self, *args):
        cont = self.container
        if cont is not None:
            if cont.status == "running":
                cont.kill()
            cont.remove()
        self.set_status()

    def start_container(self, mount, token, port):
        self.clear_container()

        # colab required the port in the container to be equal
        CMD = CONTAINERCMD + [
            "--NotebookApp.token={}".format(token),
            "--port={}".format(port),
            ]

        try:
            self.docker.containers.run(
                CONTAINER,
                CMD,
                detach=True,
                ports={int(port):int(port)},
                environment=['JUPYTER_ENABLE_LAB=yes'],
                volumes={
                    mount: {
                        'bind': DATABIND, 'mode': 'rw'}},
                name=SERVER_NAME)
            self.set_local_address(port=port, token=token)
        except Exception as e:
            #TODO: better feedback on failure
            pass

        self.set_status()



if __name__ == '__main__':
    LabsLauncherApp().run()
