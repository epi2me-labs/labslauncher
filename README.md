# ont-labslauncher

Epi2Me Labs Server Control
created by cwright

Requirements:
* python3
* make
* docker

## Quick-start
```bash
git clone git@git.oxfordnanolabs.local:custflow/labslauncher.git
cd labslauncher
make run
```
This will open a dialogue box requesting:
* **data location**: A directory that you wish to be mounted containing your datasets (default: /data)
* **token**: A secret token to add to the URL in order to access the notebook (default: epi2me)
* **port**: Port that the notebook will be found on (default: 8888)
