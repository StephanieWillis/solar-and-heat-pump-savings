import streamlit as st

import usage
import solar
import roof
#
# has_gas, heating_system = usage.render()
# solar_orientation, roof_area_m2 = solar.render()

polygons = roof.roof_mapper(800, 400)
if polygons:
    st.write([p.dimensions for p in polygons])