MAJOR    ?= 0
MINOR    ?= 1
SUB      ?= 0
PATCH    ?= 0
STREAM   ?= ""
VERSION   ="$(MAJOR).$(MINOR).$(SUB)"
CODENAME ?= $(shell awk -F= '/CODENAME/{print $$2}' /etc/lsb-release)
ifeq "$(STREAM)" ""
	PROJECT  ?= ont-epi2melabs-launcher
else
	PROJECT  ?= ont-epi2melabs-launcher-$(STREAM)
endif
DEB	  ="$(PROJECT)-$(MAJOR).$(MINOR).$(SUB)-$(PATCH)~$(CODENAME).deb"
MD5SUM    = md5sum
SEDI      = sed -i

ifeq ($(shell uname), Darwin)
        MD5SUM = md5 -r
        SEDI   = sed -i ""
endif

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
	rm -rf tmp *.deb

test:
	    lintian *.deb

deb: clean dist/Epi2MeLabs-Launcher
	mkdir -p deb-src/usr/local/bin
	cp dist/Epi2MeLabs-Launcher deb-src/usr/local/bin/
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



