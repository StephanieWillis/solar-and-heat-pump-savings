import streamlit as st

from solar import Solar


def render_solar_next_steps(solar_install: Solar):

    st.title("Solar - next steps")

    for polygon in solar_install.polygons:
        height = solar_install.convert_plan_value_to_value_along_pitch(polygon.average_plan_height)
        width = polygon.average_width
        st.write(f"First rectangle was {height} m  by {width} m (based on an assumed roof pitch of 30 degrees)")

    st.write("You can install about 4kW of solar PV without approval from your Distribution Network Operator (DNO)."
             "You can install more than this, but you need pre-approval which can take some time. ")


def render_heat_pump_next_steps():
    st.title("Heat pumps - next steps")

    st.write("A good installer is key to ensuring your heat pump runs efficiently. The [heat geek map"
            "](https://www.heatgeek.com/find-a-heat-geek/) is a great place to start your search.")
    st.write("[This article](https://help.sero.life/hc/en-gb/articles/6498847104914-What-is-an-Air-Source-Heat-Pump-)"
             " has more information on heat pumps, including answers to some frequently asked questions")