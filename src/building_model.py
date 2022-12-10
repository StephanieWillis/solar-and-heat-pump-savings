from dataclasses import dataclass
from functools import cached_property
from typing import Dict

import pandas as pd

import constants
from consumption import Consumption
from solar import Solar
from fuels import Fuel


class House:
    """ Stores info on consumption and bills """

    def __init__(self, envelope: 'BuildingEnvelope', heating_system: 'HeatingSystem', solar_install: 'Solar' = None):

        self.envelope = envelope
        # Set up initial values for heating system and tariffs but allow to be modified by the user later
        self.heating_system = heating_system
        self.tariffs = Tariff.set_up_standard_tariffs(heating_system_fuel=heating_system.fuel)

        if solar_install is None:
            solar_install = Solar.create_zero_area_instance()
        self.solar_install = solar_install

        self.lifetime = (heating_system.lifetime + solar_install.lifetime) / 2  # very rough approach

        self._heating_system_upfront_cost: int | None = None  # to help with overwrites

    @classmethod
    def set_up_from_heating_name(cls, envelope: 'BuildingEnvelope', heating_name: str) -> 'House':
        heating_system = HeatingSystem.from_constants(name=heating_name,
                                                      parameters=constants.DEFAULT_HEATING_CONSTANTS[heating_name])
        return cls(envelope=envelope, heating_system=heating_system)

    @property
    def base_consumption(self) -> Consumption:
        # Base demand is always electricity (lighting/plug loads etc.)
        return Consumption(hourly_profile_kwh=self.envelope.base_demand, fuel=constants.ELECTRICITY)

    @property
    def electricity_consumption_excluding_heating(self) -> Consumption:
        return self.base_consumption.add(self.solar_install.generation)

    @cached_property
    def heating_consumption(self) -> Consumption:
        return self.heating_system.calculate_consumption(self.envelope.annual_heating_demand)

    @property
    def has_multiple_fuels(self) -> bool:
        if self.heating_system.fuel.name == 'electricity':
            has_multiple_fuels = False
        else:
            has_multiple_fuels = True
        return has_multiple_fuels

    @property
    def consumption_per_fuel(self) -> Dict[str, 'Consumption']:

        match self.heating_system.fuel:
            case self.base_consumption.fuel:  # only one fuel (electricity)
                consumption_dict = {'electricity': self.electricity_consumption_excluding_heating.add(
                    self.heating_consumption)}
            case _:
                consumption_dict = {'electricity': self.electricity_consumption_excluding_heating,
                                    self.heating_consumption.fuel.name: self.heating_consumption}

        return consumption_dict

    @cached_property
    def annual_consumption_per_fuel_kwh(self) -> Dict[str, float]:
        return {fuel: consumption.overall.annual_sum_kwh
                for fuel, consumption in self.consumption_per_fuel.items()}

    @property
    def total_annual_consumption_kwh(self) -> float:
        return sum(self.annual_consumption_per_fuel_kwh.values())

    @property
    def annual_bill_import_and_export_per_fuel(self) -> Dict[str, Dict[str, float]]:
        bills_imported_and_exported = {}
        for fuel_name, consumption in self.consumption_per_fuel.items():
            inner_dict = {'imported': self.tariffs[fuel_name].calculate_annual_import_cost(consumption=consumption),
                          'exported': self.tariffs[fuel_name].calculate_annual_export_cost(consumption=consumption)}
            bills_imported_and_exported[fuel_name] = inner_dict
        return bills_imported_and_exported

    @property
    def annual_bill_per_fuel(self) -> Dict[str, float]:
        bills_dict = {}
        for fuel_name, consumption in self.consumption_per_fuel.items():
            bills_dict[fuel_name] = (self.annual_bill_import_and_export_per_fuel[fuel_name]['imported']
                                     - self.annual_bill_import_and_export_per_fuel[fuel_name]['exported'])
        return bills_dict

    @cached_property
    def total_annual_bill(self) -> float:
        return sum(self.annual_bill_per_fuel.values())

    @property
    def annual_tco2_per_fuel(self) -> Dict[str, float]:
        carbon_dict = {}
        for fuel_name, consumption in self.consumption_per_fuel.items():
            carbon_dict[fuel_name] = consumption.overall.annual_sum_tco2
        return carbon_dict

    @cached_property
    def total_annual_tco2(self) -> float:
        return sum(self.annual_tco2_per_fuel.values())

    @cached_property
    def energy_and_bills_df(self) -> pd.DataFrame:

        """ To make it easy to plot the results using plotly"""
        kwh = {'electricity imports': round(self.consumption_per_fuel['electricity'].imported.annual_sum_kwh, 0),
               'electricity exports': - round(self.consumption_per_fuel['electricity'].exported.annual_sum_kwh, 0)}
        bill = {'electricity imports': round(self.annual_bill_import_and_export_per_fuel['electricity']['imported'], 0),
                'electricity exports': - round(self.annual_bill_import_and_export_per_fuel['electricity']['exported'], 0)}
        co2_dict = {'electricity imports': round(self.consumption_per_fuel['electricity'].imported.annual_sum_tco2, 2),
                    'electricity exports': - round(self.consumption_per_fuel['electricity'].exported.annual_sum_tco2, 2)}

        heating_fuel = self.heating_system.fuel.name
        if heating_fuel != 'electricity':
            kwh[heating_fuel] = round(self.consumption_per_fuel[heating_fuel].overall.annual_sum_kwh, 0)
            bill[heating_fuel] = round(self.annual_bill_per_fuel[heating_fuel], 0)
            co2_dict[heating_fuel] = round(self.consumption_per_fuel[heating_fuel].overall.annual_sum_tco2, 2)

        df = pd.DataFrame(data={'Your annual energy use kwh': kwh,
                                'Your annual energy bill £': bill,
                                'Your annual carbon emissions tCO2': co2_dict})
        df.index.name = 'fuel'
        df = df.reset_index()
        return df

    @cached_property
    def annual_consumption_import_and_export_per_fuel_kwh(self) -> Dict[str, float]:
        return {fuel: {'import': consumption.imported.annual_sum_kwh, 'export': consumption.imported.annual_sum_kwh}
                for fuel, consumption in self.consumption_per_fuel.items()}

    def clear_cached_properties(self):
        cls = self.__class__
        attrs = [a for a in dir(self) if isinstance(getattr(cls, a, cls), cached_property)]
        for a in attrs:
            if a in self.__dict__.keys():
                del self.__dict__[a]

    @property
    def heating_system_upfront_cost(self) -> int:
        if self._heating_system_upfront_cost is None:
            cost = self.heating_system.calculate_upfront_cost(house_type=self.envelope.house_type)
            rounded_cost = round(cost, -2)
        else:  # if has been overwritten, will remain overwritten unless clear_cost_overwrite function called
            rounded_cost = self._heating_system_upfront_cost
        return int(rounded_cost)

    @heating_system_upfront_cost.setter
    def heating_system_upfront_cost(self, value):
        if value is not None:
            value = round(value, -2)
        self._heating_system_upfront_cost = value

    def clear_cost_overwrite(self):
        self.heating_system_upfront_cost = None

    @property
    def upfront_cost(self) -> int:
        cost = self.heating_system_upfront_cost + self.solar_install.upfront_cost
        rounded_cost = round(cost, -2)
        return rounded_cost

    @property
    def upfront_cost_after_grants(self) -> int:
        return self.upfront_cost - self.heating_system.grant


