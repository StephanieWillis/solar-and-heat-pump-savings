import plotly.express as px
import streamlit as st

from building_model import *
import house_questions
from solar import Solar
from solar_questions import render_and_update_solar_inputs


def render(house: 'House', solar_install: 'Solar'):
    st.header("Your Heat Pump and Solar Savings")
    st.subheader("Energy Bills")
    bills_chart = st.empty()
    bills_text = st.empty()
    st.subheader("Carbon Emissions")
    carbon_chart = st.empty()
    carbon_text = st.empty()
    st.subheader("Energy Consumption")
    energy_chart = st.empty()
    energy_text = st.empty()

    with st.sidebar:
        st.header("Assumptions")
        st.subheader("Current Performance")
        house = house_questions.render_and_update_current_home(house)
        st.session_state["page_state"]["house"] = dict(house=house)  # so any overwrites saved if move tabs
        # saving state may work without above but above makes clearer

        st.subheader("Improvement Options")
        upgrade_heating, upgrade_solar = render_and_update_improvement_options(solar_install=solar_install)
        st.session_state["page_state"]["solar"] = dict(solar=upgrade_solar)  # so any overwrites saved if move tabs
        # saving state may work without above but above makes clearer
    # Upgraded buildings
    hp_house, solar_house, both_house = upgrade_buildings(baseline_house=house,
                                                          upgrade_heating=upgrade_heating,
                                                          upgrade_solar=upgrade_solar)

    # Combine results
    results_df = combine_results_dfs_multiple_houses([house, solar_house, hp_house, both_house],
                                                     ['Current', 'With solar', 'With a heat pump',
                                                      'With solar and a heat pump'])

    with bills_chart:
        render_bill_chart(results_df)
    with bills_text:
        render_bill_outputs(house=house, solar_house=solar_house, hp_house=hp_house, both_house=both_house)

    with energy_chart:
        render_consumption_chart(results_df)
    with energy_text:
        render_consumption_outputs(house=house, solar_house=solar_house, hp_house=hp_house, both_house=both_house)

    with carbon_chart:
        render_carbon_chart(results_df)
    with carbon_text:
        render_carbon_outputs(house=house, solar_house=solar_house, hp_house=hp_house, both_house=both_house)


def render_and_update_improvement_options(solar_install: Solar) -> Tuple[HeatingSystem, Solar]:
    with st.expander("Heat pump assumptions"):
        if "upgrade_heating" not in st.session_state["page_state"]:
            upgrade_heating = HeatingSystem.from_constants(name='Heat pump',
                                                           parameters=constants.DEFAULT_HEATING_CONSTANTS['Heat pump'])
            st.session_state["page_state"]["upgrade_heating"] = dict(upgrade_heating=upgrade_heating)  # in case this page isn't always rendered
        else:
            upgrade_heating = st.session_state["page_state"]["upgrade_heating"]["upgrade_heating"]

        upgrade_heating = house_questions.render_and_update_heating_system(heating_system=upgrade_heating)
        st.caption("The efficiency of your heat pump depends on how well the system is designed and how low a flow "
                   "temperature it can run at. A good, low flow temperature install can have a COP of about 3.8. "
                   "The historical median COP in the UK is 2.7, but a good installer nowadays will ensure you get a "
                   "much better COP than that")

    with st.expander("Solar PV assumptions "):
        solar_install = render_and_update_solar_inputs(solar=solar_install)

    return upgrade_heating, solar_install


def render_bill_chart(results_df: pd.DataFrame):
    render_savings_chart(results_df=results_df, y_variable='Your annual energy bill £')


def render_bill_outputs(house: 'House', solar_house: 'House', hp_house: 'House', both_house: 'House'):
    st.write(f'We calculate that {produce_current_bill_sentence(house)}  \n'
             f'- with solar {produce_hypothetical_bill_sentence(solar_house)}, '
             f' {produce_bill_saving_sentence(house=solar_house, baseline_house=house)}  \n'
             f'- with a heat pump {produce_hypothetical_bill_sentence(hp_house)}, '
             f' {produce_bill_saving_sentence(house=hp_house, baseline_house=house)}  \n'
             f'- with solar and a heat pump {produce_hypothetical_bill_sentence(both_house)}, '
             f' {produce_bill_saving_sentence(house=both_house, baseline_house=house)}  \n'
             )


def produce_current_bill_sentence(house) -> str:
    sentence = f'your energy bills for the next year will be £{int(house.total_annual_bill):,}'
    return sentence


def produce_hypothetical_bill_sentence(house) -> str:
    sentence = f'they would be £{int(house.total_annual_bill):,}'
    return sentence


def produce_bill_saving_sentence(house: 'House', baseline_house: 'House') -> str:
    sentence = f"that's a saving of £{int(baseline_house.total_annual_bill - house.total_annual_bill):,}"
    return sentence


def render_carbon_chart(results_df: pd.DataFrame):
    render_savings_chart(results_df=results_df, y_variable='Your annual carbon emissions tCO2')


def render_carbon_outputs(house: 'House', solar_house: 'House', hp_house: 'House', both_house: 'House'):
    st.write(
        f"We calculate that your house emits {house.total_annual_tco2:.2f} tonnes of CO2 per year  \n"
        f"- with solar that would fall to {solar_house.total_annual_tco2:.2f} tonnes of CO2 per year  \n"
        f"- with a heat pump that would fall to {hp_house.total_annual_tco2:.2f} tonnes of CO2 per year  \n"
        f"- with solar and a heat pump that would fall to {both_house.total_annual_tco2:.2f} "
        f"tonnes of CO2 per year  \n"
    )


def render_consumption_chart(results_df: pd.DataFrame):
    render_savings_chart(results_df=results_df, y_variable='Your annual energy use kwh')


def render_consumption_outputs(house: 'House', solar_house: 'House', hp_house: 'House', both_house: 'House'):
    st.write(
        f"We calculate that your house currently needs {produce_consumption_sentence(house)}  \n"
        f"- with solar that would fall to {produce_consumption_sentence(solar_house)}  \n"
        f"- with a heat pump that would fall to {produce_consumption_sentence(hp_house)}  \n"
        f"- with solar and a heat pump that would fall to {produce_consumption_sentence(both_house)} "
    )


def produce_consumption_sentence(house):
    if house.has_multiple_fuels:
        sentence = (f"{int(house.consumption_per_fuel['electricity'].overall.annual_sum_kwh):,} "
                    f"kwh of electricity and "
                    f"{int(house.consumption_per_fuel[house.heating_system.fuel.name].overall.annual_sum_fuel_units):,}"
                    f" {house.heating_system.fuel.units} of {house.heating_system.fuel.name} per year")
    else:
        sentence = f"{int(house.consumption_per_fuel['electricity'].overall.annual_sum_kwh):,}" \
                   f" kwh of electricity per year "
    return sentence


def render_savings_chart(results_df: pd.DataFrame, y_variable: str):
    bills_fig = px.bar(results_df, x='Upgrade option', y=y_variable, color='fuel')
    st.plotly_chart(bills_fig, use_container_width=True, sharing="streamlit")
