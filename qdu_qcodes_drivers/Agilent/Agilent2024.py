from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

from qcodes.instrument import (
    ChannelList,
    InstrumentBaseKWArgs,
    InstrumentChannel,
    VisaInstrument,
    VisaInstrumentKWArgs,
)
from qcodes.parameters import ParameterWithSetpoints
from qcodes.validators import Arrays, Enum, Numbers


class Agilent2024Channel(InstrumentChannel):

    def __init__(
        self,
        parent:  VisaInstrument,
        name: str,
        channel: int,
        **kwargs: "Unpack[InstrumentBaseKWArgs]",
    ) -> None:
        super().__init__(parent, name, **kwargs)

        self.channel = channel

        self.add_parameter(
            "vertical_scale",
            label=f"Channel {channel} vertical scale",
            unit="V/div",
            get_cmd=f":CHANnel{channel}:SCALe?",
            set_cmd=f":CHANnel{channel}:SCALe {{}}",
            get_parser=float,
            vals=Numbers(min_value=0),
        )
        """Parameter vertical_scale"""

        self.add_parameter(
            "vertical_offset",
            label=f"Channel {channel} vertical offset",
            unit="V",
            get_cmd=f":CHANnel{channel}:OFFSet?",
            set_cmd=f":CHANnel{channel}:OFFSet {{}}",
            get_parser=float,
        )

        self.add_parameter(
            "trace",
            get_cmd=self._get_full_trace,
            vals=Arrays(shape=(self.parent.waveform_npoints,)),
            setpoints=(self.parent.time_axis,),
            unit="V",
            parameter_class=ParameterWithSetpoints,
            snapshot_value=False,
        )
        """Parameter trace"""

    def _get_full_trace(self) -> npt.NDArray:

        self.parent.data_source(f"ch{self.channel}")
        y_ori = self.parent.waveform_yorigin()
        y_increm = self.parent.waveform_yincrem()
        y_ref = self.parent.waveform_yref()
        y_raw = self._get_raw_trace()
#        y_raw_shifted = y_raw - y_ori - y_ref
        full_data = np.multiply(y_raw - y_ref, y_increm) + y_ori
        return full_data

    def _get_raw_trace(self) -> npt.NDArray:
        # set the out type from oscilloscope channels to WORD
        self.parent.write(":WAVeform:FORMat WORD")

        # set the channel from where data will be obtained


        # Obtain the trace
        raw_trace_val = self.parent.visa_handle.query_binary_values(
            "WAV:DATA?", datatype="H", is_big_endian=True
        )
        return np.array(raw_trace_val)


