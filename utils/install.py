#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
from subprocess import call

SUBMODULES_FOLDERS = [
    # LIBRARIES
    "libraries/logging-bootstrap",
    "libraries/pyforms-gui",
    "libraries/pyforms-generic-editor",
    "libraries/safe-collaborative-architecture",
    # BASE
    "base/pybpod-api",
    "base/pybpod-gui-api",
    "base/pybpod-gui-plugin",
    # PLUGINS
    "plugins/pge-plugin-terminal",
    "plugins/pybpod-gui-plugin-alyx",
    "plugins/pybpod-gui-plugin-emulator",
    "plugins/pybpod-gui-plugin-hifi",
    "plugins/pybpod-gui-plugin-session-history",
    "plugins/pybpod-gui-plugin-stmdiagram",
    "plugins/pybpod-gui-plugin-timeline",
    "plugins/pybpod-gui-plugin-trial-timeline",
    "plugins/pybpod-gui-plugin-waveplayer",
    "plugins/pybpod-gui-plugin-rotaryencoder",
    "plugins/pybpod-gui-plugin-soundcard",
    # TOP-LEVEL PACKAGE -- must be installed LAST: its own setup.py pins exact versions of every
    # package above (pyforms-gui, pybpod-api/gui-api/gui-plugin, every plugin), so pip only picks up
    # the local editable installs instead of trying to pull pinned versions from PyPI if this runs
    # after all of them are already in place.
    "base/pybpod",
]

DEFAULT_PLUGINS = [
    "pybpodgui_plugin",
    "pybpodgui_plugin_timeline",
    "pybpodgui_plugin_session_history",
]


def install():
    for submodule in SUBMODULES_FOLDERS:
        call(["pip", "install", "-e", os.path.join(submodule, ".")])


def conf_default_settings():
    if not os.path.exists("user_settings.py"):
        f = open("user_settings.py", "w")
        f.write("SETTINGS_PRIORITY = 0\n\n")
        f.write("GENERIC_EDITOR_PLUGINS_LIST = " + str(DEFAULT_PLUGINS))
        f.close()


if __name__ == "__main__":
    install()
    conf_default_settings()
