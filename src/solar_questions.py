import streamlit as st

from constants import SolarConstants
import roof
from solar import Solar


def render() -> "Solar":
    """Render inputs to calculate solar outputs. If a solar install has already been set up, modify that"""
    solar_install_in = get_solar_install_from_session_state_if_exists_or_create_default()

    st.header("How much solar power could you generate?")

    st.write(
        """
        - Search for your home below
        - Using the tool with the ⭓ icon, draw the biggest rectangle that fits on your most south facing roof
        - Make sure you 'close' the rectangle by clicking back on the first point at the end
        - You can draw multiple rectangles if needed
        - Enter the orientation of the side of the roof you have drawn on"""
    )

    try:
        polygons = roof.roof_mapper(800, 400)  # figure out how to save state here
    except KeyError:
        st.error("You've used a drawing tool we don't support, sorry! Please try with the ⭓ or ◼️ tools")
        polygons = None

    polygons = polygons if polygons else solar_install_in.polygons

    orientation_options = [name for name, _ in SolarConstants.ORIENTATIONS.items()]
    idx = orientation_options.index(solar_install_in.orientation.name)
    orientation_name: str = st.selectbox("Solar Orientation", orientation_options, index=idx)
    orientation = SolarConstants.ORIENTATIONS[orientation_name]

    solar_install = Solar(orientation=orientation, polygons=polygons)

    # Overwrite number of panels if it has previously been overwritten by user
    if solar_install_in.number_of_panels_has_been_overwritten:
        solar_install.number_of_panels = solar_install_in.number_of_panels

    # Overwrite panel capacity because not an issue to use the existing value even if it hasn't been overwritten
    solar_install.kwp_per_panel = solar_install_in.kwp_per_panel

    solar_install = render_results(solar_install)
    return solar_install


def get_solar_install_from_session_state_if_exists_or_create_default():
    if st.session_state["page_state"]["solar"] == {}:
        solar_install = Solar.create_zero_area_instance()
        st.session_state["page_state"]["solar"] = dict(solar=solar_install)
    else:
        solar_install = st.session_state["page_state"]["solar"]["solar"]
    return solar_install


def render_and_update_solar_inputs(solar_install: "Solar"):
    # Note: once this has been overwritten it is decoupled from roof area for the rest of the session

    if "number_of_panels" not in st.session_state or st.session_state.number_of_panels == 0:
        st.session_state.number_of_panels = solar_install.number_of_panels
        st.session_state.kwp_per_panel = solar_install.kwp_per_panel

    solar_install.number_of_panels = st.number_input(
        label="Number of panels", min_value=0, max_value=None, key="number_of_panels"
    )
    solar_install.kwp_per_panel = st.number_input(
        label="Capacity per panel (kWp)", min_value=0.0, max_value=0.8, key="kwp_per_panel"
    )

    st.session_state["page_state"]["solar"] = dict(solar=solar_install)

    return solar_install


def render_results(solar_install: Solar):
    with st.sidebar:
        st.header("Solar inputs")

        st.caption("If you have a better estimate of how much solar could fit on your roof, enter it below:")

        solar_install = render_and_update_solar_inputs(solar_install=solar_install)

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
