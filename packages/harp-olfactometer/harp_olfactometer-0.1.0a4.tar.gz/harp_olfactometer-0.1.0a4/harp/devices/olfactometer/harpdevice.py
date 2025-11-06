from dataclasses import dataclass
from enum import IntEnum, IntFlag

from harp.protocol import MessageType, PayloadType
from harp.protocol.exceptions import HarpException, HarpReadException, HarpWriteException
from harp.protocol.messages import HarpMessage
from harp.serial import Device


@dataclass
class FlowmeterPayload:
    Channel0: int
    Channel1: int
    Channel2: int
    Channel3: int
    Channel4: int


@dataclass
class ChannelsTargetFlowPayload:
    Channel0: float
    Channel1: float
    Channel2: float
    Channel3: float
    Channel4: float


class DigitalOutputs(IntFlag):
    """
    Specifies the state of the digital outputs.

    Attributes
    ----------
    DO0 : int
        _No description currently available_
    DO1 : int
        _No description currently available_
    """

    NONE = 0x0
    DO0 = 0x1
    DO1 = 0x2


class Valves(IntFlag):
    """
    Specifies the state of the valves.

    Attributes
    ----------
    VALVE0 : int
        _No description currently available_
    VALVE1 : int
        _No description currently available_
    VALVE2 : int
        _No description currently available_
    VALVE3 : int
        _No description currently available_
    END_VALVE0 : int
        _No description currently available_
    END_VALVE1 : int
        _No description currently available_
    VALVE_DUMMY : int
        _No description currently available_
    CHECK_VALVE0 : int
        _No description currently available_
    CHECK_VALVE1 : int
        _No description currently available_
    CHECK_VALVE2 : int
        _No description currently available_
    CHECK_VALVE3 : int
        _No description currently available_
    """

    NONE = 0x0
    VALVE0 = 0x1
    VALVE1 = 0x2
    VALVE2 = 0x4
    VALVE3 = 0x8
    END_VALVE0 = 0x10
    END_VALVE1 = 0x20
    VALVE_DUMMY = 0x40
    CHECK_VALVE0 = 0x100
    CHECK_VALVE1 = 0x200
    CHECK_VALVE2 = 0x400
    CHECK_VALVE3 = 0x800


class OdorValves(IntFlag):
    """
    Specifies the state of the odor valves.

    Attributes
    ----------
    VALVE0 : int
        _No description currently available_
    VALVE1 : int
        _No description currently available_
    VALVE2 : int
        _No description currently available_
    VALVE3 : int
        _No description currently available_
    """

    NONE = 0x0
    VALVE0 = 0x1
    VALVE1 = 0x2
    VALVE2 = 0x4
    VALVE3 = 0x8


class CheckValves(IntFlag):
    """
    Specifies the state of the check valves.

    Attributes
    ----------
    CHECK_VALVE0 : int
        _No description currently available_
    CHECK_VALVE1 : int
        _No description currently available_
    CHECK_VALVE2 : int
        _No description currently available_
    CHECK_VALVE3 : int
        _No description currently available_
    """

    NONE = 0x0
    CHECK_VALVE0 = 0x100
    CHECK_VALVE1 = 0x200
    CHECK_VALVE2 = 0x400
    CHECK_VALVE3 = 0x800


class EndValves(IntFlag):
    """
    Specifies the state of the end valves.

    Attributes
    ----------
    END_VALVE0 : int
        _No description currently available_
    END_VALVE1 : int
        _No description currently available_
    VALVE_DUMMY : int
        _No description currently available_
    """

    NONE = 0x0
    END_VALVE0 = 0x10
    END_VALVE1 = 0x20
    VALVE_DUMMY = 0x40


class OlfactometerEvents(IntFlag):
    """
    The events that can be enabled/disabled.

    Attributes
    ----------
    FLOWMETER : int
        _No description currently available_
    DI0_TRIGGER : int
        _No description currently available_
    CHANNEL_ACTUAL_FLOW : int
        _No description currently available_
    """

    NONE = 0x0
    FLOWMETER = 0x1
    DI0_TRIGGER = 0x2
    CHANNEL_ACTUAL_FLOW = 0x4


class DigitalState(IntEnum):
    """
    The state of a digital pin.

    Attributes
    ----------
    LOW : int
        _No description currently available_
    HIGH : int
        _No description currently available_
    """

    LOW = 0
    HIGH = 1


class DO0SyncConfig(IntEnum):
    """
    Available configurations when using DO0 pin to report firmware events.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    MIMIC_ENABLE_FLOW : int
        _No description currently available_
    """

    NONE = 0
    MIMIC_ENABLE_FLOW = 1


class DO1SyncConfig(IntEnum):
    """
    Available configurations when using DO1 pin to report firmware events.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    MIMIC_ENABLE_FLOW : int
        _No description currently available_
    """

    NONE = 0
    MIMIC_ENABLE_FLOW = 1


class DI0TriggerConfig(IntEnum):
    """
    Specifies the configuration of the digital input 0 (DIN0).

    Attributes
    ----------
    SYNC : int
        _No description currently available_
    ENABLE_FLOW_WHILE_HIGH : int
        _No description currently available_
    VALVE_TOGGLE : int
        _No description currently available_
    """

    SYNC = 0
    ENABLE_FLOW_WHILE_HIGH = 1
    VALVE_TOGGLE = 2


class MimicOutputs(IntEnum):
    """
    Specifies the target IO on which to mimic the specified register.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    DO0 : int
        _No description currently available_
    DO1 : int
        _No description currently available_
    """

    NONE = 0
    DO0 = 1
    DO1 = 2


class Channel3RangeConfig(IntEnum):
    """
    Available flow ranges for channel 3 (ml/min).

    Attributes
    ----------
    FLOW_RATE100 : int
        _No description currently available_
    FLOW_RATE1000 : int
        _No description currently available_
    """

    FLOW_RATE100 = 0
    FLOW_RATE1000 = 1


