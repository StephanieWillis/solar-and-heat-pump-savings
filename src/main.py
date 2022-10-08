import streamlit as st

import usage
import solar

st.info("This tool is to help you get a rough idea of how much money and carbon you might save by installing a "
         "heat pump and/or solar panels. The real costs and performance will depend on the specifics of your home."
         " Throughout the tool we have made estimates"
         " of various values, but you can overwrite them if you have better info. ")

use_qs_tab, solar_qs_tab, savings_tab = st.tabs(["Usage Questions", "Solar Questions", "Your Savings Potential"])
with use_qs_tab:
    house = usage.render_questions()
with solar_qs_tab:
    solar_install = solar.render_questions()
with savings_tab:
    house = usage.render_outputs(house=house)
    # solar.render_outputs(solar_install=solar_install)

