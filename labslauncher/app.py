"""LabsLauncher Application."""
import functools
import os
import sys
import uuid

import docker
from epi2melabs import ping
from kivy.config import Config
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'width', 400)
Config.set('graphics', 'height', 400)
import kivy  # noqa: I100  kivy requires Config needs to be first
from kivy.app import App
from kivy.logger import Logger
from kivy.properties import StringProperty
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.settings import SettingsWithTabbedPanel
from pkg_resources import resource_filename
from requests.exceptions import ConnectionError

import labslauncher
from labslauncher import iconfonts, screens, util


kivy.require('1.11.1')
iconfonts.register(
    'default_font',
    resource_filename('labslauncher', 'fontawesome-webfont.ttf'),
    resource_filename('labslauncher', 'fontawesome.fontd'))


class SpecialDocker(docker.client.DockerClient):
    """Wrapper around docker client class to add a method."""

    @property
    def is_running(self):
        """Bool for is docker is running or not."""
        try:
            self.from_env().version()
            return True
        except ConnectionError:
            return False


def main():
    """Entry point for application."""
    app = LabsLauncherApp()
    if '--latest' in sys.argv:
        # money patch to run 'latest' container
        app.current_image_tag = 'latest'
        app.safe_fetch_local_image()
    if '--no-pings' in sys.argv:
        app.disable_pings = True
    app.run()


