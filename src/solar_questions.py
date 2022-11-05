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

    solar_install = Solar(orientation=orientation,
                          roof_plan_area=roof_plan_area,
                          latitude=lat,
                          longitude=lng)

    # Overwrite number of panels if it has previously been overwritten by user
    if solar_install_in.number_of_panels_has_been_overwritten:
        solar_install.number_of_panels = solar_install_in.number_of_panels

    # Overwrite panel capacity because not an issue to use the existing value even if it hasn't been overwritten
    solar_install.kwp_per_panel = solar_install_in.kwp_per_panel

    solar_install = render_results(solar_install)
    return solar_install


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


def render_and_update_solar_inputs(solar: 'Solar'):
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


def render_results(solar_install: Solar):
    with st.sidebar:
        st.header("Solar inputs")
        st.markdown(
            "<p>If you have a better estimate of how much solar could fit on your roof, enter it below</p>",
            unsafe_allow_html=True)
        solar_install = render_and_update_solar_inputs(solar=solar_install)

    if solar_install.peak_capacity_kw_out_per_kw_in_per_m2 > 0:
        st.write(f"We estimate you can fit {solar_install.number_of_panels} solar panels on your roof. "
                 f"That's a {solar_install.peak_capacity_kw_out_per_kw_in_per_m2} kW installation which would generate "
                 f"about {int(solar_install.generation.exported.annual_sum_kwh)} kWh of electricity a year!")
    return solar_install
