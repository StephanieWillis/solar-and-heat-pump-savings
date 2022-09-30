import streamlit as st

import usage
import solar
import roof
#
# has_gas, heating_system = usage.render()
# solar_orientation, roof_area_m2 = solar.render()

roof.roof_mapper(800, 400)
st.text_input('demo')