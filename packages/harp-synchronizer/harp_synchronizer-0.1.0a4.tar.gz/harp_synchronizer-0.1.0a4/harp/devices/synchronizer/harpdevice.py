from dataclasses import dataclass
from enum import IntEnum, IntFlag

from harp.protocol import MessageType, PayloadType
from harp.protocol.exceptions import HarpException, HarpReadException, HarpWriteException
from harp.protocol.messages import HarpMessage
from harp.serial import Device


class DigitalInputs(IntFlag):
    """
    Specifies the state of digital input port lines.

    Attributes
    ----------
    DI0 : int
        _No description currently available_
    DI1 : int
        _No description currently available_
    DI2 : int
        _No description currently available_
    DI3 : int
        _No description currently available_
    DI4 : int
        _No description currently available_
    DI5 : int
        _No description currently available_
    DI6 : int
        _No description currently available_
    DI7 : int
        _No description currently available_
    DI8 : int
        _No description currently available_
    """

    NONE = 0x0
    DI0 = 0x1
    DI1 = 0x2
    DI2 = 0x3
    DI3 = 0x4
    DI4 = 0x8
    DI5 = 0x10
    DI6 = 0x20
    DI7 = 0x40
    DI8 = 0x80


class DigitalOutputs(IntFlag):
    """
    Specifies the state of digital output port lines.

    Attributes
    ----------
    DO0 : int
        _No description currently available_
    """

    NONE = 0x0
    DO0 = 0x1


class SynchronizerEvents(IntFlag):
    """
    The events that can be enabled/disabled.

    Attributes
    ----------
    DIGITAL_INPUT_STATE : int
        _No description currently available_
    """

    NONE = 0x0
    DIGITAL_INPUT_STATE = 0x1


class DigitalInputsSamplingConfig(IntEnum):
    """
    Available modes for catching/sampling the digital inputs.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    INPUTS_CHANGE : int
        _No description currently available_
    DI0_RISING_EDGE : int
        _No description currently available_
    DI0_FALLING_EDGE : int
        _No description currently available_
    SAMPLING_100HZ : int
        _No description currently available_
    SAMPLING_250HZ : int
        _No description currently available_
    SAMPLING_500HZ : int
        _No description currently available_
    SAMPLING_1000HZ : int
        _No description currently available_
    SAMPLING_2000HZ : int
        _No description currently available_
    """

    NONE = 0
    INPUTS_CHANGE = 1
    DI0_RISING_EDGE = 2
    DI0_FALLING_EDGE = 3
    SAMPLING_100HZ = 4
    SAMPLING_250HZ = 5
    SAMPLING_500HZ = 6
    SAMPLING_1000HZ = 7
    SAMPLING_2000HZ = 8


class DO0ConfigMode(IntEnum):
    """
    Available configuration for the DO0.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    TOGGLE_ON_INPUTS_CHANGE : int
        _No description currently available_
    MIMIC_DI0 : int
        _No description currently available_
    PULSE_5MS_ON_INPUTS_CHANGE : int
        _No description currently available_
    PULSE_2MS_ON_INPUTS_CHANGE : int
        _No description currently available_
    PULSE_1MS_ON_INPUTS_CHANGE : int
        _No description currently available_
    PULSE500US_ON_INPUTS_CHANGE : int
        _No description currently available_
    PULSE250US_ON_INPUTS_CHANGE : int
        _No description currently available_
    ANY_INPUTS : int
        _No description currently available_
    """

    NONE = 0
    TOGGLE_ON_INPUTS_CHANGE = 1
    MIMIC_DI0 = 2
    PULSE_5MS_ON_INPUTS_CHANGE = 3
    PULSE_2MS_ON_INPUTS_CHANGE = 4
    PULSE_1MS_ON_INPUTS_CHANGE = 5
    PULSE500US_ON_INPUTS_CHANGE = 6
    PULSE250US_ON_INPUTS_CHANGE = 7
    ANY_INPUTS = 8


class SynchronizerRegisters(IntEnum):
    """Enum for all available registers in the Synchronizer device.

    Attributes
    ----------
    DIGITAL_INPUT_STATE : int
        State of the digital input pins. An event will be emitted when the value of any digital input pin changes.
    DIGITAL_OUTPUT_STATE : int
        Status of the digital output pin 0.
    DIGITAL_INPUTS_SAMPLING_MODE : int
        Sets the sampling mode for digital input pins.
    DO0_CONFIG : int
        Configures how the DO0 pin behaves.
    ENABLE_EVENTS : int
        Specifies all the active events in the device.
    """

    DIGITAL_INPUT_STATE = 32
    DIGITAL_OUTPUT_STATE = 33
    DIGITAL_INPUTS_SAMPLING_MODE = 34
    DO0_CONFIG = 35
    ENABLE_EVENTS = 40


