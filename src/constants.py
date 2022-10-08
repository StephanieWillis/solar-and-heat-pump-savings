from dataclasses import dataclass
from typing import Dict

import pandas as pd

HOUSE_TYPES = ['Terrace', 'Semi-detached', 'Detached', 'Flat']

BASE_YEAR_HALF_HOUR_INDEX = pd.date_range(start="2020-01-01", end="2021-01-01", freq="30T")
EMPTY_TIMESERIES = pd.Series(index=BASE_YEAR_HALF_HOUR_INDEX, data=0)


@dataclass
class Fuel:
    name: str
    units: str = 'kWh'
    converter_consumption_units_to_kWh: float = 1

KWH_PER_LITRE_OF_OIL = 10.35
# https: // www.thegreenage.co.uk / is -heating - oil - a - cheap - way - to - heat - my - home /
ELECTRICITY = Fuel('electricity')
GAS = Fuel(name='gas')
OIL = Fuel(name='oil', units='litres', converter_consumption_units_to_kWh=KWH_PER_LITRE_OF_OIL)
FUELS = [ELECTRICITY, GAS, OIL]


@dataclass
class HeatingConstants:
    space_heating_efficiency: float
    water_heating_efficiency: float
    fuel: Fuel


DEFAULT_HEATING_CONSTANTS = {'Gas boiler': HeatingConstants(0.85, 0.8, GAS),
                             'Oil boiler': HeatingConstants(0.8, 0.75, OIL),
                             'Direct electric': HeatingConstants(1.0, 1.0, ELECTRICITY),
                             'Heat pump': HeatingConstants(3.5, 3.0, ELECTRICITY)}


@dataclass
class SolarConstants:
    SOLAR_ORIENTATIONS = ['South', 'Southwest', 'West', 'Northwest', 'North', 'Northeast', 'East', 'Southeast']
    MIN_ROOF_AREA = 0
    MAX_ROOF_AREA = 20
    DEFAULT_ROOF_AREA = 20
    PANEL_HEIGHT_M = 1.9
    PANEL_WIDTH_M = 1.0
    KW_PEAK_PER_PANEL = 0.35  # output with incident radiation of 1kW/m2
    # Panel dimensions and kW_peak from https://www.greenmatch.co.uk/blog/how-many-solar-panels-do-i-need
    PCT_OF_DIMENSION_USABLE = 0.9  # a guess

@dataclass
class TariffConstants:
    p_per_kWh_gas: float
    p_per_kWh_elec: float
    p_per_day_gas: float
    p_per_day_elec: float
    p_per_L_oil: float

STANDARD_TARIFF = TariffConstants(p_per_kWh_gas=10.3,
                                  p_per_kWh_elec=34.0,
                                  p_per_day_gas=28.0,
                                  p_per_day_elec=46.0,
                                  p_per_L_oil=95.0)
