import streamlit as st

import building_model
import constants
from savings_outputs import render_and_update_current_home


def render() -> "building_model.House":
    st.experimental_set_query_params(page="home")
    st.header("Start by telling us about your home")
    envelope = render_building_envelope_questions()
    heating_system_name = render_heating_system_questions()
    house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name=heating_system_name)

    render_results(house)

    return house


def render_building_envelope_questions() -> "building_model.BuildingEnvelope":
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("I live in a")
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


def render_results(house) -> str:
    with st.sidebar:
        st.header("Assumptions")
        st.markdown("<p>If you know details of your current usage or tariff, enter below for greater accuracy</p>", unsafe_allow_html=True)
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
