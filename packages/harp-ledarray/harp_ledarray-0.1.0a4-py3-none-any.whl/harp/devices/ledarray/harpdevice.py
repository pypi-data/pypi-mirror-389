from dataclasses import dataclass
from enum import IntEnum, IntFlag

from harp.protocol import MessageType, PayloadType
from harp.protocol.exceptions import HarpException, HarpReadException, HarpWriteException
from harp.protocol.messages import HarpMessage
from harp.serial import Device


@dataclass
class DigitalOutputSyncPayload:
        # Configuration of the DO0 functionality.
    DO0Sync: DO0SyncConfig
        # Configuration of the DO1 functionality.
    DO1Sync: DO1SyncConfig


@dataclass
class DigitalInputTriggerPayload:
        # Configuration of the DIO input pin.
    DI0Trigger: DigitalInputTriggerConfig
        # Configuration of the DI1 input pin.
    DI1Trigger: DigitalInputTriggerConfig


@dataclass
class PulseModePayload:
        # Sets the pulse mode used in LED0.
    Led0Mode: PulseModeConfig
        # Sets the pulse mode used in LED0
    Led1Mode: PulseModeConfig


class LedState(IntFlag):
    """
    Specifies the LEDs state.

    Attributes
    ----------
    LED0_ON : int
        _No description currently available_
    LED1_ON : int
        _No description currently available_
    LED0_OFF : int
        _No description currently available_
    LED1_OFF : int
        _No description currently available_
    """

    NONE = 0x0
    LED0_ON = 0x1
    LED1_ON = 0x2
    LED0_OFF = 0x4
    LED1_OFF = 0x8


class DigitalInputs(IntFlag):
    """
    Specifies the state of port digital input lines.

    Attributes
    ----------
    DI0 : int
        _No description currently available_
    DI1 : int
        _No description currently available_
    """

    NONE = 0x0
    DI0 = 0x1
    DI1 = 0x2


class AuxDigitalOutputs(IntFlag):
    """
    Specifies the state of the auxiliary digital output lines.

    Attributes
    ----------
    AUX0_SET : int
        _No description currently available_
    AUX1_SET : int
        _No description currently available_
    AUX0_CLEAR : int
        _No description currently available_
    AUX1_CLEAR : int
        _No description currently available_
    """

    NONE = 0x0
    AUX0_SET = 0x1
    AUX1_SET = 0x2
    AUX0_CLEAR = 0x4
    AUX1_CLEAR = 0x8


class DigitalOutputs(IntFlag):
    """
    Specifies the state of port digital output lines.

    Attributes
    ----------
    DO0_SET : int
        _No description currently available_
    DO1_SET : int
        _No description currently available_
    DO0_CLEAR : int
        _No description currently available_
    DO1_CLEAR : int
        _No description currently available_
    """

    NONE = 0x0
    DO0_SET = 0x1
    DO1_SET = 0x2
    DO0_CLEAR = 0x4
    DO1_CLEAR = 0x8


class LedArrayEvents(IntFlag):
    """
    The events that can be enabled/disabled.

    Attributes
    ----------
    ENABLE_LED : int
        _No description currently available_
    DIGITAL_INPUT_STATE : int
        _No description currently available_
    """

    NONE = 0x0
    ENABLE_LED = 0x1
    DIGITAL_INPUT_STATE = 0x2


class DO0SyncConfig(IntEnum):
    """
    Available configurations when using digital output pin 0 to report firmware events.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    MIMIC_LED0_ENABLE_POWER : int
        _No description currently available_
    MIMIC_LED0_ENABLE_BEHAVIOR : int
        _No description currently available_
    MIMIC_LED0_ENABLE_LED : int
        _No description currently available_
    """

    NONE = 0
    MIMIC_LED0_ENABLE_POWER = 1
    MIMIC_LED0_ENABLE_BEHAVIOR = 2
    MIMIC_LED0_ENABLE_LED = 3


