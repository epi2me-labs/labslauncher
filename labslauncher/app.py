"""LabsLauncher Application."""
import os
import sys

import docker
from kivy.config import Config
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'width', 400)
Config.set('graphics', 'height', 400)
import kivy  # noqa: I100  kivy requires Config needs to be first
from kivy.app import App
from kivy.config import Config
from kivy.garden import iconfonts
from kivy.properties import StringProperty
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager
from pkg_resources import resource_filename

from labslauncher import LauncherConfig, screens, util


kivy.require('1.11.1')
iconfonts.register(
    'default_font',
    resource_filename('labslauncher', 'fontawesome-webfont.ttf'),
    resource_filename('labslauncher', 'fontawesome.fontd'))


def main():
    """Entry point for application."""
    app = LabsLauncherApp()
    if '--latest' in sys.argv:
        # money patch to run 'latest' container
        app.im_request = 'latest'
        app.set_image()
    app.run()


class LabsLauncherApp(App):
    """LabsLauncher application class."""

    cstatus = StringProperty('unknown')
    address = StringProperty('unavailable')
    download = StringProperty('unknown')

    def __init__(self, *args, **kwargs):
        """Initialize the application."""
        super().__init__(**kwargs)
        self.docker = docker.from_env()
        self.conf = LauncherConfig()

        # a list of all tags on dockerhub
        self.im_tags = util.get_image_tags(self.conf.CONTAINER)
        # the newest tag available locally
        self.im_request = util.newest_tag(
            self.conf.CONTAINER, tags=self.im_tags, client=self.docker)
        if self.im_request is None:
            # nothing available, request newest
            self.im_request = self.im_tags[0]
        # set self.image to the newest local image, or None
        # if nothing available
        self.set_image()

    def build(self):
        """Build the application."""
        self.icon = resource_filename('labslauncher', 'epi2me.ico')
        self.title = "Epi2MeLabs Launcher"
        self.sm = ScreenManager()
        self.sm.add_widget(screens.HomeScreen(name='home'))
        self.sm.add_widget(screens.StartScreen(name='start'))

        for screen in ('home', 'start'):
            self.bind(cstatus=self.sm.get_screen(screen).setter('cstatus'))
        self.bind(address=self.sm.get_screen('home').setter('address'))
        self.set_status()
        return self.sm

    @property
    def image_name(self):
        """Return the image name for the requested tag."""
        if self.im_request is None:
            raise ValueError("No local tag available.")
        return "{}:{}".format(self.conf.CONTAINER, self.im_request)

    def get_image(self):
        """Get the docker image."""
        try:
            return self.docker.images.get(self.image_name)
        except Exception:
            raise docker.errors.ImageNotFound("No local image available.")

    def set_image(self):
        """Set image attribute of this class.

        If the image is not found locally sets `None`.
        """
        try:
            self.image = self.get_image()
        except docker.errors.ImageNotFound:
            self.image = None

    def ensure_image(self):
        """Set image attribute of this class.

        If the image is not found locally the image is pulled.
        """
        self.image = None
        try:
            self.image = self.get_image()
        except docker.errors.ImageNotFound:
            self.image = self.pull_tag(self.im_request)

    @property
    def can_update(self):
        """Determine if an updated image is available."""
        return self.im_tags[0] != self.im_request

    def update_image(self):
        """Update the image to the newest tag."""
        self.image = None
        self.im_request = self.im_tags[0]
        self.ensure_image()

    @property
    def container(self):
        """Return the server container if one is present, else None."""
        for cont in self.docker.containers.list(True):
            if cont.name == self.conf.SERVER_NAME:
                return cont
        return None

    def set_status(self):
        """Set the container status property."""
        c = self.container
        new_status = 'inactive'
        if c is not None:
            new_status = c.status
        if new_status != self.cstatus:
            self.cstatus = new_status

    def on_cstatus(self, *args):
        """Update state on container status change."""
        # find port and token
        new_address = 'Server address unavailable'
        if self.container is not None and self.cstatus == 'running':
            cargs = self.container.__dict__['attrs']['Args']
            for c in cargs:
                if c.startswith('--port='):
                    port = int(c.split('=')[1])
                elif c.startswith('--NotebookApp.token='):
                    token = c.split('=')[1]
            new_address = "http://localhost:{}?token={}".format(
                port, token)
        self.address = new_address

    def clear_container(self, *args):
        """Kill and remove the server container."""
        cont = self.container
        if cont is not None:
            if cont.status == "running":
                cont.kill()
            cont.remove()
        self.set_status()

    @staticmethod
    def check_inputs(mount, token, port):
        """Create popup warning box if mount/token/port are invalid."""
        msg = None
        if not os.path.exists(mount):
            msg = "Mount path does not exist"
        elif not token:
            msg = "Please enter a value for 'Token'"
        elif not port:
            msg = "Port must be a number."
        elif token.isnumeric():
            msg = "Token must contain letters"
        if msg is not None:
            popup = Popup(
                title='Invalid Settings:',
                content=Label(text=msg, shorten=True),
                size_hint=(0.9, 0.5))
            popup.open()
            return False
        else:
            return True

    def start_container(self, mount, token, port):
        """Start the server container, removing a previous one if necessary.

        .. note:: The behaviour of docker.run is that a pull will be invoked if
            the image is not available locally. To ensure more controlled
            behaviour check .get_image() first.
        """
        if not self.check_inputs(mount, token, port):
            return

        self.clear_container()
        # colab requires the port in the container to be equal
        CMD = self.conf.CONTAINERCMD + [
            "--NotebookApp.token={}".format(token),
            "--port={}".format(port),
            ]

        try:
            self.docker.containers.run(
                self.image_name,
                CMD,
                detach=True,
                ports={int(port): int(port)},
                environment=['JUPYTER_ENABLE_LAB=yes'],
                volumes={
                    mount: {
                        'bind': self.conf.DATABIND, 'mode': 'rw'}},
                name=self.conf.SERVER_NAME)
        except Exception as e:
            # TODO: better feedback on failure
            print(e)
            pass
        self.set_status()

    def pull_tag(self, tag):
        """Pull an image tag.

        :param tag: tag to fetch.

        :returns: the image object.

        """
        image_tag = util.get_image_tag(self.conf.CONTAINER, tag)
        total = image_tag['full_size']

        # to get feedback we need to use the low-level API
        self.download = '{:.1f}%'.format(0)
        for current, total in util.pull_with_progress(
                self.conf.CONTAINER, tag):
            self.download = '{:.1f}%'.format(100 * current / total)
        self.download = "100%"
        image = self.docker.images.get(
            '{}:{}'.format(self.conf.CONTAINER, tag))
        return image
