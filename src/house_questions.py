""" Using session state solution described here for assumptions:
https://discuss.streamlit.io/t/make-a-widget-remember-its-value-after-it-is-hidden-and-shown-again-in-later-script-runs/29702/2"""

from typing import Dict

import streamlit as st

import constants
from building_model import House, BuildingEnvelope, HeatingSystem, Tariff
from fuels import Fuel


def render() -> "House":
    house = get_house_from_session_state_if_exists_or_create_default()

    st.header("Start by telling us about your home")
    st.markdown(
        f"<p class='more-info'> If you know lots more about your home and tariff, you can"
        f"  <a  href='javascript:document.getElementsByClassName({constants.CLASS_NAME_OF_SIDEBAR_DIV}"
        f")[1].click();' target='_self'> enter more details here!</a></p>",
        unsafe_allow_html=True,
    )

    house.envelope = render_building_envelope_questions(envelope=house.envelope)
    house.heating_system = render_heating_system_questions(heating_system=house.heating_system)
    if st.session_state.heating_fuel_changed:
        house.tariffs = update_tariffs_for_new_heating_fuel(heating_fuel=house.heating_system.fuel,
                                                            tariffs=house.tariffs)
    house = render_assumptions_sidebar(house=house)

    render_results(house)
    return house


def get_house_from_session_state_if_exists_or_create_default():
    if st.session_state["page_state"]["house"] == {}:
        house = set_up_default_house()
        st.session_state["page_state"]["house"] = dict(house=house)  # in case this page isn't always rendered
    else:
        house = st.session_state["page_state"]["house"]["house"]
    return house


def set_up_default_house() -> "House":
    print("Setting up default house")
    envelope = BuildingEnvelope.from_building_type_constants(constants.BUILDING_TYPE_OPTIONS["Terrace"])
    heating_system_name = list(constants.DEFAULT_HEATING_CONSTANTS.keys())[0]
    house = House.set_up_from_heating_name(envelope=envelope, heating_name=heating_system_name)
    st.session_state.heating_fuel_changed = False  # ideally put all inits here so pattern consistent
    return house


def render_building_envelope_questions(envelope: BuildingEnvelope) -> BuildingEnvelope:
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("I live in a")
        with col2:
            if "house_type" not in st.session_state:
                st.session_state.house_type = envelope.house_type
                write_house_type_variables_to_session_state(envelope=envelope)
            house_type = st.selectbox("", options=constants.BUILDING_TYPE_OPTIONS.keys(), key="house_type",
                                      on_change=flag_change_in_house_type)

            if st.session_state.house_type_changed:  # only overwrite if house type changed by user
                print("Behaves as if house changed")
                envelope = BuildingEnvelope.from_building_type_constants(constants.BUILDING_TYPE_OPTIONS[house_type])
                write_house_type_variables_to_session_state(envelope=envelope)

    return envelope


def write_house_type_variables_to_session_state(envelope: BuildingEnvelope):
    st.session_state.house_type_changed = False

    st.session_state.annual_heating_demand = int(envelope.annual_heating_demand)
    st.session_state.heating_demand_changed = False  # delete?

    st.session_state.annual_base_demand = int(envelope.base_demand.sum())
    st.session_state.base_demand_changed = False


def flag_change_in_house_type():
    st.session_state.house_type_changed = True


def render_heating_system_questions(heating_system: HeatingSystem) -> HeatingSystem:
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("My home is heated with a")
        with col2:
            if "heating_system_name" not in st.session_state:
                st.session_state.heating_system_name = heating_system.name
                st.session_state.heating_fuel_name = heating_system.fuel.name
                write_baseline_heating_system_to_session_state(heating_system=heating_system)

            name = st.selectbox(
                "", options=list(constants.DEFAULT_HEATING_CONSTANTS.keys()), key="heating_system_name",
                on_change=flag_change_in_heating_system)

            if st.session_state.heating_system_changed:  # only overwrite heating system if changed by user
                print("Behaves as if heating system changed")
                heating_system = HeatingSystem.from_constants(name=name,
                                                              parameters=constants.DEFAULT_HEATING_CONSTANTS[name])
                write_baseline_heating_system_to_session_state(heating_system=heating_system)

    return heating_system


def write_baseline_heating_system_to_session_state(heating_system: HeatingSystem):

    if heating_system.fuel.name != st.session_state.heating_fuel_name:
        print(f"Behaves as if heating fuel changed")
        st.session_state.heating_fuel_changed = True  # flag change so tariff changes
        st.session_state.heating_fuel_name = heating_system.fuel.name

    st.session_state.baseline_heating_efficiency = heating_system.efficiency
    st.session_state.heating_system_changed = False


def flag_change_in_heating_system():
    st.session_state.heating_system_changed = True


