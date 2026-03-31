# -*- coding: utf-8 -*-
import numpy as np
from typing import Any, Tuple

from qcodes import VisaInstrument
from qcodes.utils.validators import Numbers, Enum, Arrays



class LakeShore218(VisaInstrument):
    """
    This is a very basic qcodes driver for LakeShore 218 temperature controller.
    UNDER DEVELOPMENT m.belianchikov@oist.jp
    """

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, **kwargs)


        self.add_parameter('temperature_ch1',
                           label='Ch1 temperature',
                           get_cmd='KRDG?1',
                           get_parser=float,
                           unit='K')

        self.add_parameter('temperature_ch2',
                           label='Ch2 temperature',
                           get_cmd='KRDG?2',
                           get_parser=float,
                           unit='K')
        
        self.connect_message()
