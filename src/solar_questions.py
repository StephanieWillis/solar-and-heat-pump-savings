import streamlit as st

from constants import SolarConstants
import roof
from solar import Solar


def render() -> 'Solar':
    st.header("Your solar potential")

    st.write(
        "Search for your home below and draw a square where you think solar panels might go on your most South"
        "facing roof. Use the hexagonal tool to draw the square.  "
    )
    polygons = roof.roof_mapper(800, 400)

    orientation_options = [name for name, azimuth in SolarConstants.ORIENTATIONS.items()]
    orientation_name: str = st.selectbox("Solar Orientation", orientation_options)
    orientation = SolarConstants.ORIENTATIONS[orientation_name]

    roof_plan_area = sum([polygon.area for polygon in polygons]) if polygons else 0
    (lat, lng) = polygons[0].points[0] if polygons else (SolarConstants.DEFAULT_LAT, SolarConstants.DEFAULT_LONG)
    #  just take first polygon - lat long don't need to be super precise
    solar_install = Solar(orientation=orientation,
                          roof_plan_area=roof_plan_area,
                          latitude=lat,
                          longitude=lng)
    if polygons:
        st.write(f"We estimate you can fit {solar_install.number_of_panels} solar panels on your roof!")

    return solar_install


