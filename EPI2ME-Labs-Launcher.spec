# -*- mode: python ; coding: utf-8 -*-
import pkg_resources
from platform import platform
import sys

print("Running pyinstaller script with args:")
print("    - ", ' '.join(sys.argv))
print()

def Entrypoint(dist, group, name, **kwargs):

    # get toplevel packages of distribution from metadata
    def get_toplevel(dist):
        distribution = pkg_resources.get_distribution(dist)
        if distribution.has_metadata('top_level.txt'):
            return list(distribution.get_metadata('top_level.txt').split())
        else:
            return []

    kwargs.setdefault('hiddenimports', [])
    packages = []
    for distribution in kwargs['hiddenimports']:
        packages += get_toplevel(distribution)

    kwargs.setdefault('pathex', [])
    # get the entry point
    ep = pkg_resources.get_entry_info(dist, group, name)
    # insert path of the egg at the verify front of the search path
    kwargs['pathex'] = [ep.dist.location] + kwargs['pathex']
    # script name must not be a valid module name to avoid name clashes on import
    script_path = os.path.join(workpath, name + '-script.py')
    print("creating script for entry point", dist, group, name)
    with open(script_path, 'w') as fh:
        print("import", ep.module_name, file=fh)
        print("%s.%s()" % (ep.module_name, '.'.join(ep.attrs)), file=fh)
        for package in packages:
            print("import", package, file=fh)

    return Analysis(
        [script_path] + kwargs.get('scripts', []),
        **kwargs
    )

a = Entrypoint(
    'labslauncher', 'console_scripts', 'labslauncher',
    hiddenimports=[],
    datas=[
        ('labslauncher/{}'.format(x), 'labslauncher')
        for x in ['epi2me.png', 'epi2me.ico', 'epi2me.icns', 'epi2me_labs_logo.png']]
) 
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

name = 'EPI2ME-Labs-Launcher'
common_args = { 
    'name': name,
    'strip': False, 'upx': True, 'upx_exclude': []}
exe_kwargs = {
    'debug': False,
    'bootloader_ignore_signals': False,
    'runtime_tmpdir': None,
    'console': False, 'windowed': True,
    'icon': os.path.join('labslauncher', 'epi2me.ico')}

if '--onefile' in sys.argv:
    print(" + Building single-file dist")
    exe = EXE(
        pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
        **exe_kwargs, **common_args)
else:
    print(" + Building a single-directory dist")
    exe = EXE(
        pyz, a.scripts, [],
        exclude_binaries=True,
        **exe_kwargs, **common_args)
    exe = COLLECT(
        exe, a.binaries, a.zipfiles, a.datas,
        **common_args)

    if "Darwin" in platform():
        print(" + Building macOS bundle")
        app = BUNDLE(
            exe,
            name='{}.app'.format(name),
            icon=os.path.join('labslauncher', 'epi2me.icns'),
            bundle_identifier=None)
