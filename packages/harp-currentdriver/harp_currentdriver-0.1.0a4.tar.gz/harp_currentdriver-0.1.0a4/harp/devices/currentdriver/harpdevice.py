from dataclasses import dataclass
from enum import IntEnum, IntFlag

from harp.protocol import MessageType, PayloadType
from harp.protocol.exceptions import HarpException, HarpReadException, HarpWriteException
from harp.protocol.messages import HarpMessage
from harp.serial import Device


class DigitalInputs(IntFlag):
    """
    Specifies the state of port digital input lines

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


class DigitalOutputs(IntFlag):
    """
    Specifies the state of port digital output lines

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


class LedOutputs(IntFlag):
    """
    Specifies the state of LED driver's outputs

    Attributes
    ----------
    L_E_D0 : int
        _No description currently available_
    L_E_D1 : int
        _No description currently available_
    """

    NONE = 0x0
    L_E_D0 = 0x1
    L_E_D1 = 0x2


class LedRamps(IntFlag):
    """
    Specifies the configuration of LED driver's ramps

    Attributes
    ----------
    L_E_D0_U_P : int
        _No description currently available_
    L_E_D0_DO_W_N : int
        _No description currently available_
    L_E_D1_U_P : int
        _No description currently available_
    L_E_D1_DO_W_N : int
        _No description currently available_
    """

    NONE = 0x0
    L_E_D0_U_P = 0x1
    L_E_D0_DO_W_N = 0x2
    L_E_D1_U_P = 0x4
    L_E_D1_DO_W_N = 0x8


class CurrentDriverEvents(IntFlag):
    """
    Specifies the active events in the device.

    Attributes
    ----------
    DIS : int
        _No description currently available_
    """

    NONE = 0x0
    DIS = 0x1


class CurrentDriverRegisters(IntEnum):
    """Enum for all available registers in the CurrentDriver device.

    Attributes
    ----------
    DIGITAL_INPUT_STATE : int
        Reflects the state of DI digital lines
    OUTPUT_SET : int
        Set the specified digital output lines
    OUTPUT_CLEAR : int
        Clear the specified digital output lines
    OUTPUT_TOGGLE : int
        Toggle the specified digital output lines
    OUTPUT_STATE : int
        Write the state of all digital output lines
    LED0_CURRENT : int
        Configuration of current to drive LED 0 [0:1000] mA
    LED1_CURRENT : int
        Configuration of current to drive LED 1 [0:1000] mA
    DAC0_VOLTAGE : int
        Configuration of DAC 0 voltage [0:5000] mV
    DAC1_VOLTAGE : int
        Configuration of DAC 1 voltage [0:5000] mV
    LED_ENABLE : int
        Enable driver on the selected output
    LED_DISABLE : int
        Disable driver on the selected output
    LED_STATE : int
        Control the correspondent LED output
    LED0_MAX_CURRENT : int
        Configuration of current to drive LED 0 [0:1000] mA
    LED1_MAX_CURRENT : int
        Configuration of current to drive LED 1 [0:1000] mA
    PULSE_ENABLE : int
        Enables the pulse function for the specified output DACs/LEDs
    PULSE_DUTY_CYCLE_LED0 : int
        Specifies the duty cycle of the output pulse from 1 to 100
    PULSE_DUTY_CYCLE_LED1 : int
        Specifies the duty cycle of the output pulse from 1 to 100
    PULSE_FREQUENCY_LED0 : int
        Specifies the frequency of the output pulse in Hz
    PULSE_FREQUENCY_LED1 : int
        Specifies the frequency of the output pulse in Hz
    RAMP_LED0 : int
        Specifies the ramp time of the transitions between different current/voltage values in milliseconds. The ramp will only work if the pulse function is off
    RAMP_LED1 : int
        Specifies the ramp time of the transitions between different current/voltage values in milliseconds. The ramp will only work if the pulse function is off
    RAMP_CONFIG : int
        Specifies when the ramps are applied for each DAC/LED
    ENABLE_EVENTS : int
        Specifies the active events in the device
    """

    DIGITAL_INPUT_STATE = 32
    OUTPUT_SET = 33
    OUTPUT_CLEAR = 34
    OUTPUT_TOGGLE = 35
    OUTPUT_STATE = 36
    LED0_CURRENT = 37
    LED1_CURRENT = 38
    DAC0_VOLTAGE = 39
    DAC1_VOLTAGE = 40
    LED_ENABLE = 41
    LED_DISABLE = 42
    LED_STATE = 43
    LED0_MAX_CURRENT = 44
    LED1_MAX_CURRENT = 45
    PULSE_ENABLE = 46
    PULSE_DUTY_CYCLE_LED0 = 47
    PULSE_DUTY_CYCLE_LED1 = 48
    PULSE_FREQUENCY_LED0 = 49
    PULSE_FREQUENCY_LED1 = 50
    RAMP_LED0 = 51
    RAMP_LED1 = 52
    RAMP_CONFIG = 53
    ENABLE_EVENTS = 58


