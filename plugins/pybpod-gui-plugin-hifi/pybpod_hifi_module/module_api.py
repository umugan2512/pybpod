# !/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Direct USB driver for the Sanworks Bpod HiFi Module.

Reimplemented from the official Sanworks MATLAB reference (BpodHiFi.m):
https://github.com/sanworks/Bpod_Gen2/blob/master/Functions/Modules/HiFi/BpodHiFi.m

The HiFi module exposes its own USB serial port for loading audio data, separate from the Bpod
state machine's own connection -- this driver talks to that port directly, the same way
pybpod_waveplayer_module talks to the WavePlayer module's own serial port.
"""
import struct

import numpy as np
from serial.tools import list_ports

from pybpodapi.com.arcom import ArCOM
from pybpod_hifi_module.settings import HIFI_VALID_SAMPLING_RATES, HIFI_DEFAULT_SAMPLING_RATE


class HiFiModule(object):
    """
    Provides access to the Bpod HiFi Module over its own USB serial connection: loading mono or
    true independent-channel stereo waveforms, setting the sampling rate, and (for direct/manual
    use outside a state machine) playing a loaded waveform.
    """

    def __init__(self, serial_port, sampling_rate=HIFI_DEFAULT_SAMPLING_RATE):
        """
        :param str serial_port: the HiFi module's own USB serial port (e.g. 'COM5'), not the
            Bpod state machine's own port.
        :param int sampling_rate: one of 44100, 48000, 96000, 192000 Hz.
        """
        self.arcom = ArCOM().open(serial_port, baudrate=1312500, timeout=5)

        self.arcom.write_array(bytes([243]))
        ack = self.arcom.read_uint8()
        if ack != 244:
            raise RuntimeError("HiFi module handshake failed on {0}".format(serial_port))

        self.arcom.write_array(b'I')
        info8 = self.arcom.read_uint8_array(4)
        info32 = self.arcom.read_uint32_array(3)
        self.is_hd = bool(info8[0])
        self.bit_depth = info8[1]
        self.max_waves = info8[2]
        self.max_samples_per_waveform = info32[1] * 192000

        self.sampling_rate = None
        self.set_sampling_rate(sampling_rate)

    @classmethod
    def discover(cls, sampling_rate=HIFI_DEFAULT_SAMPLING_RATE, exclude_ports=(), timeout=0.3):
        """
        Scan available serial ports for a HiFi module by probing each with the module's own
        handshake byte (243 -> 244), skipping any ports in exclude_ports (e.g. the Bpod state
        machine's own connection -- pass my_bpod.serial_port here so it's never probed).

        This is necessary because the HiFi module's own USB audio-data port is a separate
        physical connection from the Bpod state machine's Serial1-5 relay -- nothing about it is
        reported over that relay, so there's no way to read it off the connected Bpod object.

        :param int sampling_rate: passed through to the connected HiFiModule.
        :param exclude_ports: iterable of port device names (e.g. ['COM4']) to skip probing.
        :param float timeout: per-port probe read timeout, in seconds.
        :return: a connected HiFiModule on the first port that answers the handshake correctly.
        """
        candidates = [p.device for p in list_ports.comports() if p.device not in exclude_ports]

        for port in candidates:
            probe = None
            try:
                probe = ArCOM().open(port, baudrate=1312500, timeout=timeout)
                probe.write_array(bytes([243]))
                ack = probe.read_uint8()
            except Exception:
                continue
            finally:
                if probe is not None:
                    probe.close()

            if ack == 244:
                return cls(port, sampling_rate=sampling_rate)

        raise RuntimeError(
            "No HiFi module found on any serial port (probed {0}, excluding {1})".format(
                candidates, list(exclude_ports)))

    def set_sampling_rate(self, sampling_rate):
        """
        :param int sampling_rate: one of 44100, 48000, 96000, 192000 Hz.
        """
        if sampling_rate not in HIFI_VALID_SAMPLING_RATES:
            raise ValueError("Sampling rate must be one of {0}".format(HIFI_VALID_SAMPLING_RATES))

        self.arcom.write_array(b'S' + struct.pack('<I', sampling_rate))
        ack = self.arcom.read_uint8()
        if ack != 1:
            raise RuntimeError("Failed to set HiFi module sampling rate")

        self.sampling_rate = sampling_rate

    def load(self, wave_index, waveform, loop_mode=0, loop_duration=0):
        """
        Load an audio waveform to the HiFi module's internal memory at a target position.

        :param int wave_index: 0-based slot (0 to max_waves-1)
        :param waveform: numpy array, shape (n_samples,) for mono or (2, n_samples) for stereo
            (row 0 = channel 1/left, row 1 = channel 2/right), sample values in range [-1, 1].
        :param int loop_mode: 0 (off) or 1 (loop the waveform until stopped)
        :param float loop_duration: total time in seconds to play the looped sound before
            stopping (only used when loop_mode=1)
        """
        waveform = np.asarray(waveform, dtype=np.float64)

        if waveform.ndim == 1:
            is_stereo = 0
            n_samples = waveform.shape[0]
            interleaved = waveform
        elif waveform.ndim == 2 and waveform.shape[0] == 2:
            is_stereo = 1
            n_samples = waveform.shape[1]
            # column-major (L, R, L, R, ...) interleaving, matching BpodHiFi.m's linearization
            interleaved = waveform.flatten(order='F')
        else:
            raise ValueError("waveform must be shape (n_samples,) [mono] or (2, n_samples) [stereo]")

        if n_samples > self.max_samples_per_waveform:
            raise ValueError(
                "Waveform too long: {0} samples exceeds the module's {1}-sample limit".format(
                    n_samples, self.max_samples_per_waveform))

        if not (0 <= wave_index < self.max_waves):
            raise ValueError("wave_index must be in range [0, {0}]".format(self.max_waves - 1))

        pcm = np.clip(interleaved * 32767, -32768, 32767).astype('<i2')

        header = bytes([ord('L'), wave_index, is_stereo, loop_mode]) + struct.pack(
            '<II', int(loop_duration * self.sampling_rate), n_samples)

        self.arcom.write_array(header + pcm.tobytes())
        ack = self.arcom.read_uint8()
        if ack != 1:
            raise RuntimeError(
                "HiFi module failed to confirm waveform load at slot {0} (dropped USB transfer)".format(wave_index))

    def push(self):
        """
        Makes all newly loaded waveforms live, overwriting any waveforms at the same position(s).
        """
        self.arcom.write_array(b'*')
        ack = self.arcom.read_uint8()
        if ack != 1:
            raise RuntimeError("HiFi module failed to confirm push")

    def play(self, wave_index):
        """
        Play a loaded waveform immediately, over this direct USB connection. For trial-synced
        playback triggered by the Bpod state machine instead, see pybpod_hifi_module.module.HiFi.
        """
        self.arcom.write_array(bytes([ord('P'), wave_index]))

    def stop(self):
        """ Stop all currently playing sounds. """
        self.arcom.write_array(b'X')

    def close(self):
        self.arcom.close()
