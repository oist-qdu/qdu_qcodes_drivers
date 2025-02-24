# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 17:03:05 2024

@author: Misha@QDU OIST
@email: m.belianchikov@oist.jp
"""

import logging
import re
from collections import OrderedDict

from typing import Any, Callable, Dict, Optional
from pyvisa.resources.serial import SerialInstrument

from qcodes.instrument import ChannelList, InstrumentChannel, VisaInstrument
from qcodes.validators import Numbers

logger = logging.getLogger()


def _I_parser(val: str) -> float:
    """
    remove 'mA characters from the end of responce and convert it to float
    """
    return (lambda ma: float(ma) / 1000)(float(re.sub(r'mA', '', val)))


class StahlChannel(InstrumentChannel):
    """
    A Stahl source channel

    Args:
        parent
        name
        channel_number
    """

    acknowledge_reply = chr(6)  #'\x06' acknolage responce symbol

    def __init__(self, parent: VisaInstrument, name: str, channel_number: int):
        super().__init__(parent, name)
        
        self.ch_name = name
        self._channel_string = f"{channel_number:02d}"
        self._channel_number = channel_number

        self.add_parameter('voltage',
                           label=f"{self.ch_name} Voltage",
                           get_cmd=self._get_voltage,
                           get_parser=float,
                           set_cmd=self._set_voltage,
                           unit='V',
                           vals=Numbers(min_value=-10.00, max_value=10.00))

        self.add_parameter('current',
                           get_cmd=f"{self.parent.identifier} I{self._channel_string}",
                           get_parser=_I_parser,
                           unit='A')


    def _get_voltage(self) -> float:
        get_raw = self.ask_raw(f"{self.parent.identifier} V{self._channel_string}")
        return round((float(get_raw)-0.5)*2*(self.parent.voltage_range),6)



    def _set_voltage(self, voltage: float) -> None:
        set_voltage = voltage/(2*self.parent.voltage_range)+0.5
        response = self.ask_raw(f"{self.parent.identifier} CH{self._channel_string} {set_voltage:.6f}")
        if response != self.acknowledge_reply:
            self.log.warning("Didn't recieve an acknowledge reply")




    def ramp(self, ramp_to: float, step: float, delay: float) -> None:
        saved_step = self.voltage.step
        saved_inter_delay = self.voltage.inter_delay

        self.voltage.step = step
        self.voltage.inter_delay = delay
        
        self.ask(f"{self.parent.identifier} DIS L{self._channel_string} {self.ch_name} ramp  {ramp_to:.4f}V")
        
        self.voltage(ramp_to)
        
        self.ask(f"{self.parent.identifier} DIS L{self._channel_string} {self.ch_name} set  {ramp_to:.4f}V")

        self.voltage.step = saved_step
        self.voltage.inter_delay = saved_inter_delay



class HV324(VisaInstrument):

    def __init__(self, name: str, address: str, ch_names: dict = None,  **kwargs: Any):
        super().__init__(name, address, terminator="\r", **kwargs)
        assert isinstance(self.visa_handle, SerialInstrument)
        
        self.visa_handle.baud_rate = 115200

        instrument_info = self.parse_idn_string(
            self.ask_raw("IDN")
        )

        for key, value in instrument_info.items():
            setattr(self, key, value)

        self.ask(f"{self.model}{self.serial_number} DIS AUTO 0")

        channels = ChannelList(
            self, "channel", StahlChannel, snapshotable=True
        )

        for channel_number in range(1, self.n_channels + 1):
            if isinstance(ch_names, dict):
                if channel_number in ch_names.keys():
                    name = ch_names[channel_number]
                else: 
                    name = f"ch{channel_number:02d}"
            else: 
                name = f"ch{channel_number:02d}"
            channel = StahlChannel(
                self,
                name,
                channel_number
            )
            self.add_submodule(name, channel)
            channels.append(channel)
            self.ask(f"{self.model}{self.serial_number} DIS L{channel_number:02d} {name}")

        self.add_submodule("channel", channels)
        self.connect_message()






    @staticmethod
    def parse_idn_string(idn_string: str) -> Dict[str, Any]:

        result = re.search(
            r"(HV|BS)(\d{3}) (\d{3}) (\d{2}) ([buqsm])",
            idn_string
        )

        if result is None:
            raise RuntimeError(
                "Unexpected instrument response. Perhaps the model of the "
                "instrument does not match the drivers expectation or a "
                "firmware upgrade has taken place. Please get in touch "
                "with Misha"
            )

        converters: Dict[str, Callable[..., Any]] = OrderedDict({
            "model": str,
            "serial_number": str,
            "voltage_range": float,
            "n_channels": int,
            "output_type": {
                "b": "bipolar",
                "u": "unipolar",
                "q": "quadrupole",
                "s": "steerer",
                "m": "bipolar milivolt"
            }.get
        })

        return {
            name: converter(value)
            for (name, converter), value in zip(converters.items(), result.groups())
        }

    def get_idn(self) -> Dict[str, Optional[str]]:
        """
        The Stahl sends a uncommon IDN string which does not include a
        firmware version.
        """
        return {
            "vendor": "Stahl",
            "model": self.model,
            "serial": self.serial_number,
            "firmware": None
        }


    @property
    def identifier(self) -> str:
        return f"{self.model}{self.serial_number}"