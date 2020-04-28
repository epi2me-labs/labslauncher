"""Miscellaneous utility functions to support labslauncher application."""

import functools
import json
import threading
import time

import docker
import requests
import semver


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


def get_image_tag(image, tag):
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
    image_tag = get_image_tag(image, tag)
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


class Heartbeat():
    """Run a function on an interval."""

    def __init__(self):
        """Initialize the class."""
        self._running = threading.Event()

    def __del__(self):
        """Stop the thread if running."""
        self.stop()

    def start(self, callback, interval=1200):
        """Start running a function.

        :param callback: the function to run.
        :param interval: interval inseconds between calls.

        The first call to the function will be after the first interval has
        elapsed.
        """
        self.stop()
        self._running.set()
        self._thread = threading.Thread(
            target=self._runner, args=(callback, interval))
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        """Stop running the function."""
        if self._running.is_set():
            self._running.clear()
            self._thread.join()

    def _runner(self, callback, interval):
        t0 = time.time()
        while self._running.is_set():
            time.sleep(1)
            now = time.time()
            if t0 + interval < now:
                callback()
                t0 = now
