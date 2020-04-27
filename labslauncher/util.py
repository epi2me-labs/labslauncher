"""Miscellaneous utility functions to support labslauncher application."""

import functools
import json
import platform
import socket
import uuid

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


def _send_ping(data):
    """Send a ping to home.

    :param data: a dictionary containing the data to send (should be
        json serializable).

    :returns: status code of HTTP request.
    """
    url = 'https://ping.oxfordnanoportal.com/epilaby'
    ping_version = '1.0.0'
    ping = {
        "tracking_id": {"msg_id": str(uuid.uuid4()), "version": ping_version},
        "hostname": socket.gethostname(), "os": platform.platform()}
    ping.update(data)
    try:
        r = requests.post(url, json=ping)
    except Exception as e:
        print(e)
    return r.status_code


def send_container_ping(action, container, image_name):
    """Ping a status message of a container.

    :param action: one of 'start' or 'stop'.
    :param container: a docker `Container` object.
    :param image_tag: the name of the image associated with the container.

    :returns: status code of HTTP request.
    """
    allowed_status = {"start", "stop"}
    if action not in allowed_status:
        raise ValueError("`action` was not an allowed value.")
    return _send_ping({
        "action": action,
        "container_data": container.stats(stream=False),
        "image_data": image_name})
