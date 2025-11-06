from dataclasses import dataclass
from enum import IntEnum, IntFlag

from harp.protocol import MessageType, PayloadType
from harp.protocol.exceptions import HarpException, HarpReadException, HarpWriteException
from harp.protocol.messages import HarpMessage
from harp.serial import Device


class DigitalOutputs(IntFlag):
    """
    Specifies the state of port digital output lines.

    Attributes
    ----------
    DO1 : int
        _No description currently available_
    DO2 : int
        _No description currently available_
    """

    NONE = 0x0
    DO1 = 0x1
    DO2 = 0x2


class Bncs(IntFlag):
    """
    Specifies the state of BNCs

    Attributes
    ----------
    BNC1 : int
        _No description currently available_
    BNC2 : int
        _No description currently available_
    """

    NONE = 0x0
    BNC1 = 0x1
    BNC2 = 0x2


class Signals(IntFlag):
    """
    Specifies the state of Signals

    Attributes
    ----------
    SIGNAL_A : int
        _No description currently available_
    SIGNAL_B : int
        _No description currently available_
    """

    NONE = 0x0
    SIGNAL_A = 0x1
    SIGNAL_B = 0x2


class LaserDriverControllerEvents(IntFlag):
    """
    Specifies the active events in the device

    Attributes
    ----------
    EVENT_SPAD_SWITCH : int
        _No description currently available_
    EVENT_LASER_STATE : int
        _No description currently available_
    """

    NONE = 0x0
    EVENT_SPAD_SWITCH = 0x1
    EVENT_LASER_STATE = 0x2


class FrequencySelect(IntEnum):
    """
    Selects laser frequency mode

    Attributes
    ----------
    NONE : int
        _No description currently available_
    F1 : int
        _No description currently available_
    F2 : int
        _No description currently available_
    F3 : int
        _No description currently available_
    C_W : int
        _No description currently available_
    """

    NONE = 0
    F1 = 1
    F2 = 2
    F3 = 4
    C_W = 8


class LaserDriverControllerRegisters(IntEnum):
    """Enum for all available registers in the LaserDriverController device.

    Attributes
    ----------
    SPAD_SWITCH : int
        Turns ON/OFF the relay to switch SPADs supply
    LASER_STATE : int
        State of the laser, ON/OFF
    LASER_FREQUENCY_SELECT : int
        Set the laser frequency
    LASER_INTENSITY : int
        Laser intensity value [0:255]
    OUTPUT_SET : int
        Set the specified digital output lines
    OUTPUT_CLEAR : int
        Clear the specified digital output lines
    OUTPUT_TOGGLE : int
        Toggle the specified digital output lines
    OUTPUT_STATE : int
        Write the state of all digital output lines
    BNCS_STATE : int
        Configure BNCs to start
    SIGNAL_STATE : int
        Configure Signals to start
    BNC1_ON : int
        Time ON of BNC1 (milliseconds) [1:65535]
    BNC1_OFF : int
        Time OFF of BNC1 (milliseconds) [1:65535]
    BNC1_PULSES : int
        Number of pulses (BNC1) [0;65535], 0-> infinite repeat
    BNC1_TAIL : int
        Wait time to start (milliseconds) (BNC1) [1;65535]
    BNC2_ON : int
        Time ON of BNC2 (milliseconds) [1:65535]
    BNC2_OFF : int
        Time OFF of BNC2 (milliseconds) [1:65535]
    BNC2_PULSES : int
        Number of pulses (BNC2) [0;65535], 0-> infinite repeat
    BNC2_TAIL : int
        Wait time to start (milliseconds) (BNC2) [1;65535]
    SIGNAL_A_ON : int
        Time ON of SignalA (milliseconds) [1:65535]
    SIGNAL_A_OFF : int
        Time OFF of SignalA (milliseconds) [1:65535]
    SIGNAL_A_PULSES : int
        Number of pulses (SignalA) [0;65535], 0-> infinite repeat
    SIGNAL_A_TAIL : int
        Wait time to start (milliseconds) (SignalA) [1;65535]
    SIGNAL_B_ON : int
        Time ON of SignalB (milliseconds) [1:65535]
    SIGNAL_B_OFF : int
        Time OFF of SignalB (milliseconds) [1:65535]
    SIGNAL_B_PULSES : int
        Number of pulses (SignalB) [0;65535], 0-> infinite repeat
    SIGNAL_B_TAIL : int
        Wait time to start (milliseconds) (SignalB) [1;65535]
    EVENT_ENABLE : int
        Specifies the active events in the device
    """

    SPAD_SWITCH = 32
    LASER_STATE = 33
    LASER_FREQUENCY_SELECT = 38
    LASER_INTENSITY = 39
    OUTPUT_SET = 40
    OUTPUT_CLEAR = 41
    OUTPUT_TOGGLE = 42
    OUTPUT_STATE = 43
    BNCS_STATE = 44
    SIGNAL_STATE = 45
    BNC1_ON = 46
    BNC1_OFF = 47
    BNC1_PULSES = 48
    BNC1_TAIL = 49
    BNC2_ON = 50
    BNC2_OFF = 51
    BNC2_PULSES = 52
    BNC2_TAIL = 53
    SIGNAL_A_ON = 54
    SIGNAL_A_OFF = 55
    SIGNAL_A_PULSES = 56
    SIGNAL_A_TAIL = 57
    SIGNAL_B_ON = 58
    SIGNAL_B_OFF = 59
    SIGNAL_B_PULSES = 60
    SIGNAL_B_TAIL = 61
    EVENT_ENABLE = 62


