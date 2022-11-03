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
    house_type_name = st.selectbox('House Type', options=list(constants.BUILDING_TYPE_OPTIONS.keys()))
    building_type_constants = constants.BUILDING_TYPE_OPTIONS[house_type_name]
    envelope = building_model.BuildingEnvelope.from_building_type_constants(building_type_constants)
    return envelope


def render_heating_system_questions() -> str:
    heating_system_name = st.selectbox('Heating System', options=constants.DEFAULT_HEATING_CONSTANTS.keys())
    return heating_system_name
