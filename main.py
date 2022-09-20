import streamlit as st

import usage
import solar

has_gas, heating_system = usage.render()
solar_orientation, roof_area_m2 = solar.render()