class LaserDriverController(Device):
    """
    LaserDriverController class for controlling the device.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect and load already happened in the base class
        # verify that WHO_AM_I matches the expected value
        if self.WHO_AM_I != 1298:
            self.disconnect()
            raise HarpException(f"WHO_AM_I mismatch: expected {1298}, got {self.WHO_AM_I}")

    def read_spad_switch(self) -> int | None:
        """
        Reads the contents of the SpadSwitch register.

        Returns
        -------
        int | None
            Value read from the SpadSwitch register.
        """
        address = LaserDriverControllerRegisters.SPAD_SWITCH
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.SPAD_SWITCH", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_spad_switch(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SpadSwitch register.

        Parameters
        ----------
        value : int
            Value to write to the SpadSwitch register.
        """
        address = LaserDriverControllerRegisters.SPAD_SWITCH
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.SPAD_SWITCH", reply)

        return reply

    def read_laser_state(self) -> int | None:
        """
        Reads the contents of the LaserState register.

        Returns
        -------
        int | None
            Value read from the LaserState register.
        """
        address = LaserDriverControllerRegisters.LASER_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.LASER_STATE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_laser_state(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the LaserState register.

        Parameters
        ----------
        value : int
            Value to write to the LaserState register.
        """
        address = LaserDriverControllerRegisters.LASER_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.LASER_STATE", reply)

        return reply

    def read_laser_frequency_select(self) -> FrequencySelect | None:
        """
        Reads the contents of the LaserFrequencySelect register.

        Returns
        -------
        FrequencySelect | None
            Value read from the LaserFrequencySelect register.
        """
        address = LaserDriverControllerRegisters.LASER_FREQUENCY_SELECT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.LASER_FREQUENCY_SELECT", reply)

        if reply is not None:
            return FrequencySelect(reply.payload)
        return None

    def write_laser_frequency_select(self, value: FrequencySelect) -> HarpMessage | None:
        """
        Writes a value to the LaserFrequencySelect register.

        Parameters
        ----------
        value : FrequencySelect
            Value to write to the LaserFrequencySelect register.
        """
        address = LaserDriverControllerRegisters.LASER_FREQUENCY_SELECT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.LASER_FREQUENCY_SELECT", reply)

        return reply

    def read_laser_intensity(self) -> int | None:
        """
        Reads the contents of the LaserIntensity register.

        Returns
        -------
        int | None
            Value read from the LaserIntensity register.
        """
        address = LaserDriverControllerRegisters.LASER_INTENSITY
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.LASER_INTENSITY", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_laser_intensity(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the LaserIntensity register.

        Parameters
        ----------
        value : int
            Value to write to the LaserIntensity register.
        """
        address = LaserDriverControllerRegisters.LASER_INTENSITY
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.LASER_INTENSITY", reply)

        return reply

    def read_output_set(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputSet register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputSet register.
        """
        address = LaserDriverControllerRegisters.OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.OUTPUT_SET", reply)

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
        address = LaserDriverControllerRegisters.OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.OUTPUT_SET", reply)

        return reply

    def read_output_clear(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputClear register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputClear register.
        """
        address = LaserDriverControllerRegisters.OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.OUTPUT_CLEAR", reply)

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
        address = LaserDriverControllerRegisters.OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.OUTPUT_CLEAR", reply)

        return reply

    def read_output_toggle(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputToggle register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputToggle register.
        """
        address = LaserDriverControllerRegisters.OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.OUTPUT_TOGGLE", reply)

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
        address = LaserDriverControllerRegisters.OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.OUTPUT_TOGGLE", reply)

        return reply

    def read_output_state(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputState register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputState register.
        """
        address = LaserDriverControllerRegisters.OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.OUTPUT_STATE", reply)

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
        address = LaserDriverControllerRegisters.OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.OUTPUT_STATE", reply)

        return reply

    def read_bncs_state(self) -> Bncs | None:
        """
        Reads the contents of the BncsState register.

        Returns
        -------
        Bncs | None
            Value read from the BncsState register.
        """
        address = LaserDriverControllerRegisters.BNCS_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.BNCS_STATE", reply)

        if reply is not None:
            return Bncs(reply.payload)
        return None

    def write_bncs_state(self, value: Bncs) -> HarpMessage | None:
        """
        Writes a value to the BncsState register.

        Parameters
        ----------
        value : Bncs
            Value to write to the BncsState register.
        """
        address = LaserDriverControllerRegisters.BNCS_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.BNCS_STATE", reply)

        return reply

    def read_signal_state(self) -> Signals | None:
        """
        Reads the contents of the SignalState register.

        Returns
        -------
        Signals | None
            Value read from the SignalState register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.SIGNAL_STATE", reply)

        if reply is not None:
            return Signals(reply.payload)
        return None

    def write_signal_state(self, value: Signals) -> HarpMessage | None:
        """
        Writes a value to the SignalState register.

        Parameters
        ----------
        value : Signals
            Value to write to the SignalState register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.SIGNAL_STATE", reply)

        return reply

    def read_bnc1_on(self) -> int | None:
        """
        Reads the contents of the Bnc1On register.

        Returns
        -------
        int | None
            Value read from the Bnc1On register.
        """
        address = LaserDriverControllerRegisters.BNC1_ON
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.BNC1_ON", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_bnc1_on(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Bnc1On register.

        Parameters
        ----------
        value : int
            Value to write to the Bnc1On register.
        """
        address = LaserDriverControllerRegisters.BNC1_ON
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.BNC1_ON", reply)

        return reply

    def read_bnc1_off(self) -> int | None:
        """
        Reads the contents of the Bnc1Off register.

        Returns
        -------
        int | None
            Value read from the Bnc1Off register.
        """
        address = LaserDriverControllerRegisters.BNC1_OFF
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.BNC1_OFF", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_bnc1_off(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Bnc1Off register.

        Parameters
        ----------
        value : int
            Value to write to the Bnc1Off register.
        """
        address = LaserDriverControllerRegisters.BNC1_OFF
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.BNC1_OFF", reply)

        return reply

    def read_bnc1_pulses(self) -> int | None:
        """
        Reads the contents of the Bnc1Pulses register.

        Returns
        -------
        int | None
            Value read from the Bnc1Pulses register.
        """
        address = LaserDriverControllerRegisters.BNC1_PULSES
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.BNC1_PULSES", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_bnc1_pulses(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Bnc1Pulses register.

        Parameters
        ----------
        value : int
            Value to write to the Bnc1Pulses register.
        """
        address = LaserDriverControllerRegisters.BNC1_PULSES
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.BNC1_PULSES", reply)

        return reply

    def read_bnc1_tail(self) -> int | None:
        """
        Reads the contents of the Bnc1Tail register.

        Returns
        -------
        int | None
            Value read from the Bnc1Tail register.
        """
        address = LaserDriverControllerRegisters.BNC1_TAIL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.BNC1_TAIL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_bnc1_tail(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Bnc1Tail register.

        Parameters
        ----------
        value : int
            Value to write to the Bnc1Tail register.
        """
        address = LaserDriverControllerRegisters.BNC1_TAIL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.BNC1_TAIL", reply)

        return reply

    def read_bnc2_on(self) -> int | None:
        """
        Reads the contents of the Bnc2On register.

        Returns
        -------
        int | None
            Value read from the Bnc2On register.
        """
        address = LaserDriverControllerRegisters.BNC2_ON
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.BNC2_ON", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_bnc2_on(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Bnc2On register.

        Parameters
        ----------
        value : int
            Value to write to the Bnc2On register.
        """
        address = LaserDriverControllerRegisters.BNC2_ON
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.BNC2_ON", reply)

        return reply

    def read_bnc2_off(self) -> int | None:
        """
        Reads the contents of the Bnc2Off register.

        Returns
        -------
        int | None
            Value read from the Bnc2Off register.
        """
        address = LaserDriverControllerRegisters.BNC2_OFF
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.BNC2_OFF", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_bnc2_off(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Bnc2Off register.

        Parameters
        ----------
        value : int
            Value to write to the Bnc2Off register.
        """
        address = LaserDriverControllerRegisters.BNC2_OFF
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.BNC2_OFF", reply)

        return reply

    def read_bnc2_pulses(self) -> int | None:
        """
        Reads the contents of the Bnc2Pulses register.

        Returns
        -------
        int | None
            Value read from the Bnc2Pulses register.
        """
        address = LaserDriverControllerRegisters.BNC2_PULSES
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.BNC2_PULSES", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_bnc2_pulses(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Bnc2Pulses register.

        Parameters
        ----------
        value : int
            Value to write to the Bnc2Pulses register.
        """
        address = LaserDriverControllerRegisters.BNC2_PULSES
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.BNC2_PULSES", reply)

        return reply

    def read_bnc2_tail(self) -> int | None:
        """
        Reads the contents of the Bnc2Tail register.

        Returns
        -------
        int | None
            Value read from the Bnc2Tail register.
        """
        address = LaserDriverControllerRegisters.BNC2_TAIL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.BNC2_TAIL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_bnc2_tail(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Bnc2Tail register.

        Parameters
        ----------
        value : int
            Value to write to the Bnc2Tail register.
        """
        address = LaserDriverControllerRegisters.BNC2_TAIL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.BNC2_TAIL", reply)

        return reply

    def read_signal_a_on(self) -> int | None:
        """
        Reads the contents of the SignalAOn register.

        Returns
        -------
        int | None
            Value read from the SignalAOn register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_A_ON
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.SIGNAL_A_ON", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_signal_a_on(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SignalAOn register.

        Parameters
        ----------
        value : int
            Value to write to the SignalAOn register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_A_ON
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.SIGNAL_A_ON", reply)

        return reply

    def read_signal_a_off(self) -> int | None:
        """
        Reads the contents of the SignalAOff register.

        Returns
        -------
        int | None
            Value read from the SignalAOff register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_A_OFF
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.SIGNAL_A_OFF", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_signal_a_off(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SignalAOff register.

        Parameters
        ----------
        value : int
            Value to write to the SignalAOff register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_A_OFF
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.SIGNAL_A_OFF", reply)

        return reply

    def read_signal_a_pulses(self) -> int | None:
        """
        Reads the contents of the SignalAPulses register.

        Returns
        -------
        int | None
            Value read from the SignalAPulses register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_A_PULSES
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.SIGNAL_A_PULSES", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_signal_a_pulses(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SignalAPulses register.

        Parameters
        ----------
        value : int
            Value to write to the SignalAPulses register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_A_PULSES
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.SIGNAL_A_PULSES", reply)

        return reply

    def read_signal_a_tail(self) -> int | None:
        """
        Reads the contents of the SignalATail register.

        Returns
        -------
        int | None
            Value read from the SignalATail register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_A_TAIL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.SIGNAL_A_TAIL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_signal_a_tail(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SignalATail register.

        Parameters
        ----------
        value : int
            Value to write to the SignalATail register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_A_TAIL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.SIGNAL_A_TAIL", reply)

        return reply

    def read_signal_b_on(self) -> int | None:
        """
        Reads the contents of the SignalBOn register.

        Returns
        -------
        int | None
            Value read from the SignalBOn register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_B_ON
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.SIGNAL_B_ON", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_signal_b_on(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SignalBOn register.

        Parameters
        ----------
        value : int
            Value to write to the SignalBOn register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_B_ON
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.SIGNAL_B_ON", reply)

        return reply

    def read_signal_b_off(self) -> int | None:
        """
        Reads the contents of the SignalBOff register.

        Returns
        -------
        int | None
            Value read from the SignalBOff register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_B_OFF
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.SIGNAL_B_OFF", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_signal_b_off(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SignalBOff register.

        Parameters
        ----------
        value : int
            Value to write to the SignalBOff register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_B_OFF
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.SIGNAL_B_OFF", reply)

        return reply

    def read_signal_b_pulses(self) -> int | None:
        """
        Reads the contents of the SignalBPulses register.

        Returns
        -------
        int | None
            Value read from the SignalBPulses register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_B_PULSES
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.SIGNAL_B_PULSES", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_signal_b_pulses(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SignalBPulses register.

        Parameters
        ----------
        value : int
            Value to write to the SignalBPulses register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_B_PULSES
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.SIGNAL_B_PULSES", reply)

        return reply

    def read_signal_b_tail(self) -> int | None:
        """
        Reads the contents of the SignalBTail register.

        Returns
        -------
        int | None
            Value read from the SignalBTail register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_B_TAIL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.SIGNAL_B_TAIL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_signal_b_tail(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SignalBTail register.

        Parameters
        ----------
        value : int
            Value to write to the SignalBTail register.
        """
        address = LaserDriverControllerRegisters.SIGNAL_B_TAIL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.SIGNAL_B_TAIL", reply)

        return reply

    def read_event_enable(self) -> LaserDriverControllerEvents | None:
        """
        Reads the contents of the EventEnable register.

        Returns
        -------
        LaserDriverControllerEvents | None
            Value read from the EventEnable register.
        """
        address = LaserDriverControllerRegisters.EVENT_ENABLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LaserDriverControllerRegisters.EVENT_ENABLE", reply)

        if reply is not None:
            return LaserDriverControllerEvents(reply.payload)
        return None

    def write_event_enable(self, value: LaserDriverControllerEvents) -> HarpMessage | None:
        """
        Writes a value to the EventEnable register.

        Parameters
        ----------
        value : LaserDriverControllerEvents
            Value to write to the EventEnable register.
        """
        address = LaserDriverControllerRegisters.EVENT_ENABLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LaserDriverControllerRegisters.EVENT_ENABLE", reply)

        return reply

