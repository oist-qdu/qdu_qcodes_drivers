import numpy as np
from qcodes.instrument import (
    Instrument,
    VisaInstrument,
    InstrumentChannel,
    ChannelList,
)
from qcodes.utils import validators as vals


##################################################
#
# MODEL DEPENDENT SETTINGS

_chan_amps = {'31252': 2.0}



class AFGChannel(InstrumentChannel):
    """
    Class to hold a channel of the AFG.
    """

    def __init__(self, parent: Instrument, name: str, channel: str) -> None:
        """
        Args:
        Args:
            parent: The Instrument instance to which the channel is
                to be attached.
            name: The name used in the DataSet
            channel: The channel number, either 1 or 2.
        """

        super().__init__(parent, name)

        self.model = self._parent.model
        self.channel = channel
        num_channels = self._parent.num_channels


        if channel not in list(range(1, num_channels+1)):
            raise ValueError('Illegal channel value.')


        ##################################################
        # CHANNEL PARAMETERS

        self.add_parameter('state',
                           label=f'Channel {channel} state',
                           get_cmd=f'OUTPut{channel}:STATe?',
                           set_cmd=f'OUTPut{channel}:STATe {{}}',
                           vals=vals.Ints(0, 1),
                           get_parser=int)

        self.add_parameter('amplitude',
                           label=f'Channel {channel} amplitude',
                           get_cmd=f'SOURce{channel}:VOLTage:LEVel:IMMediate:AMPLitude?',
                           set_cmd=f'SOURce{channel}:VOLTage:LEVel:IMMediate:AMPLitude {{}}',
                           unit='V',
                           vals=vals.Numbers(0, _chan_amps[self.model]),
                           get_parser=float)

        self.add_parameter('offset',
                           label=f'Channel {channel} offset',
                           get_cmd=f'SOURce{channel}:VOLTage:LEVel:IMMediate:OFFSet?',
                           set_cmd=f'SOURce{channel}:VOLTage:LEVel:IMMediate:OFFSet {{}}',
                           unit='V',
                           vals=vals.Numbers(0, _chan_amps[self.model]),
                           get_parser=float)

        self.add_parameter('type',
                           label=f'Channel {channel} type',
                           get_cmd=f'SOURce{channel}:FUNCtion:SHAPe?',
                           set_cmd=f'SOURce{channel}:FUNCtion:SHAPe {{}}',
                           val_mapping={'SINE': 'SIN',
                                        'SQUARE': 'SQU',
                                        'PULSE': 'PULS',
                                        'RAMP': 'RAMP',
                                        'NOISE': 'PRN',
                                        'DC': 'DC',
                                        'SINC': 'SINC',
                                        'GAUSS': 'GAUS',
                                        'LORENTZ': 'LOR',
                                        'ERISE': 'ERIS',
                                        'EDECAY': 'EDEC',
                                        'HAVERSINE': 'HAV'})

        self.add_parameter('pulse_period',
                           label=f'Channel {channel} pulse period',
                           get_cmd=f'SOURce{channel}:PULSe:PERiod?',
                           set_cmd=f'SOURce{channel}:PULSe:PERiod {{}}',
                           unit='s',
                           get_parser=float)

        self.add_parameter('pulse_width',
                           label=f'Channel {channel} pulse width',
                           get_cmd=f'SOURce{channel}:PULSe:WIDTh?',
                           set_cmd=f'SOURce{channel}:PULSe:WIDTh {{}}',
                           unit='s',
                           get_parser=float)

        self.add_parameter('cw_freq',
                           label=f'Channel {channel} cw frequency',
                           get_cmd=f'SOURce{channel}:FREQuency:CW?',
                           set_cmd=f'SOURce{channel}:FREQuency:CW {{}}',
                           unit='Hz',
                           get_parser=float)

class AFG31000(VisaInstrument):
    """
    This is the qcodes driver for the Textronix_31000 AWG generator
    """

    def __init__(self, name: str, address: str, **kwargs) -> None:
        """
        Args:
            name: Name to use internally in QCoDeS
            address: VISA ressource address
        """
        super().__init__(name, address, terminator="\n", **kwargs)
        num_channels = 2
        self.num_channels = num_channels
        self.model = self.IDN()['model'][3:]

        if self.model!='31252':
            raise ValueError('Unknown model type: {}. Are you using '
                             'the right driver for your instrument?'
                             ''.format(self.model))

        # Add the channel to the instrument
        for ch_num in range(1, num_channels+1):
            ch_name = f'ch{ch_num}'
            channel = AFGChannel(self, ch_name, ch_num)
            self.add_submodule(ch_name, channel)


        self.connect_message()