class Agilent2024(VisaInstrument):
    """
    The QCoDeS drivers for Oscilloscope DSO-X Agilent 2024A.

    """

    default_terminator = "\n"
    default_timeout = 5

    def __init__(
        self,
        name: str,
        address: str,
        **kwargs: "Unpack[VisaInstrumentKWArgs]",
    ):
        super().__init__(name, address, **kwargs)

        self.add_parameter(
            "waveform_xorigin",
            get_cmd="WAVeform:XORigin?",
            unit="s",
            get_parser=float
        )
        """Parameter waveform_xorigin"""

        self.add_parameter(
            "waveform_xincrem",
            get_cmd=":WAVeform:XINCrement?",
            unit="s",
            get_parser=float,
        )
        """Parameter waveform_xincrem"""

        self.add_parameter(
            "waveform_npoints",
            get_cmd="WAV:POIN?",
            set_cmd="WAV:POIN {}",
            get_parser=int,
        )
        """Parameter waveform_npoints"""

        self.add_parameter(
            "waveform_yorigin",
            get_cmd="WAVeform:YORigin?",
            unit="V",
            get_parser=float
        )
        
        """Parameter waveform_yorigin"""

        self.add_parameter(
            "waveform_yincrem",
            get_cmd=":WAVeform:YINCrement?",
            unit="V",
            get_parser=float,
        )
        """Parameter waveform_yincrem"""

        self.add_parameter(
            "waveform_yref",
            get_cmd=":WAVeform:YREFerence?",
            get_parser=float
        )
        """Parameter waveform_yref"""

        self.add_parameter(
            "trigger_mode",
            get_cmd=":TRIGger:MODE?",
            set_cmd=":TRIGger:MODE {}",
            val_mapping={
                "edge": "EDGE",
                "pulse_width": "GLIT",
                "pattern": "PATT",
                "video": "TV",
            },
        )
        """Parameter trigger_mode"""

        # trigger source
        self.add_parameter(
            "trigger_edge_level",
            unit="V",
            get_cmd=":TRIGger:EDGE:LEVel?",
            set_cmd=":TRIGger:EDGE:LEVel {}",
            get_parser=float,
            vals=Numbers(),
        )
        """Parameter trigger_level"""

        self.add_parameter(
            "trigger_edge_source",
            label="Source channel for the edge trigger",
            get_cmd=":TRIGger:EDGE:SOURce?",
            set_cmd=":TRIGger:EDGE:SOURce {}",
            val_mapping={
                "ch1": "CHAN1",
                "ch2": "CHAN2",
                "ch3": "CHAN3",
                "ch4": "CHAN4",
            },
        )
        """Parameter trigger_edge_source"""

        self.add_parameter(
            "trigger_edge_slope",
            label="Slope of the edge trigger",
            get_cmd=":TRIGger:EDGE:SLOPe?",
            set_cmd=":TRIGger:EDGE:SLOPe {}",
            val_mapping={
                "positive": "POS",
                "negative": "NEG",
                "either": "EITH",
                "alternate": "ALT",
            },
        )
        """Parameter trigger_edge_slope"""

        self.add_parameter(
            "data_source",
            label="Waveform Data source",
            get_cmd=":WAVeform:SOURce?",
            set_cmd=":WAVeform:SOURce {}",
            val_mapping={
                "ch1": "CHAN1",
                "ch2": "CHAN2",
                "ch3": "CHAN3",
                "ch4": "CHAN4",
            },
        )
        """Parameter data_source"""

        self.add_parameter(
            "time_axis",
            unit="s",
            label="Time",
            set_cmd=False,
            get_cmd=self._get_time_axis,
            vals=Arrays(shape=(self.waveform_npoints,)),
            snapshot_value=False,
        )


        self.add_parameter(
            "time_scale",
            label="Time scale",
            unit="s/div",
            get_cmd=":TIMebase:SCALe?",
            set_cmd=":TIMebase:SCALe {}",
            get_parser=float,
            vals=Numbers(min_value=0),
        )

        self.add_parameter(
            "time_position",
            label="Time position",
            unit="s",
            get_cmd=":TIMebase:POSition?",
            set_cmd=":TIMebase:POSition {}",
            get_parser=float,
        )
        """Parameter time_axis"""

        
        for channel_number in range(1, 5):
            channel = Agilent2024Channel(self, f"ch{channel_number}", channel_number)
            self.add_submodule(f"ch{channel_number}", channel)


        self.connect_message()
        

    def _get_time_axis(self) -> npt.NDArray:
        xorigin = self.waveform_xorigin()
        xincrem = self.waveform_xincrem()
        npts = self.waveform_npoints()
        xdata = xorigin + np.arange(npts) * xincrem
        return xdata

    def _get_trigger_level(self) -> str:
        trigger_level = self.ask(f":TRIGger:{self.trigger_mode()}:LEVel?")
        return trigger_level

    def _set_trigger_level(self, value: str) -> None:
        self.write(f":TRIGger:{self.trigger_mode()}:LEVel {value}")

    def run(self) -> None:
        self.write(":RUN")

    def stop(self) -> None:
        self.write(":STOP")

    def single(self) -> None:
        self.write(":SINGle")

    def digitize(self, channel: int | None = None) -> None:
        if channel is None:
            self.write(":DIGitize")
            return
        if channel in (1, 2, 3, 4):
            self.write(f":DIGitize CHANnel{channel}")

    def force_trigger(self) -> None:
        self.write(":TRIGger:FORCe")