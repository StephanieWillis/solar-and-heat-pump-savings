from typing import Tuple

import numpy as np
import plotly.express as px
import streamlit as st

import house_questions
import retrofit
import solar_questions
from building_model import *
from constants import CLASS_NAME_OF_SIDEBAR_DIV
from solar import Solar
from solar_questions import render_solar_overwrite_options


def get_upgrade_heating_from_session_state_if_exists_or_create_default() -> HeatingSystem:
    if "upgrade_heating" not in st.session_state["page_state"]:
        upgrade_heating = HeatingSystem.from_constants(
            name="Heat pump", parameters=constants.DEFAULT_HEATING_CONSTANTS["Heat pump"]
        )
        st.session_state.upgrade_heating = upgrade_heating
    else:
        upgrade_heating = st.session_state.upgrade_heating
    return upgrade_heating


def render(house: "House", solar_install: "Solar", upgrade_heating: "HeatingSystem"):
    if "number_of_panels" not in st.session_state:
        st.session_state.number_of_panels = solar_install.number_of_panels
    if st.session_state.number_of_panels == 0:
        st.warning(
            "**Oops** - you didn't draw a rectangle on your roof. Please go back to the solar page and use the polygon"
            "tool to draw on your roof, or enter a number of panels in the side bar."
        )

    house, solar_house, hp_house, both_house = render_savings_assumptions_sidebar_and_calculate_upgraded_houses(
        house=house, solar_install=solar_install, upgrade_heating=upgrade_heating)

    solar_retrofit, hp_retrofit, both_retrofit = retrofit.generate_all_retrofit_cases(
        baseline_house=house, solar_house=solar_house, hp_house=hp_house, both_house=both_house)

    render_results(house=house, hp_house=hp_house, solar_house=solar_house, both_house=both_house,
                   solar_retrofit=solar_retrofit, hp_retrofit=hp_retrofit, both_retrofit=both_retrofit)
    return house, solar_house.solar_install, hp_house.heating_system


def render_savings_assumptions_sidebar_and_calculate_upgraded_houses(house: House, solar_install: Solar,
                                                                     upgrade_heating: HeatingSystem
                                                                     ) -> Tuple[House, House, House, House]:
    with st.sidebar:
        st.header("Assumptions")
        st.subheader("Current Performance")
        house = house_questions.render_house_overwrite_options(house)

        st.subheader("Improvement Options")
        solar_install, upgrade_heating = render_improvement_overwrite_options(solar_install=solar_install,
                                                                              upgrade_heating=upgrade_heating)

        solar_house, hp_house, both_house = retrofit.upgrade_buildings(
            baseline_house=house, solar_install=solar_install, upgrade_heating=upgrade_heating)

        st.subheader("Costs")
        house, solar_house, hp_house, both_house = render_cost_overwrite_options(house=house,
                                                                                 solar_house=solar_house,
                                                                                 hp_house=hp_house,
                                                                                 both_house=both_house)

        st.text("")
        st.text("")  # To give some space at the bottom
    return house, solar_house, hp_house, both_house


def render_improvement_overwrite_options(solar_install: Solar, upgrade_heating: HeatingSystem
                                         ) -> Tuple[Solar, HeatingSystem]:
    with st.expander("Solar PV assumptions "):
        solar_install = render_solar_overwrite_options(solar_install=solar_install)
    with st.expander("Heat pump assumptions"):
        upgrade_heating = render_heat_pump_overwrite_options(upgrade_heating)
    st.text("")

    return solar_install, upgrade_heating


def render_heat_pump_overwrite_options(upgrade_heating: HeatingSystem) -> HeatingSystem:
    if "upgrade_heating_efficiency" not in st.session_state:
        st.session_state.upgrade_heating_efficiency = upgrade_heating.efficiency
        st.session_state.upgrade_heating_efficiency_overwritten = False

    st.number_input(
        label="Efficiency: ",
        min_value=1.0,
        max_value=8.0,
        value=st.session_state.upgrade_heating_efficiency,
        key="upgrade_heating_efficiency_overwrite",
        on_change=overwrite_upgrade_heating_efficiency_in_session_state)

    if st.session_state.upgrade_heating_efficiency_overwritten:
        print("Behaves as if heating efficiency overwritten")
        upgrade_heating.efficiency = st.session_state.upgrade_heating_efficiency
        st.session_state.upgrade_heating_efficiency_overwritten = False

    st.session_state["page_state"]["upgrade_heating"] = dict(upgrade_heating=upgrade_heating)

    st.caption(
        "The efficiency of your heat pump depends on how well the system is designed and how low a flow "
        "temperature it can run at. A COP of 3.6 or better is possible with a [high quality, low flow temperature "
        "install](https://heatpumpmonitor.org).  \n  \n"
        "A good installer is key to ensuring your heat pump runs efficiently. The [heat geek map"
        "](https://www.heatgeek.com/find-a-heat-geek/) is a great place to start your search."
    )
    return upgrade_heating


