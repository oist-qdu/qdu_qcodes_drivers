# This Python file uses the following encoding: utf-8
# Etienne Dumur <etienne.dumur@gmail.com>, september 2020

import os
import pandas as pd
import numpy as np
from datetime import date
from typing import Optional
from qcodes.instrument.base import Instrument

class BlueFors(Instrument):
    """
    This is the QCoDeS python driver to extract the temperature and pressure
    from a BlueFors fridge
    """

    def __init__(self, name                      : str,
                       folder_path               : str,
                       channel_vacuum_can        : int,
                       channel_pumping_line      : int,
                       channel_compressor_outlet : int,
                       channel_compressor_inlet  : int,
                       channel_mixture_tank      : int,
                       channel_venting_line      : int,
                       channel_50k_plate         : int,
                       channel_4k_plate          : int,
                       channel_still             : int,
                       channel_mixing_chamber    : int,
                       channel_cell              : int,
                       channel_magnet            : Optional[int] = None,
                       **kwargs) -> None:
        """
        QCoDeS driver for BlueFors fridges.
        ! This driver get parameters from the fridge log files.
        ! It does not interact with the fridge electronics.

        Args:
        name: Name of the instrument.
        folder_path: Valid path toward the BlueFors log folder.
        channel_vacuum_can: channel of the vacuum can
        channel_pumping_line: channel of the pumping line.
        channel_compressor_outlet: channel of the compressor outlet.
        channel_compressor_inlet: channel of the compressor inlet.
        channel_mixture_tank: channel of the mixture tank.
        channel_venting_line: channel of the venting line.
        channel_50k_plate: channel of the 50k plate.
        channel_4k_plate: channel of the 4k plate.
        channel_still: channel of the still.
        channel_mixing_chamber: channel of the mixing chamber.
        channel_magnet: channel of the magnet.
        """

        super().__init__(name = name, **kwargs)

        self.folder_path = os.path.abspath(folder_path)

        self.add_parameter(name       = 'pressure_vacuum_can',
                           unit       = 'mBar',
                           get_parser = float,
                           get_cmd    = lambda: self.get_pressure(channel_vacuum_can),
                           docstring  = 'Pressure of the vacuum can',
                           )

        self.add_parameter(name       = 'pressure_pumping_line',
                           unit       = 'mBar',
                           get_parser = float,
                           get_cmd    = lambda: self.get_pressure(channel_pumping_line),
                           docstring  = 'Pressure of the pumping line',
                           )

        self.add_parameter(name       = 'pressure_compressor_outlet',
                           unit       = 'mBar',
                           get_parser = float,
                           get_cmd    = lambda: self.get_pressure(channel_compressor_outlet),
                           docstring  = 'Pressure of the compressor outlet',
                           )

        self.add_parameter(name       = 'pressure_compressor_inlet',
                           unit       = 'mBar',
                           get_parser = float,
                           get_cmd    = lambda: self.get_pressure(channel_compressor_inlet),
                           docstring  = 'Pressure of the compressor inlet',
                           )

        self.add_parameter(name       = 'pressure_mixture_tank',
                           unit       = 'mBar',
                           get_parser = float,
                           get_cmd    = lambda: self.get_pressure(channel_mixture_tank),
                           docstring  = 'Pressure of the mixture tank',
                           )

        self.add_parameter(name       = 'pressure_venting_line',
                           unit       = 'mBar',
                           get_parser = float,
                           get_cmd    = lambda: self.get_pressure(channel_venting_line),
                           docstring  = 'Pressure of the venting line',
                           )

        self.add_parameter(name       = 'temperature_50k_plate',
                           unit       = 'K',
                           get_parser = float,
                           get_cmd    = lambda: self.get_temperature(channel_50k_plate),
                           docstring  = 'Temperature of the 50K plate',
                           )

        self.add_parameter(name       = 'temperature_4k_plate',
                           unit       = 'K',
                           get_parser = float,
                           get_cmd    = lambda: self.get_temperature(channel_4k_plate),
                           docstring  = 'Temperature of the 4K plate',
                           )

        if channel_magnet is not None:
            self.add_parameter(name       = 'temperature_magnet',
                               unit       = 'K',
                               get_parser = float,
                               get_cmd    = lambda: self.get_temperature(channel_magnet),
                               docstring  = 'Temperature of the magnet',
                               )

        self.add_parameter(name       = 'temperature_still',
                           unit       = 'K',
                           get_parser = float,
                           get_cmd    = lambda: self.get_temperature(channel_still),
                           docstring  = 'Temperature of the still',
                           )

        self.add_parameter(name       = 'temperature_mixing_chamber',
                           unit       = 'K',
                           get_parser = float,
                           get_cmd    = lambda: self.get_temperature(channel_mixing_chamber),
                           docstring  = 'Temperature of the mixing chamber',
                           )

        self.add_parameter(name       = 'temperature_cell',
                                   unit       = 'K',
                                   get_parser = float,
                                   get_cmd    = lambda: self.get_temperature(channel_cell),
                                   docstring  = 'Temperature of the cell',
                                   )

        self.connect_message()


    def get_temperature(self, channel: int) -> float:
        """
        Return the last registered temperature of the current day for the
        channel.

        Args:
            channel (int): Channel from which the temperature is extracted.

        Returns:
            temperature (float): Temperature of the channel in Kelvin.
        """

        folder_name = date.today().strftime("%y-%m-%d")
        file_path = os.path.join(self.folder_path, folder_name, 'CH'+str(channel)+' T '+folder_name+'.log')

        try:
            df = pd.read_csv(file_path,
                                delimiter = ',',
                                names     = ['date', 'time', 'y'],
                                header    = None)

            # There is a space before the day
            df.index = pd.to_datetime(df['date']+'-'+df['time'], format=' %d-%m-%y-%H:%M:%S')

            return df.iloc[-1]['y']
        except (PermissionError, OSError) as err:
            self.log.warn('Cannot access log file: {}. Returning np.nan instead of the temperature value.'.format(err))
            return np.nan
        except IndexError as err:
            self.log.warn('Cannot parse log file: {}. Returning np.nan instead of the temperature value.'.format(err))
            return np.nan


    def get_pressure(self, channel: int) -> float:
        """
        Return the last registered pressure of the current day for the
        channel.

        Args:
            channel (int): Channel from which the pressure is extracted.

        Returns:
            pressure (float): Pressure of the channel in mBar.
        """

        folder_name = date.today().strftime("%y-%m-%d")
        file_path = os.path.join(self.folder_path, folder_name, 'maxigauge '+folder_name+'.log')

        try:
            df = pd.read_csv(file_path,
                            delimiter=',',
                            names=['date', 'time',
                                    'ch1_name', 'ch1_void1', 'ch1_status', 'ch1_pressure', 'ch1_void2', 'ch1_void3',
                                    'ch2_name', 'ch2_void1', 'ch2_status', 'ch2_pressure', 'ch2_void2', 'ch2_void3',
                                    'ch3_name', 'ch3_void1', 'ch3_status', 'ch3_pressure', 'ch3_void2', 'ch3_void3',
                                    'ch4_name', 'ch4_void1', 'ch4_status', 'ch4_pressure', 'ch4_void2', 'ch4_void3',
                                    'ch5_name', 'ch5_void1', 'ch5_status', 'ch5_pressure', 'ch5_void2', 'ch5_void3',
                                    'ch6_name', 'ch6_void1', 'ch6_status', 'ch6_pressure', 'ch6_void2', 'ch6_void3',
                                    'void'],
                            header=None)

            df.index = pd.to_datetime(df['date']+'-'+df['time'], format='%d-%m-%y-%H:%M:%S')

            return df.iloc[-1]['ch'+str(channel)+'_pressure']
        except (PermissionError, OSError) as err:
            self.log.warn('Cannot access log file: {}. Returning np.nan instead of the pressure value.'.format(err))
            return np.nan
        except IndexError as err:
            self.log.warn('Cannot parse log file: {}. Returning np.nan instead of the pressure value.'.format(err))
            return np.nan

    def get_idn(self):
        IDN = {'vendor': "Bluefors", 'model': "LD400",
               'serial': "0000", 'firmware': "A677"}
        return IDN

    def status(self):
        print("--------------------------------------")
        print("VC(P1) = ", self.pressure_vacuum_can(), " mbar")
        print("DR out (P2) = ",self.pressure_pumping_line(), " mbar")
        print("DR in (P3) = ", self.pressure_compressor_outlet(), " mbar")
        print("CT in (P4) = ", self.pressure_compressor_inlet(), " mbar")
        print("He3 tank (P5) = ", self.pressure_mixture_tank(), " mbar")
        print("GHS Manifold (P6) = ", self.pressure_venting_line(), " mbar")
        print("--------------------------------------")
        print("50K = ", self.temperature_50k_plate(), " K")
        print("4K = ", self.temperature_4k_plate(), " K")
        print("Still = ", self.temperature_still(), " K")
        print("MXC = ", self.temperature_mixing_chamber(), " K")
        print("Cell = ", self.temperature_cell(), " K")
        print("--------------------------------------")

    def status_api(self):
        return("--------------------------------------\n"+\
        "VC(P1) = "+ str(self.pressure_vacuum_can())+" mbar\n"+\
        "DR out (P2) = "+ str(self.pressure_pumping_line())+" mbar\n"+\
        "DR in (P3) = "+ str(self.pressure_compressor_outlet())+" mbar\n"+\
        "CT in (P4) = "+ str(self.pressure_compressor_inlet())+" mbar\n"+\
        "He3 tank (P5) = "+ str(self.pressure_mixture_tank())+" mbar\n"+\
        "GHS Manifold (P6) = "+ str(self.pressure_venting_line())+" mbar\n"+\
        "--------------------------------------\n"+\
        "50K = "+ str(self.temperature_50k_plate())+" K\n"+\
        "4K = "+ str(self.temperature_4k_plate())+" K\n"+\
        "Still = "+ str(self.temperature_still())+" K\n"+\
        "MXC = "+ str(self.temperature_mixing_chamber())+" K\n"+\
        "Cell = "+ str(self.temperature_cell())+" K\n")