import copy
from dataclasses import dataclass, field

import pandas as pd

import constants
from fuels import Fuel


@dataclass
class ConsumptionStream:

    hourly_profile_kwh: pd.Series  # series index must be hourly datetime values for one whole year
    fuel: Fuel = field(default_factory=constants.ELECTRICITY)

    def __post_init__(self):
        """ Check index is of correct form"""
        # TODO: ask Archy how to do this better
        assert isinstance(self.hourly_profile_kwh.index, pd.DatetimeIndex), "hourly_profile_kwh index must be datetime"
        assert len(set(self.hourly_profile_kwh.index.year)) == 1  # only one year
        assert self.hourly_profile_kwh.index.month[0] == 1
        assert self.hourly_profile_kwh.index.month[-1] == 12
        assert self.hourly_profile_kwh.index.day[0] == 1
        assert self.hourly_profile_kwh.index.day[-1] == 31
        assert self.hourly_profile_kwh.index.hour[0] == 0  # start at 0.00
        assert self.hourly_profile_kwh.index.hour[-1] == 23  # end at 23.00
        assert len(self.hourly_profile_kwh) == 8760 or len(self.hourly_profile_kwh) == 8760 + 24

        self.year = self.hourly_profile_kwh.index.year[0]
        self.hours_in_year = len(self.hourly_profile_kwh)
        self.days_in_year = self.hours_in_year/24
        self.leap_year = True if self.hours_in_year == 8760 + 24 else False

    @property
    def hourly_profile_fuel_units(self):
        export_profile_fuel_units = self.fuel.convert_kwh_to_fuel_units(self.hourly_profile_kwh)
        return export_profile_fuel_units

    @property
    def annual_sum_kwh(self) -> float:
        annual_sum = self.hourly_profile_kwh.sum()
        return annual_sum

    @property
    def annual_sum_fuel_units(self) -> float:
        annual_sum = self.hourly_profile_fuel_units.sum()
        return annual_sum

    @property
    def annual_sum_tco2(self) -> float:
        annual_tco2 = self.fuel.calculate_annual_tco2(self.annual_sum_kwh)
        return annual_tco2

    def add(self, other: 'ConsumptionStream') -> 'ConsumptionStream':
        if self.year == other.year:
            combined_hourly_profile_kwh = self.hourly_profile_kwh + other.hourly_profile_kwh
            combined = ConsumptionStream(hourly_profile_kwh=combined_hourly_profile_kwh, fuel=self.fuel)
        else:
            raise ValueError("The year must be the same to be able to sum two profiles")
        return combined


class Consumption:
    """ In 'overall' imports are positive and exports negative. In their respective streams they are both positive"""
    def __init__(self, hourly_profile_kwh: pd.Series, fuel: constants.Fuel = constants.ELECTRICITY):
        self.overall = ConsumptionStream(hourly_profile_kwh=hourly_profile_kwh, fuel=fuel)
        self.fuel = fuel

    @property
    def imported(self) -> ConsumptionStream:
        imported = copy.deepcopy(self.overall)
        # set negative values equal to zero as they are exports
        imported.hourly_profile_kwh.loc[imported.hourly_profile_kwh < 0] = 0
        return imported

    @property
    def exported(self) -> ConsumptionStream:
        exported = copy.deepcopy(self.overall)
        # set positive values equal to zero as they are imports
        exported.hourly_profile_kwh.loc[exported.hourly_profile_kwh > 0] = 0
        # now that it is labelled as exported, make it positive to make it easier to deal with
        exported.hourly_profile_kwh = exported.hourly_profile_kwh * -1
        return exported

    def add(self, other: 'Consumption') -> 'Consumption':
        combined_overall_consumption = self.overall.add(other.overall)
        combined_consumption = Consumption(hourly_profile_kwh=combined_overall_consumption.hourly_profile_kwh,
                                           fuel=self.fuel)
        return combined_consumption
