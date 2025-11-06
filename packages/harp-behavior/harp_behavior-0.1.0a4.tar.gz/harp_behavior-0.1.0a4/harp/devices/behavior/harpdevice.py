from dataclasses import dataclass
from enum import IntEnum, IntFlag

from harp.protocol import MessageType, PayloadType
from harp.protocol.exceptions import HarpException, HarpReadException, HarpWriteException
from harp.protocol.messages import HarpMessage
from harp.serial import Device


@dataclass
class AnalogDataPayload:
        # The voltage at the output of the ADC channel 0.
    AnalogInput0: int
        # The quadrature counter value on Port 2
    Encoder: int
        # The voltage at the output of the ADC channel 1.
    AnalogInput1: int


@dataclass
class RgbAllPayload:
        # The intensity of the green channel in the RGB0 LED.
    Green0: int
        # The intensity of the red channel in the RGB0 LED.
    Red0: int
        # The intensity of the blue channel in the RGB0 LED.
    Blue0: int
        # The intensity of the green channel in the RGB1 LED.
    Green1: int
        # The intensity of the red channel in the RGB1 LED.
    Red1: int
        # The intensity of the blue channel in the RGB1 LED.
    Blue1: int


@dataclass
class RgbPayload:
        # The intensity of the green channel in the RGB LED.
    Green: int
        # The intensity of the red channel in the RGB LED.
    Red: int
        # The intensity of the blue channel in the RGB LED.
    Blue: int


class DigitalInputs(IntFlag):
    """
    Specifies the state of port digital input lines.

    Attributes
    ----------
    DI_PORT0 : int
        _No description currently available_
    DI_PORT1 : int
        _No description currently available_
    DI_PORT2 : int
        _No description currently available_
    DI3 : int
        _No description currently available_
    """

    NONE = 0x0
    DI_PORT0 = 0x1
    DI_PORT1 = 0x2
    DI_PORT2 = 0x4
    DI3 = 0x8


class DigitalOutputs(IntFlag):
    """
    Specifies the state of port digital output lines.

    Attributes
    ----------
    DO_PORT0 : int
        _No description currently available_
    DO_PORT1 : int
        _No description currently available_
    DO_PORT2 : int
        _No description currently available_
    SUPPLY_PORT0 : int
        _No description currently available_
    SUPPLY_PORT1 : int
        _No description currently available_
    SUPPLY_PORT2 : int
        _No description currently available_
    LED0 : int
        _No description currently available_
    LED1 : int
        _No description currently available_
    RGB0 : int
        _No description currently available_
    RGB1 : int
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

    NONE = 0x0
    DO_PORT0 = 0x1
    DO_PORT1 = 0x2
    DO_PORT2 = 0x4
    SUPPLY_PORT0 = 0x8
    SUPPLY_PORT1 = 0x10
    SUPPLY_PORT2 = 0x20
    LED0 = 0x40
    LED1 = 0x80
    RGB0 = 0x100
    RGB1 = 0x200
    DO0 = 0x400
    DO1 = 0x800
    DO2 = 0x1000
    DO3 = 0x2000


class PortDigitalIOS(IntFlag):
    """
    Specifies the state of the port DIO lines.

    Attributes
    ----------
    DIO0 : int
        _No description currently available_
    DIO1 : int
        _No description currently available_
    DIO2 : int
        _No description currently available_
    """

    NONE = 0x0
    DIO0 = 0x1
    DIO1 = 0x2
    DIO2 = 0x4


class PwmOutputs(IntFlag):
    """
    Specifies the state of PWM output lines.

    Attributes
    ----------
    PWM_DO0 : int
        _No description currently available_
    PWM_DO1 : int
        _No description currently available_
    PWM_DO2 : int
        _No description currently available_
    PWM_DO3 : int
        _No description currently available_
    """

    NONE = 0x0
    PWM_DO0 = 0x1
    PWM_DO1 = 0x2
    PWM_DO2 = 0x4
    PWM_DO3 = 0x8


class Events(IntFlag):
    """
    Specifies the active events in the device.

    Attributes
    ----------
    PORT_DI : int
        _No description currently available_
    PORT_DIO : int
        _No description currently available_
    ANALOG_DATA : int
        _No description currently available_
    CAMERA0 : int
        _No description currently available_
    CAMERA1 : int
        _No description currently available_
    """

    NONE = 0x0
    PORT_DI = 0x1
    PORT_DIO = 0x2
    ANALOG_DATA = 0x4
    CAMERA0 = 0x8
    CAMERA1 = 0x10


class CameraOutputs(IntFlag):
    """
    Specifies camera output enable bits.

    Attributes
    ----------
    CAMERA_OUTPUT0 : int
        _No description currently available_
    CAMERA_OUTPUT1 : int
        _No description currently available_
    """

    NONE = 0x0
    CAMERA_OUTPUT0 = 0x1
    CAMERA_OUTPUT1 = 0x2


class ServoOutputs(IntFlag):
    """
    Specifies servo output enable bits.

    Attributes
    ----------
    SERVO_OUTPUT2 : int
        _No description currently available_
    SERVO_OUTPUT3 : int
        _No description currently available_
    """

    NONE = 0x0
    SERVO_OUTPUT2 = 0x4
    SERVO_OUTPUT3 = 0x8


class EncoderInputs(IntFlag):
    """
    Specifies quadrature counter enable bits.

    Attributes
    ----------
    ENCODER_PORT2 : int
        _No description currently available_
    """

    NONE = 0x0
    ENCODER_PORT2 = 0x4


class FrameAcquired(IntFlag):
    """
    Specifies that camera frame was acquired.

    Attributes
    ----------
    FRAME_ACQUIRED : int
        _No description currently available_
    """

    NONE = 0x0
    FRAME_ACQUIRED = 0x1


class MimicOutput(IntEnum):
    """
    Specifies the target IO on which to mimic the specified register.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    DIO0 : int
        _No description currently available_
    DIO1 : int
        _No description currently available_
    DIO2 : int
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
    DIO0 = 1
    DIO1 = 2
    DIO2 = 3
    DO0 = 4
    DO1 = 5
    DO2 = 6
    DO3 = 7


class EncoderModeConfig(IntEnum):
    """
    Specifies the type of reading made from the quadrature encoder.

    Attributes
    ----------
    POSITION : int
        _No description currently available_
    DISPLACEMENT : int
        _No description currently available_
    """

    POSITION = 0
    DISPLACEMENT = 1


