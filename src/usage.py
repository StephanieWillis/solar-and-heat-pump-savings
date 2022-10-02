from dataclasses import dataclass, asdict
from typing import Tuple, Dict, List

import pandas as pd
import streamlit as st

import constants


def render_questions() -> Tuple['House', 'HeatingSystem']:
    st.header("Your house")
    house = render_house_questions()
    heating_system = render_heating_system_questions()
    return house, heating_system


def render_outputs(house: 'House', heating_system: 'HeatingSystem'):
    st.header("Your current energy use ")
    st.write("Based on your answers in the last tab, we calculate that your home needs")
    with st.expander("Expand demand assumptions"):
        house = render_house_outputs(house=house)
    with st.expander("Expand heating system assumptions"):
        heating_system = render_heating_system_outputs(heating_system)
    consumption_dict = render_consumption_outputs(house=house, heating_system=heating_system)
    with st.expander("Expand tariff assumptions"):
        tariffs = render_tariff_outputs(consumption_dict=consumption_dict)
    annual_bills = render_bill_outputs(consumption_dict=consumption_dict, tariffs=tariffs)


def render_house_questions() -> 'House':
    house_type = st.selectbox('House Type', options=constants.HOUSE_TYPES)
    house_floor_area_m2 = st.number_input(label='House floor area (m2)', min_value=0, max_value=500, value=80)

    house = House(house_type=house_type, floor_area_m2=house_floor_area_m2)

    return house


def render_heating_system_questions() -> 'HeatingSystem':
    heating_system_name = st.selectbox('Heating System',
                                       options=constants.DEFAULT_HEATING_CONSTANTS.keys())
    heating_system = HeatingSystem.from_constants(name=heating_system_name,
                                                  parameters=constants.DEFAULT_HEATING_CONSTANTS[heating_system_name])
    return heating_system


def render_house_outputs(house: 'House') -> 'House':

    st.write(f"We assume that an {house.floor_area_m2}m\u00b2 {house.type.lower()} needs about: ")
    house.space_heating_demand = render_annual_demand_input_overwrite_if_needed(label='Heating (kWh): ',
                                                                                demand=house.space_heat_demand)
    house.water_heating_demand = render_annual_demand_input_overwrite_if_needed(label='Hot water (kWh): ',
                                                                                demand=house.water_heating_demand)
    house.base_demand = render_annual_demand_input_overwrite_if_needed(label='Other (lighting/appliances etc.) (kWh): ',
                                                                       demand=house.base_demand)
    return house


def render_annual_demand_input_overwrite_if_needed(label: str, demand: 'Demand') -> 'Demand':
    demand_overwrite = st.number_input(label=label, min_value=0, max_value=100000, value=int(demand.annual_sum))
    if demand_overwrite != int(demand.annual_sum): # scale profile  by corerction factor
        demand.profile_kWh = demand_overwrite / int(demand.annual_sum) * demand.profile_kWh
    return demand


def render_heating_system_outputs(heating_system: 'HeatingSystem') -> 'HeatingSystem':
    st.subheader("Your heating system")
    heating_system.space_heating_efficiency = st.number_input(label='Efficiency for space heating: ',
                                                              min_value=0.0,
                                                              max_value=10.0,
                                                              value=heating_system.space_heating_efficiency)
    heating_system.water_heating_efficiency = st.number_input(label='Efficiency for water heating: ',
                                                              min_value=0.0,
                                                              max_value=10.0,
                                                              value=heating_system.water_heating_efficiency)
    return heating_system


def render_consumption_outputs(house: 'House', heating_system: 'HeatingSystem') -> Dict[str, 'Consumption']:
    consumption_dict = house.calculate_consumption(heating_system=heating_system)

    if heating_system.fuel.name == 'electricity':
        st.write(
            f"We calculate that your house needs about "
            f"{int(consumption_dict['electricity'].annual_sum):,} kWh of electricity a year")
    else:
        st.write(
            f"We calculate that your house needs about "
            f"{int(consumption_dict['electricity'].annual_sum):,} kWh of electricity per year"
            f" and {int(consumption_dict[heating_system.fuel.name].annual_sum):,} {heating_system.fuel.units} of"
            f" {heating_system.fuel.name}")
    return consumption_dict


def render_tariff_outputs(consumption_dict: Dict[str, 'Consumption']) -> Dict[str, 'Tariff']:
    st.subheader("Your energy tariff")

    st.write(f"We have assumed that you are on a default energy tariff, but if you have fixed at a different rate"
             " then you can edit the numbers. Unfortunately we can't deal with variable rates like Octopus Agile/Go "
             "or Economy 7 right now, but we are working on it!")
    tariffs = {}

    st.subheader('Electricity')
    p_per_kWh_elec = st.number_input(label='Unit rate (p/kWh), electricity', min_value=0.0, max_value=100.0,
                                     value=constants.STANDARD_TARIFF.p_per_kWh_elec)
    p_per_day_elec = st.number_input(label='Standing charge (p/day), electricity', min_value=0.0, max_value=100.0,
                                     value=constants.STANDARD_TARIFF.p_per_day_elec)
    tariffs['electricity'] = Tariff(p_per_unit=p_per_kWh_elec,
                                    units='kWh',
                                    p_per_day=p_per_day_elec,
                                    fuel=constants.ELECTRICITY)
    if 'gas' in consumption_dict.keys():
        st.subheader('Gas')
        p_per_kWh_gas = st.number_input(label='Unit rate (p/kWh), gas',
                                        min_value=0.0,
                                        max_value=100.0,
                                        value=constants.STANDARD_TARIFF.p_per_kWh_gas)
        p_per_day_gas = st.number_input(label='Standing charge (p/day), gas',
                                        min_value=0.0,
                                        max_value=100.0,
                                        value=constants.STANDARD_TARIFF.p_per_day_gas)
        tariffs['gas'] = Tariff(p_per_unit=p_per_kWh_gas,
                                units='kWh',
                                p_per_day=p_per_day_gas,
                                fuel=constants.GAS)
    if 'oil' in consumption_dict.keys():
        st.subheader('Oil')
        p_per_L_oil = st.number_input(label='Oil price, (p/litre)', min_value=0.0, max_value=200.0,
                                      value=constants.STANDARD_TARIFF.p_per_L_oil)
        tariffs['oil'] = Tariff(p_per_unit=p_per_L_oil,
                                units='litres',
                                p_per_day=0.0,
                                fuel=constants.OIL)
    return tariffs


