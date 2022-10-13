import copy

import pandas as pd
import streamlit as st
import plotly.express as px

from usage import *


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

    st.header("Detailed Inputs - Current")
    house = render_and_allow_overwrite_of_current_home(house)

    st.header("Detailed Inputs - Improvement Options")
    upgrade_heating = render_and_allow_overwrite_of_improvement_options()

    # Upgraded buildings
    hp_house = copy.deepcopy(house)  # do after modifications so modifications flow through
    hp_house.heating_system = upgrade_heating

    # Combine results
    results_df = combined_results_dfs_multiple_houses([house, hp_house], ['Current', 'With a heat pump'])

    with bills_chart:
        render_bill_chart(results_df)
    with bills_text:
        render_bill_outputs(house=house, hp_house=hp_house)

    with energy_chart:
        render_consumption_chart(results_df)
    with energy_text:
        render_consumption_outputs(house=house, hp_house=hp_house)

    # with carbon_chart:
    #     NotImplemented
    with carbon_text:
        st.write("Coming soon :)")

    return house


def render_house_questions() -> 'BuildingEnvelope':
    house_type = st.selectbox('House Type', options=constants.HOUSE_TYPES)
    house_floor_area_m2 = st.number_input(label='House floor area (m2)', min_value=0, max_value=500, value=80)
    envelope = BuildingEnvelope(house_type=house_type, floor_area_m2=house_floor_area_m2)
    return envelope


def render_heating_system_questions() -> str:
    heating_system_name = st.selectbox('Heating System', options=constants.DEFAULT_HEATING_CONSTANTS.keys())
    return heating_system_name


def render_and_allow_overwrite_of_current_home(house: House):
    st.write("We have estimated your homes current energy use and bills using assumptions based on your answers."
             " You can edit those assumptions below ")
    with st.expander("Demand assumptions"):
        house.envelope = render_and_allow_overwrite_of_envelope_outputs(envelope=house.envelope)
    with st.expander("Baseline heating system assumptions"):
        house.heating_system = render_and_allow_overwrite_of_heating_system(heating_system=house.heating_system)
    with st.expander("Tariff assumptions"):
        house = render_and_allow_overwrite_of_tariffs(house=house)
    return house


def render_and_allow_overwrite_of_improvement_options() -> HeatingSystem:
    st.write("We have used various assumptions to estimate the improvement potential of your home.."
             " You can edit those assumptions below.")
    with st.expander("Upgrade heating system assumptions"):
        upgrade_heating = HeatingSystem.from_constants(name='Heat pump',
                                                       parameters=constants.DEFAULT_HEATING_CONSTANTS['Heat pump'])
        upgrade_heating = render_and_allow_overwrite_of_heating_system(heating_system=upgrade_heating)
    return upgrade_heating


def render_and_allow_overwrite_of_envelope_outputs(envelope: 'BuildingEnvelope') -> 'BuildingEnvelope':
    st.write(f"We assume that an {envelope.floor_area_m2}m\u00b2 {envelope.house_type.lower()} needs about: ")
    envelope.space_heating_demand = render_and_allow_overwrite_of_annual_demand(label='Heating (kwh): ',
                                                                                demand=envelope.space_heating_demand)
    envelope.water_heating_demand = render_and_allow_overwrite_of_annual_demand(label='Hot water (kwh): ',
                                                                                demand=envelope.water_heating_demand)
    envelope.base_demand = render_and_allow_overwrite_of_annual_demand(label='Other (lighting/appliances etc.) (kwh): ',
                                                                       demand=envelope.base_demand)
    return envelope


def render_and_allow_overwrite_of_annual_demand(label: str, demand: 'Demand') -> 'Demand':
    """ If user overwrites annual total then scale whole profile by multiplier"""
    demand_overwrite = st.number_input(label=label, min_value=0, max_value=100000, value=int(demand.annual_sum))
    if demand_overwrite != int(demand.annual_sum):  # scale profile  by correction factor
        demand.profile_kwh = demand_overwrite / int(demand.annual_sum) * demand.profile_kwh
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
            f"{int(house.consumption_profile_per_fuel['electricity'].annual_sum_kwh):,} kwh of electricity a year. "
            f" \nWith a heat pump that value would fall to "
            f"{int(hp_house.consumption_profile_per_fuel['electricity'].annual_sum_kwh):,} kwh of electricity a year")
    else:
        st.write(
            f"We calculate that your house needs about "
            f"{int(house.consumption_profile_per_fuel['electricity'].annual_sum_kwh):,} kwh of electricity per year"
            f" and {int(house.consumption_profile_per_fuel[house.heating_system.fuel.name].annual_sum_fuel_units):,}"
            f" {house.heating_system.fuel.units} of {house.heating_system.fuel.name}. "
            f"  \nWith a heat pump that value would fall to "
            f"{int(hp_house.consumption_profile_per_fuel['electricity'].annual_sum_kwh):,} kwh of electricity a year")


def render_consumption_chart(results_df: pd.DataFrame):
    energy_fig = px.bar(results_df, x='Upgrade option', y='Your annual energy use kwh', color='fuel')
    st.plotly_chart(energy_fig, use_container_width=False, sharing="streamlit")


def render_and_allow_overwrite_of_tariffs(house: 'House') -> 'House':
    st.write(f"We have assumed that you are on a default energy tariff, but if you have fixed at a different rate"
             " then you can edit the numbers. Unfortunately we can't deal with variable rates like Octopus Agile/Go "
             "or Economy 7 right now, but we are working on it!")

    st.subheader('Electricity')
    house.tariffs['electricity'].p_per_unit = st.number_input(label='Unit rate (p/kwh), electricity',
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
            house.tariffs['gas'].p_per_unit = st.number_input(label='Unit rate (p/kwh), gas',
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


def render_bill_chart(results_df:pd.DataFrame):
    bills_fig = px.bar(results_df, x='Upgrade option', y='Your annual energy bill £', color='fuel')
    st.plotly_chart(bills_fig, use_container_width=False, sharing="streamlit")


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
