from dataclasses import dataclass, asdict
from typing import Tuple, Dict, List

import pandas as pd
import streamlit as st

import constants


def render():
    house, heating_system = render_questions()
    calculate_and_render_outputs(house=house, heating_system=heating_system)


def render_questions() -> Tuple['House', 'HeatingSystem']:
    st.subheader("Your current energy usage")

    st.write("To estimate your current energy use we need a few bits of information about your house:")

    house_floor_area_m2 = st.number_input(label='House floor area (m2)', min_value=0, max_value=500, value=80)
    house_type = st.selectbox('House Type', options=constants.HOUSE_TYPES)
    house = House(house_type=house_type, floor_area_m2=house_floor_area_m2)

    heating_system_name = st.selectbox('Heating System', options=constants.DEFAULT_HEATING_CONSTANTS.keys())
    heating_system = HeatingSystem.from_constants(name=heating_system_name,
                                                  parameters=constants.DEFAULT_HEATING_CONSTANTS[heating_system_name])

    return house, heating_system


def calculate_and_render_outputs(house: 'House', heating_system: 'HeatingSystem'):
    st.write(f'Your house is an {house.floor_area_m2} m\u00b2 {house.type}')

    st.write(f'Your heating system is a {heating_system.name}. ')
    heating_system.space_heating_efficiency = st.number_input(label='Its efficiency for space heating is: ',
                                                              min_value=0.0,
                                                              max_value=10.0,
                                                              value=heating_system.space_heating_efficiency)
    heating_system.water_heating_efficiency = st.number_input(label='Its efficiency for water heating is: ',
                                                              min_value=0.0,
                                                              max_value=10.0,
                                                              value=heating_system.water_heating_efficiency)

    consumption_dict = house.calculate_consumption(heating_system=heating_system)

    if heating_system.fuel == 'electricity':
        st.write(
            f"We think your home needs {int(consumption_dict['electricity'].annual_sum):,} kWh of electricity a year"
        )
    else:
        st.write(
            f"We think your home needs {int(consumption_dict['electricity'].annual_sum):,} kWh of electricity per year"
            f" and {int(consumption_dict[heating_system.fuel].annual_sum)} kWh of {heating_system.fuel}")

    # bills =


@dataclass
class Demand:
    profile: pd.Series  # TODO: figure out how to specify index should be datetime?
    units: str

    def __post_init__(self):
        check_valid_units(self.units)

    @property
    def annual_sum(self) -> float:
        annual_consumption = self.profile.sum()
        return annual_consumption

    def add(self, other: 'Demand') -> 'Demand':
        if self.units == other.units:
            combined_time_series = self.profile + other.profile
            combined = Demand(profile=combined_time_series, units=self.units)
        else:
            raise ValueError("The units of the two energy time series must match")
        return combined


@dataclass
class Consumption(Demand):
    units: str = 'kWh'
    fuel: str = 'electricity'

    def __post_init__(self):
        check_valid_fuel(fuel=self.fuel)
        check_valid_units(self.units)

    def add(self, other: 'Consumption') -> 'Consumption':
        if self.fuel == other.fuel and self.units == other.units:
            combined_time_series = self.profile + other.profile
            combined = Consumption(profile=combined_time_series, units=self.units, fuel=self.fuel)
        else:
            raise ValueError("The fuel and units of the two consumptions must match")
            # idea: maybe this should work and just return a list?
        return combined


@dataclass
class Tariff:
    price_per_unit: float
    unit: str
    price_per_day: float
    fuel: str

    def __post_init__(self):
        check_valid_fuel(fuel=self.fuel)
        check_valid_units(unit=self.unit)


@dataclass
class HeatingSystem:
    name: str
    space_heating_efficiency: float
    water_heating_efficiency: float
    fuel: str

    @classmethod
    def from_constants(cls, name, parameters: constants.HeatingConstants):
        return cls(name=name,
                   space_heating_efficiency=parameters.space_heating_efficiency,
                   water_heating_efficiency=parameters.water_heating_efficiency,
                   fuel=parameters.fuel)

    def __post_init__(self):
        if self.fuel not in constants.FUELS:
            raise ValueError(f"fuel must be one of {constants.FUELS}")

    def calculate_space_heating_consumption(self, space_heat_demand: Demand) -> Consumption:
        return self.calculate_consumption(demand=space_heat_demand, efficiency=self.space_heating_efficiency)

    def calculate_water_heating_consumption(self, water_heat_demand: Demand) -> Consumption:
        return self.calculate_consumption(demand=water_heat_demand, efficiency=self.water_heating_efficiency)

    def calculate_consumption(self, demand: Demand, efficiency: float) -> Consumption:
        profile = demand.profile / efficiency
        return Consumption(profile=profile, fuel=self.fuel, units=demand.units)


class House:

    def __init__(self, house_type, floor_area_m2):

        self.floor_area_m2 = floor_area_m2
        self.type = house_type
        units = 'kWh'
        idx = constants.BASE_YEAR_HALF_HOUR_INDEX
        # Dummy data for now TODO get profiles from elsewhere
        self.base_demand = Demand(profile=pd.Series(index=idx, data=0.001 * floor_area_m2), units=units)
        self.water_heating_demand = Demand(profile=pd.Series(index=idx, data=0.004 * floor_area_m2), units=units)
        self.space_heat_demand = Demand(profile=pd.Series(index=idx, data=0.005 * floor_area_m2), units=units)

    def calculate_consumption(self, heating_system: HeatingSystem) -> Dict[str, Consumption]:

        # Base demand is always electricity (lighting/plug loads etc.)
        base_consumption = Consumption(profile=self.base_demand.profile,
                                       units=self.base_demand.units,
                                       fuel='electricity')
        space_heat_consumption = heating_system.calculate_space_heating_consumption(self.space_heat_demand)
        water_heat_consumption = heating_system.calculate_water_heating_consumption(self.water_heating_demand)
        heating_consumption = water_heat_consumption.add(space_heat_consumption)

        match heating_system.fuel:
            case base_consumption.fuel:
                consumption_all_fuels = {heating_system.fuel: base_consumption.add(heating_consumption)}
            case _:
                consumption_all_fuels = {base_consumption.fuel: base_consumption,
                                         heating_consumption.fuel: heating_consumption}

        return consumption_all_fuels


def check_valid_item(item: str, valid_items: List[str]):
    if item not in valid_items:
        raise ValueError(f"fuel must be one of {valid_items}")


def check_valid_fuel(fuel: str, valid_fuels: List[str] = constants.FUELS):
    check_valid_item(fuel, valid_fuels)


def check_valid_units(unit: str, valid_units: List[str] = constants.ENERGY_UNITS):
    check_valid_item(unit, valid_units)
