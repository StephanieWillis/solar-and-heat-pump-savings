from dataclasses import dataclass
from typing import Dict

import pandas as pd

BASE_YEAR_HALF_HOUR_INDEX = pd.date_range(start="2020-01-01", end="2021-01-01", freq="30T")
EMPTY_TIMESERIES = pd.Series(index=BASE_YEAR_HALF_HOUR_INDEX, data=0)

ENERGY_UNITS = ['kWh', 'GJ']
FUELS = ['electricity', 'gas', 'oil']

HOUSE_TYPES = ['Terrace', 'Semi-detached', 'Detached', 'Flat']


@dataclass
class HeatingConstants:
    space_heating_efficiency: float
    water_heating_efficiency: float
    fuel: str


DEFAULT_HEATING_CONSTANTS = {'Heat pump': HeatingConstants(3.5, 3, 'electricity'),
                             'Gas boiler': HeatingConstants(0.85, 0.8, 'gas'),
                             'Oil boiler': HeatingConstants(0.8, 0.75, 'oil'),
                             'Direct electric': HeatingConstants(1, 1, 'electricity')}


@dataclass
class SolarConstants:
    SOLAR_ORIENTATIONS = ['South', 'Southwest', 'West', 'Northwest', 'North', 'Northeast', 'East', 'Southeast']
    MIN_ROOF_AREA = 0
    MAX_ROOF_AREA = 20
    DEFAULT_ROOF_AREA = 20
    PANEL_HEIGHT_M = 0.5  # placeholder
    PANEL_WIDTH_M = 0.2  # placeholder
    PCT_OF_DIMENSION_USABLE = 0.9
    KW_PEAK_PER_PANEL = 0.6  # output with incident radiation of 1kW/m2
