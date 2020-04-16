# ont-labslauncher

EPI2ME Labs Server Controller.

Requirements:
* python3
* docker
* virtualenv
* make

The last two are not strictly required to build and run the application
but are helpful for development

## Quick-start

```bash
git clone git@git.oxfordnanolabs.local:custflow/labslauncher.git
cd labslauncher
make run
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

A hidden feature is the ability to use the `latest` image tag for development
purposes, to do this run:

    labslauncher -- --latest