@dataclass
class Tariff:
    fuel: constants.Fuel
    p_per_day: float
    p_per_unit_import: float  # unit defined by the fuel
    p_per_unit_export: float = 0.0

    def calculate_annual_import_cost(self, consumption: 'Consumption') -> float:
        """ Calculate the annual cost of the import consumption of a certain fuel with this tariff"""
        if self.fuel.name != consumption.fuel.name:
            raise ValueError("To calculate annual costs the tariff fuel must match the consumption fuel, they are"
                             f"{self.fuel} and {consumption.fuel}")
        cost_p_per_day = consumption.overall.days_in_year * self.p_per_day
        cost_p_imports = consumption.imported.annual_sum_fuel_units * self.p_per_unit_import
        annual_import_cost = (cost_p_per_day + cost_p_imports) / 100
        return annual_import_cost

    def calculate_annual_export_cost(self, consumption: 'Consumption') -> float:
        """ Calculate the annual cost of the export of a certain fuel with this tariff"""
        if self.fuel.name != consumption.fuel.name:
            raise ValueError("To calculate annual costs the tariff fuel must match the consumption fuel, they are"
                             f"{self.fuel} and {consumption.fuel}")
        income_exports = consumption.exported.annual_sum_fuel_units * self.p_per_unit_export / 100
        return income_exports

    def calculate_annual_net_cost(self, consumption: 'Consumption') -> float:
        annual_import_cost = self.calculate_annual_import_cost(consumption=consumption)
        income_exports = self.calculate_annual_export_cost(consumption=consumption)
        return annual_import_cost - income_exports

    @classmethod
    def set_up_standard_tariffs(cls, heating_system_fuel: Fuel) -> Dict[str, 'Tariff']:

        tariffs = {'electricity': Tariff(p_per_unit_import=constants.STANDARD_TARIFF.p_per_kwh_elec_import,
                                         p_per_unit_export=constants.STANDARD_TARIFF.p_per_kwh_elec_export,
                                         p_per_day=constants.STANDARD_TARIFF.p_per_day_elec,
                                         fuel=constants.ELECTRICITY)
                   }
        if heating_system_fuel.name != 'electricity':
            tariffs[heating_system_fuel.name] = cls.set_up_heating_tariff(heating_system_fuel=heating_system_fuel)

        return tariffs

    @classmethod
    def set_up_heating_tariff(cls, heating_system_fuel: Fuel) -> 'Tariff':
        match heating_system_fuel.name:
            case 'gas':
                heating_tariff = Tariff(p_per_unit_import=constants.STANDARD_TARIFF.p_per_kwh_gas,
                                        p_per_day=constants.STANDARD_TARIFF.p_per_day_gas,
                                        fuel=heating_system_fuel)
            case 'oil':
                heating_tariff = Tariff(p_per_unit_import=constants.STANDARD_TARIFF.p_per_L_oil,
                                        p_per_day=0.0,
                                        fuel=heating_system_fuel)
        return heating_tariff


