import copy
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import streamlit as st
import plotly.express as px

import constants


def render_questions() -> 'House':
    st.header("Your House")
    envelope = render_house_questions()
    heating_system_name = render_heating_system_questions()
    house = House.set_up_from_heating_name(envelope=envelope, heating_name=heating_system_name)
    return house


def render_outputs(house: 'House') -> 'House':
    st.header("Your Heat Pump and Solar Savings")
    st.subheader("Energy Bills")
    bills_chart = st.empty()
    bills_text = st.empty()
    st.subheader("Energy Consumption")
    energy_chart = st.empty()
    energy_text = st.empty()
    st.subheader("Carbon Emissions")
    carbon_chart = st.empty()
    carbon_text = st.empty()

    st.header("Detailed Inputs")
    st.write("We have estimated your homes current energy use and bills using assumptions based on your answers."
             " You can edit those assumptions below ")
    with st.expander("Demand assumptions"):
        house.envelope = render_and_allow_overwrite_of_envelope_outputs(envelope=house.envelope)
    with st.expander("Baseline heating system assumptions"):
        house.heating_system = render_and_allow_overwrite_of_heating_system(heating_system=house.heating_system)
    with st.expander("Upgrade heating system assumptions"):
        upgrade_heating = HeatingSystem.from_constants(name='Heat pump',
                                                       parameters=constants.DEFAULT_HEATING_CONSTANTS['Heat pump'])
        upgrade_heating = render_and_allow_overwrite_of_heating_system(heating_system=upgrade_heating)
    with st.expander("Tariff assumptions"):
        house = render_and_allow_overwrite_of_tariffs(house=house)

    # Upgraded buildings
    hp_house = copy.deepcopy(house)  # do after modifications so modifications flow through
    hp_house.heating_system = upgrade_heating

    # Combine results
    results_df = combined_results_dfs_multiple_houses([house, hp_house], ['Current', 'With a heat pump'])

    with bills_chart:
        bills_fig = px.bar(results_df, x='Upgrade option', y='Your annual energy bill £', color='fuel')
        st.plotly_chart(bills_fig, use_container_width=False, sharing="streamlit")
    with bills_text:
        render_bill_outputs(house=house, hp_house=hp_house)

    with energy_chart:
        energy_fig = px.bar(results_df, x='Upgrade option', y='Your annual energy use kWh', color='fuel')
        st.plotly_chart(energy_fig, use_container_width=False, sharing="streamlit")
    with energy_text:
        render_consumption_outputs(house=house, hp_house=hp_house)

    # with carbon_chart:
    #     NotImplemented
    with carbon_text:
        st.write("Coming soon :)")

    return house


def combined_results_dfs_multiple_houses(houses: List['House'], keys: List['str']):
    results_df = pd.concat([house.energy_and_bills_df for house in houses], keys=keys)
    results_df.index.names = ['Upgrade option', 'old_index']
    results_df = results_df.reset_index()
    results_df = results_df.drop(columns='old_index')
    return results_df


def render_house_questions() -> 'BuildingEnvelope':
    house_type = st.selectbox('House Type', options=constants.HOUSE_TYPES)
    house_floor_area_m2 = st.number_input(label='House floor area (m2)', min_value=0, max_value=500, value=80)
    envelope = BuildingEnvelope(house_type=house_type, floor_area_m2=house_floor_area_m2)
    return envelope


def render_heating_system_questions() -> str:
    heating_system_name = st.selectbox('Heating System', options=constants.DEFAULT_HEATING_CONSTANTS.keys())
    return heating_system_name


def render_and_allow_overwrite_of_envelope_outputs(envelope: 'BuildingEnvelope') -> 'BuildingEnvelope':
    st.write(f"We assume that an {envelope.floor_area_m2}m\u00b2 {envelope.house_type.lower()} needs about: ")
    envelope.space_heating_demand = render_and_allow_overwrite_of_annual_demand(label='Heating (kWh): ',
                                                                                demand=envelope.space_heating_demand)
    envelope.water_heating_demand = render_and_allow_overwrite_of_annual_demand(label='Hot water (kWh): ',
                                                                                demand=envelope.water_heating_demand)
    envelope.base_demand = render_and_allow_overwrite_of_annual_demand(label='Other (lighting/appliances etc.) (kWh): ',
                                                                       demand=envelope.base_demand)
    return envelope


def render_and_allow_overwrite_of_annual_demand(label: str, demand: 'Demand') -> 'Demand':
    """ If user overwrites annual total then scale whole profile by multiplier"""
    demand_overwrite = st.number_input(label=label, min_value=0, max_value=100000, value=int(demand.annual_sum))
    if demand_overwrite != int(demand.annual_sum):  # scale profile  by correction factor
        demand.profile_kWh = demand_overwrite / int(demand.annual_sum) * demand.profile_kWh
    return demand


