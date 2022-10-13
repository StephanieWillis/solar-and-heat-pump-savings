import streamlit as st

from constants import SolarConstants
import roof
from building_model import Solar


def render() -> 'Solar':
    st.header("Your solar potential")

    st.write("Search for your home below and draw a square where you think solar panels might go on your most South"
             "facing roof. Use the hexagonal tool to draw the square.  ")
    polygons = roof.roof_mapper(800, 400)
    if polygons:
        st.write([p.dimensions for p in polygons])

    # TODO: get width and height from polygons once figured out how to get working
    postcode: str = st.text_input("Postcode:")
    orientation: str = st.selectbox('Solar Orientation', SolarConstants.SOLAR_ORIENTATIONS)
    roof_height = st.number_input(label='Roof height (m)', min_value=0.0, max_value=10.0, value=2.0)
    roof_width = st.number_input(label='Roof width (m)', min_value=0.0, max_value=20.0, value=8.0)

    solar_install = Solar(orientation=orientation, roof_width_m=roof_width, roof_height_m=roof_height,
                          postcode=postcode)
    return solar_install


