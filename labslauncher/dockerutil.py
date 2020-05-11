"""Miscellaneous utility functions to support labslauncher application."""

import functools
import json

import docker
from PyQt5.QtCore import QTimer
import requests
import semver

from labslauncher import qtext


def get_image_tags(image, prefix='v'):
    """Retrieve tags from dockerhub of an image.

    :param image: image name, organisation/repository.
    :param prefix: prefix by which to filter images.

    :returns: sorted list of tags, newest first, ordered by semver.
    """
    addr = 'https://hub.docker.com/v2/repositories/{}/tags'.format(image)
    response = requests.get(addr)
    tags_data = json.loads(response.content.decode())
    if any(tags_data[x] is not None for x in ['next', 'previous']):
        raise ValueError('Tags data was paginated.')

    tags = list()
    for t in tags_data['results']:
        name = t['name']
        if name[0] != prefix:
            continue
        try:
            semver.parse(name[1:])
        except ValueError:
            continue
        else:
            tags.append(name[1:])
    ordered_tags = [
        '{}{}'.format(prefix, x) for x in
        sorted(
            tags, reverse=True,
            key=functools.cmp_to_key(semver.compare))]
    return ordered_tags


def get_image_meta(image, tag):
    """Retrieve meta data from docker hub for a tag.

    :param image: image name.
    :param tag: image tag.

    """
    addr = 'https://hub.docker.com/v2/repositories/{}/tags'.format(image)
    response = requests.get(addr)
    tags_data = json.loads(response.content.decode())
    if any(tags_data[x] is not None for x in ['next', 'previous']):
        raise ValueError('Tags data was paginated.')

    for t in tags_data['results']:
        name = t['name']
        if name == tag:
            return t
    raise IndexError("Tag was not found: \"{}\"".format(tag))


def newest_tag(image, tags=None, client=None):
    """Find the newest available local tag of an image.

    :param tag: list of tags, if None dockerhub is queried.
    :param client: a docker client.
    """
    if client is None:
        client = docker.from_env()
    if tags is None:
        tags = get_image_tags(image)

    latest = None
    for tag in tags:
        try:
            client.images.get("{}:{}".format(image, tag))
        except docker.errors.ImageNotFound:
            pass
        else:
            latest = tag
            break
    return latest


def pull_with_progress(image, tag):
    """Pull an image, yielding download progress.

    :param image: image name.
    :param tag: image tag.

    :yields: downloaded bytes, total bytes.

    """
    image_tag = get_image_meta(image, tag)
    total = image_tag['full_size']

    # to get feedback we need to use the low-level API
    client = docker.APIClient()

    layers = dict()
    pull_log = client.pull(image, tag=tag, stream=True)
    for response in (x.decode() for x in pull_log):
        for line in response.splitlines():
            resp = json.loads(line)
            if "status" in resp and resp["status"] == "Downloading":
                layers[resp['id']] = resp["progressDetail"]["current"]
                current = sum(layers.values())
                yield current, total