class DO1SyncConfig(IntEnum):
    """
    Available configurations when using digital output pin 1 to report firmware events.

    Attributes
    ----------
    NONE : int
        _No description currently available_
    MIMIC_LED1_ENABLE_POWER : int
        _No description currently available_
    MIMIC_LED1_ENABLE_BEHAVIOR : int
        _No description currently available_
    MIMIC_LED1_ENABLE_LED : int
        _No description currently available_
    """

    NONE = 0
    MIMIC_LED1_ENABLE_POWER = 16
    MIMIC_LED1_ENABLE_BEHAVIOR = 32
    MIMIC_LED1_ENABLE_LED = 48


class DigitalInputTriggerConfig(IntEnum):
    """
    Available configurations when using digital inputs as an acquisition trigger.

    Attributes
    ----------
    LED0_ENABLE_POWER : int
        _No description currently available_
    LED0_ENABLE_BEHAVIOR : int
        _No description currently available_
    LED0_ENABLE_LED : int
        _No description currently available_
    LED1_ENABLE_POWER : int
        _No description currently available_
    LED1_ENABLE_BEHAVIOR : int
        _No description currently available_
    LED1_ENABLE_LED : int
        _No description currently available_
    NONE : int
        _No description currently available_
    """

    LED0_ENABLE_POWER = 0
    LED0_ENABLE_BEHAVIOR = 1
    LED0_ENABLE_LED = 2
    LED1_ENABLE_POWER = 3
    LED1_ENABLE_BEHAVIOR = 4
    LED1_ENABLE_LED = 5
    NONE = 6


class PulseModeConfig(IntEnum):
    """
    Available configurations modes when LED behavior is enabled.

    Attributes
    ----------
    PWM : int
        _No description currently available_
    PULSE_TIME : int
        _No description currently available_
    """

    PWM = 0
    PULSE_TIME = 1


