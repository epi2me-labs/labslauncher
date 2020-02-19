
venv: venv/bin/activate
IN_VENV=. ./venv/bin/activate

venv/bin/activate:
	test -d venv || virtualenv venv --python=python3.6 --prompt "(build) "
	${IN_VENV} && pip install pip --upgrade
	${IN_VENV} && pip install -r requirements.txt


dist/Epi2MeLabs-Launcher: venv
	${IN_VENV} && pyinstaller labslauncher.py --onefile -n Epi2MeLabs-Launcher --hidden-import docker


.PHONY: run
run: venv 
	${IN_VENV} && python labslauncher.py


.PHONY: build
build: dist/Epi2MeLabs-Launcher

.PHONY: clean
clean:
	rm -rf Epi2MeLabs-Launcher.spec __pycache__ dist build venv