class CurrentDriver(Device):
    """
    CurrentDriver class for controlling the device.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect and load already happened in the base class
        # verify that WHO_AM_I matches the expected value
        if self.WHO_AM_I != 1282:
            self.disconnect()
            raise HarpException(f"WHO_AM_I mismatch: expected {1282}, got {self.WHO_AM_I}")

    def read_digital_input_state(self) -> DigitalInputs | None:
        """
        Reads the contents of the DigitalInputState register.

        Returns
        -------
        DigitalInputs | None
            Value read from the DigitalInputState register.
        """
        address = CurrentDriverRegisters.DIGITAL_INPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.DIGITAL_INPUT_STATE", reply)

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
        address = CurrentDriverRegisters.OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.OUTPUT_SET", reply)

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
        address = CurrentDriverRegisters.OUTPUT_SET
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.OUTPUT_SET", reply)

        return reply

    def read_output_clear(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputClear register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputClear register.
        """
        address = CurrentDriverRegisters.OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.OUTPUT_CLEAR", reply)

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
        address = CurrentDriverRegisters.OUTPUT_CLEAR
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.OUTPUT_CLEAR", reply)

        return reply

    def read_output_toggle(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputToggle register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputToggle register.
        """
        address = CurrentDriverRegisters.OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.OUTPUT_TOGGLE", reply)

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
        address = CurrentDriverRegisters.OUTPUT_TOGGLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.OUTPUT_TOGGLE", reply)

        return reply

    def read_output_state(self) -> DigitalOutputs | None:
        """
        Reads the contents of the OutputState register.

        Returns
        -------
        DigitalOutputs | None
            Value read from the OutputState register.
        """
        address = CurrentDriverRegisters.OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.OUTPUT_STATE", reply)

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
        address = CurrentDriverRegisters.OUTPUT_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.OUTPUT_STATE", reply)

        return reply

    def read_led0_current(self) -> float | None:
        """
        Reads the contents of the Led0Current register.

        Returns
        -------
        float | None
            Value read from the Led0Current register.
        """
        address = CurrentDriverRegisters.LED0_CURRENT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.LED0_CURRENT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_current(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Led0Current register.

        Parameters
        ----------
        value : float
            Value to write to the Led0Current register.
        """
        address = CurrentDriverRegisters.LED0_CURRENT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.LED0_CURRENT", reply)

        return reply

    def read_led1_current(self) -> float | None:
        """
        Reads the contents of the Led1Current register.

        Returns
        -------
        float | None
            Value read from the Led1Current register.
        """
        address = CurrentDriverRegisters.LED1_CURRENT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.LED1_CURRENT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_current(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Led1Current register.

        Parameters
        ----------
        value : float
            Value to write to the Led1Current register.
        """
        address = CurrentDriverRegisters.LED1_CURRENT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.LED1_CURRENT", reply)

        return reply

    def read_dac0_voltage(self) -> float | None:
        """
        Reads the contents of the Dac0Voltage register.

        Returns
        -------
        float | None
            Value read from the Dac0Voltage register.
        """
        address = CurrentDriverRegisters.DAC0_VOLTAGE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.DAC0_VOLTAGE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_dac0_voltage(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Dac0Voltage register.

        Parameters
        ----------
        value : float
            Value to write to the Dac0Voltage register.
        """
        address = CurrentDriverRegisters.DAC0_VOLTAGE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.DAC0_VOLTAGE", reply)

        return reply

    def read_dac1_voltage(self) -> float | None:
        """
        Reads the contents of the Dac1Voltage register.

        Returns
        -------
        float | None
            Value read from the Dac1Voltage register.
        """
        address = CurrentDriverRegisters.DAC1_VOLTAGE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.DAC1_VOLTAGE", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_dac1_voltage(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Dac1Voltage register.

        Parameters
        ----------
        value : float
            Value to write to the Dac1Voltage register.
        """
        address = CurrentDriverRegisters.DAC1_VOLTAGE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.DAC1_VOLTAGE", reply)

        return reply

    def read_led_enable(self) -> LedOutputs | None:
        """
        Reads the contents of the LedEnable register.

        Returns
        -------
        LedOutputs | None
            Value read from the LedEnable register.
        """
        address = CurrentDriverRegisters.LED_ENABLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.LED_ENABLE", reply)

        if reply is not None:
            return LedOutputs(reply.payload)
        return None

    def write_led_enable(self, value: LedOutputs) -> HarpMessage | None:
        """
        Writes a value to the LedEnable register.

        Parameters
        ----------
        value : LedOutputs
            Value to write to the LedEnable register.
        """
        address = CurrentDriverRegisters.LED_ENABLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.LED_ENABLE", reply)

        return reply

    def read_led_disable(self) -> LedOutputs | None:
        """
        Reads the contents of the LedDisable register.

        Returns
        -------
        LedOutputs | None
            Value read from the LedDisable register.
        """
        address = CurrentDriverRegisters.LED_DISABLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.LED_DISABLE", reply)

        if reply is not None:
            return LedOutputs(reply.payload)
        return None

    def write_led_disable(self, value: LedOutputs) -> HarpMessage | None:
        """
        Writes a value to the LedDisable register.

        Parameters
        ----------
        value : LedOutputs
            Value to write to the LedDisable register.
        """
        address = CurrentDriverRegisters.LED_DISABLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.LED_DISABLE", reply)

        return reply

    def read_led_state(self) -> LedOutputs | None:
        """
        Reads the contents of the LedState register.

        Returns
        -------
        LedOutputs | None
            Value read from the LedState register.
        """
        address = CurrentDriverRegisters.LED_STATE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.LED_STATE", reply)

        if reply is not None:
            return LedOutputs(reply.payload)
        return None

    def write_led_state(self, value: LedOutputs) -> HarpMessage | None:
        """
        Writes a value to the LedState register.

        Parameters
        ----------
        value : LedOutputs
            Value to write to the LedState register.
        """
        address = CurrentDriverRegisters.LED_STATE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.LED_STATE", reply)

        return reply

    def read_led0_max_current(self) -> float | None:
        """
        Reads the contents of the Led0MaxCurrent register.

        Returns
        -------
        float | None
            Value read from the Led0MaxCurrent register.
        """
        address = CurrentDriverRegisters.LED0_MAX_CURRENT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.LED0_MAX_CURRENT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led0_max_current(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Led0MaxCurrent register.

        Parameters
        ----------
        value : float
            Value to write to the Led0MaxCurrent register.
        """
        address = CurrentDriverRegisters.LED0_MAX_CURRENT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.LED0_MAX_CURRENT", reply)

        return reply

    def read_led1_max_current(self) -> float | None:
        """
        Reads the contents of the Led1MaxCurrent register.

        Returns
        -------
        float | None
            Value read from the Led1MaxCurrent register.
        """
        address = CurrentDriverRegisters.LED1_MAX_CURRENT
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.FLOAT, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.LED1_MAX_CURRENT", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_led1_max_current(self, value: float) -> HarpMessage | None:
        """
        Writes a value to the Led1MaxCurrent register.

        Parameters
        ----------
        value : float
            Value to write to the Led1MaxCurrent register.
        """
        address = CurrentDriverRegisters.LED1_MAX_CURRENT
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.FLOAT, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.LED1_MAX_CURRENT", reply)

        return reply

    def read_pulse_enable(self) -> LedOutputs | None:
        """
        Reads the contents of the PulseEnable register.

        Returns
        -------
        LedOutputs | None
            Value read from the PulseEnable register.
        """
        address = CurrentDriverRegisters.PULSE_ENABLE
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.PULSE_ENABLE", reply)

        if reply is not None:
            return LedOutputs(reply.payload)
        return None

    def write_pulse_enable(self, value: LedOutputs) -> HarpMessage | None:
        """
        Writes a value to the PulseEnable register.

        Parameters
        ----------
        value : LedOutputs
            Value to write to the PulseEnable register.
        """
        address = CurrentDriverRegisters.PULSE_ENABLE
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.PULSE_ENABLE", reply)

        return reply

    def read_pulse_duty_cycle_led0(self) -> int | None:
        """
        Reads the contents of the PulseDutyCycleLed0 register.

        Returns
        -------
        int | None
            Value read from the PulseDutyCycleLed0 register.
        """
        address = CurrentDriverRegisters.PULSE_DUTY_CYCLE_LED0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.PULSE_DUTY_CYCLE_LED0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_duty_cycle_led0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseDutyCycleLed0 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseDutyCycleLed0 register.
        """
        address = CurrentDriverRegisters.PULSE_DUTY_CYCLE_LED0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.PULSE_DUTY_CYCLE_LED0", reply)

        return reply

    def read_pulse_duty_cycle_led1(self) -> int | None:
        """
        Reads the contents of the PulseDutyCycleLed1 register.

        Returns
        -------
        int | None
            Value read from the PulseDutyCycleLed1 register.
        """
        address = CurrentDriverRegisters.PULSE_DUTY_CYCLE_LED1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.PULSE_DUTY_CYCLE_LED1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_duty_cycle_led1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseDutyCycleLed1 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseDutyCycleLed1 register.
        """
        address = CurrentDriverRegisters.PULSE_DUTY_CYCLE_LED1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.PULSE_DUTY_CYCLE_LED1", reply)

        return reply

    def read_pulse_frequency_led0(self) -> int | None:
        """
        Reads the contents of the PulseFrequencyLed0 register.

        Returns
        -------
        int | None
            Value read from the PulseFrequencyLed0 register.
        """
        address = CurrentDriverRegisters.PULSE_FREQUENCY_LED0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.PULSE_FREQUENCY_LED0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_frequency_led0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseFrequencyLed0 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseFrequencyLed0 register.
        """
        address = CurrentDriverRegisters.PULSE_FREQUENCY_LED0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.PULSE_FREQUENCY_LED0", reply)

        return reply

    def read_pulse_frequency_led1(self) -> int | None:
        """
        Reads the contents of the PulseFrequencyLed1 register.

        Returns
        -------
        int | None
            Value read from the PulseFrequencyLed1 register.
        """
        address = CurrentDriverRegisters.PULSE_FREQUENCY_LED1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.PULSE_FREQUENCY_LED1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_pulse_frequency_led1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the PulseFrequencyLed1 register.

        Parameters
        ----------
        value : int
            Value to write to the PulseFrequencyLed1 register.
        """
        address = CurrentDriverRegisters.PULSE_FREQUENCY_LED1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.PULSE_FREQUENCY_LED1", reply)

        return reply

    def read_ramp_led0(self) -> int | None:
        """
        Reads the contents of the RampLed0 register.

        Returns
        -------
        int | None
            Value read from the RampLed0 register.
        """
        address = CurrentDriverRegisters.RAMP_LED0
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.RAMP_LED0", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_ramp_led0(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the RampLed0 register.

        Parameters
        ----------
        value : int
            Value to write to the RampLed0 register.
        """
        address = CurrentDriverRegisters.RAMP_LED0
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.RAMP_LED0", reply)

        return reply

    def read_ramp_led1(self) -> int | None:
        """
        Reads the contents of the RampLed1 register.

        Returns
        -------
        int | None
            Value read from the RampLed1 register.
        """
        address = CurrentDriverRegisters.RAMP_LED1
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U16, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.RAMP_LED1", reply)

        if reply is not None:
            # Directly return the payload as it is a primitive type
            return reply.payload
        return None

    def write_ramp_led1(self, value: int) -> HarpMessage | None:
        """
        Writes a value to the RampLed1 register.

        Parameters
        ----------
        value : int
            Value to write to the RampLed1 register.
        """
        address = CurrentDriverRegisters.RAMP_LED1
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U16, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.RAMP_LED1", reply)

        return reply

    def read_ramp_config(self) -> LedRamps | None:
        """
        Reads the contents of the RampConfig register.

        Returns
        -------
        LedRamps | None
            Value read from the RampConfig register.
        """
        address = CurrentDriverRegisters.RAMP_CONFIG
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.RAMP_CONFIG", reply)

        if reply is not None:
            return LedRamps(reply.payload)
        return None

    def write_ramp_config(self, value: LedRamps) -> HarpMessage | None:
        """
        Writes a value to the RampConfig register.

        Parameters
        ----------
        value : LedRamps
            Value to write to the RampConfig register.
        """
        address = CurrentDriverRegisters.RAMP_CONFIG
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.RAMP_CONFIG", reply)

        return reply

    def read_enable_events(self) -> CurrentDriverEvents | None:
        """
        Reads the contents of the EnableEvents register.

        Returns
        -------
        CurrentDriverEvents | None
            Value read from the EnableEvents register.
        """
        address = CurrentDriverRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.READ, PayloadType.U8, address))
        if reply is not None and reply.is_error:
            raise HarpReadException("CurrentDriverRegisters.ENABLE_EVENTS", reply)

        if reply is not None:
            return CurrentDriverEvents(reply.payload)
        return None

    def write_enable_events(self, value: CurrentDriverEvents) -> HarpMessage | None:
        """
        Writes a value to the EnableEvents register.

        Parameters
        ----------
        value : CurrentDriverEvents
            Value to write to the EnableEvents register.
        """
        address = CurrentDriverRegisters.ENABLE_EVENTS
        reply = self.send(HarpMessage(MessageType.WRITE, PayloadType.U8, address, value))
        if reply is not None and reply.is_error:
            raise HarpWriteException("CurrentDriverRegisters.ENABLE_EVENTS", reply)

        return reply