def overwrite_upgrade_heating_efficiency_in_session_state():
    st.session_state.upgrade_heating_efficiency = st.session_state.upgrade_heating_efficiency_overwrite
    st.session_state.upgrade_heating_efficiency_overwritten = True


def render_cost_overwrite_options(house: House, solar_house: House, hp_house: House, both_house: House
                                  ) -> Tuple[House, House, House, House]:
    with st.expander("Upfront Costs"):
        house, solar_house, hp_house, both_house = render_upfront_cost_overwrite_options(house=house,
                                                                                         solar_house=solar_house,
                                                                                         hp_house=hp_house,
                                                                                         both_house=both_house)
        st.text("")
    with st.expander("Grants"):
        hp_house, both_house = render_grant_overwrite_options(hp_house=hp_house, both_house=both_house)
    return house, solar_house, hp_house, both_house


def render_upfront_cost_overwrite_options(house: House, solar_house: House, hp_house: House, both_house: House
                                          ) -> Tuple[House, House, House, House]:
    """ Update baseline heating cost, heat pump cost, or solar cost.

     Have to pass whole house as costs only defined for heating systems when have envelope plus heating system
     """

    if "solar_cost" not in st.session_state:
        solar_questions.write_solar_cost_to_session_state(solar_install=solar_house.solar_install)

    st.number_input(
        label="Solar cost",
        min_value=0,
        max_value=300000,
        value=st.session_state.solar_cost,
        key="solar_cost_overwrite",
        on_change=overwrite_solar_costs_in_session_state,
        help="The cost of scaffolding is a significant part of the cost  of installing solar. If you have scaffolding"
             " up for another job, make the most of it and install solar at the same time! "
    )

    if st.session_state.solar_cost_overwritten:
        print("Behaves as if solar cost overwritten")
        solar_house.solar_install.upfront_cost = st.session_state.solar_cost
        both_house.solar_install.upfront_cost = st.session_state.solar_cost
        st.session_state.solar_cost_overwritten = False

    if "baseline_heating_cost" not in st.session_state or st.session_state.baseline_heating_system_cost_needs_resetting:
        house.clear_cost_overwrite()
        st.session_state.baseline_heating_cost = house.heating_system_upfront_cost
        st.session_state.baseline_heating_cost_overwritten = False
        st.session_state.baseline_heating_system_cost_needs_resetting = False

    st.number_input(
        label="Baseline heating system cost",
        min_value=0,
        max_value=30000,
        value=st.session_state.baseline_heating_cost,
        key="baseline_heating_cost_overwrite",
        on_change=overwrite_baseline_heating_costs_in_session_state,
        help="For the payback calculation we assume that you would have installed a new boiler if you had not"
             " installed a heat pump so we  subtract the cost of a new boiler from the heat pump cost"
    )

    if st.session_state.baseline_heating_cost_overwritten:
        house.heating_system_upfront_cost = st.session_state.baseline_heating_cost
        solar_house.heating_system_upfront_cost = st.session_state.baseline_heating_cost
        st.session_state.baseline_heating_cost_overwritten = False

    if "heat_pump_cost" not in st.session_state or st.session_state.upgrade_heating_system_cost_needs_resetting:
        hp_house.clear_cost_overwrite()  # shouldn't currently be necessary because remade when this page renders
        st.session_state.heat_pump_cost = hp_house.heating_system_upfront_cost
        st.session_state.heat_pump_cost_overwritten = False
        st.session_state.upgrade_heating_system_cost_needs_resetting = False
    else:  # hp house gets remade each time savings page renders so the overwrite is lost
        hp_house.heating_system_upfront_cost = st.session_state.heat_pump_cost
        both_house.heating_system_upfront_cost = st.session_state.heat_pump_cost

    st.number_input(
        label="Heat pump cost (without grants)",
        min_value=0,
        max_value=30000,
        value=st.session_state.heat_pump_cost,
        key="heat_pump_cost_overwrite",
        on_change=overwrite_heat_pump_costs_in_session_state,
        help="The cost of a heat pump depends on your existing radiators and pipework: see the final page for more info"
    )

    if st.session_state.heat_pump_cost_overwritten:
        print("Behaves as if heating cost overwritten")
        hp_house.heating_system_upfront_cost = st.session_state.heat_pump_cost
        both_house.heating_system_upfront_cost = st.session_state.heat_pump_cost
        st.session_state.heat_pump_cost_overwritten = False

    return house, solar_house, hp_house, both_house


