from dataclasses import dataclass

import pandas as pd


@dataclass
class Fuel:
    name: str
    tco2_per_kwh: float  # could be a time series later
    units: str = "kwh"
    converter_consumption_units_to_kwh: float = 1

    def convert_kwh_to_fuel_units(self, value_kwh: [float | pd.Series | pd.DataFrame]):
        value_fuel_units = value_kwh / self.converter_consumption_units_to_kwh
        return value_fuel_units

    def convert_fuel_units_to_kwh(self, value_fuel_units: [float | pd.Series | pd.DataFrame]):
        value_kwh = value_fuel_units * self.converter_consumption_units_to_kwh
        return value_kwh

    def calculate_annual_tco2(self, annual_sum_kwh: float) -> float:
        annual_tco2 = self.tco2_per_kwh * annual_sum_kwh
        return annual_tco2