class DockerClient():
    """Handle interaction with docker."""

    status = qtext.Property(('', 'unknown'))
    tag = qtext.StringProperty('')
    _available = qtext.BoolProperty(False)

    def __init__(
            self, image_name, server_name, data_bind, container_cmd,
            host_only, fixed_tag=None):
        """Initialize the client."""
        self.image_name = image_name
        self.server_name = server_name
        self.data_bind = data_bind
        self.container_cmd = container_cmd
        self.host_only = host_only
        self.fixed_tag = fixed_tag
        self._client = None
        self.total_size = None
        self.final_stats = None
        self.is_running()  # sets up tag, status, and available
        self.heartbeat = QTimer()
        self.heartbeat.setInterval(1000*5)  # 5 seconds
        self.heartbeat.start()
        self.heartbeat.timeout.connect(self.is_running)

    @property
    def docker(self):
        """Return a connected docker client."""
        if self._client is None:
            try:
                self._client = docker.client.DockerClient.from_env()
            except Exception:
                pass
        try:
            self._client.version()
        except Exception:
            self._client = None
            raise ConnectionError("Could not communicate with docker.")
        return self._client

    def is_running(self):
        """Return whether docker is connected.

        Note if True value does not guaranteed subsequent API calls
        will necessarily succeed.
        """
        try:
            value = self.docker is not None
        except ConnectionError:
            value = False
        if value != self._available.value:
            self._available.value = value
            if value:
                self.tag.value = self.latest_available_tag
                self.set_status()
            else:
                self.tag.value = 'unknown'
                self.set_status('unknown')
        return self._available.value

    @property
    def latest_tag(self):
        """Return the latest tag on dockerhub."""
        if self.fixed_tag is not None:
            return self.fixed_tag
        return get_image_tags(self.image_name)[0]

    @property
    def latest_available_tag(self):
        """Return the latest tag available locally."""
        if self.fixed_tag is not None:
            return self.fixed_tag
        return newest_tag(self.image_name, client=self.docker)

    @property
    def update_available(self):
        """Return whether an updated tag available on dockerhub."""
        if not self._available.value:
            return False
        return self.latest_available_tag != self.latest_tag

    def full_image_name(self, tag=None):
        """Return the image name for the requested tag.

        :param tag: requested tag. If not given the moset recent local
            tag is returned.
        """
        if tag is None:
            tag = self.latest_available_tag
        if tag is None:
            raise ValueError("No local tag.")
        return "{}:{}".format(self.image_name, tag)

    def image(self, tag=None, update=False):
        """Return the docker image.

        :param tag: request specific tag. If not given the most recent local
            image is returned unless `update` is `True`.
        :param update: override `tag` and pull latest image from dockerhub.

        :returns: a docker `Image` or None if request cannot be fulfilled.
        """
        if tag is None:
            tag = self.latest_available_tag
        if update:
            tag = self.latest_tag
        name = self.full_image_name(tag=tag)

        image = None
        try:
            image = self.docker.images.get(name)
        except docker.errors.ImageNotFound:
            if update:
                image = self.pull_image(tag)
        return image

    def pull_image(self, tag=None, progress=None, stopped=None):
        """Pull an image tag whilst updating download progress.

        :param tag: tag to fetch. If None the latest tag is pulled.

        :returns: the image object.

        """
        if tag is None:
            tag = self.latest_tag
        full_name = self.full_image_name(tag=tag)

        # to get feedback we need to use the low-level API
        self.total_size = None
        for current, total in pull_with_progress(self.image_name, tag):
            if stopped is not None and stopped.is_set():
                return None
            if progress is not None:
                progress.emit(100 * current / total)
            self.total_size = total
        progress.emit(100.0)
        image = self.docker.images.get(full_name)
        self.tag.value = self.latest_available_tag
        return image

    @property
    def container(self):
        """Return the server container if one is present, else None."""
        try:
            for cont in self.docker.containers.list(True):
                if cont.name == self.server_name:
                    return cont
        except Exception:
            pass
        return None

    def start_container(self, mount, token, port):
        """Start the server container, removing a previous one if necessary.

        .. note:: The behaviour of docker.run is that a pull will be invoked if
            the image is not available locally. To ensure more controlled
            behaviour check .fetch_local_image() first.
        """
        self.clear_container()
        CMD = self.container_cmd.split() + [
            "--NotebookApp.token={}".format(token),
            "--port={}".format(port)]

        try:
            # note: colab requires the port in the container to be equal
            ports = {int(port): int(port)}
            if self.host_only:
                ports = {int(port): ('127.0.0.1', int(port))}
            self.docker.containers.run(
                self.full_image_name(),
                CMD,
                detach=True,
                ports=ports,
                environment=['JUPYTER_ENABLE_LAB=yes'],
                volumes={
                    mount: {
                        'bind': self.data_bind, 'mode': 'rw'}},
                name=self.server_name)
        except Exception as e:
            self.last_failure = str(e).replace("b'", "").replace("'\"", "\"")
        self.final_stats = None
        self.set_status()

    def clear_container(self, *args):
        """Kill and remove the server container."""
        cont = self.container
        if cont is not None:
            if cont.status == "running":
                self.final_stats = cont.stats(stream=False)
                cont.kill()
            cont.remove()
        self.set_status()

    def set_status(self, new=None):
        """Set the container status property."""
        # store the old and the new status
        if self._available.value and new is None:
            c = self.container
            new = "inactive" if c is None else c.status
        self.status.value = (self.status.value[1], new)