def update_tariffs_for_new_heating_fuel(heating_fuel: Fuel, tariffs: Dict[str, Tariff]):
    st.session_state.heating_fuel_changed = False
    if heating_fuel.name != 'electricity':  # if heating fuel is electric then use elec tariff already defined
        heating_tariff = Tariff.set_up_heating_tariff(heating_system_fuel=heating_fuel)
        tariffs[heating_fuel.name] = heating_tariff
        write_heating_tariffs_to_sessions_state(tariff=heating_tariff)
    return tariffs


def render_assumptions_sidebar(house: House) -> House:
    with st.sidebar:
        st.header("Assumptions")
        st.markdown(
            "<p>If you know details of your current usage or tariff, enter below for greater accuracy</p>",
            unsafe_allow_html=True,
        )
        st.subheader("Current Performance")
        house = render_house_overwrite_options(house)
    return house


def render_house_overwrite_options(house: House):
    with st.expander("Demand"):
        house.envelope = render_envelope_overwrite_options(envelope=house.envelope)
    with st.expander("Baseline heating system"):
        house.heating_system = render_baseline_heating_system_overwrite_options(heating_system=house.heating_system)
    with st.expander("Tariff"):
        house.tariffs = render_tariff_overwrite_options(tariffs=house.tariffs, fuel_name=house.heating_system.fuel.name)
    return house


def render_envelope_overwrite_options(envelope: BuildingEnvelope) -> BuildingEnvelope:

    st.number_input(
        label="Space and water heating (kwh): ",
        min_value=0, max_value=100000,
        value=st.session_state.annual_heating_demand,
        key="annual_heating_demand_overwrite",
        on_change=overwrite_heating_demand_in_session_state
    )

    if st.session_state.heating_demand_changed:  # scale profile  by correction factor
        print("Behaves as if heating demand changed")
        envelope.annual_heating_demand = st.session_state.annual_heating_demand
        st.session_state.heating_demand_changed = False

    st.number_input(
        label="Lighting, appliances, plug loads etc. (kwh): ",
        min_value=0,
        max_value=100000,
        value=st.session_state.annual_base_demand,
        key="annual_base_demand_overwrite",
        on_change=overwrite_base_demand_in_session_state
    )
    if st.session_state.base_demand_changed:  # scale profile  by correction factor
        print("Behaves as if base demand changed")
        envelope.base_demand = st.session_state.annual_base_demand / int(
            envelope.base_demand.sum()) * envelope.base_demand
        st.session_state.base_demand_changed = False


    st.caption(
        f"A typical {envelope.house_type.lower()} home needs "
        f"{constants.BUILDING_TYPE_OPTIONS[envelope.house_type].annual_heat_demand_kWh:,} kWh for heating, "
        f"and {constants.BUILDING_TYPE_OPTIONS[envelope.house_type].annual_base_electricity_demand_kWh:,} "
        f"kWh for lighting, appliances, etc. "
        f"The better your home is insulated, the less energy it will need for heating. "
    )
    return envelope


def overwrite_heating_demand_in_session_state():
    st.session_state.annual_heating_demand = st.session_state.annual_heating_demand_overwrite
    st.session_state.heating_demand_changed = True


def overwrite_base_demand_in_session_state():
    st.session_state.annual_base_demand = st.session_state.annual_base_demand_overwrite
    st.session_state.base_demand_changed = True


def render_baseline_heating_system_overwrite_options(heating_system: "HeatingSystem") -> "HeatingSystem":

    st.number_input(
        label="Efficiency: ", min_value=0.1, max_value=8.0, value=st.session_state.baseline_heating_efficiency,
        key="baseline_heating_efficiency_overwrite", on_change=overwrite_baseline_heating_efficiency_in_session_state)

    heating_system.efficiency = st.session_state.baseline_heating_efficiency

    if heating_system.fuel.name == "gas":
        st.caption(
            "Many modern boilers have a low efficiency because they run at a high a flow temperature. "
            "Your boiler may be able to run at 90% or better but in most cases the flow temperature will be too high to "
            "achieve the boiler's stated efficiency. "
            "You can learn how to turn down your flow temperature "
            "[here](https://www.nesta.org.uk/project/lowering-boiler-flow-temperature-reduce-emissions)."
        )
    return heating_system


def overwrite_baseline_heating_efficiency_in_session_state():
    st.session_state.baseline_heating_efficiency = st.session_state.baseline_heating_efficiency_overwrite


