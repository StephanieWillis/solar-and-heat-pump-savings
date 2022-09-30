from dataclasses import dataclass, asdict
from typing import Tuple, Dict, List

import pandas as pd
import streamlit as st

import constants


@dataclass
class Demand:
    profile: pd.Series  # TODO: figure out how to specify index should be datetime?
    units: str

    def __post_init__(self):
        if self.units not in constants.ENERGY_UNITS:
            raise ValueError(f"fuel must be one of {constants.ENERGY_UNITS}")

    @property
    def annual_sum(self) -> float:
        annual_consumption = self.profile.sum()
        return annual_consumption

    def add(self, other: 'Demand') -> 'Demand':
        if self.units == other.units:
            combined_time_series = self.profile + other.profile
            combined = Demand(time_series=combined_time_series, units=self.units)
        #     TODO: should this change the base class
        else:
            raise ValueError("The units of the two energy time series must match")
        return combined


@dataclass
class Consumption(Demand):
    units: str = 'kWh'
    fuel: str = 'electricity'

    def __post_init__(self):
        if self.fuel not in constants.FUELS:
            raise ValueError(f"fuel must be one of {constants.FUELS}")

    def add(self, other: 'Consumption') -> 'Consumption':
        if self.fuel == other.fuel and self.units == other.units:
            combined_time_series = self.profile + other.profile
            combined = Consumption(profile=combined_time_series, units=self.units, fuel=self.fuel)
        else:
            raise ValueError("The fuel and units of the two consumptions must match")
            # idea: maybe this should work and just return a list?
        return combined


@dataclass
class HeatingSystem:
    space_heating_efficiency: float
    water_heating_efficiency: float
    fuel: str

    @classmethod
    def from_constants(cls, parameters: constants.HeatingConstants):
        return cls(space_heating_efficiency=parameters.space_heating_efficiency,
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


def render() -> Tuple[House, Dict[str, Consumption]]:
    st.subheader("Your current energy usage")

    st.write("To estimate your current energy use we need a few bits of information about your house:")

    house_floor_area_m2 = st.number_input(label='House floor area (m2)', min_value=0, max_value=500, value=80)
    house_type = st.selectbox('House Type', options=constants.HOUSE_TYPES)
    house = House(house_type=house_type, floor_area_m2=house_floor_area_m2)

    heating_system_name = st.selectbox('Heating System', options=constants.DEFAULT_HEATING_CONSTANTS.keys())
    heating_system = HeatingSystem.from_constants(constants.DEFAULT_HEATING_CONSTANTS[heating_system_name])
    consumption_dict = house.calculate_consumption(heating_system=heating_system)

    st.write(f'Your house is an {house.floor_area_m2} m\u00b2 {house.type}')

    st.write(f'Your heating system is a {heating_system_name}. '
             f'It has an efficiency of {heating_system.space_heating_efficiency:.0%} in space heating and '
             f'{heating_system.water_heating_efficiency:.0%} when heating water')

    # TODO: figure out how to render these with a comma
    if heating_system.fuel == 'electricity':
        st.write(f"We think your home needs {int(consumption_dict['electricity'].annual_sum):,} kWh of electricity a year"
                 )
    else:
        st.write(f"We think your home needs {int(consumption_dict['electricity'].annual_sum):,} kWh of electricity a year"
                 f" and {int(consumption_dict[heating_system.fuel].annual_sum)} kWh of {heating_system.fuel}")

    return house, consumption_dict
