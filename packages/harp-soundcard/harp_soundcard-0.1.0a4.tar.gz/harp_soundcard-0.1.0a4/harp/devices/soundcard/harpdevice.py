from dataclasses import dataclass
from enum import IntEnum, IntFlag

from harp.protocol import MessageType, PayloadType
from harp.protocol.exceptions import HarpException, HarpReadException, HarpWriteException
from harp.protocol.messages import HarpMessage
from harp.serial import Device


@dataclass
class AnalogDataPayload:
        # The sampled analog input value on ADC0.
    Adc0: int
        # The sampled analog input value on ADC1.
    Adc1: int
        # The amplitude of the left channel controlled by ADC0.
    AttenuationLeft: int
        # The amplitude of the right channel controlled by ADC0.
    AttenuationRight: int
        # The output frequency controlled by ADC1.
    Frequency: int


class DigitalInputs(IntFlag):
    """
    Specifies the state of the digital input lines.

    Attributes
    ----------
    DI0 : int
        _No description currently available_
    """

    NONE = 0x0
    DI0 = 0x1


class DigitalOutputs(IntFlag):
    """
    Specifies the state of the digital output lines.

    Attributes
    ----------
    DO0 : int
        _No description currently available_
    DO1 : int
        _No description currently available_
    DO2 : int
        _No description currently available_
    """

    NONE = 0x0
    DO0 = 0x1
    DO1 = 0x2
    DO2 = 0x3


class SoundCardEvents(IntFlag):
    """
    Specifies the active events in the SoundCard.

    Attributes
    ----------
    PLAY_SOUND_OR_FREQUENCY : int
        _No description currently available_
    STOP : int
        _No description currently available_
    DIGITAL_INPUTS : int
        _No description currently available_
    ADC_VALUES : int
        _No description currently available_
    """

    NONE = 0x0
    PLAY_SOUND_OR_FREQUENCY = 0x1
    STOP = 0x2
    DIGITAL_INPUTS = 0x4
    ADC_VALUES = 0x8


class DigitalInputConfiguration(IntEnum):
    """
    Specifies the operation mode of the digital input.

    Attributes
    ----------
    DIGITAL : int
        Used as a pure digital input.
    START_AND_STOP_SOUND : int
        Starts sound when rising edge and stop when falling edge.
    START_SOUND : int
        Starts sound when rising edge.
    STOP : int
        Stops sound or frequency when rising edge.
    START_AND_STOP_FREQUENCY : int
        Starts frequency when rising edge and stop when falling edge.
    START_FREQUENCY : int
        Starts frequency when rising edge.
    """

    DIGITAL = 0
    START_AND_STOP_SOUND = 1
    START_SOUND = 2
    STOP = 3
    START_AND_STOP_FREQUENCY = 4
    START_FREQUENCY = 5


class DigitalOutputConfiguration(IntEnum):
    """
    Specifies the operation mode of the digital output.

    Attributes
    ----------
    DIGITAL : int
        Used as a pure digital output.
    PULSE : int
        The digital output will be high during a period specified by register DOxPulse.
    HIGH_WHEN_SOUND : int
        High when the sound is being played.
    PULSE_1MS_WHEN_START : int
        High when sound starts during 1 ms.
    PULSE_10MS_WHEN_START : int
        High when sound starts during 10 ms.
    PULSE_100MS_WHEN_START : int
        High when sound starts during 100 ms.
    PULSE_1MS_WHEN_STOP : int
        High when sound stops during 1 ms.
    PULSE_10MS_WHEN_STOP : int
        High when sound stops during 10 ms.
    PULSE_100MS_WHEN_STOP : int
        High when sound starts during 100 ms.
    """

    DIGITAL = 0
    PULSE = 1
    HIGH_WHEN_SOUND = 2
    PULSE_1MS_WHEN_START = 3
    PULSE_10MS_WHEN_START = 4
    PULSE_100MS_WHEN_START = 5
    PULSE_1MS_WHEN_STOP = 6
    PULSE_10MS_WHEN_STOP = 7
    PULSE_100MS_WHEN_STOP = 8


class ControllerCommand(IntEnum):
    """
    Specifies commands to send to the PIC32 micro-controller

    Attributes
    ----------
    DISABLE_BOOTLOADER : int
        _No description currently available_
    ENABLE_BOOTLOADER : int
        _No description currently available_
    DELETE_ALL_SOUNDS : int
        _No description currently available_
    """

    DISABLE_BOOTLOADER = 0
    ENABLE_BOOTLOADER = 1
    DELETE_ALL_SOUNDS = 255


