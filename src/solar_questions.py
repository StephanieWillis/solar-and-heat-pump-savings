import streamlit as st

from constants import SolarConstants
import roof
from solar import Solar


def render() -> 'Solar':
    """ Render inputs to calculate solar outputs. If a solar install has already been set up, modify that"""
    solar_install_in = get_solar_install_from_session_state_if_exists_or_create_default()

    st.header("How much solar power could you generate?")

    st.write(
        "Search for your home below and draw a square where you think solar panels might go. If you have"
        " multiple options, choose your most South facing roof. Use the hexagonal tool to draw the square.  "
    )
    polygons = roof.roof_mapper(800, 400)  # figure out how to save state here

    orientation_options = [name for name, _ in SolarConstants.ORIENTATIONS.items()]
    idx = orientation_options.index(solar_install_in.orientation.name)
    orientation_name: str = st.selectbox("Solar Orientation", orientation_options, index=idx)
    orientation = SolarConstants.ORIENTATIONS[orientation_name]

    roof_plan_area = sum([polygon.area for polygon in polygons]) if polygons else solar_install_in.roof_plan_area
    #  just take first polygon - lat long don't need to be super precise
    (lat, lng) = polygons[0].points[0] if polygons else (solar_install_in.latitude, solar_install_in.longitude)

    solar_install_out = Solar(orientation=orientation,
                              roof_plan_area=roof_plan_area,
                              latitude=lat,
                              longitude=lng)

    # Overwrite number of panels only if it has been overwritten by user because otherwise will be stuck at default of 0
    if solar_install_in.number_of_panels_has_been_overwritten:
        solar_install_out.number_of_panels = solar_install_in.number_of_panels

    # Overwrite panel capacity because not an issue to use even if it hasn't bene overwritten
    solar_install_out.kwp_per_panel = solar_install_in.kwp_per_panel

    if polygons:
        st.write(f"We estimate you can fit {solar_install_out.number_of_panels} solar panels on your roof!")

    return solar_install_out


def get_solar_install_from_session_state_if_exists_or_create_default():
    if st.session_state["page_state"]["solar"] == {}:
        solar_install = set_up_default_solar_install()
        st.session_state["page_state"]["solar"] = dict(solar=solar_install)
    else:
        solar_install = st.session_state["page_state"]["solar"]["solar"]
    return solar_install


def set_up_default_solar_install() -> 'Solar':
    orientation_options = [name for name, _ in SolarConstants.ORIENTATIONS.items()]
    solar_install = Solar(orientation=SolarConstants.ORIENTATIONS[orientation_options[0]],
                          roof_plan_area=0,
                          latitude=SolarConstants.DEFAULT_LAT,
                          longitude=SolarConstants.DEFAULT_LONG)
    return solar_install


def render_and_update_solar(solar: 'Solar'):
    # Note: once this has been overwritten it is decoupled from roof area for the rest of the session
    solar.number_of_panels = st.number_input(label='Number of panels',
                                             min_value=0,
                                             max_value=40,
                                             value=int(solar.number_of_panels))
    solar.kwp_per_panel = st.number_input(label='capacity_per_panel',
                                          min_value=0.0,
                                          max_value=0.8,
                                          value=solar.kwp_per_panel)
    return solar
