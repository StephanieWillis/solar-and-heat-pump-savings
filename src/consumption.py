import copy
from dataclasses import dataclass

import pandas as pd

import constants
from fuels import Fuel


@dataclass
class Demand:
    profile_kwh: pd.Series  # TODO: figure out how to specify index should be datetime in typing?

    @property
    def annual_sum(self) -> float:
        annual_sum = self.profile_kwh.sum()
        return annual_sum

    def add(self, other: 'Demand') -> 'Demand':
        combined_time_series = self.profile_kwh + other.profile_kwh
        combined = Demand(profile_kwh=combined_time_series)
        return combined


@dataclass
class ConsumptionStream:
    profile_kwh: pd.Series
    fuel: Fuel = constants.ELECTRICITY

    @property
    def profile_fuel_units(self):
        export_profile_fuel_units = self.fuel.convert_kwh_to_fuel_units(self.profile_kwh)
        return export_profile_fuel_units

    @property
    def annual_sum_kwh(self) -> float:
        annual_sum = self.profile_kwh.sum()
        return annual_sum

    @property
    def annual_sum_fuel_units(self) -> float:
        annual_sum = self.profile_fuel_units.sum()
        return annual_sum

    @property
    def annual_sum_tco2(self) -> float:
        annual_tco2 = self.fuel.calculate_annual_tco2(self.annual_sum_kwh)
        return annual_tco2

    def add(self, other: 'ConsumptionStream') -> 'ConsumptionStream':
        if self.fuel == other.fuel:
            combined_time_series_kwh = self.profile_kwh + other.profile_kwh
            combined = ConsumptionStream(profile_kwh=combined_time_series_kwh, fuel=self.fuel)
        else:
            raise ValueError("The fuel of the two consumption streams must match")
        return combined


class Consumption:
    def __init__(self, profile_kwh: pd.Series, fuel: constants.Fuel = constants.ELECTRICITY):
        self.overall = ConsumptionStream(profile_kwh=profile_kwh, fuel=fuel)
        self.fuel = fuel

    @property
    def imported(self) -> ConsumptionStream:
        imported = copy.deepcopy(self.overall)
        imported.profile_kwh.loc[imported.profile_kwh < 0] = 0
        return imported

    @property
    def exported(self) -> ConsumptionStream:
        exported = copy.deepcopy(self.overall)
        exported.profile_kwh.loc[exported.profile_kwh > 0] = 0
        return exported

    def add(self, other: 'Consumption') -> 'Consumption':
        if self.fuel == other.fuel:
            combined_overall_consumption = self.overall.add(other.overall)
            combined_consumption = Consumption(profile_kwh=combined_overall_consumption.profile_kwh,
                                               fuel=self.fuel)
        else:
            raise ValueError("The fuel of the two consumptions must match")
        return combined_consumption
