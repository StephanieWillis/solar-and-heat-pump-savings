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
        "<a href='#find-a-solar-installer'  class='toc'><li class='toc'> Find a solar installer </li></a>"
        "</div>"
        "<div>"
        "<p class='toc'> Heat Pumps </p> "
        "<ul class='toc'>"
        "<a href='#are-they-magic' class='toc'><li class='toc'> Are they... magic? </li></a>"
        "<a href='#find-a-heat-pump-installer' class='toc'><li class='toc'> Find a heat pump installer </li></a>"
        "<a href='#typical-costs' class='toc'><li class='toc'> Typical costs </li></a>"
        "<a href='#survey-your-own-home' class='toc'><li class='toc'> Survey your own home </li></a>"
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
        " This tool uses the dimensions of your roof and a standard solar panel to estimate how many panels "
        "could fit on your roof. We do not account for obstacles such as rooflights and chimneys. If "
        "you would like to better understand how solar panels could fit around obstacles on your roof, "
        "you can use the excellent <a href='https://easy-pv.co.uk/home'> EasyPV tool</a>.  \n  \n"
        "Here are your roof dimensions to help you get started: </p>",
        unsafe_allow_html=True,
    )

    if len(solar_install.polygons) > 1:
        st.markdown("<div class='toc'> ", unsafe_allow_html=True)
        for i, polygon in enumerate(solar_install.polygons):
            height = solar_install.convert_plan_value_to_value_along_pitch(polygon.average_plan_height)
            width = polygon.average_width
            st.markdown(f"- Polygon {i + 1} was {width:.1f} m wide by {height:.1f} m deep")
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

    st.markdown("""
        <p class='next-steps'>
        Our estimate may differ from Easy PV's: panel geometry varies, and we make slightly different assumptions
         on the gap you need to leave between your solar panels and the edge of your roof. 
         Real practices seem to vary widely! 
        </ p >""",
                unsafe_allow_html=True,
                )
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<h3> How big should I go?</h3>", unsafe_allow_html=True)
    st.markdown(
        "<p class='next-steps'>"
        "You can install up to 4kW of solar PV without pre-approval from your Distribution Network Operator "
        "(DNO). Pre-approval for larger installs can take up to 11 weeks so "
        "it's worth planning ahead! <a href='https://blog.spiritenergy.co.uk/homeowner/how-many-solar-panels-allowed#:~:text=On%20a%20single%20phase%20supply,roughly%2010%2D13%20solar%20panels_'> More info here </a>."
        "</p>"
        "<p class='next-steps'>"
        "The more panels you have, the more likely you are to want to sell some electricity back to the grid. "
        "The rate you get paid for selling electricity from your panels (~15p/kWh) isn't as high as the rate"
        "you pay for electricity (~34p/kWh), which means that your panels will make you money slower once"
        "you've replace all of your electricity purchases. This means that smaller installations (just replace"
        "your own usage) will pay back faster than bigger ones (replace your energy use + sell to the grid)"
        "However, in the long run, the bigger the installation, the more money you make!"
        "</p>"
        "<p class='next-steps'>"
        " If you install a battery at the same time as your solar panels, you will be able to use more of the "
        "energy you generate. Whether or not the battery will deliver big enough savings to cover its upfront cost "
        "depends quite a lot on how and when you use electricity, which we can't model accurately here!"
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<h3> Find a solar installer </h3>", unsafe_allow_html=True)
    st.markdown(
        """<p class='next-steps'> These are installers about whom we hear good things. <a href='mailto:stephaniewillis808@gmail.com'> Get in touch </a> if you would
        like to be added to the list!</p>
        <ul>
        <li> <a href='https://sunsave.energy'> Sunsave (National) </a> </li>
        <li> <a href='https://www.yourenergyyourway.co.uk'> Your Energy Your Way (Surrey) </a> </li>
        <li> <a href='https://www.elitesg.co.uk/solar-panels'> Elite (Hull) </a> </li> 
        <li> <a href='https://www.egeenergy.com/index.php/services/photo-voltaic-systems> EGE Energy (Norfolk and Suffolk) </a> </li>
        <li> <a href='https://cbrookesheating.co.uk/services/solar-panel-installation'> C Brookes Heating (Bristol/South West) </a></li>
        <li> <a href='https://www.jojusolar.co.uk'> Joju solar </a> </li>
        
        """,
        unsafe_allow_html=True,
    )


def render_heat_pump_next_steps():
    st.header("Heat pumps")

    st.subheader("Are they... magic?")
    st.markdown(
        "<p class='next-steps'>"
        "Yes, kind of! But in a 'technology is magical' way, rather than a 'this is made up' way. "
        " If you'd like to understand more about heat pumps, including whether a heat pump is suitable "
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

    st.subheader("Find a heat pump installer")
    st.markdown(
        "<p class='next-steps'>"
        "A good installer will ensure your heat pump runs as efficiently as possible."
        " The <a href='https://www.heatgeek.com/find-a-heat-geek/'>Heat Geek Map</a>"
        " is a great place to find high quality installers."
        "</p>"
        "<br>",
        unsafe_allow_html=True,
    )

    st.markdown("<h3> Typical costs </h3>", unsafe_allow_html=True)
    st.markdown(""" <p class='next-steps'>
        The costs we use are rough estimates based on historical data + inflation.
         The cost for your home will vary depending on:
        <ol type="1">
        <li> How many radiators need replacing</li>
        <li> Whether any of your pipework needs replacing</li>
        <li> Whether you have a hot water tank that can be repurposed to work with the heat pump</li>
        <li> How much heating your home needs</li>
        <li> Where in the country you are located</li>
        </ol>
        This <a href='http://asf-hp-cost-demo-l-b-1046547218.eu-west-1.elb.amazonaws.com'>cost estimator tool</a> 
        from Nesta is based on historical data on heat pump installs and might give you better a sense of how much a 
        heat pump might cost in a home like yours.
        </p>
        <p class='next-steps'>
        The quality of the design and install is vital to ensure you get the lowest bills possible, so it can
        definitely be worth paying more for
         <a href='https://ainsdalegas.co.uk/blog/post/what-can-go-wrong-with-a-cheap-heat-pump-installation'>
         a high quality install</a>.
        </p>
        <br>""",
                unsafe_allow_html=True,
                )

    st.markdown("<h3> What if energy prices change? </h3>", unsafe_allow_html=True)
    st.markdown(""" <p class='next-steps'>
        Whether or not a heat pump reduces your bills depends on the efficiency of your heat pump, and the ratio of
        the cost of electricity to the cost of gas. Currently, the electricity/gas ratio is relatively
        low meaning that a good heat pump install will save you money on your bills. It's hard to know what will happen
        next with energy prices, but 
        <a href='https://www.nesta.org.uk/report/how-the-energy-crisis-affects-the-case-for-heat-pumps/how-the-costs-of-heat-pumps-compare-to-gas-boilers-since-the-energy-crisis-1/#content'>
         forecasts</a> suggest that that ratio will stay low enough that 
        good heat pump installs will continue to give lower bills than gas boilers. Of course, things may change! 
        But whatever happens to energy prices, a heat pump will continue to be a massive win from a climate perspective.
        </p>
        <br>""",
                unsafe_allow_html=True,
                )

    st.subheader("Survey your own home")
    st.markdown(
        "<p class='next-steps'>"
        "If you love the detail and want to understand things for yourself, you can have a crack at "
        "calculating your own home's heat loss using <a href='https://heatpunk.co.uk/home'>Heat Punk</a>. "
        "</p>"
        "<br>",
        unsafe_allow_html=True,
    )
