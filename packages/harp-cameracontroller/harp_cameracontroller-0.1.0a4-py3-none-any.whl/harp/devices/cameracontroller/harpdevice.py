from dataclasses import dataclass
from enum import IntEnum, IntFlag

from harp.protocol import MessageType, PayloadType
from harp.protocol.exceptions import HarpException, HarpReadException, HarpWriteException
from harp.protocol.messages import HarpMessage
from harp.serial import Device


class Cameras(IntFlag):
    """
    Specifies the target camera line.

    Attributes
    ----------
    CAMERA0 : int
        _No description currently available_
    CAMERA1 : int
        _No description currently available_
    """

    NONE = 0x0
    CAMERA0 = 0x1
    CAMERA1 = 0x2


class Servos(IntFlag):
    """
    Specifies the target servo-motor lines.

    Attributes
    ----------
    SERVO0 : int
        _No description currently available_
    SERVO1 : int
        _No description currently available_
    """

    NONE = 0x0
    SERVO0 = 0x1
    SERVO1 = 0x2


class DigitalOutputs(IntFlag):
    """
    Available digital output lines.

    Attributes
    ----------
    TRIGGER0 : int
        _No description currently available_
    SYNC0 : int
        _No description currently available_
    TRIGGER1 : int
        _No description currently available_
    SYNC1 : int
        _No description currently available_
    """

    NONE = 0x0
    TRIGGER0 = 0x1
    SYNC0 = 0x2
    TRIGGER1 = 0x4
    SYNC1 = 0x8


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


class CameraControllerEvents(IntFlag):
    """
    Specifies the active events in the device.

    Attributes
    ----------
    TRIGGER_AND_SYNCH : int
        Enables CameraTrigger and CameraSync events.
    DIGITAL_INPUTS : int
        Enables DigitalInputs
    """

    NONE = 0x0
    TRIGGER_AND_SYNCH = 0x1
    DIGITAL_INPUTS = 0x2


class DI0ModeConfig(IntEnum):
    """
    Specifies the operation mode of digital input line 0.

    Attributes
    ----------
    HIGH_ENABLES_CAMERA0 : int
        When High, enables Camera0 or Servo0.
    HIGH_ENABLES_CAMERA1 : int
        When High, enables Camera1 or Servo1.
    HIGH_ENABLES_CAMERA_BOTH : int
        When High, enables both Cameras or Servos.
    LOW_ENABLES_CAMERA0 : int
        When Low, enables Camera0 or Servo0.
    LOW_ENABLES_CAMERA1 : int
        When Low, enables Camera1 or Servo1.
    LOW_ENABLES_CAMERA_BOTH : int
        When Low, enables both Cameras or Servos.
    DEFAULT : int
        The line will function as a passive digital input.
    """

    HIGH_ENABLES_CAMERA0 = 0
    HIGH_ENABLES_CAMERA1 = 1
    HIGH_ENABLES_CAMERA_BOTH = 2
    LOW_ENABLES_CAMERA0 = 3
    LOW_ENABLES_CAMERA1 = 4
    LOW_ENABLES_CAMERA_BOTH = 5
    DEFAULT = 6


class ControlModeConfig(IntEnum):
    """
    Specifies the operation mode of a specific output line.

    Attributes
    ----------
    CAMERA : int
        Enables Camera mode and it will produce the configured trigger.
    SERVO : int
        Enables Servo mode and it will produce the configured trigger.
    """

    CAMERA = 0
    SERVO = 1