def render_bill_outputs(consumption_dict: [str, 'Consumption'], tariffs: Dict[str, 'Tariff']) -> Dict[str, float]:

    annual_bills = {}
    for fuel_name, consumption in consumption_dict.items():
        annual_bills[fuel_name] = consumption.calculate_annual_cost(tariffs[fuel_name])

    annual_bill_total = sum(annual_bills.values())
    has_multiple_fuels = len(consumption_dict) > 1
    breakdown = f'({", ".join(f"£{int(amount):,} for {fuel_name}" for fuel_name, amount in annual_bills.items())})'

    st.write(f'We calculate that your annual energy bill on this tariff will be £{int(annual_bill_total):,}'
             f' {breakdown if has_multiple_fuels else ""}')
    return annual_bills


class House:

    def __init__(self, house_type, floor_area_m2):

        self.floor_area_m2 = floor_area_m2
        self.type = house_type

        idx = constants.BASE_YEAR_HALF_HOUR_INDEX
        units = 'kWh'
        # Dummy data for now TODO get profiles from elsewhere
        self.base_demand = Demand(profile_kWh=pd.Series(index=idx, data=0.001 * floor_area_m2))
        self.water_heating_demand = Demand(profile_kWh=pd.Series(index=idx, data=0.004 * floor_area_m2))
        self.space_heat_demand = Demand(profile_kWh=pd.Series(index=idx, data=0.005 * floor_area_m2))

    def calculate_consumption(self, heating_system: 'HeatingSystem') -> Dict[str, 'Consumption']:

        # Base demand is always electricity (lighting/plug loads etc.)
        base_consumption = Consumption(profile=self.base_demand.profile_kWh,
                                       fuel=constants.ELECTRICITY)
        space_heat_consumption = heating_system.calculate_space_heating_consumption(self.space_heat_demand)
        water_heat_consumption = heating_system.calculate_water_heating_consumption(self.water_heating_demand)
        heating_consumption = water_heat_consumption.add(space_heat_consumption)

        match heating_system.fuel:
            case base_consumption.fuel:  # heating system is electric so only one fuel
                consumption_all_fuels = {heating_system.fuel.name: base_consumption.add(heating_consumption)}
            case _:
                consumption_all_fuels = {base_consumption.fuel.name: base_consumption,
                                         heating_consumption.fuel.name: heating_consumption}

        return consumption_all_fuels


@dataclass
class Demand:
    profile_kWh: pd.Series  # TODO: figure out how to specify index should be datetime in typing?

    @property
    def annual_sum(self) -> float:
        annual_sum = self.profile_kWh.sum()
        return annual_sum

    def add(self, other: 'Demand') -> 'Demand':
        combined_time_series = self.profile_kWh + other.profile_kWh
        combined = Demand(profile_kWh=combined_time_series)
        return combined


@dataclass
class Consumption:
    profile: pd.Series
    fuel: constants.Fuel = 'electricity'

    @property
    def annual_sum(self) -> float:
        annual_sum = self.profile.sum()
        return annual_sum

    def add(self, other: 'Consumption') -> 'Consumption':
        if self.fuel == other.fuel:
            combined_time_series = self.profile + other.profile
            combined = Consumption(profile=combined_time_series, fuel=self.fuel)
        else:
            raise ValueError("The fuel of the two consumptions must match")
            # idea: maybe this should work and just return a list?
        return combined

    def calculate_annual_cost(self, tariff: 'Tariff') -> float:

        if self.fuel != tariff.fuel:
            raise ValueError("To calculate annual costs the tariff fuel must match the consumption fuel, they are"
                             f"{tariff.fuel} and {self.fuel}")
        annual_cost = (365 * tariff.p_per_day + self.annual_sum * tariff.p_per_unit)/100
        return annual_cost


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

    def calculate_space_heating_consumption(self, space_heat_demand: Demand) -> Consumption:
        return self.calculate_consumption(demand=space_heat_demand, efficiency=self.space_heating_efficiency)

    def calculate_water_heating_consumption(self, water_heat_demand: Demand) -> Consumption:
        return self.calculate_consumption(demand=water_heat_demand, efficiency=self.water_heating_efficiency)

    def calculate_consumption(self, demand: Demand, efficiency: float) -> Consumption:
        profile_kWh = demand.profile_kWh / efficiency
        profile = profile_kWh / self.fuel.converter_consumption_units_to_kWh
        return Consumption(profile=profile, fuel=self.fuel)


@dataclass
class Tariff:
    p_per_unit: float
    units: str
    p_per_day: float
    fuel: constants.Fuel
