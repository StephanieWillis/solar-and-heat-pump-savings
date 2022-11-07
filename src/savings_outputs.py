import plotly.express as px
import streamlit as st

from building_model import *
import house_questions
from solar import Solar
from solar_questions import render_and_update_solar_inputs


def render(house: "House", solar_install: "Solar"):

    with st.sidebar:
        st.header("Assumptions")
        st.subheader("Current Performance")
        house = house_questions.overwrite_house_assumptions(house)
        st.session_state["page_state"]["house"] = dict(house=house)  # so any overwrites saved if move tabs
        # saving state may work without above but above makes clearer

        st.subheader("Improvement Options")
        upgrade_heating, upgrade_solar = render_and_update_improvement_options(solar_install=solar_install)
        st.session_state["page_state"]["solar"] = dict(solar=upgrade_solar)  # so any overwrites saved if move tabs
        # saving state may work without above but above makes clearer

    # Upgraded buildings
    hp_house, solar_house, both_house = upgrade_buildings(
        baseline_house=house, upgrade_heating=upgrade_heating, upgrade_solar=upgrade_solar
    )

    # Combine results
    results_df = combine_results_dfs_multiple_houses(
        [house, solar_house, hp_house, both_house],
        ["Current", "With solar", "With a heat pump", "With solar and a heat pump"],
    )

    st.markdown(
        f"<h2> On your bills of <span style='color:hsl(220, 60%, 30%)'> £{int(house.total_annual_bill):,d} </span> you could save </h2>",
        unsafe_allow_html=True,
    )
    _, col1, col2, col3, _ = st.columns([0.2, 1, 1, 1, 0.2])
    with col1:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate'>☀️ £{int(house.total_annual_bill - solar_house.total_annual_bill):,d} </p>"
            "<p> with solar panels</p>" "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate'> 💨 £{int(house.total_annual_bill - hp_house.total_annual_bill):,d}</p>"
            f"<p> with a heat pump</p>" "</div>",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate'> 😍 £{int(house.total_annual_bill - both_house.total_annual_bill):,d} </p>"
            "<p> with both</p>" "</div>",
            unsafe_allow_html=True,
        )

    with st.expander("Show me the maths!"):
        render_bill_chart(results_df)
        render_consumption_outputs(house=house, solar_house=solar_house, hp_house=hp_house, both_house=both_house)
        render_consumption_chart(results_df)

    st.markdown(
        f"<h2>Your home currently emits about <span style='color:hsl(220, 60%, 30%)'>{house.total_annual_tco2:.2f} tonnes"
        f" </span>of CO2e each year, but you could cut your emissions by </h2>",
        unsafe_allow_html=True,
    )

    _, col1, col2, col3, _ = st.columns([0.2, 1, 1, 1, 0.2])

    with col1:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '>☀️ {int(100*((house.total_annual_tco2 - solar_house.total_annual_tco2)/house.total_annual_tco2))}%</p>"
            f"<p class='bill-details snug'> tCO2e</p>"
            "<p> with solar panels</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '> 💨️ {int(100*((house.total_annual_tco2 - hp_house.total_annual_tco2)/house.total_annual_tco2))}%</p>"
            f"<p class='bill-details snug '> tCO2e</p>"
            f"<p> with a heat pump</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '>😍️ {int(100*((house.total_annual_tco2 - both_house.total_annual_tco2)/house.total_annual_tco2))}%</p>"
            f"<p class='bill-details snug '> tCO2e</p>"
            "<p> with both</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with st.expander("Show me the maths!"):
        render_carbon_chart(results_df)
        render_carbon_outputs(house=house, solar_house=solar_house, hp_house=hp_house, both_house=both_house)


def render_and_update_improvement_options(solar_install: Solar) -> Tuple[HeatingSystem, Solar]:
    with st.expander("Heat pump assumptions"):
        if "upgrade_heating" not in st.session_state["page_state"]:
            upgrade_heating = HeatingSystem.from_constants(
                name="Heat pump", parameters=constants.DEFAULT_HEATING_CONSTANTS["Heat pump"]
            )
            st.session_state["page_state"]["upgrade_heating"] = dict(upgrade_heating=upgrade_heating)
            # in case this page isn't always rendered
        else:
            upgrade_heating = st.session_state["page_state"]["upgrade_heating"]["upgrade_heating"]

        upgrade_heating = overwrite_upgrade_heating_system_assumptions(heating_system=upgrade_heating)

        st.caption("The efficiency of your heat pump depends on how well the system is designed and how low a flow "
                   "temperature it can run at. A COP of 3.6 or more is possible with a high quality, low flow temperature "
                   "install.  \n  \n"
                   "A good installer is key to ensuring your heat pump runs efficiently. The [heat geek map"
                   "](https://www.heatgeek.com/find-a-heat-geek/) is a great place to start your search.")

    with st.expander("Solar PV assumptions "):
        solar_install = render_and_update_solar_inputs(solar=solar_install)

    return upgrade_heating, solar_install


