import streamlit as st

from typing import Optional, List

from constants import SolarConstants, CLASS_NAME_OF_SIDEBAR_DIV
import roof
from solar import Solar


def get_solar_install_from_session_state_if_exists_or_create_default():
    if "solar_install" not in st.session_state:
        solar_install = Solar.create_zero_area_instance()
        st.session_state.number_of_panels_defined_by_dropdown = False
    else:
        solar_install = st.session_state.solar_install
        st.session_state.number_of_panels_defined_by_dropdown = solar_install.number_of_panels_has_been_overwritten
    return solar_install


def render(solar_install: Solar) -> "Solar":
    """Render inputs to calculate solar outputs. If a solar install has already been set up, modify that"""

    st.header("How much solar power could you generate?")
    st.markdown(
        f"<p class='more-info'> If you already have a solar array <a  href='javascript:document.getElementsByClassName("
        f"{CLASS_NAME_OF_SIDEBAR_DIV})[1].click();' target='_self'>"
        "you can enter the details here</a></p>",
        unsafe_allow_html=True,
    )

    polygons = render_map()
    orientation = render_orientation_questions(solar_install)

    # if polygons changed (figure out how to persist polygons when page changes)
    if polygons != solar_install.polygons:
        print("Setting up solar install based on polygons")
        solar_install = Solar(orientation=orientation, polygons=polygons)
        st.session_state.number_of_panels = solar_install.number_of_panels
        st.session_state.number_of_panels_defined_by_dropdown = False
    else:
        print("Not changing default solar install as no polygons drawn")
        solar_install.orientation = orientation  # in case orientation changed

    solar_install = render_solar_assumptions_sidebar(solar_install)
    solar_install = render_results(solar_install)

    return solar_install


def render_map() -> Optional[List[roof.Polygon]]:

    try:
        polygons = roof.roof_mapper(800, 400)  # figure out how to save state here
    except KeyError:
        st.error("You've used a drawing tool we don't support, sorry! Please try with the ⭓ tool")
        polygons = None

    polygons = polygons if polygons else Solar.create_zero_area_instance().polygons

    return polygons


def render_orientation_questions(solar_install: Solar):
    st.subheader("Orientation")
    orientation_options = [name for name, _ in SolarConstants.ORIENTATIONS.items()]
    if "orientation_name" not in st.session_state:
        st.session_state.orientation_name = solar_install.orientation.name
    orientation_name: str = st.selectbox(label="Enter the orientation of the side of the roof you have drawn on",
                                         options=orientation_options,
                                         key="orientation_name",
                                         help="The more south-facing your roof, the more energy your solar panels will"
                                              "generate")
    orientation = SolarConstants.ORIENTATIONS[orientation_name]
    return orientation


def render_solar_assumptions_sidebar(solar_install: 'Solar') -> 'Solar':
    with st.sidebar:
        st.header("Solar inputs")

        st.caption("If you have a better estimate of how much solar could fit on your roof, enter it below:")

        solar_install = render_solar_overwrite_options(solar_install=solar_install)
    return solar_install


def render_solar_overwrite_options(solar_install: "Solar"):

    if "number_of_panels" not in st.session_state:
        st.session_state.number_of_panels = solar_install.number_of_panels
    if "number_of_panels_overwritten" not in st.session_state:
        st.session_state.number_of_panels_overwritten = False

    st.number_input(
        label="Number of panels",
        min_value=0,
        max_value=None,
        key="number_of_panels_overwrite",
        value=st.session_state.number_of_panels,
        on_change=overwrite_number_of_panels_in_session_state)

    if st.session_state.number_of_panels_overwritten:
        solar_install.number_of_panels = st.session_state.number_of_panels
        write_solar_cost_to_session_state(solar_install)
        print(f"Behaves as if number of panels changed to {solar_install.number_of_panels} and overwrite flag set to"
              f"{solar_install.number_of_panels_has_been_overwritten}")
        st.session_state.number_of_panels_overwritten = False

    if "kwp_per_panel" not in st.session_state:
        st.session_state.kwp_per_panel = solar_install.kwp_per_panel
        st.session_state.kwp_per_panel_overwritten = False

    st.number_input(
        label="Capacity per panel (kWp)",
        min_value=0.0,
        max_value=0.8,
        key="kwp_per_panel_overwrite",
        value=st.session_state.kwp_per_panel,
        on_change=overwrite_kwp_of_panels_in_session_state,
        )

    if st.session_state.kwp_per_panel_overwritten:
        print("Behaves as if kWp of panels changed")
        solar_install.kwp_per_panel = st.session_state.kwp_per_panel
        st.session_state.kwp_per_panel_overwritten = False
        write_solar_cost_to_session_state(solar_install)

    if "pitch" not in st.session_state:
        st.session_state.pitch = solar_install.pitch
        st.session_state.pitch_overwritten = False

    st.number_input(
        label="Roof pitch (°)",
        min_value=0,
        max_value=90,
        key="pitch_overwrite",
        value=st.session_state.pitch,
        on_change=overwrite_pitch_in_session_state,
        help="30° is typical but 45° is also fairly common")

    if st.session_state.pitch_overwritten:
        print("Behaves as if pitch of roof changed")
        solar_install.pitch = st.session_state.pitch
        st.session_state.pitch_overwritten = False
        write_solar_cost_to_session_state(solar_install)

    st.session_state["page_state"]["solar"] = dict(solar=solar_install)  # I think this is obsolete

    return solar_install


def overwrite_number_of_panels_in_session_state():
    st.session_state.number_of_panels_defined_by_dropdown = True
    print(st.session_state.number_of_panels_overwrite)
    st.session_state.number_of_panels = st.session_state.number_of_panels_overwrite
    print(st.session_state.number_of_panels)
    st.session_state.number_of_panels_overwritten = True


def overwrite_kwp_of_panels_in_session_state():
    st.session_state.kwp_per_panel = st.session_state.kwp_per_panel_overwrite
    st.session_state.kwp_per_panel_overwritten = True


def overwrite_pitch_in_session_state():
    st.session_state.pitch = st.session_state.pitch_overwrite
    st.session_state.pitch_overwritten = True


def write_solar_cost_to_session_state(solar_install):
    solar_install.clear_cost_overwrite()
    st.session_state.solar_cost = solar_install.upfront_cost
    st.session_state.solar_cost_overwritten = False


def render_results(solar_install: Solar):
    if solar_install.peak_capacity_kw_out_per_kw_in_per_m2 > 0:
        st.markdown(
            f"<p class='bill-label' style='text-align: center'>We estimate you can fit </p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p class='bill-estimate' style='text-align: center'>  {solar_install.number_of_panels}  </p>"
            "<p class='bill-label' style='text-align: center'> solar panels on your roof</p>",
            unsafe_allow_html=True,
        )
        st.write(
            f" <p class='bill-details' style='text-align: center'> That's a "
            f"{solar_install.peak_capacity_kw_out_per_kw_in_per_m2:.1f} kW installation which would generate "
            f"about {int(solar_install.generation.exported.annual_sum_kwh)} kWh of electricity a year! </p>",
            unsafe_allow_html=True,
        )
    elif solar_install.roof_plan_area > 0:  # for case where capacity is zero but shape has been drawn
        st.warning(
            "Oops! This shape isn't big enough to fit a"
            " solar panel in. Make sure you draw the shape right up to the edge of your roof.",
        )
    return solar_install
