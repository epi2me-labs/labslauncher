#!/usr/bin/env python
from threading import Thread
from time import sleep
import webbrowser

import docker

from kivy.core.window import Window
Window.size = (400, 200)

from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix import actionbar
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput


CONTAINER='ontresearch/nanolabs-notebook'
SERVER_NAME='Epi2Me-Labs-Server'
DATAMOUNT='/data/'
DATABIND='/home/jovyan/work'
PORTHOST=8888
PORTBIND=8888
LABSTOKEN='epi2me'
CONTAINERCMD=[
    "start-notebook.sh",
    "--NotebookApp.allow_origin='https://colab.research.google.com'",
    "--NotebookApp.disable_check_xsrf=True",
    "--port={}".format(PORTBIND),
    "--NotebookApp.port_retries=0",
    "--ip=0.0.0.0",
    "--no-browser",
    "--notebook-dir=./work"]
COLABLINK='https://colab.research.google.com/github/epi2me-labs/resources/blob/master/welcome.ipynb'


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

        self.add_widget(rows.layout)
        self.height=100

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
        elif self.cstatus in ("created", "exited", "paused", "dead", "inactive"):
            self.startbtn.disabled = False
            self.stopbtn.disabled = True
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
        for r in rows:
            layout.add_widget(r)
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

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.docker = docker.from_env()

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

        CMD = CONTAINERCMD + [
            "--NotebookApp.token={}".format(token)]

        try:
            self.docker.containers.run(
                CONTAINER,
                CMD,
                detach=True,
                ports={PORTBIND:int(port)},
                environment=['JUPYTER_ENABLE_LAB=yes'],
                volumes={
                    mount:{
                        'bind':DATABIND, 'mode':'rw'}},
                name=SERVER_NAME)
        except Exception as e:
            #TODO: better feedback on failure
            pass

        self.set_status()



if __name__ == '__main__':
    LabsLauncherApp().run()
