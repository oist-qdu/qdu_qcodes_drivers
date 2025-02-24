# -*- coding: utf-8 -*-
import numpy as np
from typing import Any, Tuple

from qcodes import VisaInstrument
from qcodes.utils.validators import Numbers, Enum, Arrays



class LI5640(VisaInstrument):
    """
    This is the qcodes driver for NF LI5640 Lock-In amplifier.
    UNDER DEVELOPMENT m.belianchikov@oist.jp
    """

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)


        self.add_parameter(name='R',
                           label='Magnitude',
                           get_cmd='OTYP 1; DOUT?',
                           get_parser=float,
                           unit='V')

        self.add_parameter(name='T',
                           label='Phase',
                           get_cmd='OTYP 2; DOUT?',
                           get_parser=float,
                           unit='V')

        self.add_parameter(name='get_data',
                           label='lock-In data',
                           get_cmd=self._fetch_data,
                           vals=Arrays(shape=(2,)))

        self.add_parameter(name='amplitude',
                           label='osc out amplitude',
                           get_cmd=self.get_amp,
                           set_cmd='AMPL {},0',
                           unit='V')

        self.connect_message()

    def get_amp(self):
        amp_string = self.ask_raw('AMPL?')
        amp, range  = map(str.strip, amp_string.split(','))
        return amp, range

    def _fetch_data(self)-> np.array:
        output = self.ask_raw('OTYP 1,2; DOUT?')
        return np.array([float(val) for val in output.split(',')])

    def check_error(self, ret_code: int) -> None:
        """
        Default error checking, raises an error if return code ``!=0``.
        Does not differentiate between warnings or specific error messages.
        Override this function in your driver if you want to add specific
        error messages.

        Args:
            ret_code: A Visa error code. See eg:
                https://github.com/hgrecco/pyvisa/blob/master/pyvisa/errors.py

        Raises:
            visa.VisaIOError: if ``ret_code`` indicates a communication
                problem.
        """
        if ret_code != 0:
            raise visa.VisaIOWarning(ret_code)
