"""Application for managing a notebook server."""

__version__ = "0.0.1"


class LauncherConfig():
    """Hold some state for the application."""

    CONTAINER = 'ontresearch/nanolabs-notebook'
    SERVER_NAME = 'Epi2Me-Labs-Server'
    DATAMOUNT = '/data/'
    DATABIND = '/epi2melabs'
    PORTHOST = 8888
    PORTBIND = 8888
    LABSTOKEN = 'epi2me'
    CONTAINERCMD = [
        "start-notebook.sh",
        "--NotebookApp.allow_origin='https://colab.research.google.com'",
        "--NotebookApp.disable_check_xsrf=True",
        "--NotebookApp.port_retries=0",
        "--ip=0.0.0.0",
        "--no-browser",
        "--notebook-dir=/"]
    COLABLINK = 'https://colab.research.google.com/github/' \
                'epi2me-labs/resources/blob/master/welcome.ipynb'
