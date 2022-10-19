import copy
from dataclasses import dataclass
from math import floor
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

import constants
from constants import SolarConstants
from fuels import Fuel


def upgrade_buildings(baseline_house: 'House', upgrade_heating: 'HeatingSystem', upgrade_solar: 'Solar'
                      ) -> Tuple['House', 'House', 'House']:
    hp_house = copy.deepcopy(baseline_house)  # do after modifications so modifications flow through
    solar_house = copy.deepcopy(baseline_house)
    hp_house.heating_system = upgrade_heating
    solar_house.solar = upgrade_solar
    both_house = copy.deepcopy(hp_house)
    both_house.solar = upgrade_solar
    return hp_house, solar_house, both_house


def combined_results_dfs_multiple_houses(houses: List['House'], keys: List['str']):
    results_df = pd.concat([house.energy_and_bills_df for house in houses], keys=keys)
    results_df.index.names = ['Upgrade option', 'old_index']
    results_df = results_df.reset_index()
    results_df = results_df.drop(columns='old_index')
    return results_df


class House:
    """ Stores info on consumption and bills """

    def __init__(self, envelope: 'BuildingEnvelope', heating_system: 'HeatingSystem', solar: 'Solar' = None):

        self.envelope = envelope
        # Set up initial values for heating system and tariffs but allow to be modified by the user later
        self.heating_system = heating_system
        self.tariffs = self.set_up_standard_tariffs()

        if solar is None:
            solar = Solar(orientation='South', roof_plan_area=0)
        self.solar = solar

    @classmethod
    def set_up_from_heating_name(cls, envelope: 'BuildingEnvelope', heating_name: str) -> 'House':
        heating_system = HeatingSystem.from_constants(name=heating_name,
                                                      parameters=constants.DEFAULT_HEATING_CONSTANTS[heating_name])
        return cls(envelope=envelope, heating_system=heating_system)

    def set_up_standard_tariffs(self) -> Dict[str, 'Tariff']:

        tariffs = {'electricity': Tariff(p_per_unit_import=constants.STANDARD_TARIFF.p_per_kwh_elec_import,
                                         p_per_unit_export=constants.STANDARD_TARIFF.p_per_kwh_elec_export,
                                         p_per_day=constants.STANDARD_TARIFF.p_per_day_elec,
                                         fuel=constants.ELECTRICITY)
                   }

        match self.heating_system.fuel.name:
            case 'gas':
                tariffs['gas'] = Tariff(p_per_unit_import=constants.STANDARD_TARIFF.p_per_kwh_gas,
                                        p_per_day=constants.STANDARD_TARIFF.p_per_day_gas,
                                        fuel=self.heating_system.fuel)
            case 'oil':
                tariffs['oil'] = Tariff(p_per_unit_import=constants.STANDARD_TARIFF.p_per_L_oil,
                                        p_per_day=0.0,
                                        fuel=self.heating_system.fuel)
        return tariffs

    @property
    def has_multiple_fuels(self) -> bool:
        if self.heating_system.fuel.name == 'electricity':
            has_multiple_fuels = False
        else:
            has_multiple_fuels = True
        return has_multiple_fuels

    @property
    def consumption_per_fuel(self) -> Dict[str, 'Consumption']:

        # Base demand is always electricity (lighting/plug loads etc.)
        base_consumption = Consumption(profile_kwh=self.envelope.base_demand.profile_kwh,
                                       fuel=constants.ELECTRICITY)
        # Solar
        electricity_consumption = base_consumption.add(self.solar.generation)

        # Heating
        space_heating_consumption = self.heating_system.calculate_space_heating_consumption(
            self.envelope.space_heating_demand)
        water_heating_consumption = self.heating_system.calculate_water_heating_consumption(
            self.envelope.water_heating_demand)
        heating_consumption = water_heating_consumption.add(space_heating_consumption)

        match self.heating_system.fuel:
            case base_consumption.fuel:  # only one fuel (electricity)
                consumption_dict = {self.heating_system.fuel.name: electricity_consumption.add(heating_consumption)}
            case _:
                consumption_dict = {electricity_consumption.fuel.name: electricity_consumption,
                                    heating_consumption.fuel.name: heating_consumption}

        return consumption_dict

    @property
    def annual_consumption_per_fuel_kwh(self) -> Dict[str, float]:
        return {fuel: consumption.overall.annual_sum_kwh
                for fuel, consumption in self.consumption_per_fuel.items()}

    @property
    def total_annual_consumption_kwh(self) -> float:
        return sum(self.annual_consumption_per_fuel_kwh.values())

    @property
    def annual_bill_per_fuel(self) -> Dict[str, float]:
        bills_dict = {}
        for fuel_name, consumption in self.consumption_per_fuel.items():
            bills_dict[fuel_name] = self.tariffs[fuel_name].calculate_annual_cost(consumption)
        return bills_dict

    @property
    def total_annual_bill(self) -> float:
        return sum(self.annual_bill_per_fuel.values())

    @property
    def annual_tco2_per_fuel(self) -> Dict[str, float]:
        carbon_dict = {}
        for fuel_name, consumption in self.consumption_per_fuel.items():
            carbon_dict[fuel_name] = consumption.overall.annual_sum_tco2
        return carbon_dict

    @property
    def total_annual_tco2(self) -> float:
        return sum(self.annual_tco2_per_fuel.values())

    @property
    def energy_and_bills_df(self) -> pd.DataFrame:
        """ To make it easy to plot the results using plotly"""
        df = pd.DataFrame(data={'Your annual energy use kwh': self.annual_consumption_per_fuel_kwh,
                                'Your annual energy bill £': self.annual_bill_per_fuel,
                                'Your annual carbon emissions tCO2': self.annual_tco2_per_fuel})
        df.index.name = 'fuel'
        df = df.reset_index()
        return df


