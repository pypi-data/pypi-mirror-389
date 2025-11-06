from dataclasses import dataclass
from enum import IntEnum, IntFlag

from harp.protocol import MessageType, PayloadType
from harp.protocol.exceptions import HarpException, HarpReadException, HarpWriteException
from harp.protocol.messages import HarpMessage
from harp.serial import Device


class DigitalInputs(IntFlag):
    """
    

    Attributes
    ----------
    DI0 : int
        _No description currently available_
    """

    NONE = 0x0
    DI0 = 0x1


class DigitalOutputs(IntFlag):
    """
    

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
    DO4 : int
        _No description currently available_
    """

    NONE = 0x0
    DO0 = 0x1
    DO1 = 0x2
    DO2 = 0x4
    DO3 = 0x8
    DO4 = 0x16


class DI0ModeConfig(IntEnum):
    """
    Specifies the operation mode of the DI0 pin.

    Attributes
    ----------
    NONE : int
        The DI0 pin functions as a passive digital input.
    UPDATE_ON_RISING_EDGE : int
        Update the LED colors when the DI0 pin transitions from low to high.
    UPDATE_ON_HIGH : int
        Able to update RGBs when the pin is HIGH. Turn LEDs off when rising edge is detected.
    """

    NONE = 0
    UPDATE_ON_RISING_EDGE = 1
    UPDATE_ON_HIGH = 2


class DOModeConfig(IntEnum):
    """
    Specifies the operation mode of a Digital Output pin.

    Attributes
    ----------
    NONE : int
        The pin will function as a pure digital output.
    PULSE_ON_UPDATE : int
        A 1ms pulse will be triggered each time an RGB is updated.
    PULSE_ON_LOAD : int
        A 1ms pulse will be triggered each time an new array is loaded RGB.
    TOGGLE_ON_UPDATE : int
        The output pin will toggle each time an RGB is updated.
    TOGGLE_ON_LOAD : int
        The output pin will toggle each time an new array is loaded RGB.
    """

    NONE = 0
    PULSE_ON_UPDATE = 1
    PULSE_ON_LOAD = 2
    TOGGLE_ON_UPDATE = 3
    TOGGLE_ON_LOAD = 4


class RgbArrayEvents(IntEnum):
    """
    Available events to be enable in the board.

    Attributes
    ----------
    LED_STATUS : int
        _No description currently available_
    DIGITAL_INPUTS : int
        _No description currently available_
    """

    LED_STATUS = 1
    DIGITAL_INPUTS = 2


class RgbArrayRegisters(IntEnum):
    """Enum for all available registers in the RgbArray device.

    Attributes
    ----------
    LED_STATUS : int
        
    LED_COUNT : int
        The number of LEDs connected on each bus of the device.
    RGB_STATE : int
        The RGB color of each LED. [R0 G0 B0 R1 G1 B1 ...].
    RGB_BUS0_STATE : int
        The RGB color of each LED. [R0 G0 B0 R1 G1 B1 ...].
    RGB_BUS1_STATE : int
        The RGB color of each LED. [R0 G0 B0 R1 G1 B1 ...].
    RGB_OFF_STATE : int
        The RGB color of the LEDs when they are off.
    DI0_MODE : int
        
    DO0_MODE : int
        
    DO1_MODE : int
        
    LATCH_ON_NEXT_UPDATE : int
        Updates the settings of the RGBs, but will queue the instruction until a valid LedStatus command.
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
    DIGITAL_OUTPUT_PULSE_PERIOD : int
        The pulse period in milliseconds for digital outputs.
    DIGITAL_OUTPUT_PULSE_COUNT : int
        Triggers the specified number of pulses on the digital output lines.
    EVENT_ENABLE : int
        Specifies the active events in the device.
    """

    LED_STATUS = 32
    LED_COUNT = 33
    RGB_STATE = 34
    RGB_BUS0_STATE = 35
    RGB_BUS1_STATE = 36
    RGB_OFF_STATE = 37
    DI0_MODE = 39
    DO0_MODE = 40
    DO1_MODE = 41
    LATCH_ON_NEXT_UPDATE = 43
    DIGITAL_INPUT_STATE = 44
    OUTPUT_SET = 45
    OUTPUT_CLEAR = 46
    OUTPUT_TOGGLE = 47
    OUTPUT_STATE = 48
    DIGITAL_OUTPUT_PULSE_PERIOD = 49
    DIGITAL_OUTPUT_PULSE_COUNT = 50
    EVENT_ENABLE = 51


