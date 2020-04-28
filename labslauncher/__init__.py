"""Application for managing a notebook server."""
import json

__version__ = "0.3.2"


class Settings(list):
    """A helper class to create configuration data."""

    @property
    def settings(self):
        """Return the configuration as a list of dictionaries."""
        keys = ("type", "title", "desc", "key", "default")
        return [dict(zip(keys, values)) for values in self]

    @property
    def kivy_json(self):
        """Return the configuration as a json string for kivy."""
        # kivy isn't happy with extra default key, so take it out
        return json.dumps([
            {k: v for k, v in self.settings.items() if k != "default"}])

    def __init__(self):
        """Initialize the class."""
        self.section = "epi2melabs-notebook"
        # note: booleans should have 0/1 not False/True!
        self.append(
            "string", "Image",
            "The container image to use from dockerhub",
            "container", "ontresearch/nanolabs-notebook")
        self.append(
            "string", "Server Name",
            "The name given to the actively running container.",
            "server_name", "Epi2Me-Labs-Server")
        self.append(
            "string", "Data Mount",
            "Location on host computer accessible within notebooks.",
            "data_mount", "/data/")
        self.append(
            "string", "Data bind",
            "Location on server where host mount is accessible.",
            "data_bind", "/epi2melabs/")
        self.append(
            "numeric", "Port",
            "Network port for communication between host and notebook server.",
            "port", 8888)
        self.append(
            "string", "Security Token",
            "Security token for notebook server.",
            "token", "epi2me")
        self.append(
            "string", "Container command.",
            "Command line arguments to run notebook server.",
            "container_cmd",
            "start-notebook.sh "
            " --NotebookApp.allow_origin='https://colab.research.google.com'"
            " --NotebookApp.disable_check_xsrf=True"
            " --NotebookApp.port_retries=0"
            " --no-browser"
            " --notebook-dir=/")
        self.append(
            "string", "Colaboratory Homepage",
            "Link displayed for getting started.",
            "colab_link",
            "https://colab.research.google.com/github/epi2me-labs/"
            "resources/blob/master/welcome.ipynb")
        self.append(
            "string", "Docker arguments",
            "Extra arguments to provide to `docker run`.",
            "docker_args", "")
        self.append(
            "bool", "Local access only",
            "Restrict access to notebook server to this computer only.",
            "docker_restrict", 1)

    def append(self, type, title, desc, key, default):
        """Append an item."""
        super().append({
            "type": type, "title": title, "desc": desc, "key": key,
            "section": self.section,
            "default": default})
