import copy
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd

import constants
from constants import SolarConstants
from consumption import Consumption
from solar import Solar


def upgrade_buildings(baseline_house: 'House', upgrade_heating: 'HeatingSystem', upgrade_solar: 'Solar'
                      ) -> Tuple['House', 'House', 'House']:
    hp_house = copy.deepcopy(baseline_house)  # do after modifications so modifications flow through
    solar_house = copy.deepcopy(baseline_house)
    hp_house.heating_system = upgrade_heating
    solar_house.solar = upgrade_solar
    both_house = copy.deepcopy(hp_house)
    both_house.solar = upgrade_solar
    return hp_house, solar_house, both_house


def combine_results_dfs_multiple_houses(houses: List['House'], keys: List['str']):
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
            solar = Solar(orientation=SolarConstants.ORIENTATIONS['South'], roof_plan_area=0)
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
        base_consumption = Consumption(hourly_profile_kwh=self.envelope.base_demand,
                                       fuel=constants.ELECTRICITY)
        # Solar
        electricity_consumption = base_consumption.add(self.solar.generation)

        # Heating
        heating_consumption = self.heating_system.calculate_consumption(
            self.envelope.annual_heating_demand)

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
        cost_p_per_day = consumption.overall.days_in_year * self.p_per_day
        cost_p_imports = consumption.imported.annual_sum_fuel_units * self.p_per_unit_import
        income_p_exports = consumption.exported.annual_sum_fuel_units * self.p_per_unit_export
        annual_cost = (cost_p_per_day + cost_p_imports - income_p_exports) / 100
        return annual_cost


@dataclass
class HeatingSystem:
    name: str
    efficiency: float
    fuel: constants.Fuel
    hourly_normalized_demand_profile: pd.Series

    @classmethod
    def from_constants(cls, name, parameters: constants.HeatingConstants):
        return cls(name=name,
                   efficiency=parameters.efficiency,
                   fuel=parameters.fuel,
                   hourly_normalized_demand_profile=parameters.normalized_hourly_heat_demand_profile)

    def __post_init__(self):
        if self.fuel not in constants.FUELS:
            raise ValueError(f"fuel must be one of {constants.FUELS}")

    def calculate_consumption(self, annual_space_heating_demand_kwh: float) -> Consumption:
        profile_kwh = self.hourly_normalized_demand_profile / self.efficiency * annual_space_heating_demand_kwh
        consumption = Consumption(hourly_profile_kwh=profile_kwh, fuel=self.fuel)
        return consumption


@dataclass()
class BuildingEnvelope:
    """ Stores info on the building and its energy demand"""

    def __init__(self, house_type: str, annual_heating_demand: float, base_electricity_demand_profile_kwh: pd.Series):
        self.house_type = house_type
        self.annual_heating_demand = annual_heating_demand
        self.base_demand = base_electricity_demand_profile_kwh
        self.units: str = 'kwh'

    @classmethod
    def from_building_type_constants(cls, building_type_constants: constants.BuildingTypeConstants
                                     ) -> "BuildingEnvelope":
        base_electricity_demand_profile = (building_type_constants.annual_base_electricity_demand_kWh
                                           * building_type_constants.normalized_base_electricity_demand_profile_kWh)
        return cls(house_type=building_type_constants.name,
                   annual_heating_demand=building_type_constants.annual_heat_demand_kWh,
                   base_electricity_demand_profile_kwh=base_electricity_demand_profile)