class AdcConfiguration(IntEnum):
    """
    Specifies the operation mode of the analog inputs.

    Attributes
    ----------
    NOT_USED : int
        _No description currently available_
    ADC_ADC : int
        _No description currently available_
    AMPLITUDE_BOTH_ADC : int
        _No description currently available_
    AMPLITUDE_LEFT_ADC : int
        _No description currently available_
    AMPLITUDE_RIGHT_ADC : int
        _No description currently available_
    AMPLITUDE_LEFT_AMPLITUDE_RIGHT : int
        _No description currently available_
    AMPLITUDE_BOTH_FREQUENCY : int
        _No description currently available_
    """

    NOT_USED = 0
    ADC_ADC = 1
    AMPLITUDE_BOTH_ADC = 2
    AMPLITUDE_LEFT_ADC = 3
    AMPLITUDE_RIGHT_ADC = 4
    AMPLITUDE_LEFT_AMPLITUDE_RIGHT = 5
    AMPLITUDE_BOTH_FREQUENCY = 6


class SoundCardRegisters(IntEnum):
    """Enum for all available registers in the SoundCard device.

    Attributes
    ----------
    PLAY_SOUND_OR_FREQUENCY : int
        Starts the sound index (if less than 32) or frequency (if greater or equal than 32)
    STOP : int
        Any value will stop the current sound
    ATTENUATION_LEFT : int
        Configure left channel's attenuation (1 LSB is 0.1dB)
    ATTENUATION_RIGHT : int
        Configure right channel's attenuation (1 LSB is 0.1dB)
    ATTENUATION_BOTH : int
        Configures both attenuation on right and left channels [Att R] [Att L]
    ATTENUATION_AND_PLAY_SOUND_OR_FREQ : int
        Configures attenuation and plays sound index [Att R] [Att L] [Index]
    INPUT_STATE : int
        State of the digital inputs
    CONFIGURE_DI0 : int
        Configuration of the digital input 0 (DI0)
    CONFIGURE_DI1 : int
        Configuration of the digital input 1 (DI1)
    CONFIGURE_DI2 : int
        Configuration of the digital input 2 (DI2)
    SOUND_INDEX_DI0 : int
        Specifies the sound index to be played when triggering DI0
    SOUND_INDEX_DI1 : int
        Specifies the sound index to be played when triggering DI1
    SOUND_INDEX_DI2 : int
        Specifies the sound index to be played when triggering DI2
    FREQUENCY_DI0 : int
        Specifies the sound frequency to be played when triggering DI0
    FREQUENCY_DI1 : int
        Specifies the sound frequency to be played when triggering DI1
    FREQUENCY_DI2 : int
        Specifies the sound frequency to be played when triggering DI2
    ATTENUATION_LEFT_DI0 : int
        Left channel's attenuation (1 LSB is 0.5dB) when triggering DI0
    ATTENUATION_LEFT_DI1 : int
        Left channel's attenuation (1 LSB is 0.5dB) when triggering DI1
    ATTENUATION_LEFT_DI2 : int
        Left channel's attenuation (1 LSB is 0.5dB) when triggering DI2
    ATTENUATION_RIGHT_DI0 : int
        Right channel's attenuation (1 LSB is 0.5dB) when triggering DI0
    ATTENUATION_RIGHT_DI1 : int
        Right channel's attenuation (1 LSB is 0.5dB) when triggering DI1
    ATTENUATION_RIGHT_DI2 : int
        Right channel's attenuation (1 LSB is 0.5dB) when triggering DI2
    ATTENUATION_AND_SOUND_INDEX_DI0 : int
        Sound index and attenuation to be played when triggering DI0 [Att R] [Att L] [Index]
    ATTENUATION_AND_SOUND_INDEX_DI1 : int
        Sound index and attenuation to be played when triggering DI1 [Att R] [Att L] [Index]
    ATTENUATION_AND_SOUND_INDEX_DI2 : int
        Sound index and attenuation to be played when triggering DI2 [Att R] [Att L] [Index]
    ATTENUATION_AND_FREQUENCY_DI0 : int
        Sound index and attenuation to be played when triggering DI0 [Att BOTH] [Frequency]
    ATTENUATION_AND_FREQUENCY_DI1 : int
        Sound index and attenuation to be played when triggering DI1 [Att BOTH] [Frequency]
    ATTENUATION_AND_FREQUENCY_DI2 : int
        Sound index and attenuation to be played when triggering DI2 [Att BOTH] [Frequency]
    CONFIGURE_DO0 : int
        Configuration of the digital output 0 (DO0)
    CONFIGURE_DO1 : int
        Configuration of the digital output 1 (DO1)
    CONFIGURE_DO2 : int
        Configuration of the digital output 2 (DO2
    PULSE_DO0 : int
        Pulse for the digital output 0 (DO0)
    PULSE_DO1 : int
        Pulse for the digital output 1 (DO1)
    PULSE_DO2 : int
        Pulse for the digital output 2 (DO2)
    OUTPUT_SET : int
        Set the specified digital output lines
    OUTPUT_CLEAR : int
        Clear the specified digital output lines
    OUTPUT_TOGGLE : int
        Toggle the specified digital output lines
    OUTPUT_STATE : int
        Write the state of all digital output lines
    CONFIGURE_ADC : int
        Configuration of Analog Inputs
    ANALOG_DATA : int
        Contains sampled analog input data or dynamic sound parameters controlled by the ADC channels. Values are zero if not used.
    COMMANDS : int
        Send commands to PIC32 micro-controller
    ENABLE_EVENTS : int
        Specifies the active events in the SoundCard device
    """

    PLAY_SOUND_OR_FREQUENCY = 32
    STOP = 33
    ATTENUATION_LEFT = 34
    ATTENUATION_RIGHT = 35
    ATTENUATION_BOTH = 36
    ATTENUATION_AND_PLAY_SOUND_OR_FREQ = 37
    INPUT_STATE = 40
    CONFIGURE_DI0 = 41
    CONFIGURE_DI1 = 42
    CONFIGURE_DI2 = 43
    SOUND_INDEX_DI0 = 44
    SOUND_INDEX_DI1 = 45
    SOUND_INDEX_DI2 = 46
    FREQUENCY_DI0 = 47
    FREQUENCY_DI1 = 48
    FREQUENCY_DI2 = 49
    ATTENUATION_LEFT_DI0 = 50
    ATTENUATION_LEFT_DI1 = 51
    ATTENUATION_LEFT_DI2 = 52
    ATTENUATION_RIGHT_DI0 = 53
    ATTENUATION_RIGHT_DI1 = 54
    ATTENUATION_RIGHT_DI2 = 55
    ATTENUATION_AND_SOUND_INDEX_DI0 = 56
    ATTENUATION_AND_SOUND_INDEX_DI1 = 57
    ATTENUATION_AND_SOUND_INDEX_DI2 = 58
    ATTENUATION_AND_FREQUENCY_DI0 = 59
    ATTENUATION_AND_FREQUENCY_DI1 = 60
    ATTENUATION_AND_FREQUENCY_DI2 = 61
    CONFIGURE_DO0 = 65
    CONFIGURE_DO1 = 66
    CONFIGURE_DO2 = 67
    PULSE_DO0 = 68
    PULSE_DO1 = 69
    PULSE_DO2 = 70
    OUTPUT_SET = 74
    OUTPUT_CLEAR = 75
    OUTPUT_TOGGLE = 76
    OUTPUT_STATE = 77
    CONFIGURE_ADC = 80
    ANALOG_DATA = 81
    COMMANDS = 82
    ENABLE_EVENTS = 86


