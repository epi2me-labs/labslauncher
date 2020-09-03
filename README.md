# ont-labslauncher

EPI2ME Labs Server Controller.

## Packages

Prebuilt packages for Windows, macOS, and Ubuntu are available on the [release](https://github.com/epi2me-labs/labslauncher/releases/latest).

## Development

Requirements:
* python3
* docker
* virtualenv
* make

The last two are not strictly required to build and run the application
but are helpful for development

To build and run the application:

```bash
git clone https://github.com/epi2me-labs/labslauncher.git
cd labslauncher
PYTHON=python3 make run
```

This will:
* create a python virtual environment
* install python requirements
* install the application with inplace (develop) installation
* run the application

After running the above once, the entrypoint `labslauncher` can be used to run
the application.

The applicaiton provides basic control over starting and stopping a docker
container and updating the image used. Images are pulled from dockerhub, with
the application detecting the newest version available. Updates to the newest
image are not forced, the newest image locally available will be used.

A hidden feature is the ability to use an arbitrary image tag for development
purposes, to do this run:

    labslauncher --fixed_tag latest --send_pings 0
    
The `--send_pings 0` stops both the launcher and notebooks from sending pings
(the launcher writes a piece of config in the notebook container to disable
pings).

