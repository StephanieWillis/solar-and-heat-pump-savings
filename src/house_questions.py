import pandas as pd
import streamlit as st

import building_model
import constants


def render() -> "building_model.House":
    house = get_house_from_session_state_if_exists_or_create_default()

    st.header("Start by telling us about your home")
    house.envelope = render_building_envelope_questions(house.envelope)
    new_heating_system = render_heating_system_questions(heating_system=house.heating_system)

    house = render_results(house)

    return house


def get_house_from_session_state_if_exists_or_create_default():
    if st.session_state["page_state"]["house"] == {}:
        house = set_up_default_house()
        st.session_state["page_state"]["house"] = dict(house=house)  # in case this page isn't always rendered
    else:
        house = st.session_state["page_state"]["house"]["house"]
    return house


def set_up_default_house() -> "building_model.House":
    envelope = building_model.BuildingEnvelope(house_type=constants.HOUSE_TYPES[0],
                                               floor_area_m2=constants.DEFAULT_FLOOR_AREA)
    heating_system_name = list(constants.DEFAULT_HEATING_CONSTANTS.keys())[0]
    house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name=heating_system_name)
    return house


def render_building_envelope_questions(envelope: building_model.BuildingEnvelope) -> building_model.BuildingEnvelope:
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("I live in a")
        with col2:
            idx = constants.HOUSE_TYPES.index(envelope.house_type)
            envelope.house_type = st.selectbox("", options=constants.HOUSE_TYPES, index=idx)

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("My floor area in metres squared is about")
        with col2:
            envelope.floor_area_m2 = st.slider(label="", min_value=0, max_value=500, value=envelope.floor_area_m2)

    return envelope


def render_heating_system_questions(heating_system: building_model.HeatingSystem) -> building_model.HeatingSystem:
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("My home is heated with a")
        with col2:
            idx = list(constants.DEFAULT_HEATING_CONSTANTS.keys()).index(heating_system.name)
            heating_name = st.selectbox("Heating System", options=list(constants.DEFAULT_HEATING_CONSTANTS.keys()),
                                        index=idx)
            if heating_name != heating_system.name:  # only overwrite heating system if changed by user
                heating_system = building_model.HeatingSystem.from_constants(
                    name=heating_name,
                    parameters=constants.DEFAULT_HEATING_CONSTANTS[heating_name])
            # when not overwritten by user keep old system so don't loose changes to efficiencies made at other steps

    return heating_system


def render_results(house) -> building_model.House:
    with st.sidebar:
        st.header("Assumptions")
        st.markdown("<p>If you know details of your current usage or tariff, enter below for greater accuracy</p>",
                    unsafe_allow_html=True)
        st.subheader("Current Performance")
        house = render_and_update_current_home(house)

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


def render_and_update_current_home(house: building_model.House):
    with st.expander("Demand"):
        house.envelope = render_and_update_envelope_outputs(envelope=house.envelope)
    with st.expander("Baseline heating system"):
        house.heating_system = render_and_update_heating_system(heating_system=house.heating_system)
    with st.expander("Tariff"):
        house = render_and_update_tariffs(house=house)
    return house


def render_and_update_envelope_outputs(envelope: building_model.BuildingEnvelope) -> building_model.BuildingEnvelope:
    st.write(f"We assume that an {envelope.floor_area_m2}m\u00b2 {envelope.house_type.lower()} needs: ")
    envelope.space_heating_demand = render_and_update_annual_demand(label='Heating (kwh): ',
                                                                    demand=envelope.space_heating_demand)
    envelope.water_heating_demand = render_and_update_annual_demand(label='Hot water (kwh): ',
                                                                    demand=envelope.water_heating_demand)
    envelope.base_demand = render_and_update_annual_demand(label='Other (lighting/appliances etc.) (kwh): ',
                                                           demand=envelope.base_demand)
    return envelope


def render_and_update_annual_demand(label: str, demand: pd.Series) -> pd.Series:
    """ If user overwrites annual total then scale whole profile by multiplier"""
    demand_overwrite = st.number_input(label=label, min_value=0, max_value=100000, value=int(demand.sum()))
    if demand_overwrite != int(demand.sum()):  # scale profile  by correction factor
        demand = demand_overwrite / int(demand.sum()) * demand
    return demand


def render_and_update_heating_system(heating_system: building_model.HeatingSystem) -> building_model.HeatingSystem:
    heating_system.space_heating_efficiency = st.number_input(label='Efficiency for space heating: ',
                                                              min_value=0.0,
                                                              max_value=8.0,
                                                              value=heating_system.space_heating_efficiency)
    heating_system.water_heating_efficiency = st.number_input(label='Efficiency for water heating: ',
                                                              min_value=0.0,
                                                              max_value=8.0,
                                                              value=heating_system.water_heating_efficiency)
    return heating_system


def render_and_update_tariffs(house: building_model.House) -> building_model.House:
    st.subheader('Electricity')
    house.tariffs['electricity'].p_per_unit_import = st.number_input(label='Unit rate (p/kwh), electricity import',
                                                                     min_value=0.0,
                                                                     max_value=100.0,
                                                                     value=house.tariffs[
                                                                         'electricity'].p_per_unit_import)
    house.tariffs['electricity'].p_per_unit_export = st.number_input(label='Unit rate (p/kwh), electricity export',
                                                                     min_value=0.0,
                                                                     max_value=100.0,
                                                                     value=house.tariffs[
                                                                         'electricity'].p_per_unit_export)
    house.tariffs['electricity'].p_per_day = st.number_input(label='Standing charge (p/day), electricity',
                                                             min_value=0.0,
                                                             max_value=100.0,
                                                             value=house.tariffs['electricity'].p_per_day)
    match house.heating_system.fuel.name:
        case 'gas':
            st.subheader('Gas')
            house.tariffs['gas'].p_per_unit_import = st.number_input(label='Unit rate (p/kwh), gas',
                                                                     min_value=0.0,
                                                                     max_value=100.0,
                                                                     value=house.tariffs['gas'].p_per_unit_import)
            house.tariffs['gas'].p_per_day = st.number_input(label='Standing charge (p/day), gas',
                                                             min_value=0.0,
                                                             max_value=100.0,
                                                             value=house.tariffs['gas'].p_per_day)
        case 'oil':
            st.subheader('Oil')
            house.tariffs['oil'].p_per_unit_import = st.number_input(label='Oil price, (p/litre)',
                                                                     min_value=0.0,
                                                                     max_value=200.0,
                                                                     value=house.tariffs['oil'].p_per_unit_import)
    return house
