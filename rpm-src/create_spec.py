import argparse
from copy import copy
import os
import re

parser = argparse.ArgumentParser(
    description="Create RPM SPEC file.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
    "input_directory",
    help="Source directory for installed files.")
parser.add_argument("output",
    help="Output installer file.")
parser.add_argument("project",
    help="Project name.")
parser.add_argument(
    "version", nargs=3,
    help="MAJOR MINOR PATCH version numbers")
parser.add_argument(
    "--template",
    default=os.path.join(os.path.dirname(__file__), "launcher_template.spec"),
    help="SPEC file template.")
args = parser.parse_args()

if args.input_directory.endswith("/"):
    args.input_directory = args.input_directory[:-1]
if os.path.basename(args.input_directory) != args.input_directory:
    print(os.path.basename(args.input_directory), args.input_directory)
    raise RuntimeError("Please run this script alongside the input directory.")

directories = list()
all_files = list()
for path, dirs, files in os.walk(args.input_directory):
    directories.append(path)
    for f in files:
        fullpath = os.path.join(path, f)
        perm = str(oct(os.stat(fullpath).st_mode & 0o777))[2:]
        all_files.append((perm, fullpath))

install_list = list()
files_list = list()
install_list.append("mkdir -p %{buildroot}%{_localbindir}")
install_list.append("mkdir -p %{buildroot}/%{_datadir}/applications")
for d in directories:
    install_list.append("mkdir -p %{{buildroot}}%{{_localbindir}}/{}".format(d))
for perm, fname in all_files:
    install_list.append('install -m {} %{{_sourcedir}}/{} %{{buildroot}}%{{_localbindir}}/{}'.format(perm, fname, fname))
    files_list.append('%{{_localbindir}}/{}'.format(fname))

# desktop file
for f in ('labslauncher.desktop', 'epi2me.png'):
    install_list.append(
        'install %{{_sourcedir}}/{}/{} %{{buildroot}}/%{{_datadir}}/applications/{}'.format(args.input_directory, f, f))
    files_list.append(
        '%{{_datadir}}/applications/{}'.format(f))

with open(args.template, 'r') as source, open(args.output, 'w') as dest:
    template = source.read() \
        .replace("<<INSTALL_LIST>>", "\n".join(install_list)) \
        .replace("<<FILES_LIST>>", "\n".join(files_list)) \
        .replace("<<PROJECT>>", args.project) \
        .replace("<<MAJOR>>", args.version[0]) \
        .replace("<<MINOR>>", args.version[1]) \
        .replace("<<PATCH>>", args.version[2])
    dest.write(template)