def overwrite_baseline_heating_costs_in_session_state():
    st.session_state.baseline_heating_cost = st.session_state.baseline_heating_cost_overwrite
    st.session_state.baseline_heating_cost_overwritten = True


def overwrite_solar_costs_in_session_state():
    st.session_state.solar_cost = st.session_state.solar_cost_overwrite
    st.session_state.solar_cost_overwritten = True


def overwrite_heat_pump_costs_in_session_state():
    st.session_state.heat_pump_cost = st.session_state.heat_pump_cost_overwrite
    st.session_state.heat_pump_cost_overwritten = True


def render_grant_overwrite_options(hp_house: House, both_house: House) -> Tuple[House, House]:
    if "heat_pump_grant_value" not in st.session_state:
        st.session_state.heat_pump_grant_value = hp_house.heating_system.grant
        st.session_state.heat_pump_grant_value_overwritten = False

    st.number_input(
        label="Heat pump grant amount",
        min_value=0,
        max_value=20000,
        value=st.session_state.heat_pump_grant_value,
        key="heat_pump_grant_value_overwrite",
        on_change=flag_that_heat_pump_grant_value_overwritten,
        help='''The [Boiler Upgrade Scheme](https://www.gov.uk/apply-boiler-upgrade-scheme) offers a grant of £5000 and
        is available in England and Wales. The [Home Energy Scotland Scheme](https://www.gov.scot/news/embargoed-enhanced-support-to-make-homes-warmer-and-greener/) is 
        available in Scotland and offers a grant of £7500.'''
    )

    if st.session_state.heat_pump_grant_value_overwritten:
        print("Behaves as if heat pump grant overwritten")
        hp_house.heating_system.grant = st.session_state.heat_pump_grant_value
        both_house.heating_system.grant = st.session_state.heat_pump_grant_value
        st.session_state.heat_pump_grant_value_overwritten = False

    return hp_house, both_house


def flag_that_heat_pump_grant_value_overwritten():
    st.session_state.heat_pump_grant_value = st.session_state.heat_pump_grant_value_overwrite
    st.session_state.heat_pump_grant_value_overwritten = True


def render_results(house: House, solar_house: House, hp_house: House, both_house: House,
                   solar_retrofit: retrofit.Retrofit, hp_retrofit: retrofit.Retrofit,
                   both_retrofit: retrofit.Retrofit):
    # Combine results all variables
    results_df = retrofit.combine_results_dfs_multiple_houses(
        [house, solar_house, hp_house, both_house],
        ["Current ", "Solar panels ", "Heat pump ", "Both "],
    )

    st.markdown(
        f"<h2> On your bills of <span style='color:hsl(220, 60%, 30%)'> "
        f"£{int(house.total_annual_bill):,d} </span> you could save </h2>",
        unsafe_allow_html=True,
    )
    _, col1, col2, col3, _ = st.columns([0.2, 1, 1, 1, 0.2])
    with col1:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate'>☀️ £{int(solar_retrofit.bill_savings_absolute):,d} </p>"
            "<p> with solar panels</p>"
            "</div>"
            "<div class='saving-maths'>"
            "<div>"
            f"<p class='saving-maths-headline'> ~£{solar_house.solar_install.upfront_cost:,d}</p>"
            "<p class='saving-maths'> to install</p>"
            "</div>"
            "<div>"
            f"<p class='saving-maths-headline'> {format_payback(solar_retrofit.simple_payback)}</p>"
            "<p class='saving-maths'> payback time</p>"
            "<br>"
            "<br>"
            "<br>"            
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate'> 💨 £{int(hp_retrofit.bill_savings_absolute):,d}</p>"
            f"<p> with a heat pump</p>"
            "<div class='saving-maths'>"
            "<div>"
            f"<p class='saving-maths-headline'> ~£{hp_house.upfront_cost_after_grants:,d}</p>"
            "<p class='saving-maths'> to install</p>"
            "</div>"
            "<div>"
            f"<p class='saving-maths-headline'> {format_payback(hp_retrofit.simple_payback)}</p>"
            "<p class='saving-maths'> payback time</p>"
            "<p class='install-disclaimer'> cost after grant, payback assumes avoided boiler replacement </p> "
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            "<div style='text-align:center'>"
            f"<p class='bill-estimate'> 😍 £{int(both_retrofit.bill_savings_absolute):,d} </p>"
            "<p> with both</p>"
            "<div class='saving-maths'>"
            "<div>"
            f"<p class='saving-maths-headline'> ~£{both_house.upfront_cost_after_grants:,d}</p>"
            "<p class='saving-maths'> to install</p>"
            "</div>"
            "<div>"
            f"<p class='saving-maths-headline'> {format_payback(both_retrofit.simple_payback)}</p>"
            "<p class='saving-maths'> payback time</p>"
            "</div>"
            "<p class='install-disclaimer'> cost after grant, payback assumes avoided boiler replacement </p> "
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
        f"<h2>Your home emits about <span style='color:hsl(220, 60%, 30%)'>{house.total_annual_tco2:.2f} tonnes"
        f" </span>of CO2e each year, you could cut your emissions by </h2>",
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
        st.subheader("Carbon")
        render_carbon_chart(results_df)
        render_carbon_outputs(house=house, solar_house=solar_house, hp_house=hp_house, both_house=both_house)

    st.markdown(
        f"<p style='margin:20px; text-align: center'> You can <a  href='javascript:document.getElementsByClassName("
        f"{CLASS_NAME_OF_SIDEBAR_DIV})[1].click();' target='_self'>"
        "view and edit </a> all of the numbers we've used in this calculation if you know the "
        "details of your tariff, heating demand, heat pump or solar install!</p>",
        unsafe_allow_html=True,
    )


