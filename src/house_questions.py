import pandas as pd
import streamlit as st

from building_model import House, BuildingEnvelope, HeatingSystem, Tariff
import constants


def render() -> "House":
    house = get_house_from_session_state_if_exists_or_create_default()

    st.header("Start by telling us about your home")
    house.envelope = render_building_envelope_questions(house.envelope)
    house = render_heating_system_questions(house=house)
    house = render_results(house)

    return house


def get_house_from_session_state_if_exists_or_create_default():
    if st.session_state["page_state"]["house"] == {}:
        house = set_up_default_house()
        st.session_state["page_state"]["house"] = dict(house=house)  # in case this page isn't always rendered
    else:
        house = st.session_state["page_state"]["house"]["house"]
    return house


def set_up_default_house() -> "House":
    envelope = BuildingEnvelope.from_building_type_constants(constants.BUILDING_TYPE_OPTIONS["Terrace"])
    heating_system_name = list(constants.DEFAULT_HEATING_CONSTANTS.keys())[0]
    house = House.set_up_from_heating_name(envelope=envelope, heating_name=heating_system_name)
    return house


def render_building_envelope_questions(envelope: BuildingEnvelope) -> BuildingEnvelope:
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("I live in a")
        with col2:
            if "house_type" not in st.session_state:  # set initial value
                st.session_state.house_type = envelope.house_type
            house_type = st.selectbox("", options=constants.BUILDING_TYPE_OPTIONS.keys(), key="house_type")
            if house_type != envelope.house_type:  # only overwrite if house type changed by user
                envelope = BuildingEnvelope.from_building_type_constants(constants.BUILDING_TYPE_OPTIONS[house_type])
    return envelope


def render_heating_system_questions(house: House) -> House:
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("My home is heated with a")
        with col2:
            if "heating_system_name" not in st.session_state:  # set initial value
                st.session_state.heating_system_name = house.heating_system.name

            heating_name = st.selectbox("Heating System", options=list(constants.DEFAULT_HEATING_CONSTANTS.keys()),
                                        key="heating_system_name")
            if heating_name != house.heating_system.name:  # only overwrite heating system if changed by user
                original_fuel_name = house.heating_system.fuel.name
                house.heating_system = HeatingSystem.from_constants(
                    name=heating_name,
                    parameters=constants.DEFAULT_HEATING_CONSTANTS[heating_name])
                if house.heating_system.fuel.name != original_fuel_name:
                    # only overwrite tariffs if heating fuel changed, keep any overwrites otherwise
                    house.tariffs = house.set_up_standard_tariffs()

    return house


def render_results(house) -> House:
    with st.sidebar:
        st.header("Assumptions")
        st.markdown("<p>If you know details of your current usage or tariff, enter below for greater accuracy</p>",
                    unsafe_allow_html=True)
        st.subheader("Current Performance")
        house = overwrite_house_assumptions(house)

    class_name_of_sidebar_div = "\"css-1f8pn94 edgvbvh3\""
    st.markdown(
        f"<div class='results-container'>"
        f"<p class='bill-label'>Your bill next year will be around <p>"
        f"<p class='bill-estimate'>£{int(house.total_annual_bill):,d}"
        f"</p>"
        f"<p class='bill-details'>Based on estimated usage of "
        f"<a class='bill-consumption-kwh' href='javascript:document.getElementsByClassName({class_name_of_sidebar_div})[1].click();' target='_self'>"
        f"{int(house.total_annual_consumption_kwh):,d} kwh</a> </p>"

        f"</div>",
        unsafe_allow_html=True,
    )
    return house


def overwrite_house_assumptions(house: House):
    with st.expander("Demand"):
        house.envelope = overwrite_envelope_assumptions(envelope=house.envelope)
    with st.expander("Baseline heating system"):
        house.heating_system = overwrite_heating_system_assumptions(heating_system=house.heating_system)
    with st.expander("Tariff"):
        house.tariffs = overwrite_tariffs(tariffs=house.tariffs, fuel_name=house.heating_system.fuel.name)
    return house


