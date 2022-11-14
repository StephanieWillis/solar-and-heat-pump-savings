import streamlit as st

from solar import Solar


def render_solar_next_steps(solar_install: Solar):
    st.header("Solar - more info")
    with st.expander("More precise solar panel layouts"):
        st.write(" This tool uses your roof dimensions and standard solar panel dimensions to estimate how many panels "
                 "could fit on your roof. We do not account for obstacles such as rooflights and chimneys. If "
                 "you would like to better understand how solar panels could fit around obstacles on your roof, "
                 "you can use the excellent [EasyPV tool](https://easy-pv.co.uk/home).  \n  \n"
                 "Here are your roof dimensions to help you get started:")

        if len(solar_install.polygons) > 1:
            for i, polygon in enumerate(solar_install.polygons):
                height = solar_install.convert_plan_value_to_value_along_pitch(polygon.average_plan_height)
                width = polygon.average_width
                st.write(f"- Polygon {i + 1} was {width:.1f} m wide by {height:.1f} m deep")
            st.caption(f"*(we've assumed your roof pitch is 30 degrees)*")
        elif solar_install.roof_plan_area > 0:
            polygon = solar_install.polygons[0]
            height = solar_install.convert_plan_value_to_value_along_pitch(polygon.average_plan_height)
            width = polygon.average_width
            st.write(f"- {width:.1f} m wide  \n"
                     f"- {height:.1f} m deep *(we've assumed your roof pitch is 30 degrees)*")
        else:
            st.write(
                "Oops - you didn't draw a rectangle on your roof. Please go back to the solar page and use the polygon"
                "tool to draw on your roof.")

        st.caption("Easy PV assumes you need to leave 400mm between the edge of the roof and your solar panels whereas "
                   "we only assume you need to leave 300mm. Real practices seem to vary widely! ")

    with st.expander("How big to go"):
        st.write("You can install about 4kW of solar PV without pre-approval from your Distribution Network Operator "
                 "(DNO). You can install more than this, but you need pre-approval which can take up to 11 weeks so "
                 "it's worth planning ahead if you want to install a bigger system. More info "
                 "[here](https://blog.spiritenergy.co.uk/homeowner/how-many-solar-panels-allowed#:~:text=On%20a%20single%20phase%20supply,roughly%2010%2D13%20solar%20panels_)."
                 "  \n  \n"
                 "The more panels you go for, the smaller the share of the generation you can use for yourself. "
                 "Avoiding buying electricity (at ~34p/kWh) gives you a bigger saving than selling electricity "
                 "(at ~15p/kWh) so smaller installations will have a quicker payback. "
                 "Bigger installations will still give you a bigger return overall however. \n   \n"
                 " If you install a battery at the same time as your solar panels, you will be able to use more of the "
                 "energy you generate. Whether or not that is worth the extra upfront cost depends quite a lot on how "
                 "and when you use electricity.")

    with st.expander("Find an installer"):
        st.write(""" The below list is installers we are aware of who have a good reputation. Get in touch if you would
        like to be added to the list!
        - [Sunsave](https://sunsave.energy)
        - [Your Energy Your Way](https://www.yourenergyyourway.co.uk) (Surrey)
        - [Elite](https://www.elitesg.co.uk/solar-panels) (Hull)
        - [EGE Energy](https://www.egeenergy.com/index.php/services/photo-voltaic-systems) (Norfolk and Suffolk)
        - [C Brookes Heating](https://cbrookesheating.co.uk/services/solar-panel-installation)  (Bristol/South West)
        - [Joju solar](https://www.jojusolar.co.uk) ()
        """)


def render_heat_pump_next_steps():

    st.header("Heat pumps - more info")

    with st.expander("Learn more about heat pumps"):
        st.write("If you'd like to better understand more about heat pumps, including whether a heat pump is suitable "
                 "for your home and whether you need to insulate your home before installing a heat pump, check out "
            "[Sero's explainer on all things heat pump.]("
                 "https://help.sero.life/hc/en-gb/articles/6498847104914-What-is-an-Air-Source-Heat-Pump-)")
        st.write("If you prefer videos, the [Heat Geek Youtube channel](https://www.youtube.com/watch?v=MU5KwrWumY8)"
                 " has some great explainers.")

    with st.expander("Find an installer"):
        st.write("A good installer will ensure your heat pump runs as efficiently as possible. The [heat geek map"
                 "](https://www.heatgeek.com/find-a-heat-geek/) is a great place to find installers who are committed "
                 "to high quality.")

    with st.expander("Survey your own home"):
        st.write("If you love the detail and want to understand things for yourself, you can have a crack at "
                 "calculating your home's heat loss yourself using [Heat Punk](https://heatpunk.co.uk/home). "
                 "You do have to register to use it however.")