def render_tariff_overwrite_options(tariffs: Tariff, fuel_name: "str") -> Tariff:
    st.subheader("Electricity")

    if "p_per_unit_elec_import" not in st.session_state:
        write_elec_tariff_to_session_state(tariff=tariffs["electricity"])

    st.number_input(label="Unit rate (p/kwh), electricity import", min_value=0.0, max_value=100.0,
                    value=st.session_state.p_per_unit_elec_import, key="p_per_unit_elec_import_overwrite",
                    on_change=overwrite_elec_p_per_unit_import_in_session_state)

    st.number_input(label="Unit rate (p/kwh), electricity export", min_value=0.0, max_value=100.0,
                    value=st.session_state.p_per_unit_elec_export, key="p_per_unit_elec_export_overwrite",
                    on_change=overwrite_elec_p_per_unit_export_in_session_state)

    st.number_input(label="Standing charge (p/day), electricity", min_value=0.0, max_value=100.0,
                    value=st.session_state.p_per_day_elec, key="p_per_day_elec_overwrite",
                    on_change=overwrite_elec_p_per_day_in_session_state)

    tariffs["electricity"].p_per_unit_import = st.session_state.p_per_unit_elec_import
    tariffs["electricity"].p_per_unit_export = st.session_state.p_per_unit_elec_export
    tariffs["electricity"].p_per_day = st.session_state.p_per_day_elec

    if 'p_per_unit_heating_fuel_import' not in st.session_state:
        write_heating_tariffs_to_sessions_state(tariff=tariffs[fuel_name])

    match fuel_name:  # only need to define other tariff if heating fuel is gas or oil as elec already defined
        case "gas":
            st.subheader("Gas")
            st.number_input(label="Unit rate (p/kwh), gas", min_value=0.0, max_value=100.0,
                            value=st.session_state.p_per_unit_heating_fuel_import,
                            key="p_per_unit_heating_fuel_import_overwrite",
                            on_change=overwrite_p_per_unit_heating_fuel_import)
            st.number_input(label="Standing charge (p/day), gas", min_value=0.0, max_value=100.0,
                            value=st.session_state.p_per_day_heating_fuel,
                            key="p_per_day_heating_fuel_overwrite",
                            on_change=overwrite_p_per_unit_heating_fuel_import)

            tariffs["gas"].p_per_unit_import = st.session_state.p_per_unit_heating_fuel_import
            tariffs["gas"].p_per_day = st.session_state.p_per_day_heating_fuel

        case "oil":
            st.subheader("Oil")
            st.number_input(label="Oil price, (p/litre)", min_value=0.0, max_value=200.0,
                            value=st.session_state.p_per_unit_heating_fuel_import,
                            key="p_per_unit_heating_fuel_import_overwrite",
                            on_change=overwrite_p_per_unit_heating_fuel_import)

            tariffs["oil"].p_per_unit_import = st.session_state.p_per_unit_heating_fuel_import

    st.caption(
        "Our default tariffs reflect the current [Energy Price Guarantee]("
        "https://www.gov.uk/government/publications/energy-bills-support/energy-bills-support-factsheet-8-september-2022)"
        " which is in place until April, but you can change them if you have fixed at a different rate."
    )

    return tariffs


def write_elec_tariff_to_session_state(tariff: Tariff):
    st.session_state.p_per_unit_elec_import = tariff.p_per_unit_import
    st.session_state.p_per_unit_elec_export = tariff.p_per_unit_export
    st.session_state.p_per_day_elec = tariff.p_per_day


def write_heating_tariffs_to_sessions_state(tariff: Tariff):
    st.session_state.p_per_unit_heating_fuel_import = tariff.p_per_unit_import
    st.session_state.p_per_day_heating_fuel = tariff.p_per_day


def overwrite_elec_p_per_unit_import_in_session_state():
    st.session_state.p_per_unit_elec_import = st.session_state.p_per_unit_elec_import_overwrite


def overwrite_elec_p_per_unit_export_in_session_state():
    st.session_state.p_per_unit_elec_export = st.session_state.p_per_unit_elec_export_overwrite


def overwrite_elec_p_per_day_in_session_state():
    st.session_state.p_per_day_elec = st.session_state.p_per_day_elec_overwrite


def overwrite_p_per_unit_heating_fuel_import():
    st.session_state.p_per_unit_heating_fuel_import = st.session_state.p_per_unit_heating_fuel_import_overwrite


def overwrite_p_per_day_heating_fuel():
    st.session_state.p_per_day_heating_fuel = st.session_state.p_per_day_heating_fuel_overwrite


def render_results(house: House):
    st.markdown(
        f"<div class='results-container'>"
        f"<p class='bill-label'>Your bill next year will be around <p>"
        f"<p class='bill-estimate'>£{int(house.total_annual_bill):,d}"
        f"</p>"
        f"<p class='bill-details'>Based on estimated usage of "
        f"<a class='bill-consumption-kwh' href='javascript:document.getElementsByClassName("
        f"{constants.CLASS_NAME_OF_SIDEBAR_DIV})[1].click();' target='_self'>"
        f"{int(house.total_annual_consumption_kwh):,d} kwh</a> </p>"
        f"</div>",
        unsafe_allow_html=True,
    )
