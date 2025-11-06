from dataclasses import dataclass
from enum import IntEnum, IntFlag

from harp.protocol import MessageType, PayloadType
from harp.protocol.exceptions import HarpException, HarpReadException, HarpWriteException
from harp.protocol.messages import HarpMessage
from harp.serial import Device


@dataclass
class AnalogDataPayload:
    Channel0: int
    Channel1: int
    Channel2: int
    Channel3: int


class DigitalInputs(IntFlag):
    """
    Available digital input lines.

    Attributes
    ----------
    DI0 : int
        _No description currently available_
    """

    NONE = 0x0
    DI0 = 0x1


class DigitalOutputs(IntFlag):
    """
    Specifies the state of port digital output lines.

    Attributes
    ----------
    DO0 : int
        _No description currently available_
    DO1 : int
        _No description currently available_
    DO2 : int
        _No description currently available_
    DO3 : int
        _No description currently available_
    DO0_CHANGED : int
        _No description currently available_
    DO1_CHANGED : int
        _No description currently available_
    DO2_CHANGED : int
        _No description currently available_
    DO4_CHANGED : int
        _No description currently available_
    """

    NONE = 0x0
    DO0 = 0x1
    DO1 = 0x2
    DO2 = 0x4
    DO3 = 0x8
    DO0_CHANGED = 0x10
    DO1_CHANGED = 0x20
    DO2_CHANGED = 0x40
    DO4_CHANGED = 0x80


class RangeAndFilterConfig(IntEnum):
    """
    Available settings to set the range (Volt) and LowPass filter cutoff (Hz) of the ADC.

    Attributes
    ----------
    RANGE_5V_LOW_PASS_1500HZ : int
        _No description currently available_
    RANGE_5V_LOW_PASS_3000HZ : int
        _No description currently available_
    RANGE_5V_LOW_PASS_6000HZ : int
        _No description currently available_
    RANGE_5V_LOW_PASS_10300HZ : int
        _No description currently available_
    RANGE_5V_LOW_PASS_13700HZ : int
        _No description currently available_
    RANGE_5V_LOW_PASS_15000HZ : int
        _No description currently available_
    RANGE_10V_LOW_PASS_1500HZ : int
        _No description currently available_
    RANGE_10V_LOW_PASS_3000HZ : int
        _No description currently available_
    RANGE_10V_LOW_PASS_6000HZ : int
        _No description currently available_
    RANGE_10V_LOW_PASS_11900HZ : int
        _No description currently available_
    RANGE_10V_LOW_PASS_18500HZ : int
        _No description currently available_
    RANGE_10V_LOW_PASS_22000HZ : int
        _No description currently available_
    """

    RANGE_5V_LOW_PASS_1500HZ = 6
    RANGE_5V_LOW_PASS_3000HZ = 5
    RANGE_5V_LOW_PASS_6000HZ = 4
    RANGE_5V_LOW_PASS_10300HZ = 3
    RANGE_5V_LOW_PASS_13700HZ = 2
    RANGE_5V_LOW_PASS_15000HZ = 1
    RANGE_10V_LOW_PASS_1500HZ = 22
    RANGE_10V_LOW_PASS_3000HZ = 21
    RANGE_10V_LOW_PASS_6000HZ = 20
    RANGE_10V_LOW_PASS_11900HZ = 19
    RANGE_10V_LOW_PASS_18500HZ = 18
    RANGE_10V_LOW_PASS_22000HZ = 17


class SamplingRateMode(IntEnum):
    """
    Available sampling frequency settings of the ADC.

    Attributes
    ----------
    SAMPLING_RATE_1000HZ : int
        _No description currently available_
    SAMPLING_RATE_2000HZ : int
        _No description currently available_
    """

    SAMPLING_RATE_1000HZ = 0
    SAMPLING_RATE_2000HZ = 1


class TriggerConfig(IntEnum):
    """
    Available configurations for when using DI0 as an acquisition trigger.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    START_ON_RISING_EDGE : int
        _No description currently available_
    START_ON_FALLING_EDGE : int
        _No description currently available_
    SAMPLE_ON_RISING_EDGE : int
        _No description currently available_
    """

    NONE = 0
    START_ON_RISING_EDGE = 1
    START_ON_FALLING_EDGE = 2
    SAMPLE_ON_RISING_EDGE = 3