class BehaviorRegisters(IntEnum):
    """Enum for all available registers in the Behavior device.

    Attributes
    ----------
    DIGITAL_INPUT_STATE : int
        Reflects the state of DI digital lines of each Port
    OUTPUT_SET : int
        Set the specified digital output lines.
    OUTPUT_CLEAR : int
        Clear the specified digital output lines
    OUTPUT_TOGGLE : int
        Toggle the specified digital output lines
    OUTPUT_STATE : int
        Write the state of all digital output lines
    PORT_DIO_SET : int
        Set the specified port DIO lines
    PORT_DIO_CLEAR : int
        Clear the specified port DIO lines
    PORT_DIO_TOGGLE : int
        Toggle the specified port DIO lines
    PORT_DIO_STATE : int
        Write the state of all port DIO lines
    PORT_DIO_DIRECTION : int
        Specifies which of the port DIO lines are outputs
    PORT_DIO_STATE_EVENT : int
        Specifies the state of the port DIO lines on a line change
    ANALOG_DATA : int
        Voltage at the ADC input and encoder value on Port 2
    OUTPUT_PULSE_ENABLE : int
        Enables the pulse function for the specified output lines
    PULSE_DO_PORT0 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_DO_PORT1 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_DO_PORT2 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_SUPPLY_PORT0 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_SUPPLY_PORT1 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_SUPPLY_PORT2 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_LED0 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_LED1 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_RGB0 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_RGB1 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_DO0 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_DO1 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_DO2 : int
        Specifies the duration of the output pulse in milliseconds.
    PULSE_DO3 : int
        Specifies the duration of the output pulse in milliseconds.
    PWM_FREQUENCY_DO0 : int
        Specifies the frequency of the PWM at DO0.
    PWM_FREQUENCY_DO1 : int
        Specifies the frequency of the PWM at DO1.
    PWM_FREQUENCY_DO2 : int
        Specifies the frequency of the PWM at DO2.
    PWM_FREQUENCY_DO3 : int
        Specifies the frequency of the PWM at DO3.
    PWM_DUTY_CYCLE_DO0 : int
        Specifies the duty cycle of the PWM at DO0.
    PWM_DUTY_CYCLE_DO1 : int
        Specifies the duty cycle of the PWM at DO1.
    PWM_DUTY_CYCLE_DO2 : int
        Specifies the duty cycle of the PWM at DO2.
    PWM_DUTY_CYCLE_DO3 : int
        Specifies the duty cycle of the PWM at DO3.
    PWM_START : int
        Starts the PWM on the selected output lines.
    PWM_STOP : int
        Stops the PWM on the selected output lines.
    RGB_ALL : int
        Specifies the state of all RGB LED channels.
    RGB0 : int
        Specifies the state of the RGB0 LED channels.
    RGB1 : int
        Specifies the state of the RGB1 LED channels.
    LED0_CURRENT : int
        Specifies the configuration of current to drive LED 0.
    LED1_CURRENT : int
        Specifies the configuration of current to drive LED 1.
    LED0_MAX_CURRENT : int
        Specifies the configuration of current to drive LED 0.
    LED1_MAX_CURRENT : int
        Specifies the configuration of current to drive LED 1.
    EVENT_ENABLE : int
        Specifies the active events in the device.
    START_CAMERAS : int
        Specifies the camera outputs to enable in the device.
    STOP_CAMERAS : int
        Specifies the camera outputs to disable in the device. An event will be issued when the trigger signal is actually stopped being generated.
    ENABLE_SERVOS : int
        Specifies the servo outputs to enable in the device.
    DISABLE_SERVOS : int
        Specifies the servo outputs to disable in the device.
    ENABLE_ENCODERS : int
        Specifies the port quadrature counters to enable in the device.
    ENCODER_MODE : int
        Configures the operation mode of the quadrature encoders.
    CAMERA0_FRAME : int
        Specifies that a frame was acquired on camera 0.
    CAMERA0_FREQUENCY : int
        Specifies the trigger frequency for camera 0.
    CAMERA1_FRAME : int
        Specifies that a frame was acquired on camera 1.
    CAMERA1_FREQUENCY : int
        Specifies the trigger frequency for camera 1.
    SERVO_MOTOR2_PERIOD : int
        Specifies the period of the servo motor in DO2, in microseconds.
    SERVO_MOTOR2_PULSE : int
        Specifies the pulse of the servo motor in DO2, in microseconds.
    SERVO_MOTOR3_PERIOD : int
        Specifies the period of the servo motor in DO3, in microseconds.
    SERVO_MOTOR3_PULSE : int
        Specifies the pulse of the servo motor in DO3, in microseconds.
    ENCODER_RESET : int
        Reset the counter of the specified encoders to zero.
    ENABLE_SERIAL_TIMESTAMP : int
        Enables the timestamp for serial TX.
    MIMIC_PORT0_IR : int
        Specifies the digital output to mimic the Port 0 IR state.
    MIMIC_PORT1_IR : int
        Specifies the digital output to mimic the Port 1 IR state.
    MIMIC_PORT2_IR : int
        Specifies the digital output to mimic the Port 2 IR state.
    MIMIC_PORT0_VALVE : int
        Specifies the digital output to mimic the Port 0 valve state.
    MIMIC_PORT1_VALVE : int
        Specifies the digital output to mimic the Port 1 valve state.
    MIMIC_PORT2_VALVE : int
        Specifies the digital output to mimic the Port 2 valve state.
    POKE_INPUT_FILTER : int
        Specifies the low pass filter time value for poke inputs, in ms.
    """

    DIGITAL_INPUT_STATE = 32
    OUTPUT_SET = 34
    OUTPUT_CLEAR = 35
    OUTPUT_TOGGLE = 36
    OUTPUT_STATE = 37
    PORT_DIO_SET = 38
    PORT_DIO_CLEAR = 39
    PORT_DIO_TOGGLE = 40
    PORT_DIO_STATE = 41
    PORT_DIO_DIRECTION = 42
    PORT_DIO_STATE_EVENT = 43
    ANALOG_DATA = 44
    OUTPUT_PULSE_ENABLE = 45
    PULSE_DO_PORT0 = 46
    PULSE_DO_PORT1 = 47
    PULSE_DO_PORT2 = 48
    PULSE_SUPPLY_PORT0 = 49
    PULSE_SUPPLY_PORT1 = 50
    PULSE_SUPPLY_PORT2 = 51
    PULSE_LED0 = 52
    PULSE_LED1 = 53
    PULSE_RGB0 = 54
    PULSE_RGB1 = 55
    PULSE_DO0 = 56
    PULSE_DO1 = 57
    PULSE_DO2 = 58
    PULSE_DO3 = 59
    PWM_FREQUENCY_DO0 = 60
    PWM_FREQUENCY_DO1 = 61
    PWM_FREQUENCY_DO2 = 62
    PWM_FREQUENCY_DO3 = 63
    PWM_DUTY_CYCLE_DO0 = 64
    PWM_DUTY_CYCLE_DO1 = 65
    PWM_DUTY_CYCLE_DO2 = 66
    PWM_DUTY_CYCLE_DO3 = 67
    PWM_START = 68
    PWM_STOP = 69
    RGB_ALL = 70
    RGB0 = 71
    RGB1 = 72
    LED0_CURRENT = 73
    LED1_CURRENT = 74
    LED0_MAX_CURRENT = 75
    LED1_MAX_CURRENT = 76
    EVENT_ENABLE = 77
    START_CAMERAS = 78
    STOP_CAMERAS = 79
    ENABLE_SERVOS = 80
    DISABLE_SERVOS = 81
    ENABLE_ENCODERS = 82
    ENCODER_MODE = 83
    CAMERA0_FRAME = 92
    CAMERA0_FREQUENCY = 93
    CAMERA1_FRAME = 94
    CAMERA1_FREQUENCY = 95
    SERVO_MOTOR2_PERIOD = 100
    SERVO_MOTOR2_PULSE = 101
    SERVO_MOTOR3_PERIOD = 102
    SERVO_MOTOR3_PULSE = 103
    ENCODER_RESET = 108
    ENABLE_SERIAL_TIMESTAMP = 110
    MIMIC_PORT0_IR = 111
    MIMIC_PORT1_IR = 112
    MIMIC_PORT2_IR = 113
    MIMIC_PORT0_VALVE = 117
    MIMIC_PORT1_VALVE = 118
    MIMIC_PORT2_VALVE = 119
    POKE_INPUT_FILTER = 122