def format_payback(payback: float) -> str:
    if np.isnan(payback):
        output = "No payback"
    else:
        output = f"~{int(payback): d} years"
    return output


def render_bill_chart(results_df: pd.DataFrame):
    render_savings_chart(results_df=results_df, x_variable="Your annual energy bill £")


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
    saving = int(baseline_house.total_annual_bill - house.total_annual_bill)
    if saving >= 0:
        sentence = f"that's a saving of £{saving:,}"
    else:
        sentence = f"that's an increase of £{saving:,}"
    return sentence


def render_carbon_chart(results_df: pd.DataFrame):
    render_savings_chart(results_df=results_df, x_variable="Your annual carbon emissions tCO2")


def render_carbon_outputs(house: "House", solar_house: "House", hp_house: "House", both_house: "House"):
    st.write(
        f"We calculate that your house emits {house.total_annual_tco2:.2f} tonnes of CO2 per year  \n"
        f"- with solar it would emit {solar_house.total_annual_tco2:.2f} tonnes of CO2 per year  \n"
        f"- with a heat pump it would emit {hp_house.total_annual_tco2:.2f} tonnes of CO2 per year  \n"
        f"- with solar and a heat pump it would emit {both_house.total_annual_tco2:.2f} "
        f"tonnes of CO2 per year  \n"
    )


def render_consumption_chart(results_df: pd.DataFrame):
    render_savings_chart(results_df=results_df, x_variable="Your annual energy use kwh")


def render_consumption_outputs(house: "House", solar_house: "House", hp_house: "House", both_house: "House"):
    st.write(
        f"We calculate that your house currently needs {produce_consumption_sentence(house)}  \n"
        f"- with solar it would need {produce_consumption_sentence(solar_house)}  \n"
        f"- with a heat pump it would need {produce_consumption_sentence(hp_house)}  \n"
        f"- with solar and a heat pump it would need {produce_consumption_sentence(both_house)} "
    )


def produce_consumption_sentence(house):
    if house.has_multiple_fuels:
        sentence = (
            f"{int(house.annual_consumption_per_fuel_kwh['electricity']):,} "
            f"kwh of electricity and "
            f"{int(house.annual_consumption_per_fuel_kwh[house.heating_system.fuel.name]):,}"
            f" {house.heating_system.fuel.units} of {house.heating_system.fuel.name} per year"
        )
    else:
        sentence = (
            f"{int(house.annual_consumption_per_fuel_kwh['electricity']):,}"
            f" kwh of electricity per year "
        )
    return sentence


def render_savings_chart(results_df: pd.DataFrame, x_variable: str):
    bills_fig = px.bar(results_df,
                       x=x_variable,
                       y="Upgrade option",
                       color="fuel",
                       color_discrete_map={'electricity imports': 'hsl(220, 60%, 80%)',
                                           'electricity exports': 'hsl(220, 60%, 90%)',
                                           'gas': 'hsl(220, 60%, 30%)',
                                           'oil': 'hsl(220, 60%, 20%)'},
                       template="plotly_white")
    bills_fig.update_layout(
        font_family="arial",
        legend=dict(orientation="h", y=1.1, x=0.6),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title=None),
    )
    st.plotly_chart(bills_fig, use_container_width=True, sharing="streamlit")