class SyncConfig(IntEnum):
    """
    Available configurations when using DO0 pin to report firmware events.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    HEARTBEAT : int
        _No description currently available_
    PULSE : int
        _No description currently available_
    """

    NONE = 0
    HEARTBEAT = 1
    PULSE = 2


class StartSyncOutputTarget(IntEnum):
    """
    Available digital output pins that are able to be triggered on acquisition start.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    DO0 : int
        _No description currently available_
    DO1 : int
        _No description currently available_
    DO2 : int
        _No description currently available_
    DO3 : int
        _No description currently available_
    """

    NONE = 0
    DO0 = 1
    DO1 = 2
    DO2 = 3
    DO3 = 4


class AdcChannel(IntEnum):
    """
    Available target analog channels to be targeted for threshold events.

    Attributes
    ----------
    CHANNEL0 : int
        _No description currently available_
    CHANNEL1 : int
        _No description currently available_
    CHANNEL2 : int
        _No description currently available_
    CHANNEL3 : int
        _No description currently available_
    NONE : int
        _No description currently available_
    """

    CHANNEL0 = 0
    CHANNEL1 = 1
    CHANNEL2 = 2
    CHANNEL3 = 3
    NONE = 8


class AnalogInputRegisters(IntEnum):
    """Enum for all available registers in the AnalogInput device.

    Attributes
    ----------
    ACQUISITION_STATE : int
        Enables the data acquisition.
    ANALOG_DATA : int
        Value from a single read of all ADC channels.
    DIGITAL_INPUT_STATE : int
        State of the digital input pin 0.
    RANGE_AND_FILTER : int
        Sets the range and LowPass filter cutoff of the ADC.
    SAMPLING_RATE : int
        Sets the sampling frequency of the ADC.
    DI0_TRIGGER : int
        Configuration of the digital input pin 0.
    DO0_SYNC : int
        Configuration of the digital output pin 0.
    DO0_PULSE_WIDTH : int
        Pulse duration (ms) for the digital output pin 0. The pulse will only be emitted when DO0Sync == Pulse.
    DIGITAL_OUTPUT_SET : int
        Set the specified digital output lines.
    DIGITAL_OUTPUT_CLEAR : int
        Clear the specified digital output lines.
    DIGITAL_OUTPUT_TOGGLE : int
        Toggle the specified digital output lines
    DIGITAL_OUTPUT_STATE : int
        Write the state of all digital output lines. An event will be emitted when the value of any pin was changed by a threshold event.
    SYNC_OUTPUT : int
        Digital output that will be set when acquisition starts.
    DO0_TARGET_CHANNEL : int
        Target ADC channel that will be used to trigger a threshold event on DO0 pin.
    DO1_TARGET_CHANNEL : int
        Target ADC channel that will be used to trigger a threshold event on DO1 pin.
    DO2_TARGET_CHANNEL : int
        Target ADC channel that will be used to trigger a threshold event on DO2 pin.
    DO3_TARGET_CHANNEL : int
        Target ADC channel that will be used to trigger a threshold event on DO3 pin.
    DO0_THRESHOLD : int
        Value used to threshold an ADC read, and trigger DO0 pin.
    DO1_THRESHOLD : int
        Value used to threshold an ADC read, and trigger DO1 pin.
    DO2_THRESHOLD : int
        Value used to threshold an ADC read, and trigger DO2 pin.
    DO3_THRESHOLD : int
        Value used to threshold an ADC read, and trigger DO3 pin.
    DO0_TIME_ABOVE_THRESHOLD : int
        Time (ms) above threshold value that is required to trigger a DO0 pin event.
    DO1_TIME_ABOVE_THRESHOLD : int
        Time (ms) above threshold value that is required to trigger a DO1 pin event.
    DO2_TIME_ABOVE_THRESHOLD : int
        Time (ms) above threshold value that is required to trigger a DO2 pin event.
    DO3_TIME_ABOVE_THRESHOLD : int
        Time (ms) above threshold value that is required to trigger a DO3 pin event.
    DO0_TIME_BELOW_THRESHOLD : int
        Time (ms) below threshold value that is required to trigger a DO0 pin event.
    DO1_TIME_BELOW_THRESHOLD : int
        Time (ms) below threshold value that is required to trigger a DO1 pin event.
    DO2_TIME_BELOW_THRESHOLD : int
        Time (ms) below threshold value that is required to trigger a DO2 pin event.
    DO3_TIME_BELOW_THRESHOLD : int
        Time (ms) below threshold value that is required to trigger a DO3 pin event.
    """

    ACQUISITION_STATE = 32
    ANALOG_DATA = 33
    DIGITAL_INPUT_STATE = 34
    RANGE_AND_FILTER = 37
    SAMPLING_RATE = 38
    DI0_TRIGGER = 39
    DO0_SYNC = 40
    DO0_PULSE_WIDTH = 41
    DIGITAL_OUTPUT_SET = 42
    DIGITAL_OUTPUT_CLEAR = 43
    DIGITAL_OUTPUT_TOGGLE = 44
    DIGITAL_OUTPUT_STATE = 45
    SYNC_OUTPUT = 48
    DO0_TARGET_CHANNEL = 58
    DO1_TARGET_CHANNEL = 59
    DO2_TARGET_CHANNEL = 60
    DO3_TARGET_CHANNEL = 61
    DO0_THRESHOLD = 66
    DO1_THRESHOLD = 67
    DO2_THRESHOLD = 68
    DO3_THRESHOLD = 69
    DO0_TIME_ABOVE_THRESHOLD = 74
    DO1_TIME_ABOVE_THRESHOLD = 75
    DO2_TIME_ABOVE_THRESHOLD = 76
    DO3_TIME_ABOVE_THRESHOLD = 77
    DO0_TIME_BELOW_THRESHOLD = 82
    DO1_TIME_BELOW_THRESHOLD = 83
    DO2_TIME_BELOW_THRESHOLD = 84
    DO3_TIME_BELOW_THRESHOLD = 85


