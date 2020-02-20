import docker


from kivy.core.window import Window
Window.size = (400, 200)

from kivy.app import App
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


class HomeScreen(Screen):


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = App.get_running_app()

        layout = BoxLayout(orientation='vertical')
        row0 = BoxLayout(height=50)
        row1 = BoxLayout()

        self.containerlbl = Label()
        self.set_status_label()
        row0.add_widget(self.containerlbl)

        startbtn = Button(text='Start', width=50)
        startbtn.bind(on_press=self.goto_start_settings)
        row1.add_widget(startbtn)

        stopbtn = Button(text='Stop', width=50)
        stopbtn.bind(on_release=self.stop_server)
        row1.add_widget(stopbtn)

        layout.add_widget(row0)
        layout.add_widget(row1)
        self.add_widget(layout)
        self.height=100

    def goto_start_settings(self, *args):
        self.manager.transition.direction = 'left'
        self.manager.current = 'start'


    def stop_server(self, *args):
        cont = self.app.container
        if cont is not None:
            self.set_status_label("Stopping")
            cont.kill()
            self.set_status_label("Removing")
            cont.remove()
            self.set_status_label()
        self.set_status_label()

    def set_status_label(self, status=None):
        if status is None:
            status = 'not running'
            if self.app.container is not None:
                status = self.app.container.status
        self.containerlbl.text = "Server status: {}.".format(status)



class StartScreen(Screen):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = App.get_running_app()

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
        startbtn = Button(text='Start')
        startbtn.bind(on_release=self.start_server)
        row.add_widget(startbtn)

        stopbtn = Button(text='Back', width=50)
        stopbtn.bind(on_release=self.goto_home)
        row.add_widget(stopbtn)

        layout = BoxLayout(orientation='vertical')
        for r in rows:
            layout.add_widget(r)
        self.add_widget(layout)

    def goto_home(self, *args):
        self.manager.transition.direction = 'right'
        self.manager.current = 'home'

    def start_server(self, *args):
        def _start():
            try:
                CMD = CONTAINERCMD + [
                    "--NotebookApp.token={}".format(self.token_input.text)]
                self.app.docker.containers.run(
                    CONTAINER,
                    CMD,
                    detach=True,
                    ports={PORTBIND:int(self.port_input.text)},
                    environment=['JUPYTER_ENABLE_LAB=yes'],
                    volumes={
                        self.datamount_input.text:{
                            'bind':DATABIND, 'mode':'rw'}},
                    name=SERVER_NAME)
            except Exception as e:
                return 1
            else:
                return 0

        cont = self.app.container
        status = None
        if cont is None:
            status = _start()
        elif cont.status in ("created", "exited"):
            cont.remove()
            status = _start()

        if status == 0:
            self.app.sm.get_screen('home').set_status_label()
            self.goto_home()
        else:
            self.containerlbl.text = 'Start server (last attempt failed)'


class LabsLauncherApp(App):


    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.docker = docker.from_env()

    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(HomeScreen(name='home'))
        self.sm.add_widget(StartScreen(name='start'))
        return self.sm

    @property
    def container(self):
        for cont in self.docker.containers.list(True):
            if cont.name == SERVER_NAME:
                return cont
        return None


if __name__ == '__main__':
    LabsLauncherApp().run()