@dataclass
class HeatingSystem:
    name: str
    efficiency: float
    fuel: constants.Fuel
    hourly_normalized_demand_profile: pd.Series
    lifetime = constants.HEATING_SYSTEM_LIFETIME

    def __post_init__(self):
        self.grant = constants.HEATING_SYSTEM_GRANTS[self.name]
        if self.fuel not in constants.FUELS:
            raise ValueError(f"fuel must be one of {constants.FUELS}")

    @classmethod
    def from_constants(cls, name, parameters: constants.HeatingConstants):
        return cls(name=name,
                   efficiency=parameters.efficiency,
                   fuel=parameters.fuel,
                   hourly_normalized_demand_profile=parameters.normalized_hourly_heat_demand_profile)

    def calculate_consumption(self, annual_space_heating_demand_kwh: float) -> Consumption:
        try:
            profile_kwh = self.hourly_normalized_demand_profile / self.efficiency * annual_space_heating_demand_kwh
        except ZeroDivisionError:  # should only happen fleetingly when heating system state hasn't caught up
            profile_kwh = self.hourly_normalized_demand_profile * 0
        consumption = Consumption(hourly_profile_kwh=profile_kwh, fuel=self.fuel)
        return consumption

    def calculate_upfront_cost(self, house_type: str):
        cost = constants.HEATING_SYSTEM_COSTS[self.name][house_type]
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
