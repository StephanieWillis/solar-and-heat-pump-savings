from typing import Tuple

import streamlit as st


def render() -> Tuple[bool, float]:
    st.subheader("Your solar potential")

    solar_orientation: bool = st.selectbox('Solar Orientation',
                                           ['south', 'southwest', 'west', 'northwest',
                                            'North', 'northeast', 'east', 'southeast'])

    roof_area_m2 = st.number_input(label='roof_area', min_value=0, max_value=20, value=20)
    st.write(f'Your roof faces {solar_orientation} and has an area of  {roof_area_m2} m\u00b2')
    return solar_orientation, roof_area_m2
