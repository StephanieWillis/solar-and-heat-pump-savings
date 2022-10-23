import streamlit as st

import building_model
import constants


def render() -> "building_model.House":
    st.header("Start by telling us about your house")
    envelope = render_building_envelope_questions()
    heating_system_name = render_heating_system_questions()
    house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name=heating_system_name)
    return house


def render_building_envelope_questions() -> "building_model.BuildingEnvelope":
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("I live in a...")
        with col2:
            house_type = st.selectbox("", options=constants.HOUSE_TYPES)

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("My floor area in metres squared is about")
        with col2:
            house_floor_area_m2 = st.slider(label="", min_value=0, max_value=500, value=80)

    envelope = building_model.BuildingEnvelope(house_type=house_type, floor_area_m2=house_floor_area_m2)
    return envelope


def render_heating_system_questions() -> str:
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("My home is heated with a")
        with col2:
            heating_system_name = st.selectbox("Heating System", options=constants.DEFAULT_HEATING_CONSTANTS.keys())
    return heating_system_name