def overwrite_envelope_assumptions(envelope: BuildingEnvelope) -> BuildingEnvelope:

    if ("annual_heating_demand" not in st.session_state or
            st.session_state.house_type_that_annual_heating_demand_is_for != envelope.house_type) :
        # Set initial values or, where house type has been changed, reset values
        st.session_state.annual_heating_demand = int(envelope.annual_heating_demand)
        st.session_state.annual_base_demand = int(envelope.base_demand.sum())
        st.session_state.house_type_that_annual_heating_demand_is_for = envelope.house_type

    envelope.annual_heating_demand = st.number_input(label='Space and water heating (kwh): ',
                                                     min_value=0,
                                                     max_value=100000,
                                                     key="annual_heating_demand")

    annual_base_demand_overwrite = st.number_input(label='Lighting, appliances, plug loads etc. (kwh): ',
                                                   min_value=0,
                                                   max_value=100000,
                                                   key="annual_base_demand")
    if annual_base_demand_overwrite != int(envelope.base_demand.sum()):  # scale profile  by correction factor
        envelope.base_demand = (annual_base_demand_overwrite / int(envelope.base_demand.sum())
                                * envelope.base_demand)

    st.caption(f"A typical {envelope.house_type.lower()} home needs "
               f"{constants.BUILDING_TYPE_OPTIONS[envelope.house_type].annual_heat_demand_kWh:,} kWh for heating, "
               f"and {constants.BUILDING_TYPE_OPTIONS[envelope.house_type].annual_base_electricity_demand_kWh:,} "
               f"kWh for lighting, appliances, etc. "
               f"The better your home is insulated, the less energy it will need for heating. "
               )
    return envelope


def overwrite_heating_system_assumptions(heating_system: 'HeatingSystem') -> 'HeatingSystem':
    heating_system.efficiency = st.number_input(label='Efficiency: ',
                                                min_value=0.0,
                                                max_value=8.0,
                                                value=heating_system.efficiency)
    if heating_system.fuel.name == 'gas':
        st.caption(
            "Many modern boilers have a low efficiency because they run at a high a flow temperature. "
            "Your boiler may be able to run at 90% or better but in most cases the flow temperature will be too high to "
            "achieve the boiler's stated efficiency. "
            "You can learn how to turn down your flow temperature "
            "[here](https://www.nesta.org.uk/project/lowering-boiler-flow-temperature-reduce-emissions).")
    return heating_system


def overwrite_tariffs(tariffs: Tariff, fuel_name: 'str') -> Tariff:
    st.subheader('Electricity')
    tariffs['electricity'].p_per_unit_import = st.number_input(label='Unit rate (p/kwh), electricity import',
                                                               min_value=0.0,
                                                               max_value=100.0,
                                                               value=tariffs[
                                                                   'electricity'].p_per_unit_import)
    tariffs['electricity'].p_per_unit_export = st.number_input(label='Unit rate (p/kwh), electricity export',
                                                               min_value=0.0,
                                                               max_value=100.0,
                                                               value=tariffs[
                                                                   'electricity'].p_per_unit_export)
    tariffs['electricity'].p_per_day = st.number_input(label='Standing charge (p/day), electricity',
                                                       min_value=0.0,
                                                       max_value=100.0,
                                                       value=tariffs['electricity'].p_per_day)
    match fuel_name:
        case 'gas':
            st.subheader('Gas')
            tariffs['gas'].p_per_unit_import = st.number_input(label='Unit rate (p/kwh), gas',
                                                               min_value=0.0,
                                                               max_value=100.0,
                                                               value=tariffs['gas'].p_per_unit_import)
            tariffs['gas'].p_per_day = st.number_input(label='Standing charge (p/day), gas',
                                                       min_value=0.0,
                                                       max_value=100.0,
                                                       value=tariffs['gas'].p_per_day)
        case 'oil':
            st.subheader('Oil')
            tariffs['oil'].p_per_unit_import = st.number_input(label='Oil price, (p/litre)',
                                                               min_value=0.0,
                                                               max_value=200.0,
                                                               value=tariffs['oil'].p_per_unit_import)
    st.caption(
        "Our default tariffs reflect the [Energy Price Guarantee]("
        "https://www.gov.uk/government/publications/energy-bills-support/energy-bills-support-factsheet-8-september-2022)"
        ", but you can change them if you have fixed at a different rate.")
    return tariffs
