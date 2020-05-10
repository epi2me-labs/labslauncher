"""Application for managing a notebook server."""
import os

from PyQt5 import sip  # noqa: F401


__version__ = "0.4.0"


class Defaults(list):
    """A helper class to create configuration data."""

    def __getitem__(self, key):
        """Retrieve list item, or the default value if key is a `str`.

        :param key: int or string.
        """
        if isinstance(key, int):
            return super().__getattr__[key]
        else:
            return self.by_key[key]["default"]
        raise KeyError()

    def get_type(self, key):
        """Return the python type of item.

        :param key: the key of the requested item.
        """
        return self.by_key[key]["type"]

    def get_description(self, key):
        """Return the description od an item.

        :param key: the key of the requested item.
        """
        return self.by_key[key]["desc"]

    def append(self, *values):
        """Append an item."""
        keys = ("title", "desc", "key", "default")
        data = dict(zip(keys, values))
        data["type"] = type(data["default"])
        data["section"] = self.section
        super().append(data)
        self.by_key[data["key"]] = data

    def __init__(self):
        """Initialize the class."""
        self.section = "epi2melabs-notebook"
        self.by_key = dict()
        self.append(
            "Image",
            "The container image to use from dockerhub.",
            "image_name", "ontresearch/nanolabs-notebook")
        self.append(
            "Fixed Tag",
            "Fix the container image to a specific tag.",
            "fixed_tag", "")
        self.append(
            "Server Name",
            "The name given to the actively running container.",
            "server_name", "Epi2Me-Labs-Server")
        self.append(
            "Data Mount",
            "Location on host computer accessible within notebooks.",
            "data_mount", os.path.expanduser("~"))
        self.append(
            "Data bind",
            "Location on server where host mount is accessible.",
            "data_bind", "/epi2melabs/")
        self.append(
            "Port",
            "Network port for communication between host and notebook server.",
            "port", 8888)
        self.append(
            "Security Token",
            "Security token for notebook server.",
            "token", "EPI2MELabs")
        self.append(
            "Container command.",
            "Command line arguments to run notebook server.",
            "container_cmd",
            "start-notebook.sh "
            " --NotebookApp.allow_origin='https://colab.research.google.com'"
            " --NotebookApp.disable_check_xsrf=True"
            " --NotebookApp.port_retries=0"
            " --no-browser"
            " --notebook-dir=/")
        self.append(
            "Colaboratory Homepage",
            "Link displayed for getting started.",
            "colab_link",
            "https://colab.research.google.com/github/epi2me-labs/"
            "resources/blob/master/welcome.ipynb")
        self.append(
            "Colaboratory help page",
            "Link to help page on Colaboratory.",
            "colab_help",
            "https://colab.research.google.com/github/epi2me-labs/"
            "resources/blob/master/epi2me-labs-server.ipynb")
        self.append(
            "Docker arguments",
            "Extra arguments to provide to `docker run`.",
            "docker_args", "")
        self.append(
            "Local access only",
            "Restrict access to notebook server to this computer only.",
            "docker_restrict", True)
        self.append(
            "Send pings",
            "Send usage statistics to ONT.",
            "send_pings", True)
