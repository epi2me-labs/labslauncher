"""LabsLauncher Application."""

import sys

import docker
from kivy.app import App
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager

from labslauncher import LauncherConfig, screens, util

Window.size = (400, 150)


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
        # set self.image to the newest local image, or None
        # if nothing available
        self.set_image()

    def build(self):
        """Build the application."""
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

    def start_container(self, mount, token, port):
        """Start the server container, removing a previous one if necessary.

        .. note:: The behaviour of docker.run is that a pull will be invoked if
            the image is not available locally. To ensure more controlled
            behaviour check .get_image() first.
        """
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
        """Pull an image tag."""
        name = "{}:{}".format(self.conf.CONTAINER, tag)
        return self.docker.images.pull(name)