class LedArrayRegisters(IntEnum):
    """Enum for all available registers in the LedArray device.

    Attributes
    ----------
    ENABLE_POWER : int
        Control the enable of both LEDs' power supply.
    ENABLE_LED_MODE : int
        Start/stop the LEDs according to the pulse configuration.
    ENABLE_LED : int
        Enables/disables the LEDs.
    DIGITAL_INPUT_STATE : int
        State of the digital input pins. An event will be emitted when the value of any digital input pin changes.
    DIGITAL_OUTPUT_SYNC : int
        Configuration of the digital outputs behavior.
    DIGITAL_INPUT_TRIGGER : int
        Configuration of the digital inputs pins behavior.
    PULSE_MODE : int
        Sets the pulse mode used by the LEDs.
    LED0_POWER : int
        Sets the power to LED0, between 1 and 120 (arbitrary units).
    LED1_POWER : int
        Sets the power to LED1, between 1 and 120 (arbitrary units).
    LED0_PWM_FREQUENCY : int
        Sets the frequency (Hz) of LED0 when in Pwm mode, between 0.5 and 2000.
    LED0_PWM_DUTY_CYCLE : int
        Sets the duty cycle (%) of LED0 when in Pwm mode, between 0.1 and 99.9.
    LED0_PWM_PULSE_COUNTER : int
        Sets the number of pulses of LED0 when in Pwm mode, between 1 and 65535.
    LED0_PULSE_TIME_ON : int
        Sets the time on (milliseconds) of LED0 when in PulseTime mode, between 1 and 65535.
    LED0_PULSE_TIME_OFF : int
        Sets the time off (milliseconds) of LED0 when in PulseTime mode, between 1 and 65535.
    LED0_PULSE_TIME_PULSE_COUNTER : int
        Sets the number of pulses of LED0 when in PulseTime mode, between 1 and 65535.
    LED0_PULSE_TIME_TAIL : int
        Sets the wait time between pulses (milliseconds) of LED0 when in PulseTime mode, between 1 and 65535.
    LED0_PULSE_REPEAT_COUNTER : int
        Sets the number of repetitions of LED0 pulse protocol when in PulseTime mode, between 1 and 65535.
    LED1_PWM_FREQUENCY : int
        Sets the frequency (Hz) of LED1 when in Pwm mode, between 0.5 and 2000.
    LED1_PWM_DUTY_CYCLE : int
        Sets the duty cycle (%) of LED1 when in Pwm mode, between 0.1 and 99.9.
    LED1_PWM_PULSE_COUNTER : int
        Sets the number of pulses of LED1 when in Pwm mode, between 1 and 65535.
    LED1_PULSE_TIME_ON : int
        Sets the time on (milliseconds) of LED1 when in PulseTime mode, between 1 and 65535.
    LED1_PULSE_TIME_OFF : int
        Sets the time off (milliseconds) of LED1 when in PulseTime mode, between 1 and 65535.
    LED1_PULSE_TIME_PULSE_COUNTER : int
        Sets the number of pulses of LED1 when in PulseTime mode, between 1 and 65535.
    LED1_PULSE_TIME_TAIL : int
        Sets the wait time between pulses (milliseconds) of LED1 when in PulseTime mode, between 1 and 65535.
    LED1_PULSE_REPEAT_COUNTER : int
        Sets the number of repetitions of LED1 pulse protocol when in PulseTime mode, between 1 and 65535.
    LED0_PWM_REAL : int
        Get the real frequency (Hz) of LED0 when in Pwm mode.
    LED0_PWM_DUTY_CYCLE_REAL : int
        Get the real duty cycle (%) of LED0 when in Pwm mode.
    LED1_PWM_REAL : int
        Get the real frequency (Hz) of LED1 when in Pwm mode.
    LED_D1_PWM_DUTY_CYCLE_REAL : int
        Get the real duty cycle (%) of LED1 when in Pwm mode.
    AUX_DIGITAL_OUTPUT_STATE : int
        Write the state of the auxiliary digital output bit.
    AUX_LED_POWER : int
        Sets the power to be applied to auxiliary LED, between 1 and 120.
    DIGITAL_OUTPUT_STATE : int
        Write the state of digital output lines.
    ENABLE_EVENTS : int
        Specifies all the active events in the device.
    """

    ENABLE_POWER = 32
    ENABLE_LED_MODE = 33
    ENABLE_LED = 34
    DIGITAL_INPUT_STATE = 35
    DIGITAL_OUTPUT_SYNC = 36
    DIGITAL_INPUT_TRIGGER = 37
    PULSE_MODE = 38
    LED0_POWER = 39
    LED1_POWER = 40
    LED0_PWM_FREQUENCY = 41
    LED0_PWM_DUTY_CYCLE = 42
    LED0_PWM_PULSE_COUNTER = 43
    LED0_PULSE_TIME_ON = 44
    LED0_PULSE_TIME_OFF = 45
    LED0_PULSE_TIME_PULSE_COUNTER = 46
    LED0_PULSE_TIME_TAIL = 47
    LED0_PULSE_REPEAT_COUNTER = 48
    LED1_PWM_FREQUENCY = 49
    LED1_PWM_DUTY_CYCLE = 50
    LED1_PWM_PULSE_COUNTER = 51
    LED1_PULSE_TIME_ON = 52
    LED1_PULSE_TIME_OFF = 53
    LED1_PULSE_TIME_PULSE_COUNTER = 54
    LED1_PULSE_TIME_TAIL = 55
    LED1_PULSE_REPEAT_COUNTER = 56
    LED0_PWM_REAL = 57
    LED0_PWM_DUTY_CYCLE_REAL = 58
    LED1_PWM_REAL = 59
    LED_D1_PWM_DUTY_CYCLE_REAL = 60
    AUX_DIGITAL_OUTPUT_STATE = 61
    AUX_LED_POWER = 62
    DIGITAL_OUTPUT_STATE = 63
    ENABLE_EVENTS = 65


