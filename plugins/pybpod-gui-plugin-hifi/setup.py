#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

requirements = ["numpy", "scipy", "pyserial"]

setup(
    name="pybpod-gui-plugin-hifi",
    version="0.1.0",
    description="""PyBpod Bpod HiFi module driver""",
    long_description="""Python driver for the Sanworks Bpod HiFi Module: loads and triggers audio
    waveforms (mono or true independent-channel stereo) over the module's own USB connection, and
    provides the state-machine-side trigger integration for use from PyBpod protocols.""",
    license="MIT",
    include_package_data=True,
    packages=find_packages(),
    install_requires=requirements,
)
