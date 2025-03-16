"""
Setup script for creating a macOS application bundle using py2app.
"""

from setuptools import setup

APP = ['infra/gui/app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['PyQt6', 'infra'],
    'includes': [
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
    ],
    'iconfile': 'infra/gui/resources/icon.icns',  # Will be created later
    'plist': {
        'CFBundleName': 'Infra',
        'CFBundleDisplayName': 'Infra Toolkit',
        'CFBundleVersion': '0.1.0',
        'CFBundleIdentifier': 'local.infratoolkit.infra',
        'NSHumanReadableCopyright': 'Copyright © 2023',
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
    }
}

setup(
    name="Infra",
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 