class RgbArray(Device):
    """
    RgbArray class for controlling the device.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect and load already happened in the base class
        # verify that WHO_AM_I matches the expected value
        if self.WHO_AM_I != 1264:
            self.disconnect()
            raise HarpException(f"WHO_AM_I mismatch: expected {1264}, got {self.WHO_AM_I}")

    def read_led_status(self) -> int | None:
        """
        Reads the contents of the LedStatus register.

        Returns
        -------
        int | None
            Value read from the LedStatus register.
        """
        address = RgbArrayRegisters.LED_STATUS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.LED_STATUS", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led_status(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the LedStatus register.

        Parameters
        ----------
        value : int
            Value to write to the LedStatus register.
        """
        address = RgbArrayRegisters.LED_STATUS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.LED_STATUS", reply)

        return reply

    def read_led_count(self) -> int | None:
        """
        Reads the contents of the LedCount register.

        Returns
        -------
        int | None
            Value read from the LedCount register.
        """
        address = RgbArrayRegisters.LED_COUNT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.LED_COUNT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led_count(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the LedCount register.

        Parameters
        ----------
        value : int
            Value to write to the LedCount register.
        """
        address = RgbArrayRegisters.LED_COUNT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.LED_COUNT", reply)

        return reply

    def read_rgb_state(self) -> bytes | None:
        """
        Reads the contents of the RgbState register.

        Returns
        -------
        bytes | None
            Value read from the RgbState register.
        """
        address = RgbArrayRegisters.RGB_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.RGB_STATE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_rgb_state(self, value: bytes) -> HarpMessage | None:
        """
        Writes a value to the RgbState register.

        Parameters
        ----------
        value : bytes
            Value to write to the RgbState register.
        """
        address = RgbArrayRegisters.RGB_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.RGB_STATE", reply)

        return reply

    def read_rgb_bus0_state(self) -> bytes | None:
        """
        Reads the contents of the RgbBus0State register.

        Returns
        -------
        bytes | None
            Value read from the RgbBus0State register.
        """
        address = RgbArrayRegisters.RGB_BUS0_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.RGB_BUS0_STATE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_rgb_bus0_state(self, value: bytes) -> HarpMessage | None:
        """
        Writes a value to the RgbBus0State register.

        Parameters
        ----------
        value : bytes
            Value to write to the RgbBus0State register.
        """
        address = RgbArrayRegisters.RGB_BUS0_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.RGB_BUS0_STATE", reply)

        return reply

    def read_rgb_bus1_state(self) -> bytes | None:
        """
        Reads the contents of the RgbBus1State register.

        Returns
        -------
        bytes | None
            Value read from the RgbBus1State register.
        """
        address = RgbArrayRegisters.RGB_BUS1_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.RGB_BUS1_STATE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_rgb_bus1_state(self, value: bytes) -> HarpMessage | None:
        """
        Writes a value to the RgbBus1State register.

        Parameters
        ----------
        value : bytes
            Value to write to the RgbBus1State register.
        """
        address = RgbArrayRegisters.RGB_BUS1_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.RGB_BUS1_STATE", reply)

        return reply

    def read_rgb_off_state(self) -> bytes | None:
        """
        Reads the contents of the RgbOffState register.

        Returns
        -------
        bytes | None
            Value read from the RgbOffState register.
        """
        address = RgbArrayRegisters.RGB_OFF_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.RGB_OFF_STATE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_rgb_off_state(self, value: bytes) -> HarpMessage | None:
        """
        Writes a value to the RgbOffState register.

        Parameters
        ----------
        value : bytes
            Value to write to the RgbOffState register.
        """
        address = RgbArrayRegisters.RGB_OFF_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.RGB_OFF_STATE", reply)

        return reply

    def read_di0_mode(self) -> DI0ModeConfig | None:
        """
        Reads the contents of the DI0Mode register.

        Returns
        -------
        DI0ModeConfig | None
            Value read from the DI0Mode register.
        """
        address = RgbArrayRegisters.DI0_MODE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.DI0_MODE", reply)

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
        address = RgbArrayRegisters.DI0_MODE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.DI0_MODE", reply)

        return reply

    def read_do0_mode(self) -> DOModeConfig | None:
        """
        Reads the contents of the DO0Mode register.

        Returns
        -------
        DOModeConfig | None
            Value read from the DO0Mode register.
        """
        address = RgbArrayRegisters.DO0_MODE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.DO0_MODE", reply)

        if reply is not None:
            return DOModeConfig(reply.payload)
        return None

    def write_do0_mode(self, value: DOModeConfig) -> HarpMessage | None:
        """
        Writes a value to the DO0Mode register.

        Parameters
        ----------
        value : DOModeConfig
            Value to write to the DO0Mode register.
        """
        address = RgbArrayRegisters.DO0_MODE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.DO0_MODE", reply)

        return reply

    def read_do1_mode(self) -> DOModeConfig | None:
        """
        Reads the contents of the DO1Mode register.

        Returns
        -------
        DOModeConfig | None
            Value read from the DO1Mode register.
        """
        address = RgbArrayRegisters.DO1_MODE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.DO1_MODE", reply)

        if reply is not None:
            return DOModeConfig(reply.payload)
        return None

    def write_do1_mode(self, value: DOModeConfig) -> HarpMessage | None:
        """
        Writes a value to the DO1Mode register.

        Parameters
        ----------
        value : DOModeConfig
            Value to write to the DO1Mode register.
        """
        address = RgbArrayRegisters.DO1_MODE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.DO1_MODE", reply)

        return reply

    def read_latch_on_next_update(self) -> bool | None:
        """
        Reads the contents of the LatchOnNextUpdate register.

        Returns
        -------
        bool | None
            Value read from the LatchOnNextUpdate register.
        """
        address = RgbArrayRegisters.LATCH_ON_NEXT_UPDATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.LATCH_ON_NEXT_UPDATE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_latch_on_next_update(self, value: bool) -> HarpMessage | None:
        """
        Writes a value to the LatchOnNextUpdate register.

        Parameters
        ----------
        value : bool
            Value to write to the LatchOnNextUpdate register.
        """
        address = RgbArrayRegisters.LATCH_ON_NEXT_UPDATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.LATCH_ON_NEXT_UPDATE", reply)

        return reply

    def read_digital_input_state(self) -> DigitalInputs | None:
        """
        Reads the contents of the DigitalInputState register.

        Returns
        -------
        DigitalInputs | None
            Value read from the DigitalInputState register.
        """
        address = RgbArrayRegisters.DIGITAL_INPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.DIGITAL_INPUT_STATE", reply)

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
        address = RgbArrayRegisters.OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.OUTPUT_SET", reply)

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
        address = RgbArrayRegisters.OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.OUTPUT_SET", reply)

        return reply

    def read_output_clear(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputClear register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputClear register.
        """
        address = RgbArrayRegisters.OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.OUTPUT_CLEAR", reply)

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
        address = RgbArrayRegisters.OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.OUTPUT_CLEAR", reply)

        return reply

    def read_output_toggle(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputToggle register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputToggle register.
        """
        address = RgbArrayRegisters.OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.OUTPUT_TOGGLE", reply)

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
        address = RgbArrayRegisters.OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.OUTPUT_TOGGLE", reply)

        return reply

    def read_output_state(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputState register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputState register.
        """
        address = RgbArrayRegisters.OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.OUTPUT_STATE", reply)

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
        address = RgbArrayRegisters.OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.OUTPUT_STATE", reply)

        return reply

    def read_digital_output_pulse_period(self) -> int | None:
        """
        Reads the contents of the DigitalOutputPulsePeriod register.

        Returns
        -------
        int | None
            Value read from the DigitalOutputPulsePeriod register.
        """
        address = RgbArrayRegisters.DIGITAL_OUTPUT_PULSE_PERIOD
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.DIGITAL_OUTPUT_PULSE_PERIOD", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_digital_output_pulse_period(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DigitalOutputPulsePeriod register.

        Parameters
        ----------
        value : int
            Value to write to the DigitalOutputPulsePeriod register.
        """
        address = RgbArrayRegisters.DIGITAL_OUTPUT_PULSE_PERIOD
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.DIGITAL_OUTPUT_PULSE_PERIOD", reply)

        return reply

    def read_digital_output_pulse_count(self) -> int | None:
        """
        Reads the contents of the DigitalOutputPulseCount register.

        Returns
        -------
        int | None
            Value read from the DigitalOutputPulseCount register.
        """
        address = RgbArrayRegisters.DIGITAL_OUTPUT_PULSE_COUNT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.DIGITAL_OUTPUT_PULSE_COUNT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_digital_output_pulse_count(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the DigitalOutputPulseCount register.

        Parameters
        ----------
        value : int
            Value to write to the DigitalOutputPulseCount register.
        """
        address = RgbArrayRegisters.DIGITAL_OUTPUT_PULSE_COUNT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.DIGITAL_OUTPUT_PULSE_COUNT", reply)

        return reply

    def read_event_enable(self) -> RgbArrayEvents | None:
        """
        Reads the contents of the EventEnable register.

        Returns
        -------
        RgbArrayEvents | None
            Value read from the EventEnable register.
        """
        address = RgbArrayRegisters.EVENT_ENABLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("RgbArrayRegisters.EVENT_ENABLE", reply)

        if reply is not None:
            return RgbArrayEvents(reply.payload)
        return None

    def write_event_enable(self, value: RgbArrayEvents) -> HarpMessage | None:
        """
        Writes a value to the EventEnable register.

        Parameters
        ----------
        value : RgbArrayEvents
            Value to write to the EventEnable register.
        """
        address = RgbArrayRegisters.EVENT_ENABLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("RgbArrayRegisters.EVENT_ENABLE", reply)

        return reply

