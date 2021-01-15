# CI sets MAJOR.MINOR.PATCH for git tags
NOCOLAB  ?= 0
DEBNAME  ?= ont-epi2melabs-launcher
ifeq ($(NOCOLAB), 0)
	PROJECT = $(DEBNAME)
	CONFLICTPROJECT = $(DEBNAME)-jupyter
else
	PROJECT = $(DEBNAME)-jupyter
	CONFLICTPROJECT = $(DEBNAME)
endif
MAJOR    ?= 0
MINOR    ?= 0
SUB      ?= 0
PATCH    ?= 0
VERSION   = "$(MAJOR).$(MINOR).$(SUB)"
CODENAME ?= $(shell awk -F= '/CODENAME/{print $$2}' /etc/lsb-release)
DEB	      = "$(PROJECT)-$(MAJOR).$(MINOR).$(SUB)-$(PATCH)~$(CODENAME).deb"
MD5SUM    = md5sum
SEDI      = sed -i
PYTHON   ?= python
VENV      = venv/bin/activate

PYQT5SIP  = $(shell grep pyqt5-sip requirements.txt)
PYWINTYPES=
PYINSTALLERARGS=


ifeq ($(shell uname), Darwin)
    MD5SUM = md5 -r
    SEDI   = sed -i ""
    PYINSTALLERARGS = ""
endif
# this is unused, see winbuild.ps1
ifneq (,$(findstring MINGW64,$(shell uname)))
    VENV = venv/Scripts/activate
    PYWINTYPES = pypiwin32
endif
IN_VENV=. ./$(VENV)


$(VENV):
	@echo Project: $(PROJECT)
	@echo Conflicts project: $(CONFLICTPROJECT)
	@echo Shell: "'"$(shell uname)"'"
	@echo
	test -d venv || virtualenv venv --python=$(PYTHON) --prompt "(build) "
	${IN_VENV} && pip install pip --upgrade
	${IN_VENV} && pip install ${PYQT5SIP} ${PYWINTYPES}
	${IN_VENV} && pip install -r requirements.txt

testenv: $(VENV)

test: $(VENV)
	${IN_VENV} && pip install flake8 flake8-rst-docstrings flake8-docstrings flake8-import-order
	${IN_VENV} && flake8 labslauncher \
		--import-order-style google --application-import-names labslauncher \
		--statistics


dist/EPI2ME-Labs-Launcher: $(VENV)
	${IN_VENV} && python setup.py develop
	${IN_VENV} && pyinstaller EPI2ME-Labs-Launcher.spec ${PYINSTALLERARGS}


.PHONY: run
run: $(VENV)
	${IN_VENV} && python setup.py develop && labslauncher


.PHONY: build
build: dist/EPI2ME-Labs-Launcher


.PHONY: clean
clean:
	rm -rf __pycache__ dist build venv labslauncher.egg-info tmp *.deb


deb: clean dist/EPI2ME-Labs-Launcher
	# To make a deb package, we simply copy all files from the pyinstaller bundle
	# Note the postrm script removes everything under /usr/local/bin/EPI2ME-Labs-Launcher
	# on the target filesystem for good measure.
	echo $(PROJECT)
	echo $(CONFLICTPROJECT)
	rm -rf deb-src/usr
	mkdir -p deb-src/usr/local/bin
	mkdir -p deb-src/usr/share/applications
	cp -r dist/EPI2ME-Labs-Launcher deb-src/usr/local/bin/
	cp labslauncher.desktop deb-src/usr/share/applications
	cp labslauncher/epi2me.png deb-src/usr/share/applications/epi2me.png
	cp -rp deb-src/ tmp/
	$(SEDI) "s/CONFLICTPROJECT/$(CONFLICTPROJECT)/g"   tmp/DEBIAN/control
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


rpm: clean dist/EPI2ME-Labs-Launcher
	# Similar to making the deb
	rpmdev-setuptree
	cd dist \
		&& python3 ../rpm-src/create_spec.py EPI2ME-Labs-Launcher launcher.spec ${DEBNAME} ${MAJOR} ${MINOR} ${SUB}  \
	    && cp -r EPI2ME-Labs-Launcher ${HOME}/rpmbuild/SOURCES/ \
		&& cp ../labslauncher.desktop ${HOME}/rpmbuild/SOURCES/EPI2ME-Labs-Launcher/ \
		&& cp ../labslauncher/epi2me.png ${HOME}/rpmbuild/SOURCES/EPI2ME-Labs-Launcher/ \
		&& QA_RPATHS=$$[ 0x0001|0x0002 ] rpmbuild -ba launcher.spec