class SoundCard(Device):
    """
    SoundCard class for controlling the device.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect and load already happened in the base class
        # verify that WHO_AM_I matches the expected value
        if self.WHO_AM_I != 1280:
            self.disconnect()
            raise HarpException(f"WHO_AM_I mismatch: expected {1280}, got {self.WHO_AM_I}")

    def read_play_sound_or_frequency(self) -> int | None:
        """
        Reads the contents of the PlaySoundOrFrequency register.

        Returns
        -------
        int | None
            Value read from the PlaySoundOrFrequency register.
        """
        address = SoundCardRegisters.PLAY_SOUND_OR_FREQUENCY
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.PLAY_SOUND_OR_FREQUENCY", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_play_sound_or_frequency(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PlaySoundOrFrequency register.

        Parameters
        ----------
        value : int
            Value to write to the PlaySoundOrFrequency register.
        """
        address = SoundCardRegisters.PLAY_SOUND_OR_FREQUENCY
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.PLAY_SOUND_OR_FREQUENCY", reply)

        return reply

    def read_stop(self) -> int | None:
        """
        Reads the contents of the Stop register.

        Returns
        -------
        int | None
            Value read from the Stop register.
        """
        address = SoundCardRegisters.STOP
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.STOP", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_stop(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Stop register.

        Parameters
        ----------
        value : int
            Value to write to the Stop register.
        """
        address = SoundCardRegisters.STOP
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.STOP", reply)

        return reply

    def read_attenuation_left(self) -> int | None:
        """
        Reads the contents of the AttenuationLeft register.

        Returns
        -------
        int | None
            Value read from the AttenuationLeft register.
        """
        address = SoundCardRegisters.ATTENUATION_LEFT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_LEFT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_left(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the AttenuationLeft register.

        Parameters
        ----------
        value : int
            Value to write to the AttenuationLeft register.
        """
        address = SoundCardRegisters.ATTENUATION_LEFT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_LEFT", reply)

        return reply

    def read_attenuation_right(self) -> int | None:
        """
        Reads the contents of the AttenuationRight register.

        Returns
        -------
        int | None
            Value read from the AttenuationRight register.
        """
        address = SoundCardRegisters.ATTENUATION_RIGHT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_RIGHT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_right(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the AttenuationRight register.

        Parameters
        ----------
        value : int
            Value to write to the AttenuationRight register.
        """
        address = SoundCardRegisters.ATTENUATION_RIGHT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_RIGHT", reply)

        return reply

    def read_attenuation_both(self) -> list[int] | None:
        """
        Reads the contents of the AttenuationBoth register.

        Returns
        -------
        list[int] | None
            Value read from the AttenuationBoth register.
        """
        address = SoundCardRegisters.ATTENUATION_BOTH
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_BOTH", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_both(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the AttenuationBoth register.

        Parameters
        ----------
        value : list[int]
            Value to write to the AttenuationBoth register.
        """
        address = SoundCardRegisters.ATTENUATION_BOTH
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_BOTH", reply)

        return reply

    def read_attenuation_and_play_sound_or_freq(self) -> list[int] | None:
        """
        Reads the contents of the AttenuationAndPlaySoundOrFreq register.

        Returns
        -------
        list[int] | None
            Value read from the AttenuationAndPlaySoundOrFreq register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_PLAY_SOUND_OR_FREQ
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_AND_PLAY_SOUND_OR_FREQ", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_and_play_sound_or_freq(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the AttenuationAndPlaySoundOrFreq register.

        Parameters
        ----------
        value : list[int]
            Value to write to the AttenuationAndPlaySoundOrFreq register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_PLAY_SOUND_OR_FREQ
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_AND_PLAY_SOUND_OR_FREQ", reply)

        return reply

    def read_input_state(self) -> DigitalInputs | None:
        """
        Reads the contents of the InputState register.

        Returns
        -------
        DigitalInputs | None
            Value read from the InputState register.
        """
        address = SoundCardRegisters.INPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.INPUT_STATE", reply)

        if reply is not None:
            return DigitalInputs(reply.payload)
        return None

    def read_configure_di0(self) -> DigitalInputConfiguration | None:
        """
        Reads the contents of the ConfigureDI0 register.

        Returns
        -------
        DigitalInputConfiguration | None
            Value read from the ConfigureDI0 register.
        """
        address = SoundCardRegisters.CONFIGURE_DI0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.CONFIGURE_DI0", reply)

        if reply is not None:
            return DigitalInputConfiguration(reply.payload)
        return None

    def write_configure_di0(self, value: DigitalInputConfiguration) -> HarpMessage | None:
        """
        Writes a value to the ConfigureDI0 register.

        Parameters
        ----------
        value : DigitalInputConfiguration
            Value to write to the ConfigureDI0 register.
        """
        address = SoundCardRegisters.CONFIGURE_DI0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.CONFIGURE_DI0", reply)

        return reply

    def read_configure_di1(self) -> DigitalInputConfiguration | None:
        """
        Reads the contents of the ConfigureDI1 register.

        Returns
        -------
        DigitalInputConfiguration | None
            Value read from the ConfigureDI1 register.
        """
        address = SoundCardRegisters.CONFIGURE_DI1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.CONFIGURE_DI1", reply)

        if reply is not None:
            return DigitalInputConfiguration(reply.payload)
        return None

    def write_configure_di1(self, value: DigitalInputConfiguration) -> HarpMessage | None:
        """
        Writes a value to the ConfigureDI1 register.

        Parameters
        ----------
        value : DigitalInputConfiguration
            Value to write to the ConfigureDI1 register.
        """
        address = SoundCardRegisters.CONFIGURE_DI1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.CONFIGURE_DI1", reply)

        return reply

    def read_configure_di2(self) -> DigitalInputConfiguration | None:
        """
        Reads the contents of the ConfigureDI2 register.

        Returns
        -------
        DigitalInputConfiguration | None
            Value read from the ConfigureDI2 register.
        """
        address = SoundCardRegisters.CONFIGURE_DI2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.CONFIGURE_DI2", reply)

        if reply is not None:
            return DigitalInputConfiguration(reply.payload)
        return None

    def write_configure_di2(self, value: DigitalInputConfiguration) -> HarpMessage | None:
        """
        Writes a value to the ConfigureDI2 register.

        Parameters
        ----------
        value : DigitalInputConfiguration
            Value to write to the ConfigureDI2 register.
        """
        address = SoundCardRegisters.CONFIGURE_DI2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.CONFIGURE_DI2", reply)

        return reply

    def read_sound_index_di0(self) -> int | None:
        """
        Reads the contents of the SoundIndexDI0 register.

        Returns
        -------
        int | None
            Value read from the SoundIndexDI0 register.
        """
        address = SoundCardRegisters.SOUND_INDEX_DI0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.SOUND_INDEX_DI0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_sound_index_di0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SoundIndexDI0 register.

        Parameters
        ----------
        value : int
            Value to write to the SoundIndexDI0 register.
        """
        address = SoundCardRegisters.SOUND_INDEX_DI0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.SOUND_INDEX_DI0", reply)

        return reply

    def read_sound_index_di1(self) -> int | None:
        """
        Reads the contents of the SoundIndexDI1 register.

        Returns
        -------
        int | None
            Value read from the SoundIndexDI1 register.
        """
        address = SoundCardRegisters.SOUND_INDEX_DI1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.SOUND_INDEX_DI1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_sound_index_di1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SoundIndexDI1 register.

        Parameters
        ----------
        value : int
            Value to write to the SoundIndexDI1 register.
        """
        address = SoundCardRegisters.SOUND_INDEX_DI1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.SOUND_INDEX_DI1", reply)

        return reply

    def read_sound_index_di2(self) -> int | None:
        """
        Reads the contents of the SoundIndexDI2 register.

        Returns
        -------
        int | None
            Value read from the SoundIndexDI2 register.
        """
        address = SoundCardRegisters.SOUND_INDEX_DI2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.SOUND_INDEX_DI2", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_sound_index_di2(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the SoundIndexDI2 register.

        Parameters
        ----------
        value : int
            Value to write to the SoundIndexDI2 register.
        """
        address = SoundCardRegisters.SOUND_INDEX_DI2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.SOUND_INDEX_DI2", reply)

        return reply

    def read_frequency_di0(self) -> int | None:
        """
        Reads the contents of the FrequencyDI0 register.

        Returns
        -------
        int | None
            Value read from the FrequencyDI0 register.
        """
        address = SoundCardRegisters.FREQUENCY_DI0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.FREQUENCY_DI0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_frequency_di0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the FrequencyDI0 register.

        Parameters
        ----------
        value : int
            Value to write to the FrequencyDI0 register.
        """
        address = SoundCardRegisters.FREQUENCY_DI0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.FREQUENCY_DI0", reply)

        return reply

    def read_frequency_di1(self) -> int | None:
        """
        Reads the contents of the FrequencyDI1 register.

        Returns
        -------
        int | None
            Value read from the FrequencyDI1 register.
        """
        address = SoundCardRegisters.FREQUENCY_DI1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.FREQUENCY_DI1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_frequency_di1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the FrequencyDI1 register.

        Parameters
        ----------
        value : int
            Value to write to the FrequencyDI1 register.
        """
        address = SoundCardRegisters.FREQUENCY_DI1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.FREQUENCY_DI1", reply)

        return reply

    def read_frequency_di2(self) -> int | None:
        """
        Reads the contents of the FrequencyDI2 register.

        Returns
        -------
        int | None
            Value read from the FrequencyDI2 register.
        """
        address = SoundCardRegisters.FREQUENCY_DI2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.FREQUENCY_DI2", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_frequency_di2(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the FrequencyDI2 register.

        Parameters
        ----------
        value : int
            Value to write to the FrequencyDI2 register.
        """
        address = SoundCardRegisters.FREQUENCY_DI2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.FREQUENCY_DI2", reply)

        return reply

    def read_attenuation_left_di0(self) -> int | None:
        """
        Reads the contents of the AttenuationLeftDI0 register.

        Returns
        -------
        int | None
            Value read from the AttenuationLeftDI0 register.
        """
        address = SoundCardRegisters.ATTENUATION_LEFT_DI0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_LEFT_DI0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_left_di0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the AttenuationLeftDI0 register.

        Parameters
        ----------
        value : int
            Value to write to the AttenuationLeftDI0 register.
        """
        address = SoundCardRegisters.ATTENUATION_LEFT_DI0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_LEFT_DI0", reply)

        return reply

    def read_attenuation_left_di1(self) -> int | None:
        """
        Reads the contents of the AttenuationLeftDI1 register.

        Returns
        -------
        int | None
            Value read from the AttenuationLeftDI1 register.
        """
        address = SoundCardRegisters.ATTENUATION_LEFT_DI1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_LEFT_DI1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_left_di1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the AttenuationLeftDI1 register.

        Parameters
        ----------
        value : int
            Value to write to the AttenuationLeftDI1 register.
        """
        address = SoundCardRegisters.ATTENUATION_LEFT_DI1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_LEFT_DI1", reply)

        return reply

    def read_attenuation_left_di2(self) -> int | None:
        """
        Reads the contents of the AttenuationLeftDI2 register.

        Returns
        -------
        int | None
            Value read from the AttenuationLeftDI2 register.
        """
        address = SoundCardRegisters.ATTENUATION_LEFT_DI2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_LEFT_DI2", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_left_di2(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the AttenuationLeftDI2 register.

        Parameters
        ----------
        value : int
            Value to write to the AttenuationLeftDI2 register.
        """
        address = SoundCardRegisters.ATTENUATION_LEFT_DI2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_LEFT_DI2", reply)

        return reply

    def read_attenuation_right_di0(self) -> int | None:
        """
        Reads the contents of the AttenuationRightDI0 register.

        Returns
        -------
        int | None
            Value read from the AttenuationRightDI0 register.
        """
        address = SoundCardRegisters.ATTENUATION_RIGHT_DI0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_RIGHT_DI0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_right_di0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the AttenuationRightDI0 register.

        Parameters
        ----------
        value : int
            Value to write to the AttenuationRightDI0 register.
        """
        address = SoundCardRegisters.ATTENUATION_RIGHT_DI0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_RIGHT_DI0", reply)

        return reply

    def read_attenuation_right_di1(self) -> int | None:
        """
        Reads the contents of the AttenuationRightDI1 register.

        Returns
        -------
        int | None
            Value read from the AttenuationRightDI1 register.
        """
        address = SoundCardRegisters.ATTENUATION_RIGHT_DI1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_RIGHT_DI1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_right_di1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the AttenuationRightDI1 register.

        Parameters
        ----------
        value : int
            Value to write to the AttenuationRightDI1 register.
        """
        address = SoundCardRegisters.ATTENUATION_RIGHT_DI1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_RIGHT_DI1", reply)

        return reply

    def read_attenuation_right_di2(self) -> int | None:
        """
        Reads the contents of the AttenuationRightDI2 register.

        Returns
        -------
        int | None
            Value read from the AttenuationRightDI2 register.
        """
        address = SoundCardRegisters.ATTENUATION_RIGHT_DI2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_RIGHT_DI2", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_right_di2(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the AttenuationRightDI2 register.

        Parameters
        ----------
        value : int
            Value to write to the AttenuationRightDI2 register.
        """
        address = SoundCardRegisters.ATTENUATION_RIGHT_DI2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_RIGHT_DI2", reply)

        return reply

    def read_attenuation_and_sound_index_di0(self) -> list[int] | None:
        """
        Reads the contents of the AttenuationAndSoundIndexDI0 register.

        Returns
        -------
        list[int] | None
            Value read from the AttenuationAndSoundIndexDI0 register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_SOUND_INDEX_DI0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_AND_SOUND_INDEX_DI0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_and_sound_index_di0(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the AttenuationAndSoundIndexDI0 register.

        Parameters
        ----------
        value : list[int]
            Value to write to the AttenuationAndSoundIndexDI0 register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_SOUND_INDEX_DI0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_AND_SOUND_INDEX_DI0", reply)

        return reply

    def read_attenuation_and_sound_index_di1(self) -> list[int] | None:
        """
        Reads the contents of the AttenuationAndSoundIndexDI1 register.

        Returns
        -------
        list[int] | None
            Value read from the AttenuationAndSoundIndexDI1 register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_SOUND_INDEX_DI1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_AND_SOUND_INDEX_DI1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_and_sound_index_di1(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the AttenuationAndSoundIndexDI1 register.

        Parameters
        ----------
        value : list[int]
            Value to write to the AttenuationAndSoundIndexDI1 register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_SOUND_INDEX_DI1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_AND_SOUND_INDEX_DI1", reply)

        return reply

    def read_attenuation_and_sound_index_di2(self) -> list[int] | None:
        """
        Reads the contents of the AttenuationAndSoundIndexDI2 register.

        Returns
        -------
        list[int] | None
            Value read from the AttenuationAndSoundIndexDI2 register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_SOUND_INDEX_DI2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_AND_SOUND_INDEX_DI2", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_and_sound_index_di2(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the AttenuationAndSoundIndexDI2 register.

        Parameters
        ----------
        value : list[int]
            Value to write to the AttenuationAndSoundIndexDI2 register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_SOUND_INDEX_DI2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_AND_SOUND_INDEX_DI2", reply)

        return reply

    def read_attenuation_and_frequency_di0(self) -> list[int] | None:
        """
        Reads the contents of the AttenuationAndFrequencyDI0 register.

        Returns
        -------
        list[int] | None
            Value read from the AttenuationAndFrequencyDI0 register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_FREQUENCY_DI0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_AND_FREQUENCY_DI0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_and_frequency_di0(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the AttenuationAndFrequencyDI0 register.

        Parameters
        ----------
        value : list[int]
            Value to write to the AttenuationAndFrequencyDI0 register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_FREQUENCY_DI0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_AND_FREQUENCY_DI0", reply)

        return reply

    def read_attenuation_and_frequency_di1(self) -> list[int] | None:
        """
        Reads the contents of the AttenuationAndFrequencyDI1 register.

        Returns
        -------
        list[int] | None
            Value read from the AttenuationAndFrequencyDI1 register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_FREQUENCY_DI1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_AND_FREQUENCY_DI1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_and_frequency_di1(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the AttenuationAndFrequencyDI1 register.

        Parameters
        ----------
        value : list[int]
            Value to write to the AttenuationAndFrequencyDI1 register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_FREQUENCY_DI1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_AND_FREQUENCY_DI1", reply)

        return reply

    def read_attenuation_and_frequency_di2(self) -> list[int] | None:
        """
        Reads the contents of the AttenuationAndFrequencyDI2 register.

        Returns
        -------
        list[int] | None
            Value read from the AttenuationAndFrequencyDI2 register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_FREQUENCY_DI2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ATTENUATION_AND_FREQUENCY_DI2", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_attenuation_and_frequency_di2(self, value: list[int]) -> HarpMessage | None:
        """
        Writes a value to the AttenuationAndFrequencyDI2 register.

        Parameters
        ----------
        value : list[int]
            Value to write to the AttenuationAndFrequencyDI2 register.
        """
        address = SoundCardRegisters.ATTENUATION_AND_FREQUENCY_DI2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ATTENUATION_AND_FREQUENCY_DI2", reply)

        return reply

    def read_configure_do0(self) -> DigitalOutputConfiguration | None:
        """
        Reads the contents of the ConfigureDO0 register.

        Returns
        -------
        DigitalOutputConfiguration | None
            Value read from the ConfigureDO0 register.
        """
        address = SoundCardRegisters.CONFIGURE_DO0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.CONFIGURE_DO0", reply)

        if reply is not None:
            return DigitalOutputConfiguration(reply.payload)
        return None

    def write_configure_do0(self, value: DigitalOutputConfiguration) -> HarpMessage | None:
        """
        Writes a value to the ConfigureDO0 register.

        Parameters
        ----------
        value : DigitalOutputConfiguration
            Value to write to the ConfigureDO0 register.
        """
        address = SoundCardRegisters.CONFIGURE_DO0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.CONFIGURE_DO0", reply)

        return reply

    def read_configure_do1(self) -> DigitalOutputConfiguration | None:
        """
        Reads the contents of the ConfigureDO1 register.

        Returns
        -------
        DigitalOutputConfiguration | None
            Value read from the ConfigureDO1 register.
        """
        address = SoundCardRegisters.CONFIGURE_DO1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.CONFIGURE_DO1", reply)

        if reply is not None:
            return DigitalOutputConfiguration(reply.payload)
        return None

    def write_configure_do1(self, value: DigitalOutputConfiguration) -> HarpMessage | None:
        """
        Writes a value to the ConfigureDO1 register.

        Parameters
        ----------
        value : DigitalOutputConfiguration
            Value to write to the ConfigureDO1 register.
        """
        address = SoundCardRegisters.CONFIGURE_DO1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.CONFIGURE_DO1", reply)

        return reply

    def read_configure_do2(self) -> DigitalOutputConfiguration | None:
        """
        Reads the contents of the ConfigureDO2 register.

        Returns
        -------
        DigitalOutputConfiguration | None
            Value read from the ConfigureDO2 register.
        """
        address = SoundCardRegisters.CONFIGURE_DO2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.CONFIGURE_DO2", reply)

        if reply is not None:
            return DigitalOutputConfiguration(reply.payload)
        return None

    def write_configure_do2(self, value: DigitalOutputConfiguration) -> HarpMessage | None:
        """
        Writes a value to the ConfigureDO2 register.

        Parameters
        ----------
        value : DigitalOutputConfiguration
            Value to write to the ConfigureDO2 register.
        """
        address = SoundCardRegisters.CONFIGURE_DO2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.CONFIGURE_DO2", reply)

        return reply

    def read_pulse_do0(self) -> int | None:
        """
        Reads the contents of the PulseDO0 register.

        Returns
        -------
        int | None
            Value read from the PulseDO0 register.
        """
        address = SoundCardRegisters.PULSE_DO0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.PULSE_DO0", reply)

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
        address = SoundCardRegisters.PULSE_DO0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.PULSE_DO0", reply)

        return reply

    def read_pulse_do1(self) -> int | None:
        """
        Reads the contents of the PulseDO1 register.

        Returns
        -------
        int | None
            Value read from the PulseDO1 register.
        """
        address = SoundCardRegisters.PULSE_DO1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.PULSE_DO1", reply)

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
        address = SoundCardRegisters.PULSE_DO1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.PULSE_DO1", reply)

        return reply

    def read_pulse_do2(self) -> int | None:
        """
        Reads the contents of the PulseDO2 register.

        Returns
        -------
        int | None
            Value read from the PulseDO2 register.
        """
        address = SoundCardRegisters.PULSE_DO2
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.PULSE_DO2", reply)

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
        address = SoundCardRegisters.PULSE_DO2
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.PULSE_DO2", reply)

        return reply

    def read_output_set(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputSet register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputSet register.
        """
        address = SoundCardRegisters.OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.OUTPUT_SET", reply)

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
        address = SoundCardRegisters.OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.OUTPUT_SET", reply)

        return reply

    def read_output_clear(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputClear register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputClear register.
        """
        address = SoundCardRegisters.OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.OUTPUT_CLEAR", reply)

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
        address = SoundCardRegisters.OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.OUTPUT_CLEAR", reply)

        return reply

    def read_output_toggle(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputToggle register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputToggle register.
        """
        address = SoundCardRegisters.OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.OUTPUT_TOGGLE", reply)

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
        address = SoundCardRegisters.OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.OUTPUT_TOGGLE", reply)

        return reply

    def read_output_state(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputState register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputState register.
        """
        address = SoundCardRegisters.OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.OUTPUT_STATE", reply)

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
        address = SoundCardRegisters.OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.OUTPUT_STATE", reply)

        return reply

    def read_configure_adc(self) -> AdcConfiguration | None:
        """
        Reads the contents of the ConfigureAdc register.

        Returns
        -------
        AdcConfiguration | None
            Value read from the ConfigureAdc register.
        """
        address = SoundCardRegisters.CONFIGURE_ADC
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.CONFIGURE_ADC", reply)

        if reply is not None:
            return AdcConfiguration(reply.payload)
        return None

    def write_configure_adc(self, value: AdcConfiguration) -> HarpMessage | None:
        """
        Writes a value to the ConfigureAdc register.

        Parameters
        ----------
        value : AdcConfiguration
            Value to write to the ConfigureAdc register.
        """
        address = SoundCardRegisters.CONFIGURE_ADC
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.CONFIGURE_ADC", reply)

        return reply

    def read_analog_data(self) -> AnalogDataPayload | None:
        """
        Reads the contents of the AnalogData register.

        Returns
        -------
        AnalogDataPayload | None
            Value read from the AnalogData register.
        """
        address = SoundCardRegisters.ANALOG_DATA
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ANALOG_DATA", reply)

        if reply is not None:
            # Map payload (list/array) to dataclass fields by offset
            payload = reply.payload
            return AnalogDataPayload(
                Adc0=payload[0],
                Adc1=payload[1],
                AttenuationLeft=payload[2],
                AttenuationRight=payload[3],
                Frequency=payload[4]
            )
        return None

    def read_commands(self) -> ControllerCommand | None:
        """
        Reads the contents of the Commands register.

        Returns
        -------
        ControllerCommand | None
            Value read from the Commands register.
        """
        address = SoundCardRegisters.COMMANDS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.COMMANDS", reply)

        if reply is not None:
            return ControllerCommand(reply.payload)
        return None

    def write_commands(self, value: ControllerCommand) -> HarpMessage | None:
        """
        Writes a value to the Commands register.

        Parameters
        ----------
        value : ControllerCommand
            Value to write to the Commands register.
        """
        address = SoundCardRegisters.COMMANDS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.COMMANDS", reply)

        return reply

    def read_enable_events(self) -> SoundCardEvents | None:
        """
        Reads the contents of the EnableEvents register.

        Returns
        -------
        SoundCardEvents | None
            Value read from the EnableEvents register.
        """
        address = SoundCardRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("SoundCardRegisters.ENABLE_EVENTS", reply)

        if reply is not None:
            return SoundCardEvents(reply.payload)
        return None

    def write_enable_events(self, value: SoundCardEvents) -> HarpMessage | None:
        """
        Writes a value to the EnableEvents register.

        Parameters
        ----------
        value : SoundCardEvents
            Value to write to the EnableEvents register.
        """
        address = SoundCardRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("SoundCardRegisters.ENABLE_EVENTS", reply)

        return reply