def render_and_allow_overwrite_of_heating_system(heating_system: 'HeatingSystem') -> 'HeatingSystem':
    heating_system.space_heating_efficiency = st.number_input(label='Efficiency for space heating: ',
                                                              min_value=0.0,
                                                              max_value=8.0,
                                                              value=heating_system.space_heating_efficiency)
    heating_system.water_heating_efficiency = st.number_input(label='Efficiency for water heating: ',
                                                              min_value=0.0,
                                                              max_value=8.0,
                                                              value=heating_system.water_heating_efficiency)
    return heating_system


def render_consumption_outputs(house: 'House', hp_house: 'House'):
    if house.heating_system.fuel.name == 'electricity':
        # TODO: catch case where there is already a heat pump?
        st.write(
            f"We calculate that your house currently needs about "
            f"{int(house.consumption_profile_per_fuel['electricity'].annual_sum):,} kWh of electricity a year"
            f" \nWith a heat pump that value would fall to "
            f"{int(hp_house.consumption_profile_per_fuel['electricity'].annual_sum):,} kWh of electricity a year")
    else:
        st.write(
            f"We calculate that your house needs about "
            f"{int(house.consumption_profile_per_fuel['electricity'].annual_sum):,} kWh of electricity per year"
            f" and {int(house.consumption_profile_per_fuel[house.heating_system.fuel.name].annual_sum):,}"
            f" {house.heating_system.fuel.units} of {house.heating_system.fuel.name}. "
            f"  \nWith a heat pump that value would fall to "
            f"{int(hp_house.consumption_profile_per_fuel['electricity'].annual_sum):,} kWh of electricity a year")


def render_and_allow_overwrite_of_tariffs(house: 'House') -> 'House':
    st.write(f"We have assumed that you are on a default energy tariff, but if you have fixed at a different rate"
             " then you can edit the numbers. Unfortunately we can't deal with variable rates like Octopus Agile/Go "
             "or Economy 7 right now, but we are working on it!")

    st.subheader('Electricity')
    house.tariffs['electricity'].p_per_unit = st.number_input(label='Unit rate (p/kWh), electricity',
                                                              min_value=0.0,
                                                              max_value=100.0,
                                                              value=house.tariffs['electricity'].p_per_unit)
    house.tariffs['electricity'].p_per_day = st.number_input(label='Standing charge (p/day), electricity',
                                                             min_value=0.0,
                                                             max_value=100.0,
                                                             value=house.tariffs['electricity'].p_per_day)
    match house.heating_system.fuel.name:
        case 'gas':
            st.subheader('Gas')
            house.tariffs['gas'].p_per_unit = st.number_input(label='Unit rate (p/kWh), gas',
                                                              min_value=0.0,
                                                              max_value=100.0,
                                                              value=house.tariffs['gas'].p_per_unit)
            house.tariffs['gas'].p_per_day = st.number_input(label='Standing charge (p/day), gas',
                                                             min_value=0.0,
                                                             max_value=100.0,
                                                             value=house.tariffs['gas'].p_per_day)
        case 'oil':
            st.subheader('Oil')
            house.tariffs['oil'].p_per_unit = st.number_input(label='Oil price, (p/litre)',
                                                              min_value=0.0,
                                                              max_value=200.0,
                                                              value=house.tariffs['oil'].p_per_unit)
    return house


def render_bill_outputs(house: 'House', hp_house: 'House'):
    breakdown = (
        f'({", ".join(f"£{int(amount):,} for {fuel_name}" for fuel_name, amount in house.annual_bill_per_fuel.items())})')
    if house.total_annual_bill > hp_house.total_annual_bill:
        verb = 'drop'
    else:
        verb = 'increase'

    st.write(f'We calculate that your energy bills for the next year will be'
             f' £{int(house.total_annual_bill):,} {breakdown if house.has_multiple_fuels else ""}. '
             f' \nWith a heat pump we calculate that your energy bills will {verb} '
             f'to £{int(hp_house.total_annual_bill):,}.'
             f'  \nThat is a saving of £{int(house.total_annual_bill - hp_house.total_annual_bill):,}.')


