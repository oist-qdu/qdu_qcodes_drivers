from qcodes import VisaInstrument

class AH2500A(VisaInstrument):
    """
    This is the qcodes driver for Andeen-Hagerling AH2500A capacitance bridge.
    """

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)


        self.add_parameter('mode',
                           label='measurement mode',
                           set_cmd='{}',
                           val_mapping={
                            "single": 'SINGLE',
                            "cont": 'CONTINUOUS'})

        self.add_parameter(name='C',
                           label='Capacitance',
                           get_cmd=self._fetch_C,
                           get_parser=float,
                           unit='pF')



        self.connect_message()

    def _fetch_C(self)-> float:
        output = self.ask_raw('TRG')
        return float(output.split()[1])

    def get_idn(self):
        IDN = {'vendor': None, 'model': None,
               'serial': None, 'firmware': None}
        return IDN
