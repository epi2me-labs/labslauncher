PROJECT  ?= ont-epi2melabs-launcher
MAJOR    ?= 0
MINOR    ?= 1
SUB      ?= 1
PATCH    ?= 0
VERSION   ="$(MAJOR).$(MINOR).$(SUB)"
CODENAME ?= $(shell awk -F= '/CODENAME/{print $$2}' /etc/lsb-release)
DEB	  ="$(PROJECT)-$(MAJOR).$(MINOR).$(SUB)-$(PATCH)~$(CODENAME).deb"
MD5SUM    = md5sum
SEDI      = sed -i

ifeq ($(shell uname), Darwin)
        MD5SUM = md5 -r
        SEDI   = sed -i ""
endif

PYTHON ?= python

IN_VENV=. ./venv/bin/activate

venv/bin/activate:
	test -d venv || virtualenv venv --python=$(PYTHON) --prompt "(build) "
	${IN_VENV} && pip install pip --upgrade
	${IN_VENV} && pip install -r requirements.txt

testenv: venv/bin/activate

test: venv/bin/activate
	${IN_VENV} && pip install flake8 flake8-rst-docstrings flake8-docstrings flake8-import-order
	${IN_VENV} && flake8 labslauncher --import-order-style google --application-import-names labslauncher --statistics

dist/Epi2MeLabs-Launcher: venv/bin/activate
	${IN_VENV} && xvfb-run pyinstaller labslauncher --onefile -n Epi2MeLabs-Launcher --hidden-import cython


.PHONY: run
run: venv/bin/activate
	${IN_VENV} && python setup.py develop && labslauncher


.PHONY: build
build: dist/Epi2MeLabs-Launcher


.PHONY: clean
clean:
	rm -rf Epi2MeLabs-Launcher.spec __pycache__ dist build venv
	rm -rf tmp *.deb


deb: clean dist/Epi2MeLabs-Launcher
	mkdir -p deb-src/usr/local/bin
	mkdir -p deb-src/usr/share/applications
	cp dist/Epi2MeLabs-Launcher deb-src/usr/local/bin/
	cp labslauncher.desktop deb-src/usr/share/applications
	cp -rp deb-src/ tmp/
	$(SEDI) "s/PROJECT/$(PROJECT)/g"   tmp/DEBIAN/control
	$(SEDI) "s/MAJOR/$(MAJOR)/g"       tmp/DEBIAN/control
	$(SEDI) "s/MINOR/$(MINOR)/g"       tmp/DEBIAN/control
	$(SEDI) "s/SUB/$(SUB)/g"           tmp/DEBIAN/control
	$(SEDI) "s/PATCH/$(PATCH)/g"       tmp/DEBIAN/control
	$(SEDI) "s/CODENAME/$(CODENAME)/g" tmp/DEBIAN/control
	$(SEDI) "s/STREAM/$(STREAM)/g"     tmp/DEBIAN/control
	find tmp -type f ! -regex '.*\(\bDEBIAN\b\|\bdeb-src\b\|\).*' -exec $(MD5SUM) {} \; | sed 's/tmp\///' > tmp/DEBIAN/md5sums
	chmod -R 755 tmp/DEBIAN
	chmod 644 tmp/DEBIAN/md5sums
	(cd tmp; fakeroot dpkg -b . ../$(DEB))
	dpkg -I $(DEB)
	dpkg -c $(DEB)

