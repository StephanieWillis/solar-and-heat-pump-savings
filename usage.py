from dataclasses import dataclass, asdict
from typing import Tuple, Dict

import pandas as pd
import streamlit as st

import constants


def render() -> Tuple[float, str]:
    st.subheader("Your current energy usage")

    house_floor_area_m2 = st.number_input(label='floor_area', min_value=0, max_value=500, value=80)
    house_type = st.selectbox('House Type', options=constants.HOUSE_TYPES)
    house = House(house_type=house_type, house_floor_area_m2=house_floor_area_m2)

    heating_systems = {'Heat Pump': HeatingSystem(3.5, 3, 'electricity'),
                       'Gas Boiler': HeatingSystem(0.85, 0.8, 'gas'),
                       'Oil Boiler': HeatingSystem(0.85, 0.8, 'oil'),
                       'Direct Electric': HeatingSystem(1, 1, 'electricity')
                       }
    heating_system_name = st.selectbox('Heating System', options=heating_systems.keys())
    heating_system = heating_systems[heating_system_name]

    consumption = house.calculate_consumption(heating_system=heating_system)

    st.write(f'Your house is an {house_floor_area_m2} m\u00b2 {house_type}')

    st.write(f'Your heating system is a {heating_system_name}. '
             f'It has an efficiency of {heating_system.space_heating_efficiency:.0%} in space heating and '
             f'{heating_system.water_heating_efficiency:.0%} when heating water')

    if heating_system.fuel == 'electricity':
        st.write(f"We think your home needs {int(consumption.annual_sum['electricity'])} kWh of electricity a year")
    else:
        st.write(f"We think your home needs {int(consumption.annual_sum['electricity'])} kWh of electricity a year"
                 f" and {int(consumption.annual_sum[heating_system.fuel])} kWh of {heating_system.fuel}")

    return house_floor_area_m2, heating_system


@dataclass
class Consumption:
    electricity: pd.Series
    gas: pd.Series = constants.EMPTY_TIMESERIES
    oil: pd.Series = constants.EMPTY_TIMESERIES

    @property
    def annual_sum(self):
        # consumption already in kWh (not in kW! so can just sum, don't need to divide by 2 because half hourly)
        aggregated_consumption = {fuel: consumption.sum() for fuel, consumption in asdict(self).items()}
        return aggregated_consumption


@dataclass
class HeatingSystem:
    space_heating_efficiency: float
    water_heating_efficiency: float
    fuel: str

    def __post_init__(self):
        if self.fuel not in constants.FUELS:
            raise ValueError(f"fuel must be one of {constants.FUELS}")

    def calculate_consumption(self, space_heat_demand: pd.Series, water_heat_demand: pd.Series
                              ) -> Tuple[pd.Series, pd.Series]:
        space_heat_consumption = space_heat_demand / self.space_heating_efficiency
        water_heat_consumption = water_heat_demand / self.water_heating_efficiency
        return space_heat_consumption, water_heat_consumption


class House:

    def __init__(self, house_type, house_floor_area_m2):
        idx = constants.BASE_YEAR_HALF_HOUR_INDEX
        self.base_demand_kwh = pd.Series(index=idx, data=0.1)  # assume 100W
        self.hot_water_demand_kwh = pd.Series(index=idx, data=0.4)  # assume 400W
        self.space_heat_demand_kwh = pd.Series(index=idx, data=0.5)  # assume 500W

    def calculate_consumption(self, heating_system: HeatingSystem) -> Consumption:

        space_heat_consumption, water_heat_consumption = heating_system.calculate_consumption(
            space_heat_demand=self.space_heat_demand_kwh,
            water_heat_demand=self.hot_water_demand_kwh)
        base_consumption_kwh = self.base_demand_kwh
        heating_consumption_kwh = water_heat_consumption + space_heat_consumption

        electricity = base_consumption_kwh

        if heating_system.fuel == 'electricity':
            electricity += heating_consumption_kwh
        return Consumption(electricity=electricity,
                           gas=heating_consumption_kwh if heating_system.fuel == 'gas' else constants.EMPTY_TIMESERIES,
                           oil=heating_consumption_kwh if heating_system.fuel == 'oil' else constants.EMPTY_TIMESERIES)