class House:
    """ Stores info on consumption and bills """

    def __init__(self, envelope: 'BuildingEnvelope', heating_system: 'HeatingSystem'):

        self.envelope = envelope
        # Set up initial values for heating system and tariffs but allow to be modified by the user later
        # Maybe I should be using getters and setters here?
        self.heating_system = heating_system
        self.tariffs = self.set_up_standard_tariffs()

    @classmethod
    def set_up_from_heating_name(cls, envelope: 'BuildingEnvelope', heating_name: str) -> 'House':
        heating_system = HeatingSystem.from_constants(name=heating_name,
                                                      parameters=constants.DEFAULT_HEATING_CONSTANTS[heating_name])
        return cls(envelope=envelope, heating_system=heating_system)

    def set_up_standard_tariffs(self) -> Dict[str, 'Tariff']:

        tariffs = {'electricity': Tariff(p_per_unit=constants.STANDARD_TARIFF.p_per_kWh_elec,
                                         p_per_day=constants.STANDARD_TARIFF.p_per_day_elec,
                                         fuel=constants.ELECTRICITY)}
        match self.heating_system.fuel.name:
            case 'gas':
                tariffs['gas'] = Tariff(p_per_unit=constants.STANDARD_TARIFF.p_per_kWh_gas,
                                        p_per_day=constants.STANDARD_TARIFF.p_per_day_gas,
                                        fuel=self.heating_system.fuel)
            case 'oil':
                tariffs['oil'] = Tariff(p_per_unit=constants.STANDARD_TARIFF.p_per_L_oil,
                                        p_per_day=0.0,
                                        fuel=self.heating_system.fuel)
        return tariffs

    @property
    def has_multiple_fuels(self) -> bool:
        return len(self.tariffs) > 1

    @property
    def consumption_profile_per_fuel(self) -> Dict[str, 'Consumption']:

        # Base demand is always electricity (lighting/plug loads etc.)
        base_consumption = Consumption(profile=self.envelope.base_demand.profile_kWh,
                                       fuel=constants.ELECTRICITY)
        space_heating_consumption = self.heating_system.calculate_space_heating_consumption(
            self.envelope.space_heating_demand)
        water_heating_consumption = self.heating_system.calculate_water_heating_consumption(
            self.envelope.water_heating_demand)
        heating_consumption = water_heating_consumption.add(space_heating_consumption)

        match self.heating_system.fuel:
            case base_consumption.fuel:  # only one fuel (electricity)
                consumption_dict = {self.heating_system.fuel.name: base_consumption.add(heating_consumption)}
            case _:
                consumption_dict = {base_consumption.fuel.name: base_consumption,
                                    heating_consumption.fuel.name: heating_consumption}

        return consumption_dict

    @property
    def annual_consumption_per_fuel(self) -> Dict[str, float]:
        return {fuel: consumption.annual_sum for fuel, consumption in self.consumption_profile_per_fuel.items()}

    @property
    def total_annual_consumption(self) -> float:
        return sum(self.annual_consumption_per_fuel.values())

    @property
    def annual_bill_per_fuel(self) -> Dict[str, float]:
        bills_dict = {}
        for fuel_name, consumption in self.consumption_profile_per_fuel.items():
            bills_dict[fuel_name] = self.tariffs[fuel_name].calculate_annual_cost(consumption)
        return bills_dict

    @property
    def total_annual_bill(self) -> float:
        return sum(self.annual_bill_per_fuel.values())

    @property
    def energy_and_bills_df(self) -> pd.DataFrame:
        df = pd.DataFrame(data={'Your annual energy use kWh': self.annual_consumption_per_fuel,
                                'Your annual energy bill £': self.annual_bill_per_fuel})
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
        self.units: str = 'kWh'

        # Set initial demand values - user can overwrite later
        # Dummy data for now TODO get profiles from elsewhere
        self.base_demand = Demand(profile_kWh=pd.Series(index=self.time_series_idx, data=0.001 * self.floor_area_m2))
        self.water_heating_demand = Demand(
            profile_kWh=pd.Series(index=self.time_series_idx, data=0.004 * self.floor_area_m2))
        self.space_heating_demand = Demand(
            profile_kWh=pd.Series(index=self.time_series_idx, data=0.005 * self.floor_area_m2))


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
    fuel: constants.Fuel = constants.ELECTRICITY

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
        profile_kwh = demand.profile_kWh / efficiency
        profile = profile_kwh / self.fuel.converter_consumption_units_to_kWh
        return Consumption(profile=profile, fuel=self.fuel)


@dataclass
class Tariff:
    p_per_unit: float  # unit defined by the fuel
    p_per_day: float
    fuel: constants.Fuel

    def calculate_annual_cost(self, consumption: 'Consumption') -> float:
        if self.fuel != consumption.fuel:
            raise ValueError("To calculate annual costs the tariff fuel must match the consumption fuel, they are"
                             f"{self.fuel} and {consumption.fuel}")
        annual_cost = (365 * self.p_per_day + consumption.annual_sum * self.p_per_unit) / 100
        return annual_cost
