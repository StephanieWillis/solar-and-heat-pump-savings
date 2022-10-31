import streamlit as st

import building_model
import constants


def render() -> 'building_model.House':
    st.header("Your House")
    envelope = render_building_envelope_questions()
    heating_system_name = render_heating_system_questions()
    house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name=heating_system_name)
    return house


def render_building_envelope_questions() -> 'building_model.BuildingEnvelope':
    house_type = st.selectbox('House Type', options=list(constants.HEATING_DEMAND_BY_HOUSE_TYPE.keys()))
    house_floor_area_m2 = st.number_input(label='House floor area (m2)', min_value=0, max_value=500, value=80)
    annual_heating_demand = constants.HEATING_DEMAND_BY_HOUSE_TYPE[house_type]
    envelope = building_model.BuildingEnvelope(floor_area_m2=house_floor_area_m2,
                                               house_type=house_type,
                                               annual_heating_demand=annual_heating_demand)
    return envelope


def render_heating_system_questions() -> str:
    heating_system_name = st.selectbox('Heating System', options=constants.DEFAULT_HEATING_CONSTANTS.keys())
    return heating_system_name