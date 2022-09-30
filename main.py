import streamlit as st

import usage
import solar

has_gas, heating_system = usage.render()
solar_install = solar.render()