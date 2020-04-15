from glob import glob
import os
import pkg_resources
import re
from setuptools import setup, find_packages
from setuptools import Distribution
from setuptools.command.install import install
import shutil
import sys

__pkg_name__ = 'labslauncher'
__author__ = 'cwright'
__description__ = 'Epi2MeLabs server manager.'

# Use readme as long description and say its github-flavour markdown
from os import path
this_directory = path.abspath(path.dirname(__file__))
kwargs = {'encoding':'utf-8'} if sys.version_info.major == 3 else {}
with open(path.join(this_directory, 'README.md'), **kwargs) as f:
    __long_description__ = f.read()
__long_description_content_type__ = 'text/markdown'

__path__ = os.path.dirname(__file__)
__pkg_path__ = os.path.join(os.path.join(__path__, __pkg_name__))

# Get the version number from __init__.py, and exe_path
verstrline = open(os.path.join(__pkg_name__, '__init__.py'), 'r').read()
vsre = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(vsre, verstrline, re.M)
if mo:
    __version__ = mo.group(1)
else:
    raise RuntimeError('Unable to find version string in "{}/__init__.py".'.format(__pkg_name__))

dir_path = os.path.dirname(__file__)
with open(os.path.join(dir_path, 'requirements.txt')) as fh:
    install_requires = [
        str(requirement) for requirement in 
        pkg_resources.parse_requirements(fh)]

data_files = []
extensions = []
extra_requires = {}

setup(
    name=__pkg_name__,
    version=__version__,
    author=__author__,
    author_email='{}@nanoporetech.com'.format(__author__),
    description=__description__,
    long_description=__long_description__,
    long_description_content_type=__long_description_content_type__,
    dependency_links=[],
    ext_modules=extensions,
    install_requires=install_requires,
    tests_require=[].extend(install_requires),
    extras_require=extra_requires,
    python_requires='>=3.5.2, <3.7',
    packages=find_packages(exclude=['*.test', '*.test.*', 'test.*', 'test']),
    # NOTE: these need to be added to the pyinstaller spec file also
    package_data={'labslauncher':[
        'labslauncher.kv', 'epi2me.ico', 'fontawesome-webfont.ttf', 'fontawesome.fontd', 'EPI2ME_labs_logo_RGB_negative_large.png']},
    zip_safe=False,
    test_suite=None,
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'labslauncher = {}.app:main'.format(__pkg_name__)
        ]},
)
