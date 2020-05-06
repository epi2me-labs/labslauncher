"""Miscellaneous utility functions to support labslauncher application."""
import platform
import socket
import uuid

import requests


ENDPOINT = 'https://ping.oxfordnanoportal.com/epilaby'


def _send_ping(data, session):
    """Attempt to send a ping to home.

    :param data: a dictionary containing the data to send (should be
        json serializable).

    :returns: status code of HTTP request.
    """
    if not isinstance(session, uuid.UUID):
        raise ValueError('`session` should be a uuid.UUID object')
    ping_version = '1.0.0'
    ping = {
        "tracking_id": {"msg_id": str(uuid.uuid4()), "version": ping_version},
        "hostname": socket.gethostname(), "os": platform.platform(),
        "session": str(session)}
    ping.update(data)
    try:
        r = requests.post(ENDPOINT, json=ping)
    except Exception as e:
        print(e)
        pass
    return r.status_code


def send_container_ping(action, stats, image_name, session, message=None):
    """Ping a status message of a container.

    :param action: one of 'start', 'stop', or 'update'.
    :param container: the result of `.stats(stream=False)` of a
        `docker.Container` instance.
    :param image_tag: the name of the image associated with the container.

    :returns: status code of HTTP request.
    """
    allowed_status = {"start", "stop", "update"}
    if action not in allowed_status:
        raise ValueError(
            "`action` was not an allowed value, got: '{}'".format(action))
    return _send_ping({
        "source": "container",
        "action": action,
        "container_data": stats,
        "image_data": image_name,
        "message": message},
        session)