class AnalogInput(Device):
    """
    AnalogInput class for controlling the device.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect and load already happened in the base class
        # verify that WHO_AM_I matches the expected value
        if self.WHO_AM_I != 1236:
            self.disconnect()
            raise HarpException(f"WHO_AM_I mismatch: expected {1236}, got {self.WHO_AM_I}")

    def read_acquisition_state(self) -> bool | None:
        """
        Reads the contents of the AcquisitionState register.

        Returns
        -------
        bool | None
            Value read from the AcquisitionState register.
        """
        address = AnalogInputRegisters.ACQUISITION_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.ACQUISITION_STATE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_acquisition_state(self, value: bool) -> HarpMessage | None:
        """
        Writes a value to the AcquisitionState register.

        Parameters
        ----------
        value : bool
            Value to write to the AcquisitionState register.
        """
        address = AnalogInputRegisters.ACQUISITION_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.ACQUISITION_STATE", reply)

        return reply

    def read_analog_data(self) -> AnalogDataPayload | None:
        """
        Reads the contents of the AnalogData register.

        Returns
        -------
        AnalogDataPayload | None
            Value read from the AnalogData register.
        """
        address = AnalogInputRegisters.ANALOG_DATA
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.S16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.ANALOG_DATA", reply)

        if reply is not None:
            # Map payload (list/array) to dataclass fields by offset
            payload = reply.payload
            return AnalogDataPayload(
                Channel0=payload[0],
                Channel1=payload[1],
                Channel2=payload[2],
                Channel3=payload[3]
            )
        return None

    def read_digital_input_state(self) -> DigitalInputs | None:
        """
        Reads the contents of the DigitalInputState register.

        Returns
        -------
        DigitalInputs | None
            Value read from the DigitalInputState register.
        """
        address = AnalogInputRegisters.DIGITAL_INPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DIGITAL_INPUT_STATE", reply)

        if reply is not None:
            return DigitalInputs(reply.payload)
        return None

    def read_range_and_filter(self) -> RangeAndFilterConfig | None:
        """
        Reads the contents of the RangeAndFilter register.

        Returns
        -------
        RangeAndFilterConfig | None
            Value read from the RangeAndFilter register.
        """
        address = AnalogInputRegisters.RANGE_AND_FILTER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.RANGE_AND_FILTER", reply)

        if reply is not None:
            return RangeAndFilterConfig(reply.payload)
        return None

    def write_range_and_filter(self, value: RangeAndFilterConfig) -> HarpMessage | None:
        """
        Writes a value to the RangeAndFilter register.

        Parameters
        ----------
        value : RangeAndFilterConfig
            Value to write to the RangeAndFilter register.
        """
        address = AnalogInputRegisters.RANGE_AND_FILTER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.RANGE_AND_FILTER", reply)

        return reply

    def read_sampling_rate(self) -> SamplingRateMode | None:
        """
        Reads the contents of the SamplingRate register.

        Returns
        -------
        SamplingRateMode | None
            Value read from the SamplingRate register.
        """
        address = AnalogInputRegisters.SAMPLING_RATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.SAMPLING_RATE", reply)

        if reply is not None:
            return SamplingRateMode(reply.payload)
        return None

    def write_sampling_rate(self, value: SamplingRateMode) -> HarpMessage | None:
        """
        Writes a value to the SamplingRate register.

        Parameters
        ----------
        value : SamplingRateMode
            Value to write to the SamplingRate register.
        """
        address = AnalogInputRegisters.SAMPLING_RATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.SAMPLING_RATE", reply)

        return reply

    def read_di0_trigger(self) -> TriggerConfig | None:
        """
        Reads the contents of the DI0Trigger register.

        Returns
        -------
        TriggerConfig | None
            Value read from the DI0Trigger register.
        """
        address = AnalogInputRegisters.DI0_TRIGGER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DI0_TRIGGER", reply)

        if reply is not None:
            return TriggerConfig(reply.payload)
        return None

    def write_di0_trigger(self, value: TriggerConfig) -> HarpMessage | None:
        """
        Writes a value to the DI0Trigger register.

        Parameters
        ----------
        value : TriggerConfig
            Value to write to the DI0Trigger register.
        """
        address = AnalogInputRegisters.DI0_TRIGGER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DI0_TRIGGER", reply)

        return reply

    def read_do0_sync(self) -> SyncConfig | None:
        """
        Reads the contents of the DO0Sync register.

        Returns
        -------
        SyncConfig | None
            Value read from the DO0Sync register.
        """
        address = AnalogInputRegisters.DO0_SYNC
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO0_SYNC", reply)

        if reply is not None:
            return SyncConfig(reply.payload)
        return None

    def write_do0_sync(self, value: SyncConfig) -> HarpMessage | None:
        """
        Writes a value to the DO0Sync register.

        Parameters
        ----------
        value : SyncConfig
            Value to write to the DO0Sync register.
        """
        address = AnalogInputRegisters.DO0_SYNC
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO0_SYNC", reply)

        return reply

    def read_do0_pulse_width(self) -> int | None:
        """
        Reads the contents of the DO0PulseWidth register.

        Returns
        -------
        int | None
            Value read from the DO0PulseWidth register.
        """
        address = AnalogInputRegisters.DO0_PULSE_WIDTH
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO0_PULSE_WIDTH", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do0_pulse_width(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO0PulseWidth register.

        Parameters
        ----------
        value : int
            Value to write to the DO0PulseWidth register.
        """
        address = AnalogInputRegisters.DO0_PULSE_WIDTH
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO0_PULSE_WIDTH", reply)

        return reply

    def read_digital_output_set(self) -> DigitalOutputs | None:
        """
        Reads the contents of the DigitalOutputSet register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the DigitalOutputSet register.
        """
        address = AnalogInputRegisters.DIGITAL_OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DIGITAL_OUTPUT_SET", reply)

        if reply is not None:
            return DigitalOutputs(reply.payload)
        return None

    def write_digital_output_set(self, value: DigitalOutputs) -> HarpMessage | None:
        """
        Writes a value to the DigitalOutputSet register.

        Parameters
        ----------
        value : DigitalOutputs
            Value to write to the DigitalOutputSet register.
        """
        address = AnalogInputRegisters.DIGITAL_OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DIGITAL_OUTPUT_SET", reply)

        return reply

    def read_digital_output_clear(self) -> DigitalOutputs | None:
        """
        Reads the contents of the DigitalOutputClear register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the DigitalOutputClear register.
        """
        address = AnalogInputRegisters.DIGITAL_OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DIGITAL_OUTPUT_CLEAR", reply)

        if reply is not None:
            return DigitalOutputs(reply.payload)
        return None

    def write_digital_output_clear(self, value: DigitalOutputs) -> HarpMessage | None:
        """
        Writes a value to the DigitalOutputClear register.

        Parameters
        ----------
        value : DigitalOutputs
            Value to write to the DigitalOutputClear register.
        """
        address = AnalogInputRegisters.DIGITAL_OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DIGITAL_OUTPUT_CLEAR", reply)

        return reply

    def read_digital_output_toggle(self) -> DigitalOutputs | None:
        """
        Reads the contents of the DigitalOutputToggle register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the DigitalOutputToggle register.
        """
        address = AnalogInputRegisters.DIGITAL_OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DIGITAL_OUTPUT_TOGGLE", reply)

        if reply is not None:
            return DigitalOutputs(reply.payload)
        return None

    def write_digital_output_toggle(self, value: DigitalOutputs) -> HarpMessage | None:
        """
        Writes a value to the DigitalOutputToggle register.

        Parameters
        ----------
        value : DigitalOutputs
            Value to write to the DigitalOutputToggle register.
        """
        address = AnalogInputRegisters.DIGITAL_OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DIGITAL_OUTPUT_TOGGLE", reply)

        return reply

    def read_digital_output_state(self) -> DigitalOutputs | None:
        """
        Reads the contents of the DigitalOutputState register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the DigitalOutputState register.
        """
        address = AnalogInputRegisters.DIGITAL_OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DIGITAL_OUTPUT_STATE", reply)

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
        address = AnalogInputRegisters.DIGITAL_OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DIGITAL_OUTPUT_STATE", reply)

        return reply

    def read_sync_output(self) -> StartSyncOutputTarget | None:
        """
        Reads the contents of the SyncOutput register.

        Returns
        -------
        StartSyncOutputTarget | None
            Value read from the SyncOutput register.
        """
        address = AnalogInputRegisters.SYNC_OUTPUT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.SYNC_OUTPUT", reply)

        if reply is not None:
            return StartSyncOutputTarget(reply.payload)
        return None

    def write_sync_output(self, value: StartSyncOutputTarget) -> HarpMessage | None:
        """
        Writes a value to the SyncOutput register.

        Parameters
        ----------
        value : StartSyncOutputTarget
            Value to write to the SyncOutput register.
        """
        address = AnalogInputRegisters.SYNC_OUTPUT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.SYNC_OUTPUT", reply)

        return reply

    def read_do0_target_channel(self) -> AdcChannel | None:
        """
        Reads the contents of the DO0TargetChannel register.

        Returns
        -------
        AdcChannel | None
            Value read from the DO0TargetChannel register.
        """
        address = AnalogInputRegisters.DO0_TARGET_CHANNEL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO0_TARGET_CHANNEL", reply)

        if reply is not None:
            return AdcChannel(reply.payload)
        return None

    def write_do0_target_channel(self, value: AdcChannel) -> HarpMessage | None:
        """
        Writes a value to the DO0TargetChannel register.

        Parameters
        ----------
        value : AdcChannel
            Value to write to the DO0TargetChannel register.
        """
        address = AnalogInputRegisters.DO0_TARGET_CHANNEL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO0_TARGET_CHANNEL", reply)

        return reply

    def read_do1_target_channel(self) -> AdcChannel | None:
        """
        Reads the contents of the DO1TargetChannel register.

        Returns
        -------
        AdcChannel | None
            Value read from the DO1TargetChannel register.
        """
        address = AnalogInputRegisters.DO1_TARGET_CHANNEL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO1_TARGET_CHANNEL", reply)

        if reply is not None:
            return AdcChannel(reply.payload)
        return None

    def write_do1_target_channel(self, value: AdcChannel) -> HarpMessage | None:
        """
        Writes a value to the DO1TargetChannel register.

        Parameters
        ----------
        value : AdcChannel
            Value to write to the DO1TargetChannel register.
        """
        address = AnalogInputRegisters.DO1_TARGET_CHANNEL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO1_TARGET_CHANNEL", reply)

        return reply

    def read_do2_target_channel(self) -> AdcChannel | None:
        """
        Reads the contents of the DO2TargetChannel register.

        Returns
        -------
        AdcChannel | None
            Value read from the DO2TargetChannel register.
        """
        address = AnalogInputRegisters.DO2_TARGET_CHANNEL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO2_TARGET_CHANNEL", reply)

        if reply is not None:
            return AdcChannel(reply.payload)
        return None

    def write_do2_target_channel(self, value: AdcChannel) -> HarpMessage | None:
        """
        Writes a value to the DO2TargetChannel register.

        Parameters
        ----------
        value : AdcChannel
            Value to write to the DO2TargetChannel register.
        """
        address = AnalogInputRegisters.DO2_TARGET_CHANNEL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO2_TARGET_CHANNEL", reply)

        return reply

    def read_do3_target_channel(self) -> AdcChannel | None:
        """
        Reads the contents of the DO3TargetChannel register.

        Returns
        -------
        AdcChannel | None
            Value read from the DO3TargetChannel register.
        """
        address = AnalogInputRegisters.DO3_TARGET_CHANNEL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO3_TARGET_CHANNEL", reply)

        if reply is not None:
            return AdcChannel(reply.payload)
        return None

    def write_do3_target_channel(self, value: AdcChannel) -> HarpMessage | None:
        """
        Writes a value to the DO3TargetChannel register.

        Parameters
        ----------
        value : AdcChannel
            Value to write to the DO3TargetChannel register.
        """
        address = AnalogInputRegisters.DO3_TARGET_CHANNEL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO3_TARGET_CHANNEL", reply)

        return reply

    def read_do0_threshold(self) -> int | None:
        """
        Reads the contents of the DO0Threshold register.

        Returns
        -------
        int | None
            Value read from the DO0Threshold register.
        """
        address = AnalogInputRegisters.DO0_THRESHOLD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.S16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO0_THRESHOLD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do0_threshold(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO0Threshold register.

        Parameters
        ----------
        value : int
            Value to write to the DO0Threshold register.
        """
        address = AnalogInputRegisters.DO0_THRESHOLD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.S16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO0_THRESHOLD", reply)

        return reply

    def read_do1_threshold(self) -> int | None:
        """
        Reads the contents of the DO1Threshold register.

        Returns
        -------
        int | None
            Value read from the DO1Threshold register.
        """
        address = AnalogInputRegisters.DO1_THRESHOLD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.S16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO1_THRESHOLD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do1_threshold(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO1Threshold register.

        Parameters
        ----------
        value : int
            Value to write to the DO1Threshold register.
        """
        address = AnalogInputRegisters.DO1_THRESHOLD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.S16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO1_THRESHOLD", reply)

        return reply

    def read_do2_threshold(self) -> int | None:
        """
        Reads the contents of the DO2Threshold register.

        Returns
        -------
        int | None
            Value read from the DO2Threshold register.
        """
        address = AnalogInputRegisters.DO2_THRESHOLD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.S16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO2_THRESHOLD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do2_threshold(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO2Threshold register.

        Parameters
        ----------
        value : int
            Value to write to the DO2Threshold register.
        """
        address = AnalogInputRegisters.DO2_THRESHOLD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.S16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO2_THRESHOLD", reply)

        return reply

    def read_do3_threshold(self) -> int | None:
        """
        Reads the contents of the DO3Threshold register.

        Returns
        -------
        int | None
            Value read from the DO3Threshold register.
        """
        address = AnalogInputRegisters.DO3_THRESHOLD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.S16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO3_THRESHOLD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do3_threshold(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO3Threshold register.

        Parameters
        ----------
        value : int
            Value to write to the DO3Threshold register.
        """
        address = AnalogInputRegisters.DO3_THRESHOLD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.S16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO3_THRESHOLD", reply)

        return reply

    def read_do0_time_above_threshold(self) -> int | None:
        """
        Reads the contents of the DO0TimeAboveThreshold register.

        Returns
        -------
        int | None
            Value read from the DO0TimeAboveThreshold register.
        """
        address = AnalogInputRegisters.DO0_TIME_ABOVE_THRESHOLD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO0_TIME_ABOVE_THRESHOLD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do0_time_above_threshold(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO0TimeAboveThreshold register.

        Parameters
        ----------
        value : int
            Value to write to the DO0TimeAboveThreshold register.
        """
        address = AnalogInputRegisters.DO0_TIME_ABOVE_THRESHOLD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO0_TIME_ABOVE_THRESHOLD", reply)

        return reply

    def read_do1_time_above_threshold(self) -> int | None:
        """
        Reads the contents of the DO1TimeAboveThreshold register.

        Returns
        -------
        int | None
            Value read from the DO1TimeAboveThreshold register.
        """
        address = AnalogInputRegisters.DO1_TIME_ABOVE_THRESHOLD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO1_TIME_ABOVE_THRESHOLD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do1_time_above_threshold(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO1TimeAboveThreshold register.

        Parameters
        ----------
        value : int
            Value to write to the DO1TimeAboveThreshold register.
        """
        address = AnalogInputRegisters.DO1_TIME_ABOVE_THRESHOLD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO1_TIME_ABOVE_THRESHOLD", reply)

        return reply

    def read_do2_time_above_threshold(self) -> int | None:
        """
        Reads the contents of the DO2TimeAboveThreshold register.

        Returns
        -------
        int | None
            Value read from the DO2TimeAboveThreshold register.
        """
        address = AnalogInputRegisters.DO2_TIME_ABOVE_THRESHOLD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO2_TIME_ABOVE_THRESHOLD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do2_time_above_threshold(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO2TimeAboveThreshold register.

        Parameters
        ----------
        value : int
            Value to write to the DO2TimeAboveThreshold register.
        """
        address = AnalogInputRegisters.DO2_TIME_ABOVE_THRESHOLD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO2_TIME_ABOVE_THRESHOLD", reply)

        return reply

    def read_do3_time_above_threshold(self) -> int | None:
        """
        Reads the contents of the DO3TimeAboveThreshold register.

        Returns
        -------
        int | None
            Value read from the DO3TimeAboveThreshold register.
        """
        address = AnalogInputRegisters.DO3_TIME_ABOVE_THRESHOLD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO3_TIME_ABOVE_THRESHOLD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do3_time_above_threshold(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO3TimeAboveThreshold register.

        Parameters
        ----------
        value : int
            Value to write to the DO3TimeAboveThreshold register.
        """
        address = AnalogInputRegisters.DO3_TIME_ABOVE_THRESHOLD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO3_TIME_ABOVE_THRESHOLD", reply)

        return reply

    def read_do0_time_below_threshold(self) -> int | None:
        """
        Reads the contents of the DO0TimeBelowThreshold register.

        Returns
        -------
        int | None
            Value read from the DO0TimeBelowThreshold register.
        """
        address = AnalogInputRegisters.DO0_TIME_BELOW_THRESHOLD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO0_TIME_BELOW_THRESHOLD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do0_time_below_threshold(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO0TimeBelowThreshold register.

        Parameters
        ----------
        value : int
            Value to write to the DO0TimeBelowThreshold register.
        """
        address = AnalogInputRegisters.DO0_TIME_BELOW_THRESHOLD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO0_TIME_BELOW_THRESHOLD", reply)

        return reply

    def read_do1_time_below_threshold(self) -> int | None:
        """
        Reads the contents of the DO1TimeBelowThreshold register.

        Returns
        -------
        int | None
            Value read from the DO1TimeBelowThreshold register.
        """
        address = AnalogInputRegisters.DO1_TIME_BELOW_THRESHOLD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO1_TIME_BELOW_THRESHOLD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do1_time_below_threshold(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO1TimeBelowThreshold register.

        Parameters
        ----------
        value : int
            Value to write to the DO1TimeBelowThreshold register.
        """
        address = AnalogInputRegisters.DO1_TIME_BELOW_THRESHOLD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO1_TIME_BELOW_THRESHOLD", reply)

        return reply

    def read_do2_time_below_threshold(self) -> int | None:
        """
        Reads the contents of the DO2TimeBelowThreshold register.

        Returns
        -------
        int | None
            Value read from the DO2TimeBelowThreshold register.
        """
        address = AnalogInputRegisters.DO2_TIME_BELOW_THRESHOLD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO2_TIME_BELOW_THRESHOLD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do2_time_below_threshold(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO2TimeBelowThreshold register.

        Parameters
        ----------
        value : int
            Value to write to the DO2TimeBelowThreshold register.
        """
        address = AnalogInputRegisters.DO2_TIME_BELOW_THRESHOLD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO2_TIME_BELOW_THRESHOLD", reply)

        return reply

    def read_do3_time_below_threshold(self) -> int | None:
        """
        Reads the contents of the DO3TimeBelowThreshold register.

        Returns
        -------
        int | None
            Value read from the DO3TimeBelowThreshold register.
        """
        address = AnalogInputRegisters.DO3_TIME_BELOW_THRESHOLD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("AnalogInputRegisters.DO3_TIME_BELOW_THRESHOLD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_do3_time_below_threshold(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DO3TimeBelowThreshold register.

        Parameters
        ----------
        value : int
            Value to write to the DO3TimeBelowThreshold register.
        """
        address = AnalogInputRegisters.DO3_TIME_BELOW_THRESHOLD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("AnalogInputRegisters.DO3_TIME_BELOW_THRESHOLD", reply)

        return reply

