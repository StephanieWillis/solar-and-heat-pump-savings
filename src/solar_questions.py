import streamlit as st

from constants import SolarConstants
import roof
from building_model import Solar


def render() -> 'Solar':
    st.header("Your solar potential")

    st.write(
        "Search for your home below and draw a square where you think solar panels might go on your most South"
        "facing roof. Use the hexagonal tool to draw the square.  "
    )
    polygons = roof.roof_mapper(800, 400)

    orientation: str = st.selectbox("Solar Orientation", SolarConstants.SOLAR_ORIENTATIONS)

    solar_install = Solar(orientation=orientation, roof_plan_area=polygons.area if polygons else 0)
    if polygons:
        st.write(f"We estimate you can fit {solar_install.number_of_panels} solar panels on your roof!")

    return solar_install


