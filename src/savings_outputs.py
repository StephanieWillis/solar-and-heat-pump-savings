from typing import Tuple

import numpy as np
import plotly.express as px
import streamlit as st

import house_questions
import retrofit
from building_model import *
from constants import CLASS_NAME_OF_SIDEBAR_DIV
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

        st.subheader("Costs")
        with st.expander("Upfront costs"):
            st.write("To do")

    # Upgraded buildings
    hp_house, solar_house, both_house = retrofit.upgrade_buildings(
        baseline_house=house, upgrade_heating=upgrade_heating, upgrade_solar=upgrade_solar
    )
    solar_retrofit, hp_retrofit, both_retrofit = retrofit.generate_all_retrofit_cases(baseline_house=house,
                                                                                      solar_house=solar_house,
                                                                                      hp_house=hp_house,
                                                                                      both_house=both_house)

    # Combine results all variables
    results_df = retrofit.combine_results_dfs_multiple_houses(
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
            f"<p class='bill-estimate'>☀️ £{int(solar_retrofit.bill_savings_absolute):,d} </p>"
            "<p> with solar panels</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate'> 💨 £{int(hp_retrofit.bill_savings_absolute):,d}</p>"
            f"<p> with a heat pump</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate'> 😍 £{int(both_retrofit.bill_savings_absolute):,d} </p>"
            "<p> with both</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    with st.expander("Show me the maths!"):
        st.subheader("Bills")
        render_bill_outputs(house=house, solar_house=solar_house, hp_house=hp_house, both_house=both_house)
        render_bill_chart(results_df)
        st.subheader("Energy")
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
            f"<p class='bill-estimate '>☀️ {int(100 * solar_retrofit.carbon_savings_pct)}%</p>"
            f"<p class='bill-details snug'> tCO2e</p>"
            "<p> with solar panels</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '> 💨️ {int(100 * hp_retrofit.carbon_savings_pct)}%</p>"
            f"<p class='bill-details snug '> tCO2e</p>"
            f"<p> with a heat pump</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '>😍️ {int(100 * both_retrofit.carbon_savings_pct)}%</p>"
            f"<p class='bill-details snug '> tCO2e</p>"
            "<p> with both</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with st.expander("Show me the maths!"):
        render_carbon_chart(results_df)
        render_carbon_outputs(house=house, solar_house=solar_house, hp_house=hp_house, both_house=both_house)

    st.markdown(
        f"<h2>After government incentives, these options would cost about </h2>",
        unsafe_allow_html=True,
    )

    _, col1, col2, col3, _ = st.columns([0.2, 1, 1, 1, 0.2])

    with col1:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '>☀️ £{int(solar_house.solar_install.upfront_cost):,d} </p>"
            "<p> for solar panels</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '> 💨️ £{int(hp_house.upfront_cost):,d} </p>"
            f"<p> for a heat pump</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '>😍️ £{int(both_house.upfront_cost):,d} </p>"
            "<p> for both</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<h2>Assuming that energy costs remain at their current levels, and that "
        f"you'd replace your current boiler at a cost of <span style='color:hsl(220, 60%, 30%)'>"
        f"£{house.upfront_cost:.0f}</span> if you didn't install a heat pump,"
        f" this  translates into a simple payback time of </h2>",
        unsafe_allow_html=True,
    )

    _, col1, col2, col3, _ = st.columns([0.2, 1, 1, 1, 0.2])

    with col1:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '>☀️ {format_payback(solar_retrofit.simple_payback)} </p>"
            "<p> for solar panels</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '> 💨️ {format_payback(hp_retrofit.simple_payback)} </p>"
            f"<p> for a heat pump</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '>😍️ {format_payback(both_retrofit.simple_payback)} </p>"
            "<p> for both</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<h2>Or an annualized return on investment of </h2>",
        unsafe_allow_html=True,
    )

    _, col1, col2, col3, _ = st.columns([0.2, 1, 1, 1, 0.2])

    with col1:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '>☀️ {format_roi(solar_retrofit.annualized_return_on_investment)}  </p>"
            "<p> for solar panels</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '> 💨️ {format_roi(hp_retrofit.annualized_return_on_investment)}  </p>"
            f"<p> for a heat pump</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate '>😍️ {format_roi(both_retrofit.annualized_return_on_investment)}  </p>"
            "<p> for both</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<p style='margin:20px; text-align: center'> You can <a  href='javascript:document.getElementsByClassName({CLASS_NAME_OF_SIDEBAR_DIV})[1].click();' target='_self'>"
        "view and edit </a> all of the numbers we've used in this calculation if you know the "
        "details of your tariff, heating demand, heat pump or solar install!</p>",
        unsafe_allow_html=True,
    )


def format_payback(payback: float) -> str:
    if np.isnan(payback):
        output = "No payback"
    else:
        output = f'{payback: .1f} years'
    return output


def format_roi(roi: float) -> str:
    if np.isnan(roi):
        output = "No return"
    else:
        output = f'{int(100 * roi)}%'
    return output


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

        st.caption(
            "The efficiency of your heat pump depends on how well the system is designed and how low a flow "
            "temperature it can run at. A COP of 3.6 or more is possible with a [high quality, low flow temperature "
            "install](https://heatpumpmonitor.org).  \n  \n"
            "A good installer is key to ensuring your heat pump runs efficiently. The [heat geek map"
            "](https://www.heatgeek.com/find-a-heat-geek/) is a great place to start your search."
        )

    with st.expander("Solar PV assumptions "):
        solar_install = render_and_update_solar_inputs(solar_install=solar_install)

    return upgrade_heating, solar_install


def overwrite_upgrade_heating_system_assumptions(heating_system: "HeatingSystem") -> "HeatingSystem":
    if "upgrade_heating_efficiency" not in st.session_state or st.session_state.upgrade_heating_efficiency == 0:
        st.session_state.upgrade_heating_efficiency = heating_system.efficiency

    heating_system.efficiency = st.number_input(
        label="Efficiency: ", min_value=0.0, max_value=8.0, key="upgrade_heating_efficiency",
        value=constants.DEFAULT_HEATING_CONSTANTS[heating_system.name].efficiency
    )
    return heating_system


def overwrite_baseline_costs(house: "House") -> "House":
    if "baseline_heating_cost" not in st.session_state:
        st.session_state.baseline_heating_cost = house.upfront_cost
    house.upfront_cost = st.number_input(
        label="Baseline heating system cost", min_value=0.0, max_value=30000, key="baseline_heating_cost",
        value=constants.GAS_BOILER_COSTS["Terrace"])  # TODO: is there a better way here?
    return house


def overwrite_upgrade_costs(house: "House", upgrade_heating: "HeatingSystem", upgrade_solar: "Solar"
                    ) -> ("House", "HeatingSystem", "Solar"):

    return house, upgrade_heating, upgrade_solar


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
    bills_fig = px.bar(results_df, y="Upgrade option", x=y_variable, color="fuel", template="plotly_white")
    bills_fig.update_layout(
        legend=dict(orientation="h", y=1.01, x=0.6),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title=None),
    )
    st.plotly_chart(bills_fig, use_container_width=True, sharing="streamlit")