class OlfactometerRegisters(IntEnum):
    """Enum for all available registers in the Olfactometer device.

    Attributes
    ----------
    ENABLE_FLOW : int
        Starts or stops the flow in all channels.
    FLOWMETER : int
        Value of single ADC read from all flowmeter channels.
    DI0_STATE : int
        State of the digital input pin 0.
    CHANNEL0_USER_CALIBRATION : int
        Calibration values for a single channel [x0,...xn], where x= ADC raw value for 0:10:100 ml/min.
    CHANNEL1_USER_CALIBRATION : int
        Calibration values for a single channel [x0,...xn], where x= ADC raw value for 0:10:100 ml/min.
    CHANNEL2_USER_CALIBRATION : int
        Calibration values for a single channel [x0,...xn], where x= ADC raw value for 0:10:100 ml/min.
    CHANNEL3_USER_CALIBRATION : int
        Calibration values for a single channel [x0,...xn], where x= ADC raw value for 0:10:100 ml/min.
    CHANNEL4_USER_CALIBRATION : int
        Calibration values specific for channel 4 [x0,...xn], where x= ADC raw value for 0:100:1000 ml/min.
    CHANNEL3_USER_CALIBRATION_AUX : int
        Calibration values specific for channel 3 if Channel3RangeConfig = FlowRate1000. [x0,...xn], where x= ADC raw value for 0:100:1000 ml/min.
    ENABLE_USER_CALIBRATION : int
        Override the factory calibration values, replacing with CHX_USER_CALIBRATION.
    CHANNEL0_TARGET_FLOW : int
        Sets the flow-rate rate for channel 0 [ml/min].
    CHANNEL1_TARGET_FLOW : int
        Sets the flow-rate rate for channel 1 [ml/min].
    CHANNEL2_TARGET_FLOW : int
        Sets the flow-rate rate for channel 2 [ml/min].
    CHANNEL3_TARGET_FLOW : int
        Sets the flow-rate rate for channel 3 [ml/min].
    CHANNEL4_TARGET_FLOW : int
        Sets the flow-rate rate for channel 4 [ml/min].
    CHANNELS_TARGET_FLOW : int
        Sets the flow-rate rate for all channels [ml/min].
    CHANNEL0_ACTUAL_FLOW : int
        Actual flow-rate read for channel 0 - flowmeter 0 [ml/min].
    CHANNEL1_ACTUAL_FLOW : int
        Actual flow-rate read for channel 1 - flowmeter 1 [ml/min].
    CHANNEL2_ACTUAL_FLOW : int
        Actual flow-rate read for channel 2 - flowmeter 2 [ml/min].
    CHANNEL3_ACTUAL_FLOW : int
        Actual flow-rate read for channel 3 - flowmeter 3 [ml/min].
    CHANNEL4_ACTUAL_FLOW : int
        Actual flow-rate read for channel 4 - flowmeter 4 [ml/min].
    CHANNEL0_DUTY_CYCLE : int
        Duty cycle for proportional valve 0 [%].
    CHANNEL1_DUTY_CYCLE : int
        Duty cycle for proportional valve 1 [%].
    CHANNEL2_DUTY_CYCLE : int
        Duty cycle for proportional valve 2 [%].
    CHANNEL3_DUTY_CYCLE : int
        Duty cycle for proportional valve 3 [%].
    CHANNEL4_DUTY_CYCLE : int
        Duty cycle for proportional valve 4 [%].
    DIGITAL_OUTPUT_SET : int
        Set the specified digital output lines.
    DIGITAL_OUTPUT_CLEAR : int
        Clears the specified digital output lines.
    DIGITAL_OUTPUT_TOGGLE : int
        Toggles the specified digital output lines.
    DIGITAL_OUTPUT_STATE : int
        Write the state of all digital output lines.
    ENABLE_VALVE_PULSE : int
        Enable pulse mode for valves.
    VALVE_SET : int
        Set the specified valve output lines.
    VALVE_CLEAR : int
        Clears the specified valve output lines.
    VALVE_TOGGLE : int
        Toggles the specified valve output lines.
    VALVE_STATE : int
        Controls the specified valve output lines.
    ODOR_VALVE_STATE : int
        Write the state of all odor valve output lines.
    END_VALVE_STATE : int
        Write the state of all end valve output lines.
    CHECK_VALVE_STATE : int
        Write the state of all check valve output lines.
    VALVE0_PULSE_DURATION : int
        Sets the pulse duration for Valve0.
    VALVE1_PULSE_DURATION : int
        Sets the pulse duration for Valve1.
    VALVE2_PULSE_DURATION : int
        Sets the pulse duration for Valve2.
    VALVE3_PULSE_DURATION : int
        Sets the pulse duration for Valve3.
    CHECK_VALVE0_DELAY_PULSE_DURATION : int
        Sets the delay when CheckValvesConfig is Sync. Otherwise, sets the pulse duration for Check Valve0.
    CHECK_VALVE1_DELAY_PULSE_DURATION : int
        Sets the delay when CheckValvesConfig is Sync. Otherwise, sets the pulse duration for Check Valve1.
    CHECK_VALVE2_DELAY_PULSE_DURATION : int
        Sets the delay when CheckValvesConfig is Sync. Otherwise, sets the pulse duration for Check Valve2.
    CHECK_VALVE3_DELAY_PULSE_DURATION : int
        Sets the delay when CheckValvesConfig is Sync. Otherwise, sets the pulse duration for Check Valve3.
    END_VALVE0_PULSE_DURATION : int
        Sets the pulse duration for EndValve0.
    END_VALVE1_PULSE_DURATION : int
        Sets the pulse duration for EndValve1.
    DO0_SYNC : int
        Configuration of the digital output 0 (DOUT0).
    DO1_SYNC : int
        Configuration of the digital output 1 (DOUT1).
    DI0_TRIGGER : int
        Configuration of the digital input pin 0 (DIN0).
    MIMIC_VALVE0 : int
        Mimic Valve0.
    MIMIC_VALVE1 : int
        Mimic Valve1.
    MIMIC_VALVE2 : int
        Mimic Valve2.
    MIMIC_VALVE3 : int
        Mimic Valve3.
    MIMIC_CHECK_VALVE0 : int
        Mimic Check Valve0.
    MIMIC_CHECK_VALVE1 : int
        Mimic Check Valve1.
    MIMIC_CHECK_VALVE2 : int
        Mimic Check Valve2.
    MIMIC_CHECK_VALVE3 : int
        Mimic Check Valve3.
    MIMIC_END_VALVE0 : int
        Mimic EndValve0.
    MIMIC_END_VALVE1 : int
        Mimic EndValve1.
    ENABLE_VALVE_EXTERNAL_CONTROL : int
        Enable the valves control via low-level IO screw terminals.
    CHANNEL3_RANGE : int
        Selects the flow range for the channel 3.
    ENABLE_CHECK_VALVE_SYNC : int
        Enable the check valve to sync with the respective odor valve.
    TEMPERATURE_VALUE : int
        Temperature sensor reading value.
    ENABLE_TEMPERATURE_CALIBRATION : int
        Enable flow adjustment based on the temperature calibration.
    TEMPERATURE_CALIBRATION_VALUE : int
        Temperature value measured during the device calibration.
    ENABLE_EVENTS : int
        Specifies the active events in the device.
    """

    ENABLE_FLOW = 32
    FLOWMETER = 33
    DI0_STATE = 34
    CHANNEL0_USER_CALIBRATION = 35
    CHANNEL1_USER_CALIBRATION = 36
    CHANNEL2_USER_CALIBRATION = 37
    CHANNEL3_USER_CALIBRATION = 38
    CHANNEL4_USER_CALIBRATION = 39
    CHANNEL3_USER_CALIBRATION_AUX = 40
    ENABLE_USER_CALIBRATION = 41
    CHANNEL0_TARGET_FLOW = 42
    CHANNEL1_TARGET_FLOW = 43
    CHANNEL2_TARGET_FLOW = 44
    CHANNEL3_TARGET_FLOW = 45
    CHANNEL4_TARGET_FLOW = 46
    CHANNELS_TARGET_FLOW = 47
    CHANNEL0_ACTUAL_FLOW = 48
    CHANNEL1_ACTUAL_FLOW = 49
    CHANNEL2_ACTUAL_FLOW = 50
    CHANNEL3_ACTUAL_FLOW = 51
    CHANNEL4_ACTUAL_FLOW = 52
    CHANNEL0_DUTY_CYCLE = 58
    CHANNEL1_DUTY_CYCLE = 59
    CHANNEL2_DUTY_CYCLE = 60
    CHANNEL3_DUTY_CYCLE = 61
    CHANNEL4_DUTY_CYCLE = 62
    DIGITAL_OUTPUT_SET = 63
    DIGITAL_OUTPUT_CLEAR = 64
    DIGITAL_OUTPUT_TOGGLE = 65
    DIGITAL_OUTPUT_STATE = 66
    ENABLE_VALVE_PULSE = 67
    VALVE_SET = 68
    VALVE_CLEAR = 69
    VALVE_TOGGLE = 70
    VALVE_STATE = 71
    ODOR_VALVE_STATE = 72
    END_VALVE_STATE = 73
    CHECK_VALVE_STATE = 74
    VALVE0_PULSE_DURATION = 75
    VALVE1_PULSE_DURATION = 76
    VALVE2_PULSE_DURATION = 77
    VALVE3_PULSE_DURATION = 78
    CHECK_VALVE0_DELAY_PULSE_DURATION = 79
    CHECK_VALVE1_DELAY_PULSE_DURATION = 80
    CHECK_VALVE2_DELAY_PULSE_DURATION = 81
    CHECK_VALVE3_DELAY_PULSE_DURATION = 82
    END_VALVE0_PULSE_DURATION = 83
    END_VALVE1_PULSE_DURATION = 84
    DO0_SYNC = 86
    DO1_SYNC = 87
    DI0_TRIGGER = 88
    MIMIC_VALVE0 = 89
    MIMIC_VALVE1 = 90
    MIMIC_VALVE2 = 91
    MIMIC_VALVE3 = 92
    MIMIC_CHECK_VALVE0 = 93
    MIMIC_CHECK_VALVE1 = 94
    MIMIC_CHECK_VALVE2 = 95
    MIMIC_CHECK_VALVE3 = 96
    MIMIC_END_VALVE0 = 97
    MIMIC_END_VALVE1 = 98
    ENABLE_VALVE_EXTERNAL_CONTROL = 100
    CHANNEL3_RANGE = 101
    ENABLE_CHECK_VALVE_SYNC = 102
    TEMPERATURE_VALUE = 103
    ENABLE_TEMPERATURE_CALIBRATION = 104
    TEMPERATURE_CALIBRATION_VALUE = 105
    ENABLE_EVENTS = 106