class LedArray(Device):
    """
    LedArray class for controlling the device.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect and load already happened in the base class
        # verify that WHO_AM_I matches the expected value
        if self.WHO_AM_I != 1088:
            self.disconnect()
            raise HarpException(f"WHO_AM_I mismatch: expected {1088}, got {self.WHO_AM_I}")

    def read_enable_power(self) -> LedState | None:
        """
        Reads the contents of the EnablePower register.

        Returns
        -------
        LedState | None
            Value read from the EnablePower register.
        """
        address = LedArrayRegisters.ENABLE_POWER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.ENABLE_POWER", reply)

        if reply is not None:
            return LedState(reply.payload)
        return None

    def write_enable_power(self, value: LedState) -> HarpMessage | None:
        """
        Writes a value to the EnablePower register.

        Parameters
        ----------
        value : LedState
            Value to write to the EnablePower register.
        """
        address = LedArrayRegisters.ENABLE_POWER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.ENABLE_POWER", reply)

        return reply

    def read_enable_led_mode(self) -> LedState | None:
        """
        Reads the contents of the EnableLedMode register.

        Returns
        -------
        LedState | None
            Value read from the EnableLedMode register.
        """
        address = LedArrayRegisters.ENABLE_LED_MODE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.ENABLE_LED_MODE", reply)

        if reply is not None:
            return LedState(reply.payload)
        return None

    def write_enable_led_mode(self, value: LedState) -> HarpMessage | None:
        """
        Writes a value to the EnableLedMode register.

        Parameters
        ----------
        value : LedState
            Value to write to the EnableLedMode register.
        """
        address = LedArrayRegisters.ENABLE_LED_MODE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.ENABLE_LED_MODE", reply)

        return reply

    def read_enable_led(self) -> LedState | None:
        """
        Reads the contents of the EnableLed register.

        Returns
        -------
        LedState | None
            Value read from the EnableLed register.
        """
        address = LedArrayRegisters.ENABLE_LED
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.ENABLE_LED", reply)

        if reply is not None:
            return LedState(reply.payload)
        return None

    def write_enable_led(self, value: LedState) -> HarpMessage | None:
        """
        Writes a value to the EnableLed register.

        Parameters
        ----------
        value : LedState
            Value to write to the EnableLed register.
        """
        address = LedArrayRegisters.ENABLE_LED
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.ENABLE_LED", reply)

        return reply

    def read_digital_input_state(self) -> DigitalInputs | None:
        """
        Reads the contents of the DigitalInputState register.

        Returns
        -------
        DigitalInputs | None
            Value read from the DigitalInputState register.
        """
        address = LedArrayRegisters.DIGITAL_INPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.DIGITAL_INPUT_STATE", reply)

        if reply is not None:
            return DigitalInputs(reply.payload)
        return None

    def read_digital_output_sync(self) -> DigitalOutputSyncPayload | None:
        """
        Reads the contents of the DigitalOutputSync register.

        Returns
        -------
        DigitalOutputSyncPayload | None
            Value read from the DigitalOutputSync register.
        """
        address = LedArrayRegisters.DIGITAL_OUTPUT_SYNC
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.DIGITAL_OUTPUT_SYNC", reply)

        if reply is not None:
            # Map payload (list/array) to dataclass fields by offset
            payload = reply.payload
            return DigitalOutputSyncPayload(
                DO0Sync=payload[0],
                DO1Sync=payload[1]
            )
        return None

    def write_digital_output_sync(self, value: DigitalOutputSyncPayload) -> HarpMessage | None:
        """
        Writes a value to the DigitalOutputSync register.

        Parameters
        ----------
        value : DigitalOutputSyncPayload
            Value to write to the DigitalOutputSync register.
        """
        address = LedArrayRegisters.DIGITAL_OUTPUT_SYNC
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.DIGITAL_OUTPUT_SYNC", reply)

        return reply

    def read_digital_input_trigger(self) -> DigitalInputTriggerPayload | None:
        """
        Reads the contents of the DigitalInputTrigger register.

        Returns
        -------
        DigitalInputTriggerPayload | None
            Value read from the DigitalInputTrigger register.
        """
        address = LedArrayRegisters.DIGITAL_INPUT_TRIGGER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.DIGITAL_INPUT_TRIGGER", reply)

        if reply is not None:
            # Map payload (list/array) to dataclass fields by offset
            payload = reply.payload
            return DigitalInputTriggerPayload(
                DI0Trigger=payload[0],
                DI1Trigger=payload[1]
            )
        return None

    def write_digital_input_trigger(self, value: DigitalInputTriggerPayload) -> HarpMessage | None:
        """
        Writes a value to the DigitalInputTrigger register.

        Parameters
        ----------
        value : DigitalInputTriggerPayload
            Value to write to the DigitalInputTrigger register.
        """
        address = LedArrayRegisters.DIGITAL_INPUT_TRIGGER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.DIGITAL_INPUT_TRIGGER", reply)

        return reply

    def read_pulse_mode(self) -> PulseModePayload | None:
        """
        Reads the contents of the PulseMode register.

        Returns
        -------
        PulseModePayload | None
            Value read from the PulseMode register.
        """
        address = LedArrayRegisters.PULSE_MODE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.PULSE_MODE", reply)

        if reply is not None:
            # Map payload (list/array) to dataclass fields by offset
            payload = reply.payload
            return PulseModePayload(
                Led0Mode=payload[0],
                Led1Mode=payload[1]
            )
        return None

    def write_pulse_mode(self, value: PulseModePayload) -> HarpMessage | None:
        """
        Writes a value to the PulseMode register.

        Parameters
        ----------
        value : PulseModePayload
            Value to write to the PulseMode register.
        """
        address = LedArrayRegisters.PULSE_MODE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.PULSE_MODE", reply)

        return reply

    def read_led0_power(self) -> int | None:
        """
        Reads the contents of the Led0Power register.

        Returns
        -------
        int | None
            Value read from the Led0Power register.
        """
        address = LedArrayRegisters.LED0_POWER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED0_POWER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_power(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led0Power register.

        Parameters
        ----------
        value : int
            Value to write to the Led0Power register.
        """
        address = LedArrayRegisters.LED0_POWER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED0_POWER", reply)

        return reply

    def read_led1_power(self) -> int | None:
        """
        Reads the contents of the Led1Power register.

        Returns
        -------
        int | None
            Value read from the Led1Power register.
        """
        address = LedArrayRegisters.LED1_POWER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED1_POWER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_power(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led1Power register.

        Parameters
        ----------
        value : int
            Value to write to the Led1Power register.
        """
        address = LedArrayRegisters.LED1_POWER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED1_POWER", reply)

        return reply

    def read_led0_pwm_frequency(self) -> float | None:
        """
        Reads the contents of the Led0PwmFrequency register.

        Returns
        -------
        float | None
            Value read from the Led0PwmFrequency register.
        """
        address = LedArrayRegisters.LED0_PWM_FREQUENCY
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED0_PWM_FREQUENCY", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_pwm_frequency(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Led0PwmFrequency register.

        Parameters
        ----------
        value : float
            Value to write to the Led0PwmFrequency register.
        """
        address = LedArrayRegisters.LED0_PWM_FREQUENCY
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED0_PWM_FREQUENCY", reply)

        return reply

    def read_led0_pwm_duty_cycle(self) -> float | None:
        """
        Reads the contents of the Led0PwmDutyCycle register.

        Returns
        -------
        float | None
            Value read from the Led0PwmDutyCycle register.
        """
        address = LedArrayRegisters.LED0_PWM_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED0_PWM_DUTY_CYCLE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_pwm_duty_cycle(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Led0PwmDutyCycle register.

        Parameters
        ----------
        value : float
            Value to write to the Led0PwmDutyCycle register.
        """
        address = LedArrayRegisters.LED0_PWM_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED0_PWM_DUTY_CYCLE", reply)

        return reply

    def read_led0_pwm_pulse_counter(self) -> int | None:
        """
        Reads the contents of the Led0PwmPulseCounter register.

        Returns
        -------
        int | None
            Value read from the Led0PwmPulseCounter register.
        """
        address = LedArrayRegisters.LED0_PWM_PULSE_COUNTER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED0_PWM_PULSE_COUNTER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_pwm_pulse_counter(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led0PwmPulseCounter register.

        Parameters
        ----------
        value : int
            Value to write to the Led0PwmPulseCounter register.
        """
        address = LedArrayRegisters.LED0_PWM_PULSE_COUNTER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED0_PWM_PULSE_COUNTER", reply)

        return reply

    def read_led0_pulse_time_on(self) -> int | None:
        """
        Reads the contents of the Led0PulseTimeOn register.

        Returns
        -------
        int | None
            Value read from the Led0PulseTimeOn register.
        """
        address = LedArrayRegisters.LED0_PULSE_TIME_ON
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED0_PULSE_TIME_ON", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_pulse_time_on(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led0PulseTimeOn register.

        Parameters
        ----------
        value : int
            Value to write to the Led0PulseTimeOn register.
        """
        address = LedArrayRegisters.LED0_PULSE_TIME_ON
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED0_PULSE_TIME_ON", reply)

        return reply

    def read_led0_pulse_time_off(self) -> int | None:
        """
        Reads the contents of the Led0PulseTimeOff register.

        Returns
        -------
        int | None
            Value read from the Led0PulseTimeOff register.
        """
        address = LedArrayRegisters.LED0_PULSE_TIME_OFF
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED0_PULSE_TIME_OFF", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_pulse_time_off(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led0PulseTimeOff register.

        Parameters
        ----------
        value : int
            Value to write to the Led0PulseTimeOff register.
        """
        address = LedArrayRegisters.LED0_PULSE_TIME_OFF
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED0_PULSE_TIME_OFF", reply)

        return reply

    def read_led0_pulse_time_pulse_counter(self) -> int | None:
        """
        Reads the contents of the Led0PulseTimePulseCounter register.

        Returns
        -------
        int | None
            Value read from the Led0PulseTimePulseCounter register.
        """
        address = LedArrayRegisters.LED0_PULSE_TIME_PULSE_COUNTER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED0_PULSE_TIME_PULSE_COUNTER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_pulse_time_pulse_counter(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led0PulseTimePulseCounter register.

        Parameters
        ----------
        value : int
            Value to write to the Led0PulseTimePulseCounter register.
        """
        address = LedArrayRegisters.LED0_PULSE_TIME_PULSE_COUNTER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED0_PULSE_TIME_PULSE_COUNTER", reply)

        return reply

    def read_led0_pulse_time_tail(self) -> int | None:
        """
        Reads the contents of the Led0PulseTimeTail register.

        Returns
        -------
        int | None
            Value read from the Led0PulseTimeTail register.
        """
        address = LedArrayRegisters.LED0_PULSE_TIME_TAIL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED0_PULSE_TIME_TAIL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_pulse_time_tail(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led0PulseTimeTail register.

        Parameters
        ----------
        value : int
            Value to write to the Led0PulseTimeTail register.
        """
        address = LedArrayRegisters.LED0_PULSE_TIME_TAIL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED0_PULSE_TIME_TAIL", reply)

        return reply

    def read_led0_pulse_repeat_counter(self) -> int | None:
        """
        Reads the contents of the Led0PulseRepeatCounter register.

        Returns
        -------
        int | None
            Value read from the Led0PulseRepeatCounter register.
        """
        address = LedArrayRegisters.LED0_PULSE_REPEAT_COUNTER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED0_PULSE_REPEAT_COUNTER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_pulse_repeat_counter(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led0PulseRepeatCounter register.

        Parameters
        ----------
        value : int
            Value to write to the Led0PulseRepeatCounter register.
        """
        address = LedArrayRegisters.LED0_PULSE_REPEAT_COUNTER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED0_PULSE_REPEAT_COUNTER", reply)

        return reply

    def read_led1_pwm_frequency(self) -> float | None:
        """
        Reads the contents of the Led1PwmFrequency register.

        Returns
        -------
        float | None
            Value read from the Led1PwmFrequency register.
        """
        address = LedArrayRegisters.LED1_PWM_FREQUENCY
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED1_PWM_FREQUENCY", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_pwm_frequency(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Led1PwmFrequency register.

        Parameters
        ----------
        value : float
            Value to write to the Led1PwmFrequency register.
        """
        address = LedArrayRegisters.LED1_PWM_FREQUENCY
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED1_PWM_FREQUENCY", reply)

        return reply

    def read_led1_pwm_duty_cycle(self) -> float | None:
        """
        Reads the contents of the Led1PwmDutyCycle register.

        Returns
        -------
        float | None
            Value read from the Led1PwmDutyCycle register.
        """
        address = LedArrayRegisters.LED1_PWM_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED1_PWM_DUTY_CYCLE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_pwm_duty_cycle(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Led1PwmDutyCycle register.

        Parameters
        ----------
        value : float
            Value to write to the Led1PwmDutyCycle register.
        """
        address = LedArrayRegisters.LED1_PWM_DUTY_CYCLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED1_PWM_DUTY_CYCLE", reply)

        return reply

    def read_led1_pwm_pulse_counter(self) -> int | None:
        """
        Reads the contents of the Led1PwmPulseCounter register.

        Returns
        -------
        int | None
            Value read from the Led1PwmPulseCounter register.
        """
        address = LedArrayRegisters.LED1_PWM_PULSE_COUNTER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED1_PWM_PULSE_COUNTER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_pwm_pulse_counter(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led1PwmPulseCounter register.

        Parameters
        ----------
        value : int
            Value to write to the Led1PwmPulseCounter register.
        """
        address = LedArrayRegisters.LED1_PWM_PULSE_COUNTER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED1_PWM_PULSE_COUNTER", reply)

        return reply

    def read_led1_pulse_time_on(self) -> int | None:
        """
        Reads the contents of the Led1PulseTimeOn register.

        Returns
        -------
        int | None
            Value read from the Led1PulseTimeOn register.
        """
        address = LedArrayRegisters.LED1_PULSE_TIME_ON
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED1_PULSE_TIME_ON", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_pulse_time_on(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led1PulseTimeOn register.

        Parameters
        ----------
        value : int
            Value to write to the Led1PulseTimeOn register.
        """
        address = LedArrayRegisters.LED1_PULSE_TIME_ON
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED1_PULSE_TIME_ON", reply)

        return reply

    def read_led1_pulse_time_off(self) -> int | None:
        """
        Reads the contents of the Led1PulseTimeOff register.

        Returns
        -------
        int | None
            Value read from the Led1PulseTimeOff register.
        """
        address = LedArrayRegisters.LED1_PULSE_TIME_OFF
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED1_PULSE_TIME_OFF", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_pulse_time_off(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led1PulseTimeOff register.

        Parameters
        ----------
        value : int
            Value to write to the Led1PulseTimeOff register.
        """
        address = LedArrayRegisters.LED1_PULSE_TIME_OFF
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED1_PULSE_TIME_OFF", reply)

        return reply

    def read_led1_pulse_time_pulse_counter(self) -> int | None:
        """
        Reads the contents of the Led1PulseTimePulseCounter register.

        Returns
        -------
        int | None
            Value read from the Led1PulseTimePulseCounter register.
        """
        address = LedArrayRegisters.LED1_PULSE_TIME_PULSE_COUNTER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED1_PULSE_TIME_PULSE_COUNTER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_pulse_time_pulse_counter(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led1PulseTimePulseCounter register.

        Parameters
        ----------
        value : int
            Value to write to the Led1PulseTimePulseCounter register.
        """
        address = LedArrayRegisters.LED1_PULSE_TIME_PULSE_COUNTER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED1_PULSE_TIME_PULSE_COUNTER", reply)

        return reply

    def read_led1_pulse_time_tail(self) -> int | None:
        """
        Reads the contents of the Led1PulseTimeTail register.

        Returns
        -------
        int | None
            Value read from the Led1PulseTimeTail register.
        """
        address = LedArrayRegisters.LED1_PULSE_TIME_TAIL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED1_PULSE_TIME_TAIL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_pulse_time_tail(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led1PulseTimeTail register.

        Parameters
        ----------
        value : int
            Value to write to the Led1PulseTimeTail register.
        """
        address = LedArrayRegisters.LED1_PULSE_TIME_TAIL
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED1_PULSE_TIME_TAIL", reply)

        return reply

    def read_led1_pulse_repeat_counter(self) -> int | None:
        """
        Reads the contents of the Led1PulseRepeatCounter register.

        Returns
        -------
        int | None
            Value read from the Led1PulseRepeatCounter register.
        """
        address = LedArrayRegisters.LED1_PULSE_REPEAT_COUNTER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED1_PULSE_REPEAT_COUNTER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_pulse_repeat_counter(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the Led1PulseRepeatCounter register.

        Parameters
        ----------
        value : int
            Value to write to the Led1PulseRepeatCounter register.
        """
        address = LedArrayRegisters.LED1_PULSE_REPEAT_COUNTER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.LED1_PULSE_REPEAT_COUNTER", reply)

        return reply

    def read_led0_pwm_real(self) -> float | None:
        """
        Reads the contents of the Led0PwmReal register.

        Returns
        -------
        float | None
            Value read from the Led0PwmReal register.
        """
        address = LedArrayRegisters.LED0_PWM_REAL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED0_PWM_REAL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_led0_pwm_duty_cycle_real(self) -> float | None:
        """
        Reads the contents of the Led0PwmDutyCycleReal register.

        Returns
        -------
        float | None
            Value read from the Led0PwmDutyCycleReal register.
        """
        address = LedArrayRegisters.LED0_PWM_DUTY_CYCLE_REAL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED0_PWM_DUTY_CYCLE_REAL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_led1_pwm_real(self) -> float | None:
        """
        Reads the contents of the Led1PwmReal register.

        Returns
        -------
        float | None
            Value read from the Led1PwmReal register.
        """
        address = LedArrayRegisters.LED1_PWM_REAL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED1_PWM_REAL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_led_d1_pwm_duty_cycle_real(self) -> float | None:
        """
        Reads the contents of the LedD1PwmDutyCycleReal register.

        Returns
        -------
        float | None
            Value read from the LedD1PwmDutyCycleReal register.
        """
        address = LedArrayRegisters.LED_D1_PWM_DUTY_CYCLE_REAL
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.LED_D1_PWM_DUTY_CYCLE_REAL", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def read_aux_digital_output_state(self) -> AuxDigitalOutputs | None:
        """
        Reads the contents of the AuxDigitalOutputState register.

        Returns
        -------
        AuxDigitalOutputs | None
            Value read from the AuxDigitalOutputState register.
        """
        address = LedArrayRegisters.AUX_DIGITAL_OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.AUX_DIGITAL_OUTPUT_STATE", reply)

        if reply is not None:
            return AuxDigitalOutputs(reply.payload)
        return None

    def write_aux_digital_output_state(self, value: AuxDigitalOutputs) -> HarpMessage | None:
        """
        Writes a value to the AuxDigitalOutputState register.

        Parameters
        ----------
        value : AuxDigitalOutputs
            Value to write to the AuxDigitalOutputState register.
        """
        address = LedArrayRegisters.AUX_DIGITAL_OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.AUX_DIGITAL_OUTPUT_STATE", reply)

        return reply

    def read_aux_led_power(self) -> int | None:
        """
        Reads the contents of the AuxLedPower register.

        Returns
        -------
        int | None
            Value read from the AuxLedPower register.
        """
        address = LedArrayRegisters.AUX_LED_POWER
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.AUX_LED_POWER", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_aux_led_power(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the AuxLedPower register.

        Parameters
        ----------
        value : int
            Value to write to the AuxLedPower register.
        """
        address = LedArrayRegisters.AUX_LED_POWER
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.AUX_LED_POWER", reply)

        return reply

    def read_digital_output_state(self) -> DigitalOutputs | None:
        """
        Reads the contents of the DigitalOutputState register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the DigitalOutputState register.
        """
        address = LedArrayRegisters.DIGITAL_OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.DIGITAL_OUTPUT_STATE", reply)

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
        address = LedArrayRegisters.DIGITAL_OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.DIGITAL_OUTPUT_STATE", reply)

        return reply

    def read_enable_events(self) -> LedArrayEvents | None:
        """
        Reads the contents of the EnableEvents register.

        Returns
        -------
        LedArrayEvents | None
            Value read from the EnableEvents register.
        """
        address = LedArrayRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("LedArrayRegisters.ENABLE_EVENTS", reply)

        if reply is not None:
            return LedArrayEvents(reply.payload)
        return None

    def write_enable_events(self, value: LedArrayEvents) -> HarpMessage | None:
        """
        Writes a value to the EnableEvents register.

        Parameters
        ----------
        value : LedArrayEvents
            Value to write to the EnableEvents register.
        """
        address = LedArrayRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("LedArrayRegisters.ENABLE_EVENTS", reply)

        return reply

