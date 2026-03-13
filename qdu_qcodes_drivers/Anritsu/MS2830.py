# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 18:21:54 2024

@author: QDUnit
"""
import numpy as np
from qcodes import VisaInstrument
from qcodes.validators import Arrays, Enum, Ints, Numbers

from qcodes.parameters import (
    Parameter,
    ParameterWithSetpoints,
    ParamRawDataType,
    create_on_off_val_mapping,
    ParameterWithSetpoints
)


class GeneratedSetPoints(Parameter):
    """
    A parameter that generates a setpoint array from start, stop and num points
    parameters.
    """

    def __init__(self, startparam, stopparam, numpointsparam, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._startparam = startparam
        self._stopparam = stopparam
        self._numpointsparam = numpointsparam

    def get_raw(self):
        return np.linspace(self._startparam(), self._stopparam(),
                              self._numpointsparam())


class DataArray(ParameterWithSetpoints):

    def get_raw(self):
        trac_raw = self.instrument.ask("TRAC? TRAC1")
        trac = np.fromstring(trac_raw, dtype=float, sep=',')
        return trac



class MS2830(VisaInstrument):


    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)


        self._min_freq = 9e3
        self._max_freq = 26.5e9
        
        self.add_parameter(
            name="start",
            unit="Hz",
            get_cmd=":SENSe:FREQuency:STARt?",
            set_cmd=self._set_start,
            get_parser=float,
            vals=Numbers(self._min_freq, self._max_freq - 10),
            docstring="start frequency for the sweep",
        )

        self.add_parameter(
            name="stop",
            unit="Hz",
            get_cmd=":SENSe:FREQuency:STOP?",
            set_cmd=self._set_stop,
            get_parser=float,
            vals=Numbers(self._min_freq + 10, self._max_freq),
            docstring="stop frequency for the sweep",
        )


        self.add_parameter(
            name="center",
            unit="Hz",
            get_cmd=":SENSe:FREQuency:CENTer?",
            set_cmd=self._set_center,
            get_parser=float,
            vals=Numbers(self._min_freq + 5, self._max_freq - 5),
            docstring="Sets and gets center frequency",
        )



        self.add_parameter(
            name="span",
            unit="Hz",
            get_cmd=":SENSe:FREQuency:SPAN?",
            set_cmd=self._set_span,
            get_parser=float,
            vals=Numbers(10, self._max_freq - self._min_freq),
            docstring="Changes span of frequency",
        )

        self.add_parameter(
            name="npts",
            get_cmd=":SENSe:SWEep:POINts?",
            set_cmd=self._set_npts,
            get_parser=int,
            vals=Ints(1, 20001),
            docstring="Number of points for the sweep",
        )

        self.add_parameter(
            name="average",
            get_cmd=":SENSe:AVERage:COUNt?",
            set_cmd=":SENSe:AVERage:COUNt {}",
            get_parser=int,
            docstring="trave average number",
        )

        self.add_parameter(
            name="RBW",
            get_cmd=":BAND?",
            set_cmd=":BAND {}",
            get_parser=int,
            docstring="trave average number",
        )

        self.add_parameter(
            name="cont_meas",
            get_cmd=":INITiate:CONTinuous?",
            set_cmd=self._enable_cont_meas,
            val_mapping=create_on_off_val_mapping(on_val="ON", off_val="OFF"),
            docstring="Enables or disables continuous measurement.",
        )


        self.add_parameter(
            name="single",
#            get_cmd=":INITiate:SWP?",
            set_cmd=self._ini_sweep,
            docstring="Sets the sweep mode to Single and starts the single sweep.",
        )


        self.add_parameter(
            name="marker1X",
            get_cmd=":CALCulate:MARKer1:X?",
            set_cmd=":CALCulate:MARKer1:X {}",
            get_parser=float,
            unit="Hz",
            docstring="marker 1, frequency.",
        )

        self.add_parameter(
            name="marker2X",
            get_cmd=":CALCulate:MARKer2:X?",
            set_cmd=":CALCulate:MARKer2:X {}",
            get_parser=float,
            unit="Hz",
            docstring="marker 2, frequency.",
        )

        self.add_parameter(
            name="marker3X",
            get_cmd=":CALCulate:MARKer3:X?",
            set_cmd=":CALCulate:MARKer3:X {}",
            get_parser=float,
            unit="Hz",
            docstring="marker 3, frequency.",
        )

        self.add_parameter(
            name="marker1Y",
            get_cmd=":CALCulate:MARKer1:Y?",
            get_parser=float,
            unit="Hz",
            docstring="marker 1, Y.",
        )

        self.add_parameter(
            name="marker2Y",
            get_cmd=":CALCulate:MARKer2:Y?",
            get_parser=float,
            unit="V",
            docstring="marker 2, Y.",
        )

        self.add_parameter(
            name="marker3Y",
            get_cmd=":CALCulate:MARKer3:Y?",
            get_parser=float,
            unit="V",
            docstring="marker 3, Y.",
        )

        self.add_parameter('freq_axis',
            unit='Hz',
            label='Freq Axis',
            parameter_class=GeneratedSetPoints,
            startparam=self.start,
            stopparam=self.stop,
            numpointsparam=self.npts,
            vals=Arrays(shape=(self.npts.get_latest,)))

        self.add_parameter('spectrum',
            unit='dBm',
            setpoints=(self.freq_axis,),
            label='Spectrum',
            parameter_class=DataArray,
            vals=Arrays(shape=(self.npts.get_latest,)))


        self.connect_message()


    def _set_start(self, val: float) -> None:
        """
        Sets start frequency
        """
        stop = self.stop()
        if val >= stop:
            raise ValueError(
                f"Start frequency must be smaller than stop "
                f"frequency. Provided start freq is: {val} Hz and "
                f"set stop freq is: {stop} Hz"
            )

        self.write(f":SENSe:FREQuency:STARt {val}")

        start = self.start()
        if abs(val - start) >= 1:
            self.log.warning(f"Could not set start to {val} setting it to {start}")

    def _set_stop(self, val: float) -> None:
        """
        Sets stop frequency
        """
        start = self.start()
        if val <= start:
            raise ValueError(
                f"Stop frequency must be larger than start "
                f"frequency. Provided stop freq is: {val} Hz and "
                f"set start freq is: {start} Hz"
            )
    def _set_center(self, val: float) -> None:
        """
        Sets center frequency and updates start and stop frequencies if they
        change.
        """
        self.write(f":SENSe:FREQuency:CENTer {val}")
        self.update_trace()
        
    def _set_span(self, val: float) -> None:
        """
        Sets frequency span and updates start and stop frequencies if they
        change.
        """
        self.write(f":SENSe:FREQuency:SPAN {val}")
        self.update_trace()


    def update_trace(self) -> None:
        """
        Updates start and stop frequencies whenever span of/or center frequency
        is updated.
        """
        self.start()
        self.stop()


    def _set_npts(self, val: int) -> None:
        """
        Sets number of points for sweep
        """
        self.write(f":SENSe:SWEep:POINts {val}")


    def _enable_cont_meas(self, val: str) -> None:
        """
        Sets continuous measurement to ON or OFF.
        """
        self.write(f":INITiate:CONTinuous {val}")
        
        
    def _ini_sweep(self, val: int) -> None:
        """
        """
        self.write(f":SENSe:AVERage:COUNt {val}")
        self.write("TRAC1:STOR:MODE AVER")
        self.ask(":INITiate:SWP\n*WAI\n:INITiate:SWP?")