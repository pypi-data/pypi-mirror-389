from dataclasses import dataclass
from enum import IntEnum, IntFlag

from harp.protocol import MessageType, PayloadType
from harp.protocol.exceptions import HarpException, HarpReadException, HarpWriteException
from harp.protocol.messages import HarpMessage
from harp.serial import Device


class DigitalOutputs(IntFlag):
    """
    The digital output lines.

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


class DigitalInputs(IntFlag):
    """
    The state of the digital input pin.

    Attributes
    ----------
    DI0 : int
        _No description currently available_
    """

    NONE = 0x0
    DI0 = 0x1


class PumpEvents(IntFlag):
    """
    The events that can be enabled/disabled.

    Attributes
    ----------
    STEP : int
        _No description currently available_
    DIRECTION : int
        _No description currently available_
    FORWARD_SWITCH : int
        _No description currently available_
    REVERSE_SWITCH : int
        _No description currently available_
    DIGITAL_INPUT : int
        _No description currently available_
    PROTOCOL : int
        _No description currently available_
    """

    NONE = 0x0
    STEP = 0x1
    DIRECTION = 0x2
    FORWARD_SWITCH = 0x4
    REVERSE_SWITCH = 0x8
    DIGITAL_INPUT = 0x10
    PROTOCOL = 0x20


class StepState(IntEnum):
    """
    The state of the STEP motor controller pin.

    Attributes
    ----------
    LOW : int
        _No description currently available_
    HIGH : int
        _No description currently available_
    """

    LOW = 0
    HIGH = 1


class DirectionState(IntEnum):
    """
    The state of the DIR motor controller pin.

    Attributes
    ----------
    REVERSE : int
        _No description currently available_
    FORWARD : int
        _No description currently available_
    """

    REVERSE = 0
    FORWARD = 1


class ForwardSwitchState(IntEnum):
    """
    The state of the forward limit switch.

    Attributes
    ----------
    LOW : int
        _No description currently available_
    HIGH : int
        _No description currently available_
    """

    LOW = 0
    HIGH = 1


class ReverseSwitchState(IntEnum):
    """
    The state of the reverse limit switch.

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
    Configures which signal is mimicked in the digital output 0.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    SWITCH_STATE : int
        _No description currently available_
    """

    NONE = 0
    SWITCH_STATE = 1


class DO1SyncConfig(IntEnum):
    """
    Configures which signal is mimicked in the digital output 1.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    HEARTBEAT : int
        _No description currently available_
    STEP : int
        _No description currently available_
    """

    NONE = 0
    HEARTBEAT = 1
    STEP = 2


class DI0TriggerConfig(IntEnum):
    """
    Configures the function executed when digital input is triggered.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    STEP : int
        _No description currently available_
    START_PROTOCOL : int
        _No description currently available_
    """

    NONE = 0
    STEP = 1
    START_PROTOCOL = 2


class StepModeType(IntEnum):
    """
    Available step modes.

    Attributes
    ----------
    FULL : int
        _No description currently available_
    HALF : int
        _No description currently available_
    QUARTER : int
        _No description currently available_
    EIGHTH : int
        _No description currently available_
    SIXTEENTH : int
        _No description currently available_
    """

    FULL = 0
    HALF = 1
    QUARTER = 2
    EIGHTH = 3
    SIXTEENTH = 4


class PumpProtocolType(IntEnum):
    """
    Available protocol types.

    Attributes
    ----------
    STEP : int
        _No description currently available_
    VOLUME : int
        _No description currently available_
    """

    STEP = 0
    VOLUME = 1


class PumpBoardType(IntEnum):
    """
    Available board configurations.

    Attributes
    ----------
    PUMP : int
        _No description currently available_
    FISH_FEEDER : int
        _No description currently available_
    STEPPER_MOTOR : int
        _No description currently available_
    """

    PUMP = 0
    FISH_FEEDER = 1
    STEPPER_MOTOR = 2


class ProtocolState(IntEnum):
    """
    The state of the protocol execution.

    Attributes
    ----------
    IDLE : int
        _No description currently available_
    RUNNING : int
        _No description currently available_
    """

    IDLE = 0
    RUNNING = 1


class ProtocolDirectionState(IntEnum):
    """
    The state of the protocol execution.

    Attributes
    ----------
    REVERSE : int
        _No description currently available_
    FORWARD : int
        _No description currently available_
    """

    REVERSE = 0
    FORWARD = 1


class SyringePumpRegisters(IntEnum):
    """Enum for all available registers in the SyringePump device.

    Attributes
    ----------
    ENABLE_MOTOR_DRIVER : int
        Enables the motor driver.
    ENABLE_PROTOCOL : int
        Enables the currently defined protocol.
    STEP : int
        Status of the STEP motor controller pin.
    DIRECTION : int
        Status of the DIR motor controller pin.
    FORWARD_SWITCH : int
        Status of the forward limit switch.
    REVERSE_SWITCH : int
        Status of the reverse limit switch.
    DIGITAL_INPUT_STATE : int
        Status of the digital input pin.
    DIGITAL_OUTPUT_SET : int
        Set the specified digital output lines.
    DIGITAL_OUTPUT_CLEAR : int
        Clear the specified digital output lines.
    DO0_SYNC : int
        Configures which signal is mimicked in the digital output 0.
    DO1_SYNC : int
        Configures which signal is mimicked in the digital output 1.
    DI0_TRIGGER : int
        Configures the callback function triggered when digital input is triggered.
    STEP_MODE : int
        Sets the motor step mode from a list of available types.
    PROTOCOL_STEP_COUNT : int
        Sets the number of steps to be executed in the current protocol.
    PROTOCOL_PERIOD : int
        Sets the period, in ms, of of each step in the protocol.
    ENABLE_EVENTS : int
        Specifies all the active events in the device.
    PROTOCOL : int
        Status of the protocol execution.
    PROTOCOL_DIRECTION : int
        Sets the direction of the protocol execution.
    """

    ENABLE_MOTOR_DRIVER = 32
    ENABLE_PROTOCOL = 33
    STEP = 34
    DIRECTION = 35
    FORWARD_SWITCH = 36
    REVERSE_SWITCH = 37
    DIGITAL_INPUT_STATE = 38
    DIGITAL_OUTPUT_SET = 39
    DIGITAL_OUTPUT_CLEAR = 40
    DO0_SYNC = 41
    DO1_SYNC = 42
    DI0_TRIGGER = 43
    STEP_MODE = 44
    PROTOCOL_STEP_COUNT = 45
    PROTOCOL_PERIOD = 47
    ENABLE_EVENTS = 52
    PROTOCOL = 54
    PROTOCOL_DIRECTION = 55


class SyringePump(Device):
    """
    SyringePump class for controlling the device.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect and load already happened in the base class
        # verify that WHO_AM_I matches the expected value
        if self.WHO_AM_I != 1296:
            self.disconnect()
            raise HarpException(f"WHO_AM_I mismatch: expected {1296}, got {self.WHO_AM_I}")

    def read_enable_motor_driver(self) -> bool | None:
        """
        Reads the contents of the EnableMotorDriver register.

        Returns
        -------
        bool | None
            Value read from the EnableMotorDriver register.
        """
        address = SyringePumpRegisters.ENABLE_MOTOR_DRIVER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.ENABLE_MOTOR_DRIVER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_enable_motor_driver(self, value: bool) -> HarpMessage | None:
        """
        Writes a value to the EnableMotorDriver register.

        Parameters
        ----------
        value : bool
            Value to write to the EnableMotorDriver register.
        """
        address = SyringePumpRegisters.ENABLE_MOTOR_DRIVER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.ENABLE_MOTOR_DRIVER", reply)

        return reply

    def read_enable_protocol(self) -> bool | None:
        """
        Reads the contents of the EnableProtocol register.

        Returns
        -------
        bool | None
            Value read from the EnableProtocol register.
        """
        address = SyringePumpRegisters.ENABLE_PROTOCOL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.ENABLE_PROTOCOL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_enable_protocol(self, value: bool) -> HarpMessage | None:
        """
        Writes a value to the EnableProtocol register.

        Parameters
        ----------
        value : bool
            Value to write to the EnableProtocol register.
        """
        address = SyringePumpRegisters.ENABLE_PROTOCOL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.ENABLE_PROTOCOL", reply)

        return reply

    def read_step(self) -> StepState | None:
        """
        Reads the contents of the Step register.

        Returns
        -------
        StepState | None
            Value read from the Step register.
        """
        address = SyringePumpRegisters.STEP
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.STEP", reply)

        if reply is not None:
            return StepState(reply.payload)
        return None

    def write_step(self, value: StepState) -> HarpMessage | None:
        """
        Writes a value to the Step register.

        Parameters
        ----------
        value : StepState
            Value to write to the Step register.
        """
        address = SyringePumpRegisters.STEP
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.STEP", reply)

        return reply

    def read_direction(self) -> DirectionState | None:
        """
        Reads the contents of the Direction register.

        Returns
        -------
        DirectionState | None
            Value read from the Direction register.
        """
        address = SyringePumpRegisters.DIRECTION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.DIRECTION", reply)

        if reply is not None:
            return DirectionState(reply.payload)
        return None

    def write_direction(self, value: DirectionState) -> HarpMessage | None:
        """
        Writes a value to the Direction register.

        Parameters
        ----------
        value : DirectionState
            Value to write to the Direction register.
        """
        address = SyringePumpRegisters.DIRECTION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.DIRECTION", reply)

        return reply

    def read_forward_switch(self) -> ForwardSwitchState | None:
        """
        Reads the contents of the ForwardSwitch register.

        Returns
        -------
        ForwardSwitchState | None
            Value read from the ForwardSwitch register.
        """
        address = SyringePumpRegisters.FORWARD_SWITCH
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.FORWARD_SWITCH", reply)

        if reply is not None:
            return ForwardSwitchState(reply.payload)
        return None

    def read_reverse_switch(self) -> ReverseSwitchState | None:
        """
        Reads the contents of the ReverseSwitch register.

        Returns
        -------
        ReverseSwitchState | None
            Value read from the ReverseSwitch register.
        """
        address = SyringePumpRegisters.REVERSE_SWITCH
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.REVERSE_SWITCH", reply)

        if reply is not None:
            return ReverseSwitchState(reply.payload)
        return None

    def read_digital_input_state(self) -> DigitalInputs | None:
        """
        Reads the contents of the DigitalInputState register.

        Returns
        -------
        DigitalInputs | None
            Value read from the DigitalInputState register.
        """
        address = SyringePumpRegisters.DIGITAL_INPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.DIGITAL_INPUT_STATE", reply)

        if reply is not None:
            return DigitalInputs(reply.payload)
        return None

    def read_digital_output_set(self) -> DigitalOutputs | None:
        """
        Reads the contents of the DigitalOutputSet register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the DigitalOutputSet register.
        """
        address = SyringePumpRegisters.DIGITAL_OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.DIGITAL_OUTPUT_SET", reply)

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
        address = SyringePumpRegisters.DIGITAL_OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.DIGITAL_OUTPUT_SET", reply)

        return reply

    def read_digital_output_clear(self) -> DigitalOutputs | None:
        """
        Reads the contents of the DigitalOutputClear register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the DigitalOutputClear register.
        """
        address = SyringePumpRegisters.DIGITAL_OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.DIGITAL_OUTPUT_CLEAR", reply)

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
        address = SyringePumpRegisters.DIGITAL_OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.DIGITAL_OUTPUT_CLEAR", reply)

        return reply

    def read_do0_sync(self) -> DO0SyncConfig | None:
        """
        Reads the contents of the DO0Sync register.

        Returns
        -------
        DO0SyncConfig | None
            Value read from the DO0Sync register.
        """
        address = SyringePumpRegisters.DO0_SYNC
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.DO0_SYNC", reply)

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
        address = SyringePumpRegisters.DO0_SYNC
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.DO0_SYNC", reply)

        return reply

    def read_do1_sync(self) -> DO1SyncConfig | None:
        """
        Reads the contents of the DO1Sync register.

        Returns
        -------
        DO1SyncConfig | None
            Value read from the DO1Sync register.
        """
        address = SyringePumpRegisters.DO1_SYNC
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.DO1_SYNC", reply)

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
        address = SyringePumpRegisters.DO1_SYNC
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.DO1_SYNC", reply)

        return reply

    def read_di0_trigger(self) -> DI0TriggerConfig | None:
        """
        Reads the contents of the DI0Trigger register.

        Returns
        -------
        DI0TriggerConfig | None
            Value read from the DI0Trigger register.
        """
        address = SyringePumpRegisters.DI0_TRIGGER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.DI0_TRIGGER", reply)

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
        address = SyringePumpRegisters.DI0_TRIGGER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.DI0_TRIGGER", reply)

        return reply

    def read_step_mode(self) -> StepModeType | None:
        """
        Reads the contents of the StepMode register.

        Returns
        -------
        StepModeType | None
            Value read from the StepMode register.
        """
        address = SyringePumpRegisters.STEP_MODE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.STEP_MODE", reply)

        if reply is not None:
            return StepModeType(reply.payload)
        return None

    def write_step_mode(self, value: StepModeType) -> HarpMessage | None:
        """
        Writes a value to the StepMode register.

        Parameters
        ----------
        value : StepModeType
            Value to write to the StepMode register.
        """
        address = SyringePumpRegisters.STEP_MODE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.STEP_MODE", reply)

        return reply

    def read_protocol_step_count(self) -> int | None:
        """
        Reads the contents of the ProtocolStepCount register.

        Returns
        -------
        int | None
            Value read from the ProtocolStepCount register.
        """
        address = SyringePumpRegisters.PROTOCOL_STEP_COUNT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.PROTOCOL_STEP_COUNT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_protocol_step_count(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the ProtocolStepCount register.

        Parameters
        ----------
        value : int
            Value to write to the ProtocolStepCount register.
        """
        address = SyringePumpRegisters.PROTOCOL_STEP_COUNT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.PROTOCOL_STEP_COUNT", reply)

        return reply

    def read_protocol_period(self) -> int | None:
        """
        Reads the contents of the ProtocolPeriod register.

        Returns
        -------
        int | None
            Value read from the ProtocolPeriod register.
        """
        address = SyringePumpRegisters.PROTOCOL_PERIOD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.PROTOCOL_PERIOD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_protocol_period(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the ProtocolPeriod register.

        Parameters
        ----------
        value : int
            Value to write to the ProtocolPeriod register.
        """
        address = SyringePumpRegisters.PROTOCOL_PERIOD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.PROTOCOL_PERIOD", reply)

        return reply

    def read_enable_events(self) -> PumpEvents | None:
        """
        Reads the contents of the EnableEvents register.

        Returns
        -------
        PumpEvents | None
            Value read from the EnableEvents register.
        """
        address = SyringePumpRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.ENABLE_EVENTS", reply)

        if reply is not None:
            return PumpEvents(reply.payload)
        return None

    def write_enable_events(self, value: PumpEvents) -> HarpMessage | None:
        """
        Writes a value to the EnableEvents register.

        Parameters
        ----------
        value : PumpEvents
            Value to write to the EnableEvents register.
        """
        address = SyringePumpRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.ENABLE_EVENTS", reply)

        return reply

    def read_protocol(self) -> ProtocolState | None:
        """
        Reads the contents of the Protocol register.

        Returns
        -------
        ProtocolState | None
            Value read from the Protocol register.
        """
        address = SyringePumpRegisters.PROTOCOL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.PROTOCOL", reply)

        if reply is not None:
            return ProtocolState(reply.payload)
        return None

    def read_protocol_direction(self) -> ProtocolDirectionState | None:
        """
        Reads the contents of the ProtocolDirection register.

        Returns
        -------
        ProtocolDirectionState | None
            Value read from the ProtocolDirection register.
        """
        address = SyringePumpRegisters.PROTOCOL_DIRECTION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SyringePumpRegisters.PROTOCOL_DIRECTION", reply)

        if reply is not None:
            return ProtocolDirectionState(reply.payload)
        return None

    def write_protocol_direction(self, value: ProtocolDirectionState) -> HarpMessage | None:
        """
        Writes a value to the ProtocolDirection register.

        Parameters
        ----------
        value : ProtocolDirectionState
            Value to write to the ProtocolDirection register.
        """
        address = SyringePumpRegisters.PROTOCOL_DIRECTION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SyringePumpRegisters.PROTOCOL_DIRECTION", reply)

        return reply

