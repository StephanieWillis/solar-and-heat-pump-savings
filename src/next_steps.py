import streamlit as st

from solar import Solar


def render_solar_next_steps(solar_install: Solar):

    st.header("Solar - next steps")

    st.subheader("More precise solar panel layouts")
    st.write(" This webapp uses your roof dimensions and standard solar panel dimensions to estimate how many panels"
             "could fit on your roof. We do not however account for obstacles such as velux windows and chimneys. If "
             "you would like to better understand how solar panels could fit around obstacles on your roof, you can use"
             "the excellent [EasyPV tool](https://easy-pv.co.uk/home). You can use the dimensions of the shapes you"
             " have drawn in this tool to help you get started."
             ""
             " This tool assumes you need to leave 400mm between the"
             " edge of the roof and your solar panels whereas we only assume you need to leave 300mm. Real practices "
             "seem to vary widely! ")

    if len(solar_install.polygons > 1):
        for i, polygon in enumerate(solar_install.polygons):
            height = solar_install.convert_plan_value_to_value_along_pitch(polygon.average_plan_height)
            width = polygon.average_width
            st.write(f"- Polygon {i} was {height} m  by {width} m (based on an assumed roof pitch of 30 degrees)")
        else:
            polygon = solar_install.polygons[0]
            height = solar_install.convert_plan_value_to_value_along_pitch(polygon.average_plan_height)
            width = polygon.average_width
            st.write(f"The roof measurements are {height} m  by {width} m (based on an assumed roof pitch of 30 degrees)")

    st.write("You can install about 4kW of solar PV without approval from your Distribution Network Operator (DNO)."
             "You can install more than this, but you need pre-approval which can take some time. ")


def render_heat_pump_next_steps():
    st.title("Heat pumps - next steps")

    st.write("A good installer is key to ensuring your heat pump runs efficiently. The [heat geek map"
            "](https://www.heatgeek.com/find-a-heat-geek/) is a great place to start your search.")
    st.write("[This article](https://help.sero.life/hc/en-gb/articles/6498847104914-What-is-an-Air-Source-Heat-Pump-)"
             " has more information on heat pumps, including answers to some frequently asked questions")