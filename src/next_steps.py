import streamlit as st

from solar import Solar


def render(solar_install: Solar):
    render_table_of_contents()
    render_solar_next_steps(solar_install)
    render_heat_pump_next_steps()


def render_table_of_contents():
    st.markdown(
        "<div class='toc'> "
        "<div style='margin-bottom:20px'>"
        "<p class='toc'> Solar Panels </p> "
        "<ul class='toc'>"
        "<a href='#detailed-panel-positioning' class='toc'><li class='toc'> Detailed panel positioning </li></a>"
        "<a href='#how-big-should-i-go'  class='toc'><li class='toc'> How big should I go? </li></a>"
        "<a href='#find-an-installer'  class='toc'><li class='toc'> Find an installer </li></a>"
        "</div>"
        "<div>"
        "<p class='toc'> Heat Pumps </p> "
        "<ul class='toc'>"
        "<a href='#are-they-magic' class='toc'><li class='toc'> Are they... magic? </li></a>"
        "<a href='#survey-your-own-home' class='toc'><li class='toc'> Survey your own home </li></a>"
        "<a href='#find-an-installer' class='toc'><li class='toc'> How big should I go? </li></a>"
        "</div>"
        "</div>"
        ""
        "",
        unsafe_allow_html=True,
    )


def render_solar_next_steps(solar_install: Solar):
    st.header("Solar Panels")
    st.markdown("<h3> Detailed panel positioning</h3>", unsafe_allow_html=True)
    st.markdown(
        "<p class='next-steps'>"
        " This tool uses your roof dimensions and standard solar panel dimensions to estimate how many panels "
        "could fit on your roof. We do not account for obstacles such as rooflights and chimneys. If "
        "you would like to better understand how solar panels could fit around obstacles on your roof, "
        "you can use the excellent <a href='https://easy-pv.co.uk/home'> EasyPV tool</a>.  \n  \n"
        "Here are your roof dimensions to help you get started: </p>",
        unsafe_allow_html=True,
    )

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
        st.write(f"- {width:.1f} m wide  \n" f"- {height:.1f} m deep *(we've assumed your roof pitch is 30 degrees)*")
    else:
        st.warning(
            "Oops - you didn't draw a rectangle on your roof. Please go back to the solar page and use the polygon"
            "tool to draw on your roof."
        )

    st.caption(
        "Our estimate may differ from Easy PV's because you might have chosen panels a with different geometry to the "
        "ones we are modelling. We also make slightly different assumptions than Easy PV on how big a gap you need "
        "to leave between your solar panels and the edge of your roof. Real practices seem to vary widely! "
    )
    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("How big should I go?")
    st.markdown(
        "<p class='next-steps'>"
        "You can install about 4kW of solar PV without pre-approval from your Distribution Network Operator "
        "(DNO). You can install more than this, but you need pre-approval which can take up to 11 weeks so "
        "it's worth planning ahead if you want to install a bigger system. <a href='https://blog.spiritenergy.co.uk/homeowner/how-many-solar-panels-allowed#:~:text=On%20a%20single%20phase%20supply,roughly%2010%2D13%20solar%20panels_'> More info here </a>."
        "</p>"
        "<p class='next-steps'>"
        "The more panels you go for, the smaller the share of the generation you can use for yourself. "
        "Avoiding buying electricity (at ~34p/kWh) gives you a bigger saving than selling electricity "
        "(at ~15p/kWh) so smaller installations will have a quicker payback. "
        "Bigger installations will still give you a bigger return overall however."
        "</p>"
        "<p class='next-steps'>"
        " If you install a battery at the same time as your solar panels, you will be able to use more of the "
        "energy you generate. Whether or not that is worth the extra upfront cost depends quite a lot on how "
        "and when you use electricity."
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Find an installer")
    st.markdown(
        """<p class='next-steps'> These are installers about whom we hear good things. <a href='mailto:stephaniewillis808@gmail.com'> Get in touch </a> if you would
        like to be added to the list!</p>
        <ul>
        <li> <a href='https://sunsave.energy'> Sunsave (National) </a> </li>
        <li> <a href='https://www.yourenergyyourway.co.uk'> Your Energy Your Way (Surrey) </a> </li>
        <li> <a href='https://www.elitesg.co.uk/solar-panels'> Elite (Hull) </a> </li> 
        <li> <a href='https://www.egeenergy.com/index.php/services/photo-voltaic-systems> EGE Energy (Norfolk and Suffolk) </a> </li>
        <li> <a href='https://cbrookesheating.co.uk/services/solar-panel-installation'> C Brookes Heating (Bristol/South West) </a></li>
        <li><a href='https://www.jojusolar.co.uk'> Joju solar </a> </li>
        """,
        unsafe_allow_html=True,
    )


def render_heat_pump_next_steps():
    st.header("Heat pumps")

    st.subheader("Are they... magic?")
    st.markdown(
        "<p class='next-steps'>"
        "If you'd like to understand more about heat pumps, including whether a heat pump is suitable "
        "for your home and whether you need to insulate your home before installing a heat pump, check out "
        "<a href='https://help.sero.life/hc/en-gb/articles/6498847104914-What-is-an-Air-Source-Heat-Pump-'>Sero's explainer on all things heat pump. </a>"
        ""
        "</p>"
        "<p class='next-steps'>"
        "If you prefer videos, the <a href='https://www.youtube.com/watch?v=MU5KwrWumY8'>Heat Geek Youtube channel</a>"
        " has some great explainers."
        "<br>"
        "<br>",
        unsafe_allow_html=True,
    )

    st.write()

    st.subheader("Survey your own home")
    st.markdown(
        "<p class='next-steps'>"
        "If you love the detail and want to understand things for yourself, you can have a crack at "
        "calculating your home's heat loss yourself using <a href='https://heatpunk.co.uk/home'>Heat Punk</a>. "
        "</p>"    
        "<br>",
        unsafe_allow_html=True,
    )

    st.subheader("Find an installer")
    st.markdown(
        "<p class='next-steps'>"
        "A good installer will ensure your heat pump runs as efficiently as possible. The <a href='https://www.heatgeek.com/find-a-heat-geek/'>heat geek map</a>"
        " is a great place to find installers who are certified "
        "to perform high quality installs."
        "</p>"
        "<br>",
        unsafe_allow_html=True,
    )