@dataclass()
class BuildingEnvelope:
    """ Stores info on the building and its energy demand"""

    def __init__(self, floor_area_m2: float, house_type: str):
        self.floor_area_m2 = floor_area_m2
        self.house_type = house_type
        self.time_series_idx: pd.Index = constants.BASE_YEAR_HALF_HOUR_INDEX
        self.units: str = 'kwh'

        # Set initial demand values - user can overwrite later
        # Dummy data for now TODO get profiles from elsewhere
        self.base_demand = Demand(profile_kwh=pd.Series(index=self.time_series_idx, data=0.001 * self.floor_area_m2))
        self.water_heating_demand = Demand(
            profile_kwh=pd.Series(index=self.time_series_idx, data=0.004 * self.floor_area_m2))
        self.space_heating_demand = Demand(
            profile_kwh=pd.Series(index=self.time_series_idx, data=0.005 * self.floor_area_m2))


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


@dataclass
class HeatingSystem:
    name: str
    space_heating_efficiency: float
    water_heating_efficiency: float
    fuel: constants.Fuel

    @classmethod
    def from_constants(cls, name, parameters: constants.HeatingConstants):
        return cls(name=name,
                   space_heating_efficiency=parameters.space_heating_efficiency,
                   water_heating_efficiency=parameters.water_heating_efficiency,
                   fuel=parameters.fuel)

    def __post_init__(self):
        if self.fuel not in constants.FUELS:
            raise ValueError(f"fuel must be one of {constants.FUELS}")

    def calculate_space_heating_consumption(self, space_heating_demand: Demand) -> Consumption:
        return self.calculate_consumption(demand=space_heating_demand, efficiency=self.space_heating_efficiency)

    def calculate_water_heating_consumption(self, water_heating_demand: Demand) -> Consumption:
        return self.calculate_consumption(demand=water_heating_demand, efficiency=self.water_heating_efficiency)

    def calculate_consumption(self, demand: Demand, efficiency: float) -> Consumption:
        profile_kwh = demand.profile_kwh / efficiency
        consumption = Consumption(profile_kwh=profile_kwh, fuel=self.fuel)
        return consumption


@dataclass
class Tariff:
    fuel: constants.Fuel
    p_per_day: float
    p_per_unit_import: float  # unit defined by the fuel
    p_per_unit_export: float = 0

    def calculate_annual_cost(self, consumption: 'Consumption') -> float:
        """ Calculate the annual cost of the consumption of a certain fuel with this tariff"""
        if self.fuel != consumption.fuel:
            raise ValueError("To calculate annual costs the tariff fuel must match the consumption fuel, they are"
                             f"{self.fuel} and {consumption.fuel}")
        cost_p_per_day = 365 * self.p_per_day
        cost_p_imports = consumption.imported.annual_sum_fuel_units * self.p_per_unit_import
        cost_p_exports = consumption.exported.annual_sum_fuel_units * self.p_per_unit_export
        annual_cost = (cost_p_per_day + cost_p_imports + cost_p_exports) / 100
        return annual_cost


class Solar:

    def __init__(self, orientation: str, roof_plan_area: float):
        """ Roof plan area because based on lat long therefore doesn't account for roof pitch"""

        self.orientation = orientation
        self.profile_kwh_per_m2 = self.get_generation_profile()

        self.number_of_panels = self.get_number_of_panels(roof_plan_area)
        self.kwp_per_panel = SolarConstants.KW_PEAK_PER_PANEL

    @staticmethod
    def get_number_of_panels(roof_plan_area: float) -> int:
        roof_area = roof_plan_area / np.cos(np.radians(SolarConstants.ROOF_PITCH_DEGREES))
        usable_area = roof_area * SolarConstants.PERCENT_SQUARE_USABLE
        number_of_panels = floor(usable_area / SolarConstants.PANEL_AREA)

        return number_of_panels

    @staticmethod
    def get_generation_profile():
        # TODO properly using orientation and location

        # Stand in for now in absense of proper data
        idx = constants.BASE_YEAR_HALF_HOUR_INDEX
        minute_of_the_day = idx.hour * 60 + idx.minute
        kw_per_m2_peak = 0.3
        generation = - np.cos(minute_of_the_day * np.pi * 2 / (24 * 60)) * kw_per_m2_peak
        profile_kw_per_m2 = pd.Series(index=constants.BASE_YEAR_HALF_HOUR_INDEX, data=generation)
        profile_kw_per_m2.loc[profile_kw_per_m2 < 0] = 0
        profile_kwh_per_m2 = profile_kw_per_m2 / 2  # because we know the time base is half hourly
        # If not importing this from elsewhere think about whether need to integrate (take the previous half hour)

        return profile_kwh_per_m2

    @property
    def peak_capacity_kw_out_per_kw_in_per_m2(self):
        return self.number_of_panels * self.kwp_per_panel

    @property
    def generation(self):
        # set negative as generation not consumption
        profile_kwh = -1 * self.profile_kwh_per_m2 * self.peak_capacity_kw_out_per_kw_in_per_m2
        generation = Consumption(profile_kwh=profile_kwh, fuel=constants.ELECTRICITY)
        return generation