class CameraControllerRegisters(IntEnum):
    """Enum for all available registers in the CameraController device.

    Attributes
    ----------
    CAMERA_START : int
        Starts the generation of triggers on the specified camera lines.
    CAMERA_STOP : int
        Stops the generation of triggers on the specified camera lines.
    SERVO_ENABLE : int
        Enables servo control on the specified camera lines.
    SERVO_DISABLE : int
        Disables servo control on the specified camera lines.
    OUTPUT_SET : int
        Set the specified digital output lines.
    OUTPUT_CLEAR : int
        Clear the specified digital output lines
    OUTPUT_STATE : int
        Write the state of all digital output lines
    DIGITAL_INPUT_STATE : int
        Emits an event when the state of the digital input line changes.
    CAMERA0_TRIGGER : int
        Emits an event when a frame is triggered on camera 0.
    CAMERA1_TRIGGER : int
        Emits an event when a frame is triggered on camera 1.
    CAMERA0_SYNC : int
        Emits an event when a sync state is toggled on camera 0.
    CAMERA1_SYNC : int
        Emits an event when a sync state is toggled on camera 0.
    SERVO_STATE : int
        Returns the current state of the servo motors.
    SYNC_INTERVAL : int
        Configures the interval in seconds between each sync pulse
    DI0_MODE : int
        Configures the mode of the digital input line 0.
    CONTROL0_MODE : int
        Configures the control mode of Camera/Servo 0.
    CAMERA0_FREQUENCY : int
        Configures the frequency (Hz) of the trigger pulses on Camera 0 when using Camera mode.
    SERVO0_PERIOD : int
        Configures the servo motor period (us) when using Servo mode (sensitive to 2 us)
    SERVO0_PULSE_WIDTH : int
        Configures the servo pulse width (us) when using Servo mode (sensitive to 2 us)
    CONTROL1_MODE : int
        Configures the control mode of Camera/Servo 1.
    CAMERA1_FREQUENCY : int
        Configures the frequency (Hz) of the trigger pulses on Camera 1 when using Camera mode.
    SERVO1_PERIOD : int
        Configures the servo motor period (us) when using Servo mode (sensitive to 2 us)
    SERVO1_PULSE_WIDTH : int
        Configures the servo pulse width (us) when using Servo mode (sensitive to 2 us)
    ENABLE_EVENTS : int
        Specifies the active events in the device.
    """

    CAMERA_START = 32
    CAMERA_STOP = 33
    SERVO_ENABLE = 34
    SERVO_DISABLE = 35
    OUTPUT_SET = 36
    OUTPUT_CLEAR = 37
    OUTPUT_STATE = 38
    DIGITAL_INPUT_STATE = 39
    CAMERA0_TRIGGER = 40
    CAMERA1_TRIGGER = 41
    CAMERA0_SYNC = 42
    CAMERA1_SYNC = 43
    SERVO_STATE = 44
    SYNC_INTERVAL = 46
    DI0_MODE = 48
    CONTROL0_MODE = 49
    CAMERA0_FREQUENCY = 50
    SERVO0_PERIOD = 51
    SERVO0_PULSE_WIDTH = 52
    CONTROL1_MODE = 53
    CAMERA1_FREQUENCY = 54
    SERVO1_PERIOD = 55
    SERVO1_PULSE_WIDTH = 56
    ENABLE_EVENTS = 59


