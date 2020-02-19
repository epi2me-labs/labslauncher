import docker

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label


CONTAINER='ontresearch/nanolabs-notebook'
SERVER_NAME='Epi2Me-Labs-Server'
DATAMOUNT='/Users/cwright/git/nanolabs/labfolder/'
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
    "--NotebookApp.token={}".format(LABSTOKEN),
    "--notebook-dir=./work"]


class LabsLauncher(FloatLayout):


    def __init__(self, **kwargs):
        super(LabsLauncher, self).__init__(**kwargs)

        self.docker = docker.from_env()

        layout = BoxLayout(orientation='vertical')
        row0 = BoxLayout(height=50)
        row1 = BoxLayout()

        self.containerlbl = Label(text="Done", width=100)
        self.set_status_label()
        row0.add_widget(self.containerlbl)

        startbtn = Button(text='Start', width=50)
        startbtn.bind(on_release=self.start_server)
        row1.add_widget(startbtn)

        stopbtn = Button(text='Stop', width=50)
        stopbtn.bind(on_release=self.stop_server)
        row1.add_widget(stopbtn)

        layout.add_widget(row0)
        layout.add_widget(row1)
        self.add_widget(layout)
        self.height=100


    def start_server(self, args):
        def _start():
            self.docker.containers.run(
                CONTAINER,
                CONTAINERCMD,
                detach=True,
                ports={PORTBIND:PORTHOST},
                environment=['JUPYTER_ENABLE_LAB=yes'],
                volumes={DATAMOUNT:{'bind':DATABIND, 'mode':'rw'}},
                name=SERVER_NAME)

        cont = self.container
        if cont is None:
            _start()
        elif cont.status in ("created", "exited"):
            cont.remove()
            _start()
        cont = self.container
        self.set_status_label()

    def stop_server(self, args):
        cont = self.container
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
            if self.container is not None:
                status = self.container.status
        self.containerlbl.text = "Server status: {}.".format(status)

    @property
    def container(self):
        for cont in self.docker.containers.list(True):
            if cont.name == SERVER_NAME:
                return cont
        return None


class LabsLauncherApp(App):
    def build(self):
        return LabsLauncher()


if __name__ == '__main__':
    Window.size = (300, 100)
    LabsLauncherApp().run()
