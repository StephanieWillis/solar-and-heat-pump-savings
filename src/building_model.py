from dataclasses import dataclass
from typing import Dict

import pandas as pd

import constants
from consumption import Consumption
from solar import Solar


class House:
    """ Stores info on consumption and bills """

    def __init__(self, envelope: 'BuildingEnvelope', heating_system: 'HeatingSystem', solar_install: 'Solar' = None):

        self.envelope = envelope
        # Set up initial values for heating system and tariffs but allow to be modified by the user later
        self.heating_system = heating_system
        self.tariffs = self.set_up_standard_tariffs()

        if solar_install is None:
            solar_install = Solar.create_zero_area_instance()
        self.solar_install = solar_install

        self.lifetime = (heating_system.lifetime + solar_install.lifetime)/2  # very rough approach

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
        electricity_consumption = base_consumption.add(self.solar_install.generation)

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

    @property
    def upfront_cost(self) -> int:
        cost = (self.heating_system.calculate_upfront_cost(house_type=self.envelope.house_type)
                + self.solar_install.upfront_cost)
        rounded_cost = round(cost, -2)
        return rounded_cost


@dataclass
class Tariff:
    fuel: constants.Fuel
    p_per_day: float
    p_per_unit_import: float  # unit defined by the fuel
    p_per_unit_export: float = 0.0

    def calculate_annual_cost(self, consumption: 'Consumption') -> float:
        """ Calculate the annual cost of the consumption of a certain fuel with this tariff"""
        if self.fuel.name != consumption.fuel.name:
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
    lifetime = constants.HEATING_SYSTEM_LIFETIME

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
        try:
            profile_kwh = self.hourly_normalized_demand_profile / self.efficiency * annual_space_heating_demand_kwh
        except ZeroDivisionError:  # should only happen fleetingly when heating system state hasn't caught up
            profile_kwh = self.hourly_normalized_demand_profile * 0
        consumption = Consumption(hourly_profile_kwh=profile_kwh, fuel=self.fuel)
        return consumption

    def calculate_upfront_cost(self, house_type: str):
        cost = constants.HEATING_SYSTEM_COSTS[self.name][house_type]
        if self.name == "Heat pump":
            cost = cost - constants.HEAT_PUMP_GRANT
        return cost


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


