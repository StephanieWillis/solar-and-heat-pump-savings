import streamlit as st

import usage
import solar


st.write("This tool is to help you get a rough idea of how much money and carbon you might save by installing a "
         "heat pump and/or solar panels. The real costs and performance will depend on the specifics of your home, this"
         " tool merely aims to help you sense for what the impacts might be. Throughout the tool we have made estimates"
         " of various values, but you can overwrite them if you have better info. ")
house, heating_system = usage.render_questions()
usage.render_outputs(house=house, heating_system=heating_system)

solar_install = solar.render_questions()
solar.render_outputs(solar_install=solar_install)

# Print baseline (and let fiddle)
# Run case with HP if no HP
# Run case with solar
# Run case with HP + solar