class LabsLauncherApp(App):
    """LabsLauncher application class."""

    cstatus = StringProperty('unknown')
    address = StringProperty('unavailable')
    download = StringProperty('unknown')

    def __init__(self, *args, **kwargs):
        """Initialize the application."""
        self.version = labslauncher.__version__
        self.defaults = labslauncher.Settings()
        self.disable_pings = False
        # TODO: can read this from config
        self.session = uuid.uuid4()
        self.pinger = ping.Pingu(session=self.session)
        self._heartbeat = util.Heartbeat()
        super().__init__(*args, **kwargs)

    def get_application_config(self):
        """Return location of application configuration file."""
        return super().get_application_config(
            '~/.%(appname)s.ini')

    def build(self):
        """Build the application."""
        self.settings_cls = SettingsWithTabbedPanel
        self.icon = resource_filename('labslauncher', 'epi2me.ico')
        self.title = "EPI2ME-Labs Launcher"

        if not hasattr(self, '_current_image_tag'):
            self._current_image_tag = None
            self.__image = None
            if self.docker_is_running:
                r = self.fetch_latest_remote_tag()
                if r:  # we have the latest
                    self._current_image_tag = r
                else:
                    self._current_image_tag = self.dockerhub_image_tags[0]
            self.safe_fetch_local_image()
        Logger.info("Image tag: {}".format(self.current_image_tag))

        self.sm = ScreenManager()
        self.sm.add_widget(screens.HomeScreen(name='home'))
        self.sm.add_widget(screens.StartScreen(name='start'))

        for screen in ('home', 'start'):
            self.bind(cstatus=self.sm.get_screen(screen).setter('cstatus'))
        self.bind(address=self.sm.get_screen('home').setter('address'))
        if self.docker_is_running:
            self.set_status()
        else:
            self.cstatus = "Docker not running"
        return self.sm

    def build_config(self, config):
        """Set the default values for the config."""
        self.use_kivy_settings = False
        config.read(self.get_application_config())
        defaults = {obj["key"]: obj["default"] for obj in self.defaults}
        config.setdefaults(self.defaults.section, defaults)

    def build_settings(self, settings):
        """Add custom section to the default configuration object."""
        settings = labslauncher.Settings()
        settings.add_json_panel(
            'Settings', self.config, data=settings.kivy_json)

    def get_config(self, key):
        """Get a config item.

        :param key: the item name.

        """
        return self.config.get(self.defaults.section, key)

    def set_config(self, key, value):
        """Set a config item.

        :param key: the item name.
        :param value: new value of item.

        """
        self.config.set(self.defaults.section, key, value)
        self.config.write()

    @property
    def dockerhub_image_tags(self):
        """All available image tags on dockerhub."""
        return util.get_image_tags(self.get_config("container"))

    @property
    def docker(self):
        """Local docker instance."""
        return SpecialDocker.from_env()

    @staticmethod
    def docker_not_running_popup():
        """Create popup if docker service cannot be contacted."""
        msg = "Could not connect to docker."
        popup = Popup(
            title='Error:',
            content=Label(text=msg, shorten=True),
            size_hint=(0.9, 0.5))
        popup.open()

    @property
    def docker_is_running(self):
        """Check if docker is running or not."""
        return self.docker.is_running

    @property
    def image_name(self):
        """Return the image name for the requested tag."""
        if self.current_image_tag is None:
            raise ValueError("No local tag.")
        return "{}:{}".format(
            self.get_config("container"), self.current_image_tag)

    def fetch_latest_remote_tag(self):
        """Scrape the latest remote tag available locally."""
        return util.newest_tag(
            self.get_config("container"),
            tags=self.dockerhub_image_tags,
            client=self.docker)

    @property
    def current_image_tag(self):
        """Get the current image tag."""
        if self._current_image_tag is None and self.docker_is_running:
            self._current_image_tag = self.fetch_latest_remote_tag()
        return self._current_image_tag

    @current_image_tag.setter
    def current_image_tag(self, tag):
        """Change the current image tag."""
        self._current_image_tag = tag

    def fetch_local_image(self):
        """Get the docker image."""
        try:
            return self.docker.images.get(self.image_name)
        except Exception:
            raise docker.errors.ImageNotFound("No local image available.")

    def safe_fetch_local_image(self):
        """Set image attribute of this class.

        If the image is not found locally sets `None`.
        """
        try:
            self.image = self.fetch_local_image()
        except docker.errors.ImageNotFound:
            self.image = None

    @property
    def image(self):
        """Get the docker image object used by the app."""
        return self.__image

    @image.setter
    def image(self, image):
        """Set the docker image object used by the app."""
        self.__image = image

    def ensure_image(self):
        """Set image attribute of this class.

        If the image is not found locally the image is pulled.
        """
        self.image = None
        try:
            self.image = self.fetch_local_image()
        except docker.errors.ImageNotFound:
            self.image = self.pull_tag(self.current_image_tag)

    @property
    def can_update(self):
        """Determine if an updated image is available."""
        return self.dockerhub_image_tags[0] != self.current_image_tag

    def update_image(self):
        """Update the image to the newest tag."""
        self.image = None
        self.current_image_tag = self.dockerhub_image_tags[0]
        self.ensure_image()
        # if things succeeded this shouldn't do anything, else it will reset
        self.current_image_tag = self.fetch_latest_remote_tag()
        # TODO: this is a bit of a hack, should setup a Property and bind
        self.sm.get_screen('home').ids.versionlbl.text = \
            "Launcher Version: {}    Server Version: {}".format(
                self.version, self.current_image_tag)

    @property
    def container(self):
        """Return the server container if one is present, else None."""
        if self.docker_is_running:
            for cont in self.docker.containers.list(True):
                if cont.name == self.get_config("server_name"):
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
            new_address = "http://localhost:{}?token={}".format(port, token)
        self.address = new_address

    def clear_container(self, *args):
        """Kill and remove the server container."""
        cont = self.container
        if cont is not None:
            if not self.disable_pings:
                self.pinger.send_container_ping('stop', cont, self.image_name)
            if cont.status == "running":
                cont.kill()
            cont.remove()
        # no harm stopping regardless of conditionals above
        self._heartbeat.stop()
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
            behaviour check .fetch_local_image() first.
        """
        host_only = self.get_config('docker_restrict')
        if not self.check_inputs(mount, token, port):
            return

        self.clear_container()
        CMD = self.get_config("container_cmd").split() + [
            "--NotebookApp.token={}".format(token),
            "--port={}".format(port),
            ]

        try:
            # note: colab requires the port in the container to be equal
            ports = {int(port): int(port)}
            if host_only:
                ports = {int(port): ('127.0.0.1', int(port))}
            Logger.info("Docker: {}".format(ports))
            self.docker.containers.run(
                self.image_name,
                CMD,
                detach=True,
                ports=ports,
                environment=['JUPYTER_ENABLE_LAB=yes'],
                volumes={
                    mount: {
                        'bind': self.get_config("data_bind"), 'mode': 'rw'}},
                name=self.get_config("server_name"))
        except Exception as e:
            # TODO: better feedback on failure
            print(e)
            pass
        self.set_status()
        if not self.disable_pings:
            self.pinger.send_container_ping(
                'start', self.container, self.image_name)
            callback = functools.partial(
                self.pinger.send_container_ping,
                'update', self.container, self.image_name)
            self._heartbeat.start(callback)

    def pull_tag(self, tag):
        """Pull an image tag.

        :param tag: tag to fetch.

        :returns: the image object.

        """
        image_tag = util.get_image_tag(self.get_config("container"), tag)
        total = image_tag['full_size']

        # to get feedback we need to use the low-level API
        self.download = '{:.1f}%'.format(0)
        for current, total in util.pull_with_progress(
                self.get_config("container"), tag):
            self.download = '{:.1f}%'.format(100 * current / total)
        self.download = "100%"
        image = self.docker.images.get(
            '{}:{}'.format(self.get_config("container"), tag))
        return image