class CameraController(Device):
    """
    CameraController class for controlling the device.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect and load already happened in the base class
        # verify that WHO_AM_I matches the expected value
        if self.WHO_AM_I != 1168:
            self.disconnect()
            raise HarpException(f"WHO_AM_I mismatch: expected {1168}, got {self.WHO_AM_I}")

    def read_camera_start(self) -> Cameras | None:
        """
        Reads the contents of the CameraStart register.

        Returns
        -------
        Cameras | None
            Value read from the CameraStart register.
        """
        address = CameraControllerRegisters.CAMERA_START
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.CAMERA_START", reply)

        if reply is not None:
            return Cameras(reply.payload)
        return None

    def write_camera_start(self, value: Cameras) -> HarpMessage | None:
        """
        Writes a value to the CameraStart register.

        Parameters
        ----------
        value : Cameras
            Value to write to the CameraStart register.
        """
        address = CameraControllerRegisters.CAMERA_START
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.CAMERA_START", reply)

        return reply

    def read_camera_stop(self) -> Cameras | None:
        """
        Reads the contents of the CameraStop register.

        Returns
        -------
        Cameras | None
            Value read from the CameraStop register.
        """
        address = CameraControllerRegisters.CAMERA_STOP
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.CAMERA_STOP", reply)

        if reply is not None:
            return Cameras(reply.payload)
        return None

    def write_camera_stop(self, value: Cameras) -> HarpMessage | None:
        """
        Writes a value to the CameraStop register.

        Parameters
        ----------
        value : Cameras
            Value to write to the CameraStop register.
        """
        address = CameraControllerRegisters.CAMERA_STOP
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.CAMERA_STOP", reply)

        return reply

    def read_servo_enable(self) -> Servos | None:
        """
        Reads the contents of the ServoEnable register.

        Returns
        -------
        Servos | None
            Value read from the ServoEnable register.
        """
        address = CameraControllerRegisters.SERVO_ENABLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.SERVO_ENABLE", reply)

        if reply is not None:
            return Servos(reply.payload)
        return None

    def write_servo_enable(self, value: Servos) -> HarpMessage | None:
        """
        Writes a value to the ServoEnable register.

        Parameters
        ----------
        value : Servos
            Value to write to the ServoEnable register.
        """
        address = CameraControllerRegisters.SERVO_ENABLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.SERVO_ENABLE", reply)

        return reply

    def read_servo_disable(self) -> Servos | None:
        """
        Reads the contents of the ServoDisable register.

        Returns
        -------
        Servos | None
            Value read from the ServoDisable register.
        """
        address = CameraControllerRegisters.SERVO_DISABLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.SERVO_DISABLE", reply)

        if reply is not None:
            return Servos(reply.payload)
        return None

    def write_servo_disable(self, value: Servos) -> HarpMessage | None:
        """
        Writes a value to the ServoDisable register.

        Parameters
        ----------
        value : Servos
            Value to write to the ServoDisable register.
        """
        address = CameraControllerRegisters.SERVO_DISABLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.SERVO_DISABLE", reply)

        return reply

    def read_output_set(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputSet register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputSet register.
        """
        address = CameraControllerRegisters.OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.OUTPUT_SET", reply)

        if reply is not None:
            return DigitalOutputs(reply.payload)
        return None

    def write_output_set(self, value: DigitalOutputs) -> HarpMessage | None:
        """
        Writes a value to the OutputSet register.

        Parameters
        ----------
        value : DigitalOutputs
            Value to write to the OutputSet register.
        """
        address = CameraControllerRegisters.OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.OUTPUT_SET", reply)

        return reply

    def read_output_clear(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputClear register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputClear register.
        """
        address = CameraControllerRegisters.OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.OUTPUT_CLEAR", reply)

        if reply is not None:
            return DigitalOutputs(reply.payload)
        return None

    def write_output_clear(self, value: DigitalOutputs) -> HarpMessage | None:
        """
        Writes a value to the OutputClear register.

        Parameters
        ----------
        value : DigitalOutputs
            Value to write to the OutputClear register.
        """
        address = CameraControllerRegisters.OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.OUTPUT_CLEAR", reply)

        return reply

    def read_output_state(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputState register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputState register.
        """
        address = CameraControllerRegisters.OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.OUTPUT_STATE", reply)

        if reply is not None:
            return DigitalOutputs(reply.payload)
        return None

    def write_output_state(self, value: DigitalOutputs) -> HarpMessage | None:
        """
        Writes a value to the OutputState register.

        Parameters
        ----------
        value : DigitalOutputs
            Value to write to the OutputState register.
        """
        address = CameraControllerRegisters.OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.OUTPUT_STATE", reply)

        return reply

    def read_digital_input_state(self) -> DigitalInputs | None:
        """
        Reads the contents of the DigitalInputState register.

        Returns
        -------
        DigitalInputs | None
            Value read from the DigitalInputState register.
        """
        address = CameraControllerRegisters.DIGITAL_INPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.DIGITAL_INPUT_STATE", reply)

        if reply is not None:
            return DigitalInputs(reply.payload)
        return None

    def read_camera0_trigger(self) -> int | None:
        """
        Reads the contents of the Camera0Trigger register.

        Returns
        -------
        int | None
            Value read from the Camera0Trigger register.
        """
        address = CameraControllerRegisters.CAMERA0_TRIGGER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.CAMERA0_TRIGGER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_camera1_trigger(self) -> int | None:
        """
        Reads the contents of the Camera1Trigger register.

        Returns
        -------
        int | None
            Value read from the Camera1Trigger register.
        """
        address = CameraControllerRegisters.CAMERA1_TRIGGER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.CAMERA1_TRIGGER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_camera0_sync(self) -> int | None:
        """
        Reads the contents of the Camera0Sync register.

        Returns
        -------
        int | None
            Value read from the Camera0Sync register.
        """
        address = CameraControllerRegisters.CAMERA0_SYNC
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.CAMERA0_SYNC", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_camera1_sync(self) -> int | None:
        """
        Reads the contents of the Camera1Sync register.

        Returns
        -------
        int | None
            Value read from the Camera1Sync register.
        """
        address = CameraControllerRegisters.CAMERA1_SYNC
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.CAMERA1_SYNC", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_servo_state(self) -> Servos | None:
        """
        Reads the contents of the ServoState register.

        Returns
        -------
        Servos | None
            Value read from the ServoState register.
        """
        address = CameraControllerRegisters.SERVO_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.SERVO_STATE", reply)

        if reply is not None:
            return Servos(reply.payload)
        return None

    def read_sync_interval(self) -> int | None:
        """
        Reads the contents of the SyncInterval register.

        Returns
        -------
        int | None
            Value read from the SyncInterval register.
        """
        address = CameraControllerRegisters.SYNC_INTERVAL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.SYNC_INTERVAL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_sync_interval(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SyncInterval register.

        Parameters
        ----------
        value : int
            Value to write to the SyncInterval register.
        """
        address = CameraControllerRegisters.SYNC_INTERVAL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.SYNC_INTERVAL", reply)

        return reply

    def read_di0_mode(self) -> DI0ModeConfig | None:
        """
        Reads the contents of the DI0Mode register.

        Returns
        -------
        DI0ModeConfig | None
            Value read from the DI0Mode register.
        """
        address = CameraControllerRegisters.DI0_MODE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.DI0_MODE", reply)

        if reply is not None:
            return DI0ModeConfig(reply.payload)
        return None

    def write_di0_mode(self, value: DI0ModeConfig) -> HarpMessage | None:
        """
        Writes a value to the DI0Mode register.

        Parameters
        ----------
        value : DI0ModeConfig
            Value to write to the DI0Mode register.
        """
        address = CameraControllerRegisters.DI0_MODE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.DI0_MODE", reply)

        return reply

    def read_control0_mode(self) -> ControlModeConfig | None:
        """
        Reads the contents of the Control0Mode register.

        Returns
        -------
        ControlModeConfig | None
            Value read from the Control0Mode register.
        """
        address = CameraControllerRegisters.CONTROL0_MODE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.CONTROL0_MODE", reply)

        if reply is not None:
            return ControlModeConfig(reply.payload)
        return None

    def write_control0_mode(self, value: ControlModeConfig) -> HarpMessage | None:
        """
        Writes a value to the Control0Mode register.

        Parameters
        ----------
        value : ControlModeConfig
            Value to write to the Control0Mode register.
        """
        address = CameraControllerRegisters.CONTROL0_MODE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.CONTROL0_MODE", reply)

        return reply

    def read_camera0_frequency(self) -> int | None:
        """
        Reads the contents of the Camera0Frequency register.

        Returns
        -------
        int | None
            Value read from the Camera0Frequency register.
        """
        address = CameraControllerRegisters.CAMERA0_FREQUENCY
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.CAMERA0_FREQUENCY", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_camera0_frequency(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Camera0Frequency register.

        Parameters
        ----------
        value : int
            Value to write to the Camera0Frequency register.
        """
        address = CameraControllerRegisters.CAMERA0_FREQUENCY
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.CAMERA0_FREQUENCY", reply)

        return reply

    def read_servo0_period(self) -> int | None:
        """
        Reads the contents of the Servo0Period register.

        Returns
        -------
        int | None
            Value read from the Servo0Period register.
        """
        address = CameraControllerRegisters.SERVO0_PERIOD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.SERVO0_PERIOD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_servo0_period(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Servo0Period register.

        Parameters
        ----------
        value : int
            Value to write to the Servo0Period register.
        """
        address = CameraControllerRegisters.SERVO0_PERIOD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.SERVO0_PERIOD", reply)

        return reply

    def read_servo0_pulse_width(self) -> int | None:
        """
        Reads the contents of the Servo0PulseWidth register.

        Returns
        -------
        int | None
            Value read from the Servo0PulseWidth register.
        """
        address = CameraControllerRegisters.SERVO0_PULSE_WIDTH
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.SERVO0_PULSE_WIDTH", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_servo0_pulse_width(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Servo0PulseWidth register.

        Parameters
        ----------
        value : int
            Value to write to the Servo0PulseWidth register.
        """
        address = CameraControllerRegisters.SERVO0_PULSE_WIDTH
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.SERVO0_PULSE_WIDTH", reply)

        return reply

    def read_control1_mode(self) -> ControlModeConfig | None:
        """
        Reads the contents of the Control1Mode register.

        Returns
        -------
        ControlModeConfig | None
            Value read from the Control1Mode register.
        """
        address = CameraControllerRegisters.CONTROL1_MODE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.CONTROL1_MODE", reply)

        if reply is not None:
            return ControlModeConfig(reply.payload)
        return None

    def write_control1_mode(self, value: ControlModeConfig) -> HarpMessage | None:
        """
        Writes a value to the Control1Mode register.

        Parameters
        ----------
        value : ControlModeConfig
            Value to write to the Control1Mode register.
        """
        address = CameraControllerRegisters.CONTROL1_MODE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.CONTROL1_MODE", reply)

        return reply

    def read_camera1_frequency(self) -> int | None:
        """
        Reads the contents of the Camera1Frequency register.

        Returns
        -------
        int | None
            Value read from the Camera1Frequency register.
        """
        address = CameraControllerRegisters.CAMERA1_FREQUENCY
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.CAMERA1_FREQUENCY", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_camera1_frequency(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Camera1Frequency register.

        Parameters
        ----------
        value : int
            Value to write to the Camera1Frequency register.
        """
        address = CameraControllerRegisters.CAMERA1_FREQUENCY
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.CAMERA1_FREQUENCY", reply)

        return reply

    def read_servo1_period(self) -> int | None:
        """
        Reads the contents of the Servo1Period register.

        Returns
        -------
        int | None
            Value read from the Servo1Period register.
        """
        address = CameraControllerRegisters.SERVO1_PERIOD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.SERVO1_PERIOD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_servo1_period(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Servo1Period register.

        Parameters
        ----------
        value : int
            Value to write to the Servo1Period register.
        """
        address = CameraControllerRegisters.SERVO1_PERIOD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.SERVO1_PERIOD", reply)

        return reply

    def read_servo1_pulse_width(self) -> int | None:
        """
        Reads the contents of the Servo1PulseWidth register.

        Returns
        -------
        int | None
            Value read from the Servo1PulseWidth register.
        """
        address = CameraControllerRegisters.SERVO1_PULSE_WIDTH
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.SERVO1_PULSE_WIDTH", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_servo1_pulse_width(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Servo1PulseWidth register.

        Parameters
        ----------
        value : int
            Value to write to the Servo1PulseWidth register.
        """
        address = CameraControllerRegisters.SERVO1_PULSE_WIDTH
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.SERVO1_PULSE_WIDTH", reply)

        return reply

    def read_enable_events(self) -> CameraControllerEvents | None:
        """
        Reads the contents of the EnableEvents register.

        Returns
        -------
        CameraControllerEvents | None
            Value read from the EnableEvents register.
        """
        address = CameraControllerRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CameraControllerRegisters.ENABLE_EVENTS", reply)

        if reply is not None:
            return CameraControllerEvents(reply.payload)
        return None

    def write_enable_events(self, value: CameraControllerEvents) -> HarpMessage | None:
        """
        Writes a value to the EnableEvents register.

        Parameters
        ----------
        value : CameraControllerEvents
            Value to write to the EnableEvents register.
        """
        address = CameraControllerRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CameraControllerRegisters.ENABLE_EVENTS", reply)

        return reply

