from dataclasses import dataclass
from typing import Dict

import pandas as pd

FUELS = ['electricity', 'gas', 'oil']

ENERGY_UNITS = ['kWh', 'GJ']

HOUSE_TYPES = ['terrace', 'semi-detached', 'detached', 'flat']

BASE_YEAR_HALF_HOUR_INDEX = pd.date_range(start="2020-01-01", end="2021-01-01", freq="30T")
EMPTY_TIMESERIES = pd.Series(index= BASE_YEAR_HALF_HOUR_INDEX, data=0)

