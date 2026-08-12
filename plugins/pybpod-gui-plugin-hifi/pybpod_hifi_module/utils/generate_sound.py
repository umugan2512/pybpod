# !/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Reusable waveform-generation helpers for the HiFi module: gating envelopes, pure tones, and
narrowband noise bursts. Bandpass filtering follows the same scipy.signal.firwin + lfilter
convention used in the del Rocha lab's sound-calibration-plugin (sound_utils.py) for consistency.
"""
import numpy as np
from scipy.signal import firwin, lfilter


def cosine_ramp_gate(n_samples, ramp_samples):
    """
    Raised-cosine (half-cosine) onset/offset ramp, flat/steady in between.

    :param int n_samples: total length of the gate, in samples
    :param int ramp_samples: length of each ramp (onset and offset), in samples
    :return: numpy array of length n_samples, values in [0, 1]
    """
    if ramp_samples * 2 > n_samples:
        raise ValueError("ramp_samples*2 must not exceed n_samples")

    gate = np.ones(n_samples)
    ramp = 0.5 * (1 - np.cos(np.linspace(0, np.pi, ramp_samples)))
    gate[:ramp_samples] = ramp
    gate[n_samples - ramp_samples:] = ramp[::-1]
    return gate


def pure_tone(duration_s, frequency, sampling_rate, ramp_ms=None):
    """
    Generate a sine-wave tone, peak-normalized to amplitude 1, optionally cosine-gated.

    :param float duration_s: tone duration, in seconds
    :param float frequency: tone frequency, in Hz
    :param int sampling_rate: samples per second
    :param float ramp_ms: (optional) cosine ramp duration at onset/offset, in milliseconds
    :return: numpy array, shape (n_samples,), values in [-1, 1]
    """
    n_samples = int(duration_s * sampling_rate)
    t = np.arange(n_samples) / sampling_rate
    tone = np.sin(2 * np.pi * frequency * t)

    if ramp_ms:
        ramp_samples = int((ramp_ms / 1000) * sampling_rate)
        tone = tone * cosine_ramp_gate(n_samples, ramp_samples)

    return tone


def narrowband_noise(duration_s, center_freq, bandwidth_octaves, sampling_rate, ramp_ms=None, filter_length=1000):
    """
    Generate band-limited Gaussian white noise, peak-normalized to amplitude 1, optionally
    cosine-gated.

    :param float duration_s: burst duration, in seconds
    :param float center_freq: band center frequency, in Hz
    :param float bandwidth_octaves: bandpass width, in octaves, centered on center_freq
        (e.g. 1/3 for a 1/3-octave band)
    :param int sampling_rate: samples per second
    :param float ramp_ms: (optional) cosine ramp duration at onset/offset, in milliseconds
    :param int filter_length: FIR bandpass filter order (taps)
    :return: numpy array, shape (n_samples,), values in [-1, 1]
    """
    n_samples = int(duration_s * sampling_rate)

    low_freq = center_freq * 2 ** (-bandwidth_octaves / 2)
    high_freq = center_freq * 2 ** (bandwidth_octaves / 2)
    nyquist = sampling_rate * 0.5
    if high_freq >= nyquist:
        raise ValueError("high edge of the band ({0}Hz) must be below Nyquist ({1}Hz)".format(high_freq, nyquist))

    # generate extra samples up front so the filter's transient settles before the window we keep
    pad_samples = filter_length
    white_noise = np.random.normal(0, 1, size=n_samples + pad_samples)

    band_pass = firwin(filter_length, [low_freq / nyquist, high_freq / nyquist], pass_zero=False)
    band_noise = lfilter(band_pass, 1, white_noise)
    noise = band_noise[pad_samples:pad_samples + n_samples]

    peak = np.max(np.abs(noise))
    if peak > 0:
        noise = noise / peak

    if ramp_ms:
        ramp_samples = int((ramp_ms / 1000) * sampling_rate)
        noise = noise * cosine_ramp_gate(n_samples, ramp_samples)

    return noise
