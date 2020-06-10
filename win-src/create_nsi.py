import argparse
import os
import re

parser = argparse.ArgumentParser(
    description="Create NSIS installer file.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
    "input_directory",
    help="Source directory for installed files.")
parser.add_argument("output",
    help="Output installer file.")
parser.add_argument(
    "--template",
    default=os.path.join(os.path.dirname(__file__), "winstaller_template.nsi"),
    help="NSIS template.")
parser.add_argument(
    "--init",
    default=os.path.join(os.path.dirname(__file__), '..', 'labslauncher', '__init__.py'),
    help="Package __init__.py, used for finding version.")
args = parser.parse_args()


# Get the version number from __init__.py, and exe_path
verstrline = open(args.init, 'r').read()
vsre = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(vsre, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError('Unable to find version string in "{}/__init__.py".'.format(__pkg_name__))
major, minor, build = verstr.split(".")


directories = list()
all_files = list()
for path, dirs, files in os.walk(args.input_directory):
    directories.append(path)
    all_files.extend(os.path.join(path, x) for x in files)

stem = directories[0]
items = list()
for f in all_files:
    f = f.replace(stem, "")
    items.append('delete "$INSTDIR\{}"'.format(f))
for d in directories[-1:0:-1]:
    d = d.replace(stem, "")
    items.append('rmDir "$INSTDIR\{}"'.format(d))

for item in items:
    print("Adding: ", item)
items = '\n'.join(items)

with open(args.template, 'r') as source, open(args.output, 'w') as dest:
    template = source.read() \
        .replace("<<UNINSTALL_LIST>>", items) \
        .replace("<<VERSIONMAJOR>>", major) \
        .replace("<<VERSIONMINOR>>", minor) \
        .replace("<<VERSIONBUILD>>", build)
    dest.write(template)
