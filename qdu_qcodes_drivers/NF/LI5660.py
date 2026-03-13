# -*- coding: utf-8 -*-
import numpy as np
from typing import Any, Tuple

from qcodes import VisaInstrument
from qcodes.utils.validators import Numbers, Enum, Arrays



class LI5660(VisaInstrument):
    """
    This is the qcodes driver for NF LI5660 Lock-In amplifier.
    UNDER DEVELOPMENT m.belianchikov@oist.jp
    """

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)


        self.add_parameter('osc_frequency',
                           label='OSC Frequency',
                           get_cmd='SOUR:FREQ?',
                           get_parser=float,
                           set_cmd='SOUR:FREQ {:.4f}',
                           unit='Hz',
                           vals=Numbers(min_value=5e-1, max_value=11e6))

        self.add_parameter('mod_frequency',
                           label='Modulation Frequency',
                           get_cmd='SENS:FREQ?',
                           get_parser=float,
                           unit='Hz',
                           vals=Numbers(min_value=5e-1, max_value=11e6))

        self.add_parameter('osc_amplitude',
                           label='OSC Amplitude',
                           get_cmd='SOUR:VOLT?',
                           get_parser=float,
                           set_cmd='SOUR:VOLT {:.3f}',
                           unit='V',
                           vals=Numbers(min_value=0.00, max_value=1.000))

        self.add_parameter(name='slope',
                           label='Filter slope',
                           unit='dB/oct',
                           get_cmd=':FILT:SLOP?',
                           set_cmd=':FILT:SLOP {}',
                           vals= Enum(6, 12, 18, 24, 30))

        self.add_parameter(name='tc',
                           label='Filter timeconstant',
                           unit='s',
                           get_cmd=':FILT:TCON?',
                           set_cmd=':FILT:TCON {}',
                           vals=Numbers(min_value=1e-6, max_value=50e3))

        self.add_parameter(name='R',
                           label='Magnitude',
                           get_cmd=self._fetch_R,
                           get_parser=float,
                           unit='V')

        self.add_parameter(name='T',
                           label='Phase',
                           get_cmd=self._fetch_T,
                           get_parser=float,
                           unit='deg')

        self.add_parameter(name='X',
                           label='in-phase',
                           get_cmd=self._fetch_X,
                           get_parser=float,
                           unit='V')

        self.add_parameter(name='Y',
                           label='out-phase',
                           get_cmd=self._fetch_Y,
                           get_parser=float,
                           unit='V')

        self.add_parameter(name='get_data',
                           label='lock-In data',
                           get_cmd=self._fetch_data,
                           vals=Arrays(shape=(2,)))

        self.add_parameter('output_config',
                           label='Output config',
                           get_cmd=':DATA?',
                           set_cmd='DATA {}',
                           val_mapping={
                            "R,T": 6,
                            "X,Y": 24,
                            "R,T,X,Y": 30})

        self.connect_message()



    def _fetch_data(self)-> np.array:
        output = self.ask_raw(':FETC?')
        return np.array([float(val) for val in output.split(',')])


    def _fetch_R(self)-> float:
        output = self.ask_raw(':FETC?')
        return float(output.split(',')[0])

    def _fetch_T(self)-> float:
        output = self.ask_raw(':FETC?')
        return float(output.split(',')[1])

    def _fetch_X(self)-> float:
        output = self.ask_raw(':FETC?')
        return float(output.split(',')[2])

    def _fetch_Y(self)-> float:
        output = self.ask_raw(':FETC?')
        return float(output.split(',')[3])

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