def overwrite_upgrade_heating_system_assumptions(heating_system: 'HeatingSystem') -> 'HeatingSystem':

    if "upgrade_heating_efficiency" not in st.session_state:
        st.session_state.upgrade_heating_efficiency = heating_system.efficiency
    heating_system.efficiency = st.number_input(label='Efficiency: ',
                                                min_value=0.0,
                                                max_value=8.0,
                                                key="upgrade_heating_efficiency")
    return heating_system


def render_bill_chart(results_df: pd.DataFrame):
    render_savings_chart(results_df=results_df, y_variable="Your annual energy bill £")


def render_bill_outputs(house: "House", solar_house: "House", hp_house: "House", both_house: "House"):
    st.write(
        f"We calculate that {produce_current_bill_sentence(house)}  \n"
        f"- with solar {produce_hypothetical_bill_sentence(solar_house)}, "
        f" {produce_bill_saving_sentence(house=solar_house, baseline_house=house)}  \n"
        f"- with a heat pump {produce_hypothetical_bill_sentence(hp_house)}, "
        f" {produce_bill_saving_sentence(house=hp_house, baseline_house=house)}  \n"
        f"- with solar and a heat pump {produce_hypothetical_bill_sentence(both_house)}, "
        f" {produce_bill_saving_sentence(house=both_house, baseline_house=house)}  \n"
    )


def produce_current_bill_sentence(house) -> str:
    sentence = f"your energy bills for the next year will be £{int(house.total_annual_bill):,}"
    return sentence


def produce_hypothetical_bill_sentence(house) -> str:
    sentence = f"they would be £{int(house.total_annual_bill):,}"
    return sentence


def produce_bill_saving_sentence(house: "House", baseline_house: "House") -> str:
    sentence = f"that's a saving of £{int(baseline_house.total_annual_bill - house.total_annual_bill):,}"
    return sentence


def render_carbon_chart(results_df: pd.DataFrame):
    render_savings_chart(results_df=results_df, y_variable="Your annual carbon emissions tCO2")


def render_carbon_outputs(house: "House", solar_house: "House", hp_house: "House", both_house: "House"):
    st.write(
        f"We calculate that your house emits {house.total_annual_tco2:.2f} tonnes of CO2 per year  \n"
        f"- with solar that would fall to {solar_house.total_annual_tco2:.2f} tonnes of CO2 per year  \n"
        f"- with a heat pump that would fall to {hp_house.total_annual_tco2:.2f} tonnes of CO2 per year  \n"
        f"- with solar and a heat pump that would fall to {both_house.total_annual_tco2:.2f} "
        f"tonnes of CO2 per year  \n"
    )


def render_consumption_chart(results_df: pd.DataFrame):
    render_savings_chart(results_df=results_df, y_variable="Your annual energy use kwh")


def render_consumption_outputs(house: "House", solar_house: "House", hp_house: "House", both_house: "House"):
    st.write(
        f"We calculate that your house currently needs {produce_consumption_sentence(house)}  \n"
        f"- with solar that would fall to {produce_consumption_sentence(solar_house)}  \n"
        f"- with a heat pump that would fall to {produce_consumption_sentence(hp_house)}  \n"
        f"- with solar and a heat pump that would fall to {produce_consumption_sentence(both_house)} "
    )


def produce_consumption_sentence(house):
    if house.has_multiple_fuels:
        sentence = (
            f"{int(house.consumption_per_fuel['electricity'].overall.annual_sum_kwh):,} "
            f"kwh of electricity and "
            f"{int(house.consumption_per_fuel[house.heating_system.fuel.name].overall.annual_sum_fuel_units):,}"
            f" {house.heating_system.fuel.units} of {house.heating_system.fuel.name} per year"
        )
    else:
        sentence = (
            f"{int(house.consumption_per_fuel['electricity'].overall.annual_sum_kwh):,}"
            f" kwh of electricity per year "
        )
    return sentence


def render_savings_chart(results_df: pd.DataFrame, y_variable: str):
    bills_fig = px.bar(results_df, x="Upgrade option", y=y_variable, color="fuel")
    st.plotly_chart(bills_fig, use_container_width=True, sharing="streamlit")
