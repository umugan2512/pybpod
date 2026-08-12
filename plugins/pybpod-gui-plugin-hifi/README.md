# What is the PyBpod HiFi module driver?

Python driver for the [Sanworks Bpod HiFi Module](https://sanworks.github.io/Bpod_Wiki/module-documentation/hifi-module/),
reimplemented from Sanworks' official `BpodHiFi.m` MATLAB class
(https://github.com/sanworks/Bpod_Gen2/blob/master/Functions/Modules/HiFi/BpodHiFi.m) against its
documented USB serial protocol.

`pybpod_hifi_module.module_api.HiFiModule` connects directly to the module's own USB serial port
(separate from the Bpod state machine's own connection) to load mono or true independent-channel
stereo waveforms and set the sampling rate. `pybpod_hifi_module.module.HiFi` is the
`pybpodapi.bpod_modules.bpod_module.BpodModule` subclass used to trigger playback from a running
state machine's `output_actions`, once the module is auto-detected by its self-announced name
(`HiFi1`).

## Setup

Add `'pybpod_hifi_module'` to `PYBPOD_API_MODULES` in the project's `user_settings.py` so
`pybpodapi` classifies the connected module as `HiFi` instead of a generic `BpodModule`.

## Status

Grounded in the official protocol documentation but not yet verified against real hardware.
