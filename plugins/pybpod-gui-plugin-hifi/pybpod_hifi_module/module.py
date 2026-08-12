# !/usr/bin/python3
# -*- coding: utf-8 -*-
from enum import IntEnum

from pybpodapi.bpod_modules.bpod_module import BpodModule


class HiFiCommandType(IntEnum):
    """
    Enumeration for the commands that can be sent through the HiFi module, when connected through
    the Bpod's State Machine.
    """
    #: Plays a specific waveform slot (0-based index)
    PLAY = 1
    #: Stops all currently playing sounds
    STOP_ALL = 2


class HiFi(BpodModule):
    """
    State-machine-side integration for the Bpod HiFi Module. Waveforms are loaded ahead of time
    over the module's own direct USB connection (see pybpod_hifi_module.module_api.HiFiModule);
    this class only concerns triggering playback from a running state machine.
    """

    @staticmethod
    def check_module_type(module_name):
        return module_name and module_name.startswith('HiFi')

    @staticmethod
    def get_command(command_type, sound_index=None):
        """
        Returns the bytes to send as an output_actions entry in a BPod StateMachine state.

        .. note:: Multi-byte commands (PLAY) must first be registered with the Bpod's
            load_serial_message method (messages up to 3 bytes long), then triggered in
            output_actions with the resulting message_id -- a raw multi-byte tuple in
            output_actions is not supported by this version of pybpod-api. See
            pybpodapi.bpod.bpod_base.BpodBase.load_serial_message.

        :param command_type: Instruction of type :class:`.HiFiCommandType`
        :param sound_index: The waveform slot to play (0-based), required for PLAY
        """
        if not command_type:
            raise Exception("You need to provide the type of the command you want returned")

        if command_type is HiFiCommandType.PLAY:
            if sound_index is None:
                raise Exception("You need to provide the sound_index value to play")
            return [ord('P'), sound_index]

        # STOP_ALL
        return [ord('X')]
