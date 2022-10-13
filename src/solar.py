import pandas as pd
import numpy as np
import streamlit as st

from constants import SolarConstants
import constants
import usage
import roof


def render_questions() -> 'Solar':
    st.header("Your solar potential")

    st.write("Search for your home below and draw a square where you think solar panels might go on your most South"
             "facing roof. Use the hexagonal tool to draw the square.  ")
    polygons = roof.roof_mapper(800, 400)
    # returns list of list of polygons
    if polygons:
        st.write([p.dimensions for p in polygons])

    # TODO: get width and height from polygons once figured out how to get working
    postcode: str = st.text_input("Postcode:")
    orientation: str = st.selectbox('Solar Orientation', SolarConstants.SOLAR_ORIENTATIONS)
    roof_height = st.number_input(label='Roof height (m)', min_value=0.0, max_value=10.0, value=2.0)
    roof_width = st.number_input(label='Roof width (m)', min_value=0.0, max_value=20.0, value=8.0)

    solar_install = Solar(orientation=orientation, roof_width_m=roof_width, roof_height_m=roof_height,
                          postcode=postcode)
    return solar_install


def render_outputs(solar_install: 'Solar'):
    st.header("Solar potential")
    st.write(f'Your roof faces {solar_install.orientation} and could fit  {solar_install.number_of_panels} panels')
    st.write(f'That amounts to {round(solar_install.peak_capacity_kw_out_per_kw_in_per_m2, 1)} kw of peak capacity.')
    st.write(f'We estimate that would generate {int(solar_install.generation.annual_sum_kwh):,} '
             f' kwh of electricity per year')


class Solar:

    def __init__(self, orientation: str, roof_height_m: float, roof_width_m: float, postcode: str):

        self.orientation = orientation
        self.number_of_panels = self.get_number_of_panels(roof_width_m, roof_height_m)
        self.peak_capacity_kw_out_per_kw_in_per_m2 = self.get_peak_capacity(
            kwp_per_panel=SolarConstants.KW_PEAK_PER_PANEL)
        profile_kwh_per_m2 = self.get_generation_profile(postcode=postcode)
        profile_kwh = profile_kwh_per_m2 * self.peak_capacity_kw_out_per_kw_in_per_m2
        self.generation = usage.Consumption(profile_kwh=profile_kwh,
                                            fuel=constants.ELECTRICITY)

    @staticmethod
    def get_number_of_panels(roof_width_m: float, roof_height_m: float) -> float:
        height_available_for_panels = roof_height_m * SolarConstants.PCT_OF_DIMENSION_USABLE
        width_available_for_panels = roof_width_m * SolarConstants.PCT_OF_DIMENSION_USABLE

        number_of_rows = int(height_available_for_panels/SolarConstants.PANEL_HEIGHT_M)
        number_of_columns = int(width_available_for_panels/SolarConstants.PANEL_WIDTH_M)

        number_of_panels = number_of_columns * number_of_rows
        return number_of_panels

    def get_peak_capacity(self, kwp_per_panel: float):
        return self.number_of_panels * kwp_per_panel

    @staticmethod
    def get_generation_profile(postcode: str):
        # TODO properly using orientation and postcode

        # Stand in for now in absense of proper data
        idx = constants.BASE_YEAR_HALF_HOUR_INDEX
        minute_of_the_day = idx.hour * 60 + idx.minute
        kw_per_m2_peak = 0.3
        generation = - np.cos(minute_of_the_day * np.pi * 2/(24 * 60)) * kw_per_m2_peak
        profile_kw_per_m2 = pd.Series(index=constants.BASE_YEAR_HALF_HOUR_INDEX, data=generation)
        profile_kw_per_m2.loc[profile_kw_per_m2 < 0] = 0
        profile_kwh_per_m2 = profile_kw_per_m2/2  # because we know the time base is half hourly
        # If not importing this from elsewhere think about whether need to integrate (take the previous half hour)

        return profile_kwh_per_m2
