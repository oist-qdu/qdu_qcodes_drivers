# -*- coding: utf-8 -*-
from qcodes import VisaInstrument
from qcodes.utils.validators import Numbers


class MG3692(VisaInstrument):
    """
    This is the qcodes driver for Anritsu scalar RF sources.
    UNDER DEVELOPMENT bradmitchell@berkeley.edu
    """

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)

        self.add_parameter('power',
                           label='Power',
                           get_cmd='OL0',
                           get_parser=float,
                           set_cmd='L0 {:.2f} DM',
                           unit='dBm',
                           vals=Numbers(min_value=-130, max_value=19))


        self.add_parameter('frequency',
                           label='Frequency',
                           get_cmd='OF0',
                           get_parser=float,
                           set_cmd='CF0 {:.6f} MH',
                           unit='MHz',
                           vals=Numbers(min_value=24e3, max_value=240e3))


        self.add_parameter('rf_output',
                           set_cmd='RF{}',
                           val_mapping={'on': 1, 'off': 0})

        
        self.add_parameter('fm_dev',
                           label='Frequency',
                           get_cmd='OFD',
                           get_parser=float,
                           set_cmd='FDV {:.6f} MH',
                           unit='MHz')

        self.add_parameter('fm_rate',
                           label='Frequency',
                           get_cmd='OFR',
                           get_parser=float,
                           set_cmd='FMR {:.6f} MH',
                           unit='MHz')


        self.connect_message()

    def get_idn(self):
        IDN = self.ask_raw('*IDN?')
        vendor, model, serial, firmware = map(str.strip, IDN.split(','))
        IDN = {'vendor': vendor, 'model': model,
               'serial': serial, 'firmware': firmware}
        return IDN