class Olfactometer(Device):
    """
    Olfactometer class for controlling the device.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect and load already happened in the base class
        # verify that WHO_AM_I matches the expected value
        if self.WHO_AM_I != 1140:
            self.disconnect()
            raise HarpException(f"WHO_AM_I mismatch: expected {1140}, got {self.WHO_AM_I}")

    def read_enable_flow(self) -> bool | None:
        """
        Reads the contents of the EnableFlow register.

        Returns
        -------
        bool | None
            Value read from the EnableFlow register.
        """
        address = OlfactometerRegisters.ENABLE_FLOW
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.ENABLE_FLOW", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_enable_flow(self, value: bool) -> HarpMessage | None:
        """
        Writes a value to the EnableFlow register.

        Parameters
        ----------
        value : bool
            Value to write to the EnableFlow register.
        """
        address = OlfactometerRegisters.ENABLE_FLOW
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.ENABLE_FLOW", reply)

        return reply

    def read_flowmeter(self) -> FlowmeterPayload | None:
        """
        Reads the contents of the Flowmeter register.

        Returns
        -------
        FlowmeterPayload | None
            Value read from the Flowmeter register.
        """
        address = OlfactometerRegisters.FLOWMETER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.S16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.FLOWMETER", reply)

        if reply is not None:
            # Map payload (list/array) to dataclass fields by offset
            payload = reply.payload
            return FlowmeterPayload(
                Channel0=payload[0],
                Channel1=payload[1],
                Channel2=payload[2],
                Channel3=payload[3],
                Channel4=payload[4]
            )
        return None

    def read_di0_state(self) -> DigitalState | None:
        """
        Reads the contents of the DI0State register.

        Returns
        -------
        DigitalState | None
            Value read from the DI0State register.
        """
        address = OlfactometerRegisters.DI0_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.DI0_STATE", reply)

        if reply is not None:
            return DigitalState(reply.payload)
        return None

    def read_channel0_user_calibration(self) -> list[int] | None:
        """
        Reads the contents of the Channel0UserCalibration register.

        Returns
        -------
        list[int] | None
            Value read from the Channel0UserCalibration register.
        """
        address = OlfactometerRegisters.CHANNEL0_USER_CALIBRATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL0_USER_CALIBRATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel0_user_calibration(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the Channel0UserCalibration register.

        Parameters
        ----------
        value : list[int]
            Value to write to the Channel0UserCalibration register.
        """
        address = OlfactometerRegisters.CHANNEL0_USER_CALIBRATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL0_USER_CALIBRATION", reply)

        return reply

    def read_channel1_user_calibration(self) -> list[int] | None:
        """
        Reads the contents of the Channel1UserCalibration register.

        Returns
        -------
        list[int] | None
            Value read from the Channel1UserCalibration register.
        """
        address = OlfactometerRegisters.CHANNEL1_USER_CALIBRATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL1_USER_CALIBRATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel1_user_calibration(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the Channel1UserCalibration register.

        Parameters
        ----------
        value : list[int]
            Value to write to the Channel1UserCalibration register.
        """
        address = OlfactometerRegisters.CHANNEL1_USER_CALIBRATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL1_USER_CALIBRATION", reply)

        return reply

    def read_channel2_user_calibration(self) -> list[int] | None:
        """
        Reads the contents of the Channel2UserCalibration register.

        Returns
        -------
        list[int] | None
            Value read from the Channel2UserCalibration register.
        """
        address = OlfactometerRegisters.CHANNEL2_USER_CALIBRATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL2_USER_CALIBRATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel2_user_calibration(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the Channel2UserCalibration register.

        Parameters
        ----------
        value : list[int]
            Value to write to the Channel2UserCalibration register.
        """
        address = OlfactometerRegisters.CHANNEL2_USER_CALIBRATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL2_USER_CALIBRATION", reply)

        return reply

    def read_channel3_user_calibration(self) -> list[int] | None:
        """
        Reads the contents of the Channel3UserCalibration register.

        Returns
        -------
        list[int] | None
            Value read from the Channel3UserCalibration register.
        """
        address = OlfactometerRegisters.CHANNEL3_USER_CALIBRATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL3_USER_CALIBRATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel3_user_calibration(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the Channel3UserCalibration register.

        Parameters
        ----------
        value : list[int]
            Value to write to the Channel3UserCalibration register.
        """
        address = OlfactometerRegisters.CHANNEL3_USER_CALIBRATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL3_USER_CALIBRATION", reply)

        return reply

    def read_channel4_user_calibration(self) -> list[int] | None:
        """
        Reads the contents of the Channel4UserCalibration register.

        Returns
        -------
        list[int] | None
            Value read from the Channel4UserCalibration register.
        """
        address = OlfactometerRegisters.CHANNEL4_USER_CALIBRATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL4_USER_CALIBRATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel4_user_calibration(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the Channel4UserCalibration register.

        Parameters
        ----------
        value : list[int]
            Value to write to the Channel4UserCalibration register.
        """
        address = OlfactometerRegisters.CHANNEL4_USER_CALIBRATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL4_USER_CALIBRATION", reply)

        return reply

    def read_channel3_user_calibration_aux(self) -> list[int] | None:
        """
        Reads the contents of the Channel3UserCalibrationAux register.

        Returns
        -------
        list[int] | None
            Value read from the Channel3UserCalibrationAux register.
        """
        address = OlfactometerRegisters.CHANNEL3_USER_CALIBRATION_AUX
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL3_USER_CALIBRATION_AUX", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel3_user_calibration_aux(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the Channel3UserCalibrationAux register.

        Parameters
        ----------
        value : list[int]
            Value to write to the Channel3UserCalibrationAux register.
        """
        address = OlfactometerRegisters.CHANNEL3_USER_CALIBRATION_AUX
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL3_USER_CALIBRATION_AUX", reply)

        return reply

    def read_enable_user_calibration(self) -> bool | None:
        """
        Reads the contents of the EnableUserCalibration register.

        Returns
        -------
        bool | None
            Value read from the EnableUserCalibration register.
        """
        address = OlfactometerRegisters.ENABLE_USER_CALIBRATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.ENABLE_USER_CALIBRATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_enable_user_calibration(self, value: bool) -> HarpMessage | None:
        """
        Writes a value to the EnableUserCalibration register.

        Parameters
        ----------
        value : bool
            Value to write to the EnableUserCalibration register.
        """
        address = OlfactometerRegisters.ENABLE_USER_CALIBRATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.ENABLE_USER_CALIBRATION", reply)

        return reply

    def read_channel0_target_flow(self) -> float | None:
        """
        Reads the contents of the Channel0TargetFlow register.

        Returns
        -------
        float | None
            Value read from the Channel0TargetFlow register.
        """
        address = OlfactometerRegisters.CHANNEL0_TARGET_FLOW
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL0_TARGET_FLOW", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel0_target_flow(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Channel0TargetFlow register.

        Parameters
        ----------
        value : float
            Value to write to the Channel0TargetFlow register.
        """
        address = OlfactometerRegisters.CHANNEL0_TARGET_FLOW
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL0_TARGET_FLOW", reply)

        return reply

    def read_channel1_target_flow(self) -> float | None:
        """
        Reads the contents of the Channel1TargetFlow register.

        Returns
        -------
        float | None
            Value read from the Channel1TargetFlow register.
        """
        address = OlfactometerRegisters.CHANNEL1_TARGET_FLOW
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL1_TARGET_FLOW", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel1_target_flow(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Channel1TargetFlow register.

        Parameters
        ----------
        value : float
            Value to write to the Channel1TargetFlow register.
        """
        address = OlfactometerRegisters.CHANNEL1_TARGET_FLOW
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL1_TARGET_FLOW", reply)

        return reply

    def read_channel2_target_flow(self) -> float | None:
        """
        Reads the contents of the Channel2TargetFlow register.

        Returns
        -------
        float | None
            Value read from the Channel2TargetFlow register.
        """
        address = OlfactometerRegisters.CHANNEL2_TARGET_FLOW
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL2_TARGET_FLOW", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel2_target_flow(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Channel2TargetFlow register.

        Parameters
        ----------
        value : float
            Value to write to the Channel2TargetFlow register.
        """
        address = OlfactometerRegisters.CHANNEL2_TARGET_FLOW
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL2_TARGET_FLOW", reply)

        return reply

    def read_channel3_target_flow(self) -> float | None:
        """
        Reads the contents of the Channel3TargetFlow register.

        Returns
        -------
        float | None
            Value read from the Channel3TargetFlow register.
        """
        address = OlfactometerRegisters.CHANNEL3_TARGET_FLOW
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL3_TARGET_FLOW", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel3_target_flow(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Channel3TargetFlow register.

        Parameters
        ----------
        value : float
            Value to write to the Channel3TargetFlow register.
        """
        address = OlfactometerRegisters.CHANNEL3_TARGET_FLOW
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL3_TARGET_FLOW", reply)

        return reply

    def read_channel4_target_flow(self) -> float | None:
        """
        Reads the contents of the Channel4TargetFlow register.

        Returns
        -------
        float | None
            Value read from the Channel4TargetFlow register.
        """
        address = OlfactometerRegisters.CHANNEL4_TARGET_FLOW
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL4_TARGET_FLOW", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel4_target_flow(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Channel4TargetFlow register.

        Parameters
        ----------
        value : float
            Value to write to the Channel4TargetFlow register.
        """
        address = OlfactometerRegisters.CHANNEL4_TARGET_FLOW
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL4_TARGET_FLOW", reply)

        return reply

    def read_channels_target_flow(self) -> ChannelsTargetFlowPayload | None:
        """
        Reads the contents of the ChannelsTargetFlow register.

        Returns
        -------
        ChannelsTargetFlowPayload | None
            Value read from the ChannelsTargetFlow register.
        """
        address = OlfactometerRegisters.CHANNELS_TARGET_FLOW
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNELS_TARGET_FLOW", reply)

        if reply is not None:
            # Map payload (list/array) to dataclass fields by offset
            payload = reply.payload
            return ChannelsTargetFlowPayload(
                Channel0=payload[0],
                Channel1=payload[1],
                Channel2=payload[2],
                Channel3=payload[3],
                Channel4=payload[4]
            )
        return None

    def write_channels_target_flow(self, value: ChannelsTargetFlowPayload) -> HarpMessage | None:
        """
        Writes a value to the ChannelsTargetFlow register.

        Parameters
        ----------
        value : ChannelsTargetFlowPayload
            Value to write to the ChannelsTargetFlow register.
        """
        address = OlfactometerRegisters.CHANNELS_TARGET_FLOW
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNELS_TARGET_FLOW", reply)

        return reply

    def read_channel0_actual_flow(self) -> float | None:
        """
        Reads the contents of the Channel0ActualFlow register.

        Returns
        -------
        float | None
            Value read from the Channel0ActualFlow register.
        """
        address = OlfactometerRegisters.CHANNEL0_ACTUAL_FLOW
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL0_ACTUAL_FLOW", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_channel1_actual_flow(self) -> float | None:
        """
        Reads the contents of the Channel1ActualFlow register.

        Returns
        -------
        float | None
            Value read from the Channel1ActualFlow register.
        """
        address = OlfactometerRegisters.CHANNEL1_ACTUAL_FLOW
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL1_ACTUAL_FLOW", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_channel2_actual_flow(self) -> float | None:
        """
        Reads the contents of the Channel2ActualFlow register.

        Returns
        -------
        float | None
            Value read from the Channel2ActualFlow register.
        """
        address = OlfactometerRegisters.CHANNEL2_ACTUAL_FLOW
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL2_ACTUAL_FLOW", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_channel3_actual_flow(self) -> float | None:
        """
        Reads the contents of the Channel3ActualFlow register.

        Returns
        -------
        float | None
            Value read from the Channel3ActualFlow register.
        """
        address = OlfactometerRegisters.CHANNEL3_ACTUAL_FLOW
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL3_ACTUAL_FLOW", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_channel4_actual_flow(self) -> float | None:
        """
        Reads the contents of the Channel4ActualFlow register.

        Returns
        -------
        float | None
            Value read from the Channel4ActualFlow register.
        """
        address = OlfactometerRegisters.CHANNEL4_ACTUAL_FLOW
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL4_ACTUAL_FLOW", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_channel0_duty_cycle(self) -> float | None:
        """
        Reads the contents of the Channel0DutyCycle register.

        Returns
        -------
        float | None
            Value read from the Channel0DutyCycle register.
        """
        address = OlfactometerRegisters.CHANNEL0_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL0_DUTY_CYCLE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel0_duty_cycle(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Channel0DutyCycle register.

        Parameters
        ----------
        value : float
            Value to write to the Channel0DutyCycle register.
        """
        address = OlfactometerRegisters.CHANNEL0_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL0_DUTY_CYCLE", reply)

        return reply

    def read_channel1_duty_cycle(self) -> float | None:
        """
        Reads the contents of the Channel1DutyCycle register.

        Returns
        -------
        float | None
            Value read from the Channel1DutyCycle register.
        """
        address = OlfactometerRegisters.CHANNEL1_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL1_DUTY_CYCLE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel1_duty_cycle(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Channel1DutyCycle register.

        Parameters
        ----------
        value : float
            Value to write to the Channel1DutyCycle register.
        """
        address = OlfactometerRegisters.CHANNEL1_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL1_DUTY_CYCLE", reply)

        return reply

    def read_channel2_duty_cycle(self) -> float | None:
        """
        Reads the contents of the Channel2DutyCycle register.

        Returns
        -------
        float | None
            Value read from the Channel2DutyCycle register.
        """
        address = OlfactometerRegisters.CHANNEL2_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL2_DUTY_CYCLE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel2_duty_cycle(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Channel2DutyCycle register.

        Parameters
        ----------
        value : float
            Value to write to the Channel2DutyCycle register.
        """
        address = OlfactometerRegisters.CHANNEL2_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL2_DUTY_CYCLE", reply)

        return reply

    def read_channel3_duty_cycle(self) -> float | None:
        """
        Reads the contents of the Channel3DutyCycle register.

        Returns
        -------
        float | None
            Value read from the Channel3DutyCycle register.
        """
        address = OlfactometerRegisters.CHANNEL3_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL3_DUTY_CYCLE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel3_duty_cycle(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Channel3DutyCycle register.

        Parameters
        ----------
        value : float
            Value to write to the Channel3DutyCycle register.
        """
        address = OlfactometerRegisters.CHANNEL3_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL3_DUTY_CYCLE", reply)

        return reply

    def read_channel4_duty_cycle(self) -> float | None:
        """
        Reads the contents of the Channel4DutyCycle register.

        Returns
        -------
        float | None
            Value read from the Channel4DutyCycle register.
        """
        address = OlfactometerRegisters.CHANNEL4_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL4_DUTY_CYCLE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_channel4_duty_cycle(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Channel4DutyCycle register.

        Parameters
        ----------
        value : float
            Value to write to the Channel4DutyCycle register.
        """
        address = OlfactometerRegisters.CHANNEL4_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL4_DUTY_CYCLE", reply)

        return reply

    def read_digital_output_set(self) -> DigitalOutputs | None:
        """
        Reads the contents of the DigitalOutputSet register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the DigitalOutputSet register.
        """
        address = OlfactometerRegisters.DIGITAL_OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.DIGITAL_OUTPUT_SET", reply)

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
        address = OlfactometerRegisters.DIGITAL_OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.DIGITAL_OUTPUT_SET", reply)

        return reply

    def read_digital_output_clear(self) -> DigitalOutputs | None:
        """
        Reads the contents of the DigitalOutputClear register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the DigitalOutputClear register.
        """
        address = OlfactometerRegisters.DIGITAL_OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.DIGITAL_OUTPUT_CLEAR", reply)

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
        address = OlfactometerRegisters.DIGITAL_OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.DIGITAL_OUTPUT_CLEAR", reply)

        return reply

    def read_digital_output_toggle(self) -> DigitalOutputs | None:
        """
        Reads the contents of the DigitalOutputToggle register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the DigitalOutputToggle register.
        """
        address = OlfactometerRegisters.DIGITAL_OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.DIGITAL_OUTPUT_TOGGLE", reply)

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
        address = OlfactometerRegisters.DIGITAL_OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.DIGITAL_OUTPUT_TOGGLE", reply)

        return reply

    def read_digital_output_state(self) -> DigitalOutputs | None:
        """
        Reads the contents of the DigitalOutputState register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the DigitalOutputState register.
        """
        address = OlfactometerRegisters.DIGITAL_OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.DIGITAL_OUTPUT_STATE", reply)

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
        address = OlfactometerRegisters.DIGITAL_OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.DIGITAL_OUTPUT_STATE", reply)

        return reply

    def read_enable_valve_pulse(self) -> Valves | None:
        """
        Reads the contents of the EnableValvePulse register.

        Returns
        -------
        Valves | None
            Value read from the EnableValvePulse register.
        """
        address = OlfactometerRegisters.ENABLE_VALVE_PULSE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.ENABLE_VALVE_PULSE", reply)

        if reply is not None:
            return Valves(reply.payload)
        return None

    def write_enable_valve_pulse(self, value: Valves) -> HarpMessage | None:
        """
        Writes a value to the EnableValvePulse register.

        Parameters
        ----------
        value : Valves
            Value to write to the EnableValvePulse register.
        """
        address = OlfactometerRegisters.ENABLE_VALVE_PULSE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.ENABLE_VALVE_PULSE", reply)

        return reply

    def read_valve_set(self) -> Valves | None:
        """
        Reads the contents of the ValveSet register.

        Returns
        -------
        Valves | None
            Value read from the ValveSet register.
        """
        address = OlfactometerRegisters.VALVE_SET
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.VALVE_SET", reply)

        if reply is not None:
            return Valves(reply.payload)
        return None

    def write_valve_set(self, value: Valves) -> HarpMessage | None:
        """
        Writes a value to the ValveSet register.

        Parameters
        ----------
        value : Valves
            Value to write to the ValveSet register.
        """
        address = OlfactometerRegisters.VALVE_SET
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.VALVE_SET", reply)

        return reply

    def read_valve_clear(self) -> Valves | None:
        """
        Reads the contents of the ValveClear register.

        Returns
        -------
        Valves | None
            Value read from the ValveClear register.
        """
        address = OlfactometerRegisters.VALVE_CLEAR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.VALVE_CLEAR", reply)

        if reply is not None:
            return Valves(reply.payload)
        return None

    def write_valve_clear(self, value: Valves) -> HarpMessage | None:
        """
        Writes a value to the ValveClear register.

        Parameters
        ----------
        value : Valves
            Value to write to the ValveClear register.
        """
        address = OlfactometerRegisters.VALVE_CLEAR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.VALVE_CLEAR", reply)

        return reply

    def read_valve_toggle(self) -> Valves | None:
        """
        Reads the contents of the ValveToggle register.

        Returns
        -------
        Valves | None
            Value read from the ValveToggle register.
        """
        address = OlfactometerRegisters.VALVE_TOGGLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.VALVE_TOGGLE", reply)

        if reply is not None:
            return Valves(reply.payload)
        return None

    def write_valve_toggle(self, value: Valves) -> HarpMessage | None:
        """
        Writes a value to the ValveToggle register.

        Parameters
        ----------
        value : Valves
            Value to write to the ValveToggle register.
        """
        address = OlfactometerRegisters.VALVE_TOGGLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.VALVE_TOGGLE", reply)

        return reply

    def read_valve_state(self) -> Valves | None:
        """
        Reads the contents of the ValveState register.

        Returns
        -------
        Valves | None
            Value read from the ValveState register.
        """
        address = OlfactometerRegisters.VALVE_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.VALVE_STATE", reply)

        if reply is not None:
            return Valves(reply.payload)
        return None

    def write_valve_state(self, value: Valves) -> HarpMessage | None:
        """
        Writes a value to the ValveState register.

        Parameters
        ----------
        value : Valves
            Value to write to the ValveState register.
        """
        address = OlfactometerRegisters.VALVE_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.VALVE_STATE", reply)

        return reply

    def read_odor_valve_state(self) -> OdorValves | None:
        """
        Reads the contents of the OdorValveState register.

        Returns
        -------
        OdorValves | None
            Value read from the OdorValveState register.
        """
        address = OlfactometerRegisters.ODOR_VALVE_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.ODOR_VALVE_STATE", reply)

        if reply is not None:
            return OdorValves(reply.payload)
        return None

    def write_odor_valve_state(self, value: OdorValves) -> HarpMessage | None:
        """
        Writes a value to the OdorValveState register.

        Parameters
        ----------
        value : OdorValves
            Value to write to the OdorValveState register.
        """
        address = OlfactometerRegisters.ODOR_VALVE_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.ODOR_VALVE_STATE", reply)

        return reply

    def read_end_valve_state(self) -> EndValves | None:
        """
        Reads the contents of the EndValveState register.

        Returns
        -------
        EndValves | None
            Value read from the EndValveState register.
        """
        address = OlfactometerRegisters.END_VALVE_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.END_VALVE_STATE", reply)

        if reply is not None:
            return EndValves(reply.payload)
        return None

    def write_end_valve_state(self, value: EndValves) -> HarpMessage | None:
        """
        Writes a value to the EndValveState register.

        Parameters
        ----------
        value : EndValves
            Value to write to the EndValveState register.
        """
        address = OlfactometerRegisters.END_VALVE_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.END_VALVE_STATE", reply)

        return reply

    def read_check_valve_state(self) -> CheckValves | None:
        """
        Reads the contents of the CheckValveState register.

        Returns
        -------
        CheckValves | None
            Value read from the CheckValveState register.
        """
        address = OlfactometerRegisters.CHECK_VALVE_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHECK_VALVE_STATE", reply)

        if reply is not None:
            return CheckValves(reply.payload)
        return None

    def write_check_valve_state(self, value: CheckValves) -> HarpMessage | None:
        """
        Writes a value to the CheckValveState register.

        Parameters
        ----------
        value : CheckValves
            Value to write to the CheckValveState register.
        """
        address = OlfactometerRegisters.CHECK_VALVE_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHECK_VALVE_STATE", reply)

        return reply

    def read_valve0_pulse_duration(self) -> int | None:
        """
        Reads the contents of the Valve0PulseDuration register.

        Returns
        -------
        int | None
            Value read from the Valve0PulseDuration register.
        """
        address = OlfactometerRegisters.VALVE0_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.VALVE0_PULSE_DURATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_valve0_pulse_duration(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Valve0PulseDuration register.

        Parameters
        ----------
        value : int
            Value to write to the Valve0PulseDuration register.
        """
        address = OlfactometerRegisters.VALVE0_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.VALVE0_PULSE_DURATION", reply)

        return reply

    def read_valve1_pulse_duration(self) -> int | None:
        """
        Reads the contents of the Valve1PulseDuration register.

        Returns
        -------
        int | None
            Value read from the Valve1PulseDuration register.
        """
        address = OlfactometerRegisters.VALVE1_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.VALVE1_PULSE_DURATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_valve1_pulse_duration(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Valve1PulseDuration register.

        Parameters
        ----------
        value : int
            Value to write to the Valve1PulseDuration register.
        """
        address = OlfactometerRegisters.VALVE1_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.VALVE1_PULSE_DURATION", reply)

        return reply

    def read_valve2_pulse_duration(self) -> int | None:
        """
        Reads the contents of the Valve2PulseDuration register.

        Returns
        -------
        int | None
            Value read from the Valve2PulseDuration register.
        """
        address = OlfactometerRegisters.VALVE2_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.VALVE2_PULSE_DURATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_valve2_pulse_duration(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Valve2PulseDuration register.

        Parameters
        ----------
        value : int
            Value to write to the Valve2PulseDuration register.
        """
        address = OlfactometerRegisters.VALVE2_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.VALVE2_PULSE_DURATION", reply)

        return reply

    def read_valve3_pulse_duration(self) -> int | None:
        """
        Reads the contents of the Valve3PulseDuration register.

        Returns
        -------
        int | None
            Value read from the Valve3PulseDuration register.
        """
        address = OlfactometerRegisters.VALVE3_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.VALVE3_PULSE_DURATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_valve3_pulse_duration(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Valve3PulseDuration register.

        Parameters
        ----------
        value : int
            Value to write to the Valve3PulseDuration register.
        """
        address = OlfactometerRegisters.VALVE3_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.VALVE3_PULSE_DURATION", reply)

        return reply

    def read_check_valve0_delay_pulse_duration(self) -> int | None:
        """
        Reads the contents of the CheckValve0DelayPulseDuration register.

        Returns
        -------
        int | None
            Value read from the CheckValve0DelayPulseDuration register.
        """
        address = OlfactometerRegisters.CHECK_VALVE0_DELAY_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHECK_VALVE0_DELAY_PULSE_DURATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_check_valve0_delay_pulse_duration(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the CheckValve0DelayPulseDuration register.

        Parameters
        ----------
        value : int
            Value to write to the CheckValve0DelayPulseDuration register.
        """
        address = OlfactometerRegisters.CHECK_VALVE0_DELAY_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHECK_VALVE0_DELAY_PULSE_DURATION", reply)

        return reply

    def read_check_valve1_delay_pulse_duration(self) -> int | None:
        """
        Reads the contents of the CheckValve1DelayPulseDuration register.

        Returns
        -------
        int | None
            Value read from the CheckValve1DelayPulseDuration register.
        """
        address = OlfactometerRegisters.CHECK_VALVE1_DELAY_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHECK_VALVE1_DELAY_PULSE_DURATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_check_valve1_delay_pulse_duration(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the CheckValve1DelayPulseDuration register.

        Parameters
        ----------
        value : int
            Value to write to the CheckValve1DelayPulseDuration register.
        """
        address = OlfactometerRegisters.CHECK_VALVE1_DELAY_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHECK_VALVE1_DELAY_PULSE_DURATION", reply)

        return reply

    def read_check_valve2_delay_pulse_duration(self) -> int | None:
        """
        Reads the contents of the CheckValve2DelayPulseDuration register.

        Returns
        -------
        int | None
            Value read from the CheckValve2DelayPulseDuration register.
        """
        address = OlfactometerRegisters.CHECK_VALVE2_DELAY_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHECK_VALVE2_DELAY_PULSE_DURATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_check_valve2_delay_pulse_duration(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the CheckValve2DelayPulseDuration register.

        Parameters
        ----------
        value : int
            Value to write to the CheckValve2DelayPulseDuration register.
        """
        address = OlfactometerRegisters.CHECK_VALVE2_DELAY_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHECK_VALVE2_DELAY_PULSE_DURATION", reply)

        return reply

    def read_check_valve3_delay_pulse_duration(self) -> int | None:
        """
        Reads the contents of the CheckValve3DelayPulseDuration register.

        Returns
        -------
        int | None
            Value read from the CheckValve3DelayPulseDuration register.
        """
        address = OlfactometerRegisters.CHECK_VALVE3_DELAY_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHECK_VALVE3_DELAY_PULSE_DURATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_check_valve3_delay_pulse_duration(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the CheckValve3DelayPulseDuration register.

        Parameters
        ----------
        value : int
            Value to write to the CheckValve3DelayPulseDuration register.
        """
        address = OlfactometerRegisters.CHECK_VALVE3_DELAY_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHECK_VALVE3_DELAY_PULSE_DURATION", reply)

        return reply

    def read_end_valve0_pulse_duration(self) -> int | None:
        """
        Reads the contents of the EndValve0PulseDuration register.

        Returns
        -------
        int | None
            Value read from the EndValve0PulseDuration register.
        """
        address = OlfactometerRegisters.END_VALVE0_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.END_VALVE0_PULSE_DURATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_end_valve0_pulse_duration(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the EndValve0PulseDuration register.

        Parameters
        ----------
        value : int
            Value to write to the EndValve0PulseDuration register.
        """
        address = OlfactometerRegisters.END_VALVE0_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.END_VALVE0_PULSE_DURATION", reply)

        return reply

    def read_end_valve1_pulse_duration(self) -> int | None:
        """
        Reads the contents of the EndValve1PulseDuration register.

        Returns
        -------
        int | None
            Value read from the EndValve1PulseDuration register.
        """
        address = OlfactometerRegisters.END_VALVE1_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.END_VALVE1_PULSE_DURATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_end_valve1_pulse_duration(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the EndValve1PulseDuration register.

        Parameters
        ----------
        value : int
            Value to write to the EndValve1PulseDuration register.
        """
        address = OlfactometerRegisters.END_VALVE1_PULSE_DURATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.END_VALVE1_PULSE_DURATION", reply)

        return reply

    def read_do0_sync(self) -> DO0SyncConfig | None:
        """
        Reads the contents of the DO0Sync register.

        Returns
        -------
        DO0SyncConfig | None
            Value read from the DO0Sync register.
        """
        address = OlfactometerRegisters.DO0_SYNC
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.DO0_SYNC", reply)

        if reply is not None:
            return DO0SyncConfig(reply.payload)
        return None

    def write_do0_sync(self, value: DO0SyncConfig) -> HarpMessage | None:
        """
        Writes a value to the DO0Sync register.

        Parameters
        ----------
        value : DO0SyncConfig
            Value to write to the DO0Sync register.
        """
        address = OlfactometerRegisters.DO0_SYNC
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.DO0_SYNC", reply)

        return reply

    def read_do1_sync(self) -> DO1SyncConfig | None:
        """
        Reads the contents of the DO1Sync register.

        Returns
        -------
        DO1SyncConfig | None
            Value read from the DO1Sync register.
        """
        address = OlfactometerRegisters.DO1_SYNC
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.DO1_SYNC", reply)

        if reply is not None:
            return DO1SyncConfig(reply.payload)
        return None

    def write_do1_sync(self, value: DO1SyncConfig) -> HarpMessage | None:
        """
        Writes a value to the DO1Sync register.

        Parameters
        ----------
        value : DO1SyncConfig
            Value to write to the DO1Sync register.
        """
        address = OlfactometerRegisters.DO1_SYNC
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.DO1_SYNC", reply)

        return reply

    def read_di0_trigger(self) -> DI0TriggerConfig | None:
        """
        Reads the contents of the DI0Trigger register.

        Returns
        -------
        DI0TriggerConfig | None
            Value read from the DI0Trigger register.
        """
        address = OlfactometerRegisters.DI0_TRIGGER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.DI0_TRIGGER", reply)

        if reply is not None:
            return DI0TriggerConfig(reply.payload)
        return None

    def write_di0_trigger(self, value: DI0TriggerConfig) -> HarpMessage | None:
        """
        Writes a value to the DI0Trigger register.

        Parameters
        ----------
        value : DI0TriggerConfig
            Value to write to the DI0Trigger register.
        """
        address = OlfactometerRegisters.DI0_TRIGGER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.DI0_TRIGGER", reply)

        return reply

    def read_mimic_valve0(self) -> MimicOutputs | None:
        """
        Reads the contents of the MimicValve0 register.

        Returns
        -------
        MimicOutputs | None
            Value read from the MimicValve0 register.
        """
        address = OlfactometerRegisters.MIMIC_VALVE0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.MIMIC_VALVE0", reply)

        if reply is not None:
            return MimicOutputs(reply.payload)
        return None

    def write_mimic_valve0(self, value: MimicOutputs) -> HarpMessage | None:
        """
        Writes a value to the MimicValve0 register.

        Parameters
        ----------
        value : MimicOutputs
            Value to write to the MimicValve0 register.
        """
        address = OlfactometerRegisters.MIMIC_VALVE0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.MIMIC_VALVE0", reply)

        return reply

    def read_mimic_valve1(self) -> MimicOutputs | None:
        """
        Reads the contents of the MimicValve1 register.

        Returns
        -------
        MimicOutputs | None
            Value read from the MimicValve1 register.
        """
        address = OlfactometerRegisters.MIMIC_VALVE1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.MIMIC_VALVE1", reply)

        if reply is not None:
            return MimicOutputs(reply.payload)
        return None

    def write_mimic_valve1(self, value: MimicOutputs) -> HarpMessage | None:
        """
        Writes a value to the MimicValve1 register.

        Parameters
        ----------
        value : MimicOutputs
            Value to write to the MimicValve1 register.
        """
        address = OlfactometerRegisters.MIMIC_VALVE1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.MIMIC_VALVE1", reply)

        return reply

    def read_mimic_valve2(self) -> MimicOutputs | None:
        """
        Reads the contents of the MimicValve2 register.

        Returns
        -------
        MimicOutputs | None
            Value read from the MimicValve2 register.
        """
        address = OlfactometerRegisters.MIMIC_VALVE2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.MIMIC_VALVE2", reply)

        if reply is not None:
            return MimicOutputs(reply.payload)
        return None

    def write_mimic_valve2(self, value: MimicOutputs) -> HarpMessage | None:
        """
        Writes a value to the MimicValve2 register.

        Parameters
        ----------
        value : MimicOutputs
            Value to write to the MimicValve2 register.
        """
        address = OlfactometerRegisters.MIMIC_VALVE2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.MIMIC_VALVE2", reply)

        return reply

    def read_mimic_valve3(self) -> MimicOutputs | None:
        """
        Reads the contents of the MimicValve3 register.

        Returns
        -------
        MimicOutputs | None
            Value read from the MimicValve3 register.
        """
        address = OlfactometerRegisters.MIMIC_VALVE3
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.MIMIC_VALVE3", reply)

        if reply is not None:
            return MimicOutputs(reply.payload)
        return None

    def write_mimic_valve3(self, value: MimicOutputs) -> HarpMessage | None:
        """
        Writes a value to the MimicValve3 register.

        Parameters
        ----------
        value : MimicOutputs
            Value to write to the MimicValve3 register.
        """
        address = OlfactometerRegisters.MIMIC_VALVE3
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.MIMIC_VALVE3", reply)

        return reply

    def read_mimic_check_valve0(self) -> MimicOutputs | None:
        """
        Reads the contents of the MimicCheckValve0 register.

        Returns
        -------
        MimicOutputs | None
            Value read from the MimicCheckValve0 register.
        """
        address = OlfactometerRegisters.MIMIC_CHECK_VALVE0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.MIMIC_CHECK_VALVE0", reply)

        if reply is not None:
            return MimicOutputs(reply.payload)
        return None

    def write_mimic_check_valve0(self, value: MimicOutputs) -> HarpMessage | None:
        """
        Writes a value to the MimicCheckValve0 register.

        Parameters
        ----------
        value : MimicOutputs
            Value to write to the MimicCheckValve0 register.
        """
        address = OlfactometerRegisters.MIMIC_CHECK_VALVE0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.MIMIC_CHECK_VALVE0", reply)

        return reply

    def read_mimic_check_valve1(self) -> MimicOutputs | None:
        """
        Reads the contents of the MimicCheckValve1 register.

        Returns
        -------
        MimicOutputs | None
            Value read from the MimicCheckValve1 register.
        """
        address = OlfactometerRegisters.MIMIC_CHECK_VALVE1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.MIMIC_CHECK_VALVE1", reply)

        if reply is not None:
            return MimicOutputs(reply.payload)
        return None

    def write_mimic_check_valve1(self, value: MimicOutputs) -> HarpMessage | None:
        """
        Writes a value to the MimicCheckValve1 register.

        Parameters
        ----------
        value : MimicOutputs
            Value to write to the MimicCheckValve1 register.
        """
        address = OlfactometerRegisters.MIMIC_CHECK_VALVE1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.MIMIC_CHECK_VALVE1", reply)

        return reply

    def read_mimic_check_valve2(self) -> MimicOutputs | None:
        """
        Reads the contents of the MimicCheckValve2 register.

        Returns
        -------
        MimicOutputs | None
            Value read from the MimicCheckValve2 register.
        """
        address = OlfactometerRegisters.MIMIC_CHECK_VALVE2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.MIMIC_CHECK_VALVE2", reply)

        if reply is not None:
            return MimicOutputs(reply.payload)
        return None

    def write_mimic_check_valve2(self, value: MimicOutputs) -> HarpMessage | None:
        """
        Writes a value to the MimicCheckValve2 register.

        Parameters
        ----------
        value : MimicOutputs
            Value to write to the MimicCheckValve2 register.
        """
        address = OlfactometerRegisters.MIMIC_CHECK_VALVE2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.MIMIC_CHECK_VALVE2", reply)

        return reply

    def read_mimic_check_valve3(self) -> MimicOutputs | None:
        """
        Reads the contents of the MimicCheckValve3 register.

        Returns
        -------
        MimicOutputs | None
            Value read from the MimicCheckValve3 register.
        """
        address = OlfactometerRegisters.MIMIC_CHECK_VALVE3
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.MIMIC_CHECK_VALVE3", reply)

        if reply is not None:
            return MimicOutputs(reply.payload)
        return None

    def write_mimic_check_valve3(self, value: MimicOutputs) -> HarpMessage | None:
        """
        Writes a value to the MimicCheckValve3 register.

        Parameters
        ----------
        value : MimicOutputs
            Value to write to the MimicCheckValve3 register.
        """
        address = OlfactometerRegisters.MIMIC_CHECK_VALVE3
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.MIMIC_CHECK_VALVE3", reply)

        return reply

    def read_mimic_end_valve0(self) -> MimicOutputs | None:
        """
        Reads the contents of the MimicEndValve0 register.

        Returns
        -------
        MimicOutputs | None
            Value read from the MimicEndValve0 register.
        """
        address = OlfactometerRegisters.MIMIC_END_VALVE0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.MIMIC_END_VALVE0", reply)

        if reply is not None:
            return MimicOutputs(reply.payload)
        return None

    def write_mimic_end_valve0(self, value: MimicOutputs) -> HarpMessage | None:
        """
        Writes a value to the MimicEndValve0 register.

        Parameters
        ----------
        value : MimicOutputs
            Value to write to the MimicEndValve0 register.
        """
        address = OlfactometerRegisters.MIMIC_END_VALVE0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.MIMIC_END_VALVE0", reply)

        return reply

    def read_mimic_end_valve1(self) -> MimicOutputs | None:
        """
        Reads the contents of the MimicEndValve1 register.

        Returns
        -------
        MimicOutputs | None
            Value read from the MimicEndValve1 register.
        """
        address = OlfactometerRegisters.MIMIC_END_VALVE1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.MIMIC_END_VALVE1", reply)

        if reply is not None:
            return MimicOutputs(reply.payload)
        return None

    def write_mimic_end_valve1(self, value: MimicOutputs) -> HarpMessage | None:
        """
        Writes a value to the MimicEndValve1 register.

        Parameters
        ----------
        value : MimicOutputs
            Value to write to the MimicEndValve1 register.
        """
        address = OlfactometerRegisters.MIMIC_END_VALVE1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.MIMIC_END_VALVE1", reply)

        return reply

    def read_enable_valve_external_control(self) -> bool | None:
        """
        Reads the contents of the EnableValveExternalControl register.

        Returns
        -------
        bool | None
            Value read from the EnableValveExternalControl register.
        """
        address = OlfactometerRegisters.ENABLE_VALVE_EXTERNAL_CONTROL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.ENABLE_VALVE_EXTERNAL_CONTROL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_enable_valve_external_control(self, value: bool) -> HarpMessage | None:
        """
        Writes a value to the EnableValveExternalControl register.

        Parameters
        ----------
        value : bool
            Value to write to the EnableValveExternalControl register.
        """
        address = OlfactometerRegisters.ENABLE_VALVE_EXTERNAL_CONTROL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.ENABLE_VALVE_EXTERNAL_CONTROL", reply)

        return reply

    def read_channel3_range(self) -> Channel3RangeConfig | None:
        """
        Reads the contents of the Channel3Range register.

        Returns
        -------
        Channel3RangeConfig | None
            Value read from the Channel3Range register.
        """
        address = OlfactometerRegisters.CHANNEL3_RANGE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.CHANNEL3_RANGE", reply)

        if reply is not None:
            return Channel3RangeConfig(reply.payload)
        return None

    def write_channel3_range(self, value: Channel3RangeConfig) -> HarpMessage | None:
        """
        Writes a value to the Channel3Range register.

        Parameters
        ----------
        value : Channel3RangeConfig
            Value to write to the Channel3Range register.
        """
        address = OlfactometerRegisters.CHANNEL3_RANGE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.CHANNEL3_RANGE", reply)

        return reply

    def read_enable_check_valve_sync(self) -> CheckValves | None:
        """
        Reads the contents of the EnableCheckValveSync register.

        Returns
        -------
        CheckValves | None
            Value read from the EnableCheckValveSync register.
        """
        address = OlfactometerRegisters.ENABLE_CHECK_VALVE_SYNC
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.ENABLE_CHECK_VALVE_SYNC", reply)

        if reply is not None:
            return CheckValves(reply.payload)
        return None

    def write_enable_check_valve_sync(self, value: CheckValves) -> HarpMessage | None:
        """
        Writes a value to the EnableCheckValveSync register.

        Parameters
        ----------
        value : CheckValves
            Value to write to the EnableCheckValveSync register.
        """
        address = OlfactometerRegisters.ENABLE_CHECK_VALVE_SYNC
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.ENABLE_CHECK_VALVE_SYNC", reply)

        return reply

    def read_temperature_value(self) -> int | None:
        """
        Reads the contents of the TemperatureValue register.

        Returns
        -------
        int | None
            Value read from the TemperatureValue register.
        """
        address = OlfactometerRegisters.TEMPERATURE_VALUE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.TEMPERATURE_VALUE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_enable_temperature_calibration(self) -> bool | None:
        """
        Reads the contents of the EnableTemperatureCalibration register.

        Returns
        -------
        bool | None
            Value read from the EnableTemperatureCalibration register.
        """
        address = OlfactometerRegisters.ENABLE_TEMPERATURE_CALIBRATION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.ENABLE_TEMPERATURE_CALIBRATION", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_enable_temperature_calibration(self, value: bool) -> HarpMessage | None:
        """
        Writes a value to the EnableTemperatureCalibration register.

        Parameters
        ----------
        value : bool
            Value to write to the EnableTemperatureCalibration register.
        """
        address = OlfactometerRegisters.ENABLE_TEMPERATURE_CALIBRATION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.ENABLE_TEMPERATURE_CALIBRATION", reply)

        return reply

    def read_temperature_calibration_value(self) -> int | None:
        """
        Reads the contents of the TemperatureCalibrationValue register.

        Returns
        -------
        int | None
            Value read from the TemperatureCalibrationValue register.
        """
        address = OlfactometerRegisters.TEMPERATURE_CALIBRATION_VALUE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.TEMPERATURE_CALIBRATION_VALUE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_temperature_calibration_value(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the TemperatureCalibrationValue register.

        Parameters
        ----------
        value : int
            Value to write to the TemperatureCalibrationValue register.
        """
        address = OlfactometerRegisters.TEMPERATURE_CALIBRATION_VALUE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.TEMPERATURE_CALIBRATION_VALUE", reply)

        return reply

    def read_enable_events(self) -> OlfactometerEvents | None:
        """
        Reads the contents of the EnableEvents register.

        Returns
        -------
        OlfactometerEvents | None
            Value read from the EnableEvents register.
        """
        address = OlfactometerRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("OlfactometerRegisters.ENABLE_EVENTS", reply)

        if reply is not None:
            return OlfactometerEvents(reply.payload)
        return None

    def write_enable_events(self, value: OlfactometerEvents) -> HarpMessage | None:
        """
        Writes a value to the EnableEvents register.

        Parameters
        ----------
        value : OlfactometerEvents
            Value to write to the EnableEvents register.
        """
        address = OlfactometerRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("OlfactometerRegisters.ENABLE_EVENTS", reply)

        return reply