class Behavior(Device):
    """
    Behavior class for controlling the device.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect and load already happened in the base class
        # verify that WHO_AM_I matches the expected value
        if self.WHO_AM_I != 1216:
            self.disconnect()
            raise HarpException(f"WHO_AM_I mismatch: expected {1216}, got {self.WHO_AM_I}")

    def read_digital_input_state(self) -> DigitalInputs | None:
        """
        Reads the contents of the DigitalInputState register.

        Returns
        -------
        DigitalInputs | None
            Value read from the DigitalInputState register.
        """
        address = BehaviorRegisters.DIGITAL_INPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.DIGITAL_INPUT_STATE", reply)

        if reply is not None:
            return DigitalInputs(reply.payload)
        return None

    def read_output_set(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputSet register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputSet register.
        """
        address = BehaviorRegisters.OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.OUTPUT_SET", reply)

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
        address = BehaviorRegisters.OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.OUTPUT_SET", reply)

        return reply

    def read_output_clear(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputClear register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputClear register.
        """
        address = BehaviorRegisters.OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.OUTPUT_CLEAR", reply)

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
        address = BehaviorRegisters.OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.OUTPUT_CLEAR", reply)

        return reply

    def read_output_toggle(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputToggle register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputToggle register.
        """
        address = BehaviorRegisters.OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.OUTPUT_TOGGLE", reply)

        if reply is not None:
            return DigitalOutputs(reply.payload)
        return None

    def write_output_toggle(self, value: DigitalOutputs) -> HarpMessage | None:
        """
        Writes a value to the OutputToggle register.

        Parameters
        ----------
        value : DigitalOutputs
            Value to write to the OutputToggle register.
        """
        address = BehaviorRegisters.OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.OUTPUT_TOGGLE", reply)

        return reply

    def read_output_state(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputState register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputState register.
        """
        address = BehaviorRegisters.OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.OUTPUT_STATE", reply)

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
        address = BehaviorRegisters.OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.OUTPUT_STATE", reply)

        return reply

    def read_port_dio_set(self) -> PortDigitalIOS | None:
        """
        Reads the contents of the PortDIOSet register.

        Returns
        -------
        PortDigitalIOS | None
            Value read from the PortDIOSet register.
        """
        address = BehaviorRegisters.PORT_DIO_SET
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PORT_DIO_SET", reply)

        if reply is not None:
            return PortDigitalIOS(reply.payload)
        return None

    def write_port_dio_set(self, value: PortDigitalIOS) -> HarpMessage | None:
        """
        Writes a value to the PortDIOSet register.

        Parameters
        ----------
        value : PortDigitalIOS
            Value to write to the PortDIOSet register.
        """
        address = BehaviorRegisters.PORT_DIO_SET
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PORT_DIO_SET", reply)

        return reply

    def read_port_dio_clear(self) -> PortDigitalIOS | None:
        """
        Reads the contents of the PortDIOClear register.

        Returns
        -------
        PortDigitalIOS | None
            Value read from the PortDIOClear register.
        """
        address = BehaviorRegisters.PORT_DIO_CLEAR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PORT_DIO_CLEAR", reply)

        if reply is not None:
            return PortDigitalIOS(reply.payload)
        return None

    def write_port_dio_clear(self, value: PortDigitalIOS) -> HarpMessage | None:
        """
        Writes a value to the PortDIOClear register.

        Parameters
        ----------
        value : PortDigitalIOS
            Value to write to the PortDIOClear register.
        """
        address = BehaviorRegisters.PORT_DIO_CLEAR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PORT_DIO_CLEAR", reply)

        return reply

    def read_port_dio_toggle(self) -> PortDigitalIOS | None:
        """
        Reads the contents of the PortDIOToggle register.

        Returns
        -------
        PortDigitalIOS | None
            Value read from the PortDIOToggle register.
        """
        address = BehaviorRegisters.PORT_DIO_TOGGLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PORT_DIO_TOGGLE", reply)

        if reply is not None:
            return PortDigitalIOS(reply.payload)
        return None

    def write_port_dio_toggle(self, value: PortDigitalIOS) -> HarpMessage | None:
        """
        Writes a value to the PortDIOToggle register.

        Parameters
        ----------
        value : PortDigitalIOS
            Value to write to the PortDIOToggle register.
        """
        address = BehaviorRegisters.PORT_DIO_TOGGLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PORT_DIO_TOGGLE", reply)

        return reply

    def read_port_dio_state(self) -> PortDigitalIOS | None:
        """
        Reads the contents of the PortDIOState register.

        Returns
        -------
        PortDigitalIOS | None
            Value read from the PortDIOState register.
        """
        address = BehaviorRegisters.PORT_DIO_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PORT_DIO_STATE", reply)

        if reply is not None:
            return PortDigitalIOS(reply.payload)
        return None

    def write_port_dio_state(self, value: PortDigitalIOS) -> HarpMessage | None:
        """
        Writes a value to the PortDIOState register.

        Parameters
        ----------
        value : PortDigitalIOS
            Value to write to the PortDIOState register.
        """
        address = BehaviorRegisters.PORT_DIO_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PORT_DIO_STATE", reply)

        return reply

    def read_port_dio_direction(self) -> PortDigitalIOS | None:
        """
        Reads the contents of the PortDIODirection register.

        Returns
        -------
        PortDigitalIOS | None
            Value read from the PortDIODirection register.
        """
        address = BehaviorRegisters.PORT_DIO_DIRECTION
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PORT_DIO_DIRECTION", reply)

        if reply is not None:
            return PortDigitalIOS(reply.payload)
        return None

    def write_port_dio_direction(self, value: PortDigitalIOS) -> HarpMessage | None:
        """
        Writes a value to the PortDIODirection register.

        Parameters
        ----------
        value : PortDigitalIOS
            Value to write to the PortDIODirection register.
        """
        address = BehaviorRegisters.PORT_DIO_DIRECTION
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PORT_DIO_DIRECTION", reply)

        return reply

    def read_port_dio_state_event(self) -> PortDigitalIOS | None:
        """
        Reads the contents of the PortDIOStateEvent register.

        Returns
        -------
        PortDigitalIOS | None
            Value read from the PortDIOStateEvent register.
        """
        address = BehaviorRegisters.PORT_DIO_STATE_EVENT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PORT_DIO_STATE_EVENT", reply)

        if reply is not None:
            return PortDigitalIOS(reply.payload)
        return None

    def read_analog_data(self) -> AnalogDataPayload | None:
        """
        Reads the contents of the AnalogData register.

        Returns
        -------
        AnalogDataPayload | None
            Value read from the AnalogData register.
        """
        address = BehaviorRegisters.ANALOG_DATA
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.S16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.ANALOG_DATA", reply)

        if reply is not None:
            # Map payload (list/array) to dataclass fields by offset
            payload = reply.payload
            return AnalogDataPayload(
                AnalogInput0=payload[0],
                Encoder=payload[1],
                AnalogInput1=payload[2]
            )
        return None

    def read_output_pulse_enable(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputPulseEnable register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputPulseEnable register.
        """
        address = BehaviorRegisters.OUTPUT_PULSE_ENABLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.OUTPUT_PULSE_ENABLE", reply)

        if reply is not None:
            return DigitalOutputs(reply.payload)
        return None

    def write_output_pulse_enable(self, value: DigitalOutputs) -> HarpMessage | None:
        """
        Writes a value to the OutputPulseEnable register.

        Parameters
        ----------
        value : DigitalOutputs
            Value to write to the OutputPulseEnable register.
        """
        address = BehaviorRegisters.OUTPUT_PULSE_ENABLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.OUTPUT_PULSE_ENABLE", reply)

        return reply

    def read_pulse_do_port0(self) -> int | None:
        """
        Reads the contents of the PulseDOPort0 register.

        Returns
        -------
        int | None
            Value read from the PulseDOPort0 register.
        """
        address = BehaviorRegisters.PULSE_DO_PORT0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_DO_PORT0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_do_port0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseDOPort0 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseDOPort0 register.
        """
        address = BehaviorRegisters.PULSE_DO_PORT0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_DO_PORT0", reply)

        return reply

    def read_pulse_do_port1(self) -> int | None:
        """
        Reads the contents of the PulseDOPort1 register.

        Returns
        -------
        int | None
            Value read from the PulseDOPort1 register.
        """
        address = BehaviorRegisters.PULSE_DO_PORT1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_DO_PORT1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_do_port1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseDOPort1 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseDOPort1 register.
        """
        address = BehaviorRegisters.PULSE_DO_PORT1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_DO_PORT1", reply)

        return reply

    def read_pulse_do_port2(self) -> int | None:
        """
        Reads the contents of the PulseDOPort2 register.

        Returns
        -------
        int | None
            Value read from the PulseDOPort2 register.
        """
        address = BehaviorRegisters.PULSE_DO_PORT2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_DO_PORT2", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_do_port2(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseDOPort2 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseDOPort2 register.
        """
        address = BehaviorRegisters.PULSE_DO_PORT2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_DO_PORT2", reply)

        return reply

    def read_pulse_supply_port0(self) -> int | None:
        """
        Reads the contents of the PulseSupplyPort0 register.

        Returns
        -------
        int | None
            Value read from the PulseSupplyPort0 register.
        """
        address = BehaviorRegisters.PULSE_SUPPLY_PORT0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_SUPPLY_PORT0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_supply_port0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseSupplyPort0 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseSupplyPort0 register.
        """
        address = BehaviorRegisters.PULSE_SUPPLY_PORT0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_SUPPLY_PORT0", reply)

        return reply

    def read_pulse_supply_port1(self) -> int | None:
        """
        Reads the contents of the PulseSupplyPort1 register.

        Returns
        -------
        int | None
            Value read from the PulseSupplyPort1 register.
        """
        address = BehaviorRegisters.PULSE_SUPPLY_PORT1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_SUPPLY_PORT1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_supply_port1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseSupplyPort1 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseSupplyPort1 register.
        """
        address = BehaviorRegisters.PULSE_SUPPLY_PORT1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_SUPPLY_PORT1", reply)

        return reply

    def read_pulse_supply_port2(self) -> int | None:
        """
        Reads the contents of the PulseSupplyPort2 register.

        Returns
        -------
        int | None
            Value read from the PulseSupplyPort2 register.
        """
        address = BehaviorRegisters.PULSE_SUPPLY_PORT2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_SUPPLY_PORT2", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_supply_port2(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseSupplyPort2 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseSupplyPort2 register.
        """
        address = BehaviorRegisters.PULSE_SUPPLY_PORT2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_SUPPLY_PORT2", reply)

        return reply

    def read_pulse_led0(self) -> int | None:
        """
        Reads the contents of the PulseLed0 register.

        Returns
        -------
        int | None
            Value read from the PulseLed0 register.
        """
        address = BehaviorRegisters.PULSE_LED0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_LED0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_led0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseLed0 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseLed0 register.
        """
        address = BehaviorRegisters.PULSE_LED0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_LED0", reply)

        return reply

    def read_pulse_led1(self) -> int | None:
        """
        Reads the contents of the PulseLed1 register.

        Returns
        -------
        int | None
            Value read from the PulseLed1 register.
        """
        address = BehaviorRegisters.PULSE_LED1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_LED1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_led1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseLed1 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseLed1 register.
        """
        address = BehaviorRegisters.PULSE_LED1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_LED1", reply)

        return reply

    def read_pulse_rgb0(self) -> int | None:
        """
        Reads the contents of the PulseRgb0 register.

        Returns
        -------
        int | None
            Value read from the PulseRgb0 register.
        """
        address = BehaviorRegisters.PULSE_RGB0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_RGB0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_rgb0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseRgb0 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseRgb0 register.
        """
        address = BehaviorRegisters.PULSE_RGB0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_RGB0", reply)

        return reply

    def read_pulse_rgb1(self) -> int | None:
        """
        Reads the contents of the PulseRgb1 register.

        Returns
        -------
        int | None
            Value read from the PulseRgb1 register.
        """
        address = BehaviorRegisters.PULSE_RGB1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_RGB1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_rgb1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseRgb1 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseRgb1 register.
        """
        address = BehaviorRegisters.PULSE_RGB1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_RGB1", reply)

        return reply

    def read_pulse_do0(self) -> int | None:
        """
        Reads the contents of the PulseDO0 register.

        Returns
        -------
        int | None
            Value read from the PulseDO0 register.
        """
        address = BehaviorRegisters.PULSE_DO0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_DO0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_do0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseDO0 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseDO0 register.
        """
        address = BehaviorRegisters.PULSE_DO0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_DO0", reply)

        return reply

    def read_pulse_do1(self) -> int | None:
        """
        Reads the contents of the PulseDO1 register.

        Returns
        -------
        int | None
            Value read from the PulseDO1 register.
        """
        address = BehaviorRegisters.PULSE_DO1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_DO1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_do1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseDO1 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseDO1 register.
        """
        address = BehaviorRegisters.PULSE_DO1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_DO1", reply)

        return reply

    def read_pulse_do2(self) -> int | None:
        """
        Reads the contents of the PulseDO2 register.

        Returns
        -------
        int | None
            Value read from the PulseDO2 register.
        """
        address = BehaviorRegisters.PULSE_DO2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_DO2", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_do2(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseDO2 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseDO2 register.
        """
        address = BehaviorRegisters.PULSE_DO2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_DO2", reply)

        return reply

    def read_pulse_do3(self) -> int | None:
        """
        Reads the contents of the PulseDO3 register.

        Returns
        -------
        int | None
            Value read from the PulseDO3 register.
        """
        address = BehaviorRegisters.PULSE_DO3
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PULSE_DO3", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_do3(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseDO3 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseDO3 register.
        """
        address = BehaviorRegisters.PULSE_DO3
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PULSE_DO3", reply)

        return reply

    def read_pwm_frequency_do0(self) -> int | None:
        """
        Reads the contents of the PwmFrequencyDO0 register.

        Returns
        -------
        int | None
            Value read from the PwmFrequencyDO0 register.
        """
        address = BehaviorRegisters.PWM_FREQUENCY_DO0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PWM_FREQUENCY_DO0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pwm_frequency_do0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PwmFrequencyDO0 register.

        Parameters
        ----------
        value : int
            Value to write to the PwmFrequencyDO0 register.
        """
        address = BehaviorRegisters.PWM_FREQUENCY_DO0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PWM_FREQUENCY_DO0", reply)

        return reply

    def read_pwm_frequency_do1(self) -> int | None:
        """
        Reads the contents of the PwmFrequencyDO1 register.

        Returns
        -------
        int | None
            Value read from the PwmFrequencyDO1 register.
        """
        address = BehaviorRegisters.PWM_FREQUENCY_DO1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PWM_FREQUENCY_DO1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pwm_frequency_do1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PwmFrequencyDO1 register.

        Parameters
        ----------
        value : int
            Value to write to the PwmFrequencyDO1 register.
        """
        address = BehaviorRegisters.PWM_FREQUENCY_DO1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PWM_FREQUENCY_DO1", reply)

        return reply

    def read_pwm_frequency_do2(self) -> int | None:
        """
        Reads the contents of the PwmFrequencyDO2 register.

        Returns
        -------
        int | None
            Value read from the PwmFrequencyDO2 register.
        """
        address = BehaviorRegisters.PWM_FREQUENCY_DO2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PWM_FREQUENCY_DO2", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pwm_frequency_do2(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PwmFrequencyDO2 register.

        Parameters
        ----------
        value : int
            Value to write to the PwmFrequencyDO2 register.
        """
        address = BehaviorRegisters.PWM_FREQUENCY_DO2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PWM_FREQUENCY_DO2", reply)

        return reply

    def read_pwm_frequency_do3(self) -> int | None:
        """
        Reads the contents of the PwmFrequencyDO3 register.

        Returns
        -------
        int | None
            Value read from the PwmFrequencyDO3 register.
        """
        address = BehaviorRegisters.PWM_FREQUENCY_DO3
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PWM_FREQUENCY_DO3", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pwm_frequency_do3(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PwmFrequencyDO3 register.

        Parameters
        ----------
        value : int
            Value to write to the PwmFrequencyDO3 register.
        """
        address = BehaviorRegisters.PWM_FREQUENCY_DO3
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PWM_FREQUENCY_DO3", reply)

        return reply

    def read_pwm_duty_cycle_do0(self) -> int | None:
        """
        Reads the contents of the PwmDutyCycleDO0 register.

        Returns
        -------
        int | None
            Value read from the PwmDutyCycleDO0 register.
        """
        address = BehaviorRegisters.PWM_DUTY_CYCLE_DO0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PWM_DUTY_CYCLE_DO0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pwm_duty_cycle_do0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PwmDutyCycleDO0 register.

        Parameters
        ----------
        value : int
            Value to write to the PwmDutyCycleDO0 register.
        """
        address = BehaviorRegisters.PWM_DUTY_CYCLE_DO0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PWM_DUTY_CYCLE_DO0", reply)

        return reply

    def read_pwm_duty_cycle_do1(self) -> int | None:
        """
        Reads the contents of the PwmDutyCycleDO1 register.

        Returns
        -------
        int | None
            Value read from the PwmDutyCycleDO1 register.
        """
        address = BehaviorRegisters.PWM_DUTY_CYCLE_DO1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PWM_DUTY_CYCLE_DO1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pwm_duty_cycle_do1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PwmDutyCycleDO1 register.

        Parameters
        ----------
        value : int
            Value to write to the PwmDutyCycleDO1 register.
        """
        address = BehaviorRegisters.PWM_DUTY_CYCLE_DO1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PWM_DUTY_CYCLE_DO1", reply)

        return reply

    def read_pwm_duty_cycle_do2(self) -> int | None:
        """
        Reads the contents of the PwmDutyCycleDO2 register.

        Returns
        -------
        int | None
            Value read from the PwmDutyCycleDO2 register.
        """
        address = BehaviorRegisters.PWM_DUTY_CYCLE_DO2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PWM_DUTY_CYCLE_DO2", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pwm_duty_cycle_do2(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PwmDutyCycleDO2 register.

        Parameters
        ----------
        value : int
            Value to write to the PwmDutyCycleDO2 register.
        """
        address = BehaviorRegisters.PWM_DUTY_CYCLE_DO2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PWM_DUTY_CYCLE_DO2", reply)

        return reply

    def read_pwm_duty_cycle_do3(self) -> int | None:
        """
        Reads the contents of the PwmDutyCycleDO3 register.

        Returns
        -------
        int | None
            Value read from the PwmDutyCycleDO3 register.
        """
        address = BehaviorRegisters.PWM_DUTY_CYCLE_DO3
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PWM_DUTY_CYCLE_DO3", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pwm_duty_cycle_do3(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PwmDutyCycleDO3 register.

        Parameters
        ----------
        value : int
            Value to write to the PwmDutyCycleDO3 register.
        """
        address = BehaviorRegisters.PWM_DUTY_CYCLE_DO3
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PWM_DUTY_CYCLE_DO3", reply)

        return reply

    def read_pwm_start(self) -> PwmOutputs | None:
        """
        Reads the contents of the PwmStart register.

        Returns
        -------
        PwmOutputs | None
            Value read from the PwmStart register.
        """
        address = BehaviorRegisters.PWM_START
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PWM_START", reply)

        if reply is not None:
            return PwmOutputs(reply.payload)
        return None

    def write_pwm_start(self, value: PwmOutputs) -> HarpMessage | None:
        """
        Writes a value to the PwmStart register.

        Parameters
        ----------
        value : PwmOutputs
            Value to write to the PwmStart register.
        """
        address = BehaviorRegisters.PWM_START
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PWM_START", reply)

        return reply

    def read_pwm_stop(self) -> PwmOutputs | None:
        """
        Reads the contents of the PwmStop register.

        Returns
        -------
        PwmOutputs | None
            Value read from the PwmStop register.
        """
        address = BehaviorRegisters.PWM_STOP
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.PWM_STOP", reply)

        if reply is not None:
            return PwmOutputs(reply.payload)
        return None

    def write_pwm_stop(self, value: PwmOutputs) -> HarpMessage | None:
        """
        Writes a value to the PwmStop register.

        Parameters
        ----------
        value : PwmOutputs
            Value to write to the PwmStop register.
        """
        address = BehaviorRegisters.PWM_STOP
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.PWM_STOP", reply)

        return reply

    def read_rgb_all(self) -> RgbAllPayload | None:
        """
        Reads the contents of the RgbAll register.

        Returns
        -------
        RgbAllPayload | None
            Value read from the RgbAll register.
        """
        address = BehaviorRegisters.RGB_ALL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.RGB_ALL", reply)

        if reply is not None:
            # Map payload (list/array) to dataclass fields by offset
            payload = reply.payload
            return RgbAllPayload(
                Green0=payload[0],
                Red0=payload[1],
                Blue0=payload[2],
                Green1=payload[3],
                Red1=payload[4],
                Blue1=payload[5]
            )
        return None

    def write_rgb_all(self, value: RgbAllPayload) -> HarpMessage | None:
        """
        Writes a value to the RgbAll register.

        Parameters
        ----------
        value : RgbAllPayload
            Value to write to the RgbAll register.
        """
        address = BehaviorRegisters.RGB_ALL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.RGB_ALL", reply)

        return reply

    def read_rgb0(self) -> RgbPayload | None:
        """
        Reads the contents of the Rgb0 register.

        Returns
        -------
        RgbPayload | None
            Value read from the Rgb0 register.
        """
        address = BehaviorRegisters.RGB0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.RGB0", reply)

        if reply is not None:
            # Map payload (list/array) to dataclass fields by offset
            payload = reply.payload
            return RgbPayload(
                Green=payload[0],
                Red=payload[1],
                Blue=payload[2]
            )
        return None

    def write_rgb0(self, value: RgbPayload) -> HarpMessage | None:
        """
        Writes a value to the Rgb0 register.

        Parameters
        ----------
        value : RgbPayload
            Value to write to the Rgb0 register.
        """
        address = BehaviorRegisters.RGB0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.RGB0", reply)

        return reply

    def read_rgb1(self) -> RgbPayload | None:
        """
        Reads the contents of the Rgb1 register.

        Returns
        -------
        RgbPayload | None
            Value read from the Rgb1 register.
        """
        address = BehaviorRegisters.RGB1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.RGB1", reply)

        if reply is not None:
            # Map payload (list/array) to dataclass fields by offset
            payload = reply.payload
            return RgbPayload(
                Green=payload[0],
                Red=payload[1],
                Blue=payload[2]
            )
        return None

    def write_rgb1(self, value: RgbPayload) -> HarpMessage | None:
        """
        Writes a value to the Rgb1 register.

        Parameters
        ----------
        value : RgbPayload
            Value to write to the Rgb1 register.
        """
        address = BehaviorRegisters.RGB1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.RGB1", reply)

        return reply

    def read_led0_current(self) -> int | None:
        """
        Reads the contents of the Led0Current register.

        Returns
        -------
        int | None
            Value read from the Led0Current register.
        """
        address = BehaviorRegisters.LED0_CURRENT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.LED0_CURRENT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_current(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led0Current register.

        Parameters
        ----------
        value : int
            Value to write to the Led0Current register.
        """
        address = BehaviorRegisters.LED0_CURRENT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.LED0_CURRENT", reply)

        return reply

    def read_led1_current(self) -> int | None:
        """
        Reads the contents of the Led1Current register.

        Returns
        -------
        int | None
            Value read from the Led1Current register.
        """
        address = BehaviorRegisters.LED1_CURRENT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.LED1_CURRENT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_current(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led1Current register.

        Parameters
        ----------
        value : int
            Value to write to the Led1Current register.
        """
        address = BehaviorRegisters.LED1_CURRENT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.LED1_CURRENT", reply)

        return reply

    def read_led0_max_current(self) -> int | None:
        """
        Reads the contents of the Led0MaxCurrent register.

        Returns
        -------
        int | None
            Value read from the Led0MaxCurrent register.
        """
        address = BehaviorRegisters.LED0_MAX_CURRENT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.LED0_MAX_CURRENT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_max_current(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led0MaxCurrent register.

        Parameters
        ----------
        value : int
            Value to write to the Led0MaxCurrent register.
        """
        address = BehaviorRegisters.LED0_MAX_CURRENT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.LED0_MAX_CURRENT", reply)

        return reply

    def read_led1_max_current(self) -> int | None:
        """
        Reads the contents of the Led1MaxCurrent register.

        Returns
        -------
        int | None
            Value read from the Led1MaxCurrent register.
        """
        address = BehaviorRegisters.LED1_MAX_CURRENT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.LED1_MAX_CURRENT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_max_current(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led1MaxCurrent register.

        Parameters
        ----------
        value : int
            Value to write to the Led1MaxCurrent register.
        """
        address = BehaviorRegisters.LED1_MAX_CURRENT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.LED1_MAX_CURRENT", reply)

        return reply

    def read_event_enable(self) -> Events | None:
        """
        Reads the contents of the EventEnable register.

        Returns
        -------
        Events | None
            Value read from the EventEnable register.
        """
        address = BehaviorRegisters.EVENT_ENABLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.EVENT_ENABLE", reply)

        if reply is not None:
            return Events(reply.payload)
        return None

    def write_event_enable(self, value: Events) -> HarpMessage | None:
        """
        Writes a value to the EventEnable register.

        Parameters
        ----------
        value : Events
            Value to write to the EventEnable register.
        """
        address = BehaviorRegisters.EVENT_ENABLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.EVENT_ENABLE", reply)

        return reply

    def read_start_cameras(self) -> CameraOutputs | None:
        """
        Reads the contents of the StartCameras register.

        Returns
        -------
        CameraOutputs | None
            Value read from the StartCameras register.
        """
        address = BehaviorRegisters.START_CAMERAS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.START_CAMERAS", reply)

        if reply is not None:
            return CameraOutputs(reply.payload)
        return None

    def write_start_cameras(self, value: CameraOutputs) -> HarpMessage | None:
        """
        Writes a value to the StartCameras register.

        Parameters
        ----------
        value : CameraOutputs
            Value to write to the StartCameras register.
        """
        address = BehaviorRegisters.START_CAMERAS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.START_CAMERAS", reply)

        return reply

    def read_stop_cameras(self) -> CameraOutputs | None:
        """
        Reads the contents of the StopCameras register.

        Returns
        -------
        CameraOutputs | None
            Value read from the StopCameras register.
        """
        address = BehaviorRegisters.STOP_CAMERAS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.STOP_CAMERAS", reply)

        if reply is not None:
            return CameraOutputs(reply.payload)
        return None

    def write_stop_cameras(self, value: CameraOutputs) -> HarpMessage | None:
        """
        Writes a value to the StopCameras register.

        Parameters
        ----------
        value : CameraOutputs
            Value to write to the StopCameras register.
        """
        address = BehaviorRegisters.STOP_CAMERAS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.STOP_CAMERAS", reply)

        return reply

    def read_enable_servos(self) -> ServoOutputs | None:
        """
        Reads the contents of the EnableServos register.

        Returns
        -------
        ServoOutputs | None
            Value read from the EnableServos register.
        """
        address = BehaviorRegisters.ENABLE_SERVOS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.ENABLE_SERVOS", reply)

        if reply is not None:
            return ServoOutputs(reply.payload)
        return None

    def write_enable_servos(self, value: ServoOutputs) -> HarpMessage | None:
        """
        Writes a value to the EnableServos register.

        Parameters
        ----------
        value : ServoOutputs
            Value to write to the EnableServos register.
        """
        address = BehaviorRegisters.ENABLE_SERVOS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.ENABLE_SERVOS", reply)

        return reply

    def read_disable_servos(self) -> ServoOutputs | None:
        """
        Reads the contents of the DisableServos register.

        Returns
        -------
        ServoOutputs | None
            Value read from the DisableServos register.
        """
        address = BehaviorRegisters.DISABLE_SERVOS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.DISABLE_SERVOS", reply)

        if reply is not None:
            return ServoOutputs(reply.payload)
        return None

    def write_disable_servos(self, value: ServoOutputs) -> HarpMessage | None:
        """
        Writes a value to the DisableServos register.

        Parameters
        ----------
        value : ServoOutputs
            Value to write to the DisableServos register.
        """
        address = BehaviorRegisters.DISABLE_SERVOS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.DISABLE_SERVOS", reply)

        return reply

    def read_enable_encoders(self) -> EncoderInputs | None:
        """
        Reads the contents of the EnableEncoders register.

        Returns
        -------
        EncoderInputs | None
            Value read from the EnableEncoders register.
        """
        address = BehaviorRegisters.ENABLE_ENCODERS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.ENABLE_ENCODERS", reply)

        if reply is not None:
            return EncoderInputs(reply.payload)
        return None

    def write_enable_encoders(self, value: EncoderInputs) -> HarpMessage | None:
        """
        Writes a value to the EnableEncoders register.

        Parameters
        ----------
        value : EncoderInputs
            Value to write to the EnableEncoders register.
        """
        address = BehaviorRegisters.ENABLE_ENCODERS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.ENABLE_ENCODERS", reply)

        return reply

    def read_encoder_mode(self) -> EncoderModeConfig | None:
        """
        Reads the contents of the EncoderMode register.

        Returns
        -------
        EncoderModeConfig | None
            Value read from the EncoderMode register.
        """
        address = BehaviorRegisters.ENCODER_MODE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.ENCODER_MODE", reply)

        if reply is not None:
            return EncoderModeConfig(reply.payload)
        return None

    def write_encoder_mode(self, value: EncoderModeConfig) -> HarpMessage | None:
        """
        Writes a value to the EncoderMode register.

        Parameters
        ----------
        value : EncoderModeConfig
            Value to write to the EncoderMode register.
        """
        address = BehaviorRegisters.ENCODER_MODE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.ENCODER_MODE", reply)

        return reply

    def read_camera0_frame(self) -> FrameAcquired | None:
        """
        Reads the contents of the Camera0Frame register.

        Returns
        -------
        FrameAcquired | None
            Value read from the Camera0Frame register.
        """
        address = BehaviorRegisters.CAMERA0_FRAME
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.CAMERA0_FRAME", reply)

        if reply is not None:
            return FrameAcquired(reply.payload)
        return None

    def read_camera0_frequency(self) -> int | None:
        """
        Reads the contents of the Camera0Frequency register.

        Returns
        -------
        int | None
            Value read from the Camera0Frequency register.
        """
        address = BehaviorRegisters.CAMERA0_FREQUENCY
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.CAMERA0_FREQUENCY", reply)

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
        address = BehaviorRegisters.CAMERA0_FREQUENCY
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.CAMERA0_FREQUENCY", reply)

        return reply

    def read_camera1_frame(self) -> FrameAcquired | None:
        """
        Reads the contents of the Camera1Frame register.

        Returns
        -------
        FrameAcquired | None
            Value read from the Camera1Frame register.
        """
        address = BehaviorRegisters.CAMERA1_FRAME
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.CAMERA1_FRAME", reply)

        if reply is not None:
            return FrameAcquired(reply.payload)
        return None

    def read_camera1_frequency(self) -> int | None:
        """
        Reads the contents of the Camera1Frequency register.

        Returns
        -------
        int | None
            Value read from the Camera1Frequency register.
        """
        address = BehaviorRegisters.CAMERA1_FREQUENCY
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.CAMERA1_FREQUENCY", reply)

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
        address = BehaviorRegisters.CAMERA1_FREQUENCY
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.CAMERA1_FREQUENCY", reply)

        return reply

    def read_servo_motor2_period(self) -> int | None:
        """
        Reads the contents of the ServoMotor2Period register.

        Returns
        -------
        int | None
            Value read from the ServoMotor2Period register.
        """
        address = BehaviorRegisters.SERVO_MOTOR2_PERIOD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.SERVO_MOTOR2_PERIOD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_servo_motor2_period(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the ServoMotor2Period register.

        Parameters
        ----------
        value : int
            Value to write to the ServoMotor2Period register.
        """
        address = BehaviorRegisters.SERVO_MOTOR2_PERIOD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.SERVO_MOTOR2_PERIOD", reply)

        return reply

    def read_servo_motor2_pulse(self) -> int | None:
        """
        Reads the contents of the ServoMotor2Pulse register.

        Returns
        -------
        int | None
            Value read from the ServoMotor2Pulse register.
        """
        address = BehaviorRegisters.SERVO_MOTOR2_PULSE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.SERVO_MOTOR2_PULSE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_servo_motor2_pulse(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the ServoMotor2Pulse register.

        Parameters
        ----------
        value : int
            Value to write to the ServoMotor2Pulse register.
        """
        address = BehaviorRegisters.SERVO_MOTOR2_PULSE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.SERVO_MOTOR2_PULSE", reply)

        return reply

    def read_servo_motor3_period(self) -> int | None:
        """
        Reads the contents of the ServoMotor3Period register.

        Returns
        -------
        int | None
            Value read from the ServoMotor3Period register.
        """
        address = BehaviorRegisters.SERVO_MOTOR3_PERIOD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.SERVO_MOTOR3_PERIOD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_servo_motor3_period(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the ServoMotor3Period register.

        Parameters
        ----------
        value : int
            Value to write to the ServoMotor3Period register.
        """
        address = BehaviorRegisters.SERVO_MOTOR3_PERIOD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.SERVO_MOTOR3_PERIOD", reply)

        return reply

    def read_servo_motor3_pulse(self) -> int | None:
        """
        Reads the contents of the ServoMotor3Pulse register.

        Returns
        -------
        int | None
            Value read from the ServoMotor3Pulse register.
        """
        address = BehaviorRegisters.SERVO_MOTOR3_PULSE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.SERVO_MOTOR3_PULSE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_servo_motor3_pulse(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the ServoMotor3Pulse register.

        Parameters
        ----------
        value : int
            Value to write to the ServoMotor3Pulse register.
        """
        address = BehaviorRegisters.SERVO_MOTOR3_PULSE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.SERVO_MOTOR3_PULSE", reply)

        return reply

    def read_encoder_reset(self) -> EncoderInputs | None:
        """
        Reads the contents of the EncoderReset register.

        Returns
        -------
        EncoderInputs | None
            Value read from the EncoderReset register.
        """
        address = BehaviorRegisters.ENCODER_RESET
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.ENCODER_RESET", reply)

        if reply is not None:
            return EncoderInputs(reply.payload)
        return None

    def write_encoder_reset(self, value: EncoderInputs) -> HarpMessage | None:
        """
        Writes a value to the EncoderReset register.

        Parameters
        ----------
        value : EncoderInputs
            Value to write to the EncoderReset register.
        """
        address = BehaviorRegisters.ENCODER_RESET
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.ENCODER_RESET", reply)

        return reply

    def read_enable_serial_timestamp(self) -> int | None:
        """
        Reads the contents of the EnableSerialTimestamp register.

        Returns
        -------
        int | None
            Value read from the EnableSerialTimestamp register.
        """
        address = BehaviorRegisters.ENABLE_SERIAL_TIMESTAMP
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.ENABLE_SERIAL_TIMESTAMP", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_enable_serial_timestamp(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the EnableSerialTimestamp register.

        Parameters
        ----------
        value : int
            Value to write to the EnableSerialTimestamp register.
        """
        address = BehaviorRegisters.ENABLE_SERIAL_TIMESTAMP
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.ENABLE_SERIAL_TIMESTAMP", reply)

        return reply

    def read_mimic_port0_ir(self) -> MimicOutput | None:
        """
        Reads the contents of the MimicPort0IR register.

        Returns
        -------
        MimicOutput | None
            Value read from the MimicPort0IR register.
        """
        address = BehaviorRegisters.MIMIC_PORT0_IR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.MIMIC_PORT0_IR", reply)

        if reply is not None:
            return MimicOutput(reply.payload)
        return None

    def write_mimic_port0_ir(self, value: MimicOutput) -> HarpMessage | None:
        """
        Writes a value to the MimicPort0IR register.

        Parameters
        ----------
        value : MimicOutput
            Value to write to the MimicPort0IR register.
        """
        address = BehaviorRegisters.MIMIC_PORT0_IR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.MIMIC_PORT0_IR", reply)

        return reply

    def read_mimic_port1_ir(self) -> MimicOutput | None:
        """
        Reads the contents of the MimicPort1IR register.

        Returns
        -------
        MimicOutput | None
            Value read from the MimicPort1IR register.
        """
        address = BehaviorRegisters.MIMIC_PORT1_IR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.MIMIC_PORT1_IR", reply)

        if reply is not None:
            return MimicOutput(reply.payload)
        return None

    def write_mimic_port1_ir(self, value: MimicOutput) -> HarpMessage | None:
        """
        Writes a value to the MimicPort1IR register.

        Parameters
        ----------
        value : MimicOutput
            Value to write to the MimicPort1IR register.
        """
        address = BehaviorRegisters.MIMIC_PORT1_IR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.MIMIC_PORT1_IR", reply)

        return reply

    def read_mimic_port2_ir(self) -> MimicOutput | None:
        """
        Reads the contents of the MimicPort2IR register.

        Returns
        -------
        MimicOutput | None
            Value read from the MimicPort2IR register.
        """
        address = BehaviorRegisters.MIMIC_PORT2_IR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.MIMIC_PORT2_IR", reply)

        if reply is not None:
            return MimicOutput(reply.payload)
        return None

    def write_mimic_port2_ir(self, value: MimicOutput) -> HarpMessage | None:
        """
        Writes a value to the MimicPort2IR register.

        Parameters
        ----------
        value : MimicOutput
            Value to write to the MimicPort2IR register.
        """
        address = BehaviorRegisters.MIMIC_PORT2_IR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.MIMIC_PORT2_IR", reply)

        return reply

    def read_mimic_port0_valve(self) -> MimicOutput | None:
        """
        Reads the contents of the MimicPort0Valve register.

        Returns
        -------
        MimicOutput | None
            Value read from the MimicPort0Valve register.
        """
        address = BehaviorRegisters.MIMIC_PORT0_VALVE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.MIMIC_PORT0_VALVE", reply)

        if reply is not None:
            return MimicOutput(reply.payload)
        return None

    def write_mimic_port0_valve(self, value: MimicOutput) -> HarpMessage | None:
        """
        Writes a value to the MimicPort0Valve register.

        Parameters
        ----------
        value : MimicOutput
            Value to write to the MimicPort0Valve register.
        """
        address = BehaviorRegisters.MIMIC_PORT0_VALVE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.MIMIC_PORT0_VALVE", reply)

        return reply

    def read_mimic_port1_valve(self) -> MimicOutput | None:
        """
        Reads the contents of the MimicPort1Valve register.

        Returns
        -------
        MimicOutput | None
            Value read from the MimicPort1Valve register.
        """
        address = BehaviorRegisters.MIMIC_PORT1_VALVE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.MIMIC_PORT1_VALVE", reply)

        if reply is not None:
            return MimicOutput(reply.payload)
        return None

    def write_mimic_port1_valve(self, value: MimicOutput) -> HarpMessage | None:
        """
        Writes a value to the MimicPort1Valve register.

        Parameters
        ----------
        value : MimicOutput
            Value to write to the MimicPort1Valve register.
        """
        address = BehaviorRegisters.MIMIC_PORT1_VALVE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.MIMIC_PORT1_VALVE", reply)

        return reply

    def read_mimic_port2_valve(self) -> MimicOutput | None:
        """
        Reads the contents of the MimicPort2Valve register.

        Returns
        -------
        MimicOutput | None
            Value read from the MimicPort2Valve register.
        """
        address = BehaviorRegisters.MIMIC_PORT2_VALVE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.MIMIC_PORT2_VALVE", reply)

        if reply is not None:
            return MimicOutput(reply.payload)
        return None

    def write_mimic_port2_valve(self, value: MimicOutput) -> HarpMessage | None:
        """
        Writes a value to the MimicPort2Valve register.

        Parameters
        ----------
        value : MimicOutput
            Value to write to the MimicPort2Valve register.
        """
        address = BehaviorRegisters.MIMIC_PORT2_VALVE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.MIMIC_PORT2_VALVE", reply)

        return reply

    def read_poke_input_filter(self) -> int | None:
        """
        Reads the contents of the PokeInputFilter register.

        Returns
        -------
        int | None
            Value read from the PokeInputFilter register.
        """
        address = BehaviorRegisters.POKE_INPUT_FILTER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("BehaviorRegisters.POKE_INPUT_FILTER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_poke_input_filter(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PokeInputFilter register.

        Parameters
        ----------
        value : int
            Value to write to the PokeInputFilter register.
        """
        address = BehaviorRegisters.POKE_INPUT_FILTER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("BehaviorRegisters.POKE_INPUT_FILTER", reply)

        return reply