class Synchronizer(Device):
    """
    Synchronizer class for controlling the device.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect and load already happened in the base class
        # verify that WHO_AM_I matches the expected value
        if self.WHO_AM_I != 1104:
            self.disconnect()
            raise HarpException(f"WHO_AM_I mismatch: expected {1104}, got {self.WHO_AM_I}")

    def read_digital_input_state(self) -> DigitalInputs | None:
        """
        Reads the contents of the DigitalInputState register.

        Returns
        -------
        DigitalInputs | None
            Value read from the DigitalInputState register.
        """
        address = SynchronizerRegisters.DIGITAL_INPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SynchronizerRegisters.DIGITAL_INPUT_STATE", reply)

        if reply is not None:
            return DigitalInputs(reply.payload)
        return None

    def read_digital_output_state(self) -> DigitalOutputs | None:
        """
        Reads the contents of the DigitalOutputState register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the DigitalOutputState register.
        """
        address = SynchronizerRegisters.DIGITAL_OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SynchronizerRegisters.DIGITAL_OUTPUT_STATE", reply)

        if reply is not None:
            return DigitalOutputs(reply.payload)
        return None

    def write_digital_output_state(self, value: DigitalOutputs) -> HarpMessage | None:
        """
        Writes a value to the DigitalOutputState register.

        Parameters
        ----------
        value : DigitalOutputs
            Value to write to the DigitalOutputState register.
        """
        address = SynchronizerRegisters.DIGITAL_OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SynchronizerRegisters.DIGITAL_OUTPUT_STATE", reply)

        return reply

    def read_digital_inputs_sampling_mode(self) -> DigitalInputsSamplingConfig | None:
        """
        Reads the contents of the DigitalInputsSamplingMode register.

        Returns
        -------
        DigitalInputsSamplingConfig | None
            Value read from the DigitalInputsSamplingMode register.
        """
        address = SynchronizerRegisters.DIGITAL_INPUTS_SAMPLING_MODE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SynchronizerRegisters.DIGITAL_INPUTS_SAMPLING_MODE", reply)

        if reply is not None:
            return DigitalInputsSamplingConfig(reply.payload)
        return None

    def write_digital_inputs_sampling_mode(self, value: DigitalInputsSamplingConfig) -> HarpMessage | None:
        """
        Writes a value to the DigitalInputsSamplingMode register.

        Parameters
        ----------
        value : DigitalInputsSamplingConfig
            Value to write to the DigitalInputsSamplingMode register.
        """
        address = SynchronizerRegisters.DIGITAL_INPUTS_SAMPLING_MODE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SynchronizerRegisters.DIGITAL_INPUTS_SAMPLING_MODE", reply)

        return reply

    def read_do0_config(self) -> DO0ConfigMode | None:
        """
        Reads the contents of the DO0Config register.

        Returns
        -------
        DO0ConfigMode | None
            Value read from the DO0Config register.
        """
        address = SynchronizerRegisters.DO0_CONFIG
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SynchronizerRegisters.DO0_CONFIG", reply)

        if reply is not None:
            return DO0ConfigMode(reply.payload)
        return None

    def write_do0_config(self, value: DO0ConfigMode) -> HarpMessage | None:
        """
        Writes a value to the DO0Config register.

        Parameters
        ----------
        value : DO0ConfigMode
            Value to write to the DO0Config register.
        """
        address = SynchronizerRegisters.DO0_CONFIG
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SynchronizerRegisters.DO0_CONFIG", reply)

        return reply

    def read_enable_events(self) -> SynchronizerEvents | None:
        """
        Reads the contents of the EnableEvents register.

        Returns
        -------
        SynchronizerEvents | None
            Value read from the EnableEvents register.
        """
        address = SynchronizerRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SynchronizerRegisters.ENABLE_EVENTS", reply)

        if reply is not None:
            return SynchronizerEvents(reply.payload)
        return None

    def write_enable_events(self, value: SynchronizerEvents) -> HarpMessage | None:
        """
        Writes a value to the EnableEvents register.

        Parameters
        ----------
        value : SynchronizerEvents
            Value to write to the EnableEvents register.
        """
        address = SynchronizerRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SynchronizerRegisters.ENABLE_EVENTS", reply)

        return reply

