from functools import cache
from math import floor
from typing import List

import numpy as np
import pandas as pd
import requests

import constants
from constants import SolarConstants, Orientation
from consumption import Consumption
from roof import Polygon


class Solar:

    def __init__(self, orientation: Orientation, polygons: List[Polygon],
                 pitch: float = SolarConstants.ROOF_PITCH_DEGREES):

        self.orientation = orientation
        self.polygons = polygons
        self.pitch = pitch

        #  just take first polygon - lat long don't need to be super precise
        (lat, lng) = polygons[0].points[0]
        self.latitude = lat  # Latitude, in decimal degrees, south is negative
        self.longitude = lng  # Longitude, in decimal degrees, west is negative

        roof_plan_area = sum([polygon.area for polygon in polygons])
        self.roof_plan_area = roof_plan_area  # Plan area because based on lat long therefore doesn't account for pitch

        # The below two can be overwritten by user, so they are not set up as properties.
        # This means changes in roof area after initial set up won't change the number of panels
        self.number_of_panels = self.get_number_of_panels_from_polygons()
        self.kwp_per_panel = SolarConstants.KW_PEAK_PER_PANEL

    def __hash__(self):
        return hash((self.latitude,
                     self.longitude,
                     self.pitch,
                     self.peak_capacity_kw_out_per_kw_in_per_m2,
                     self.orientation.azimuth_degrees
                     ))

    def __eq__(self, other: 'Solar'):
        result = (self.latitude == other.latitude
                  and self.longitude == other.longitude
                  and self.pitch == other.pitch
                  and self.peak_capacity_kw_out_per_kw_in_per_m2 == other.peak_capacity_kw_out_per_kw_in_per_m2
                  and self.orientation.azimuth_degrees == other.orientation.azimuth_degrees
                  )
        return result

    @classmethod
    def create_zero_area_instance(cls):
        # select orientation to match first dropdown option
        orientation = [orientation for orientation in SolarConstants.ORIENTATIONS.values()][0]
        default_install = cls(orientation=orientation,
                              polygons=[Polygon.make_zero_area_instance()],
                              pitch=SolarConstants.ROOF_PITCH_DEGREES)
        return default_install

    @property
    def roof_area(self):
        area = self.convert_plan_value_to_value_along_pitch(self.roof_plan_area)
        return area

    def convert_plan_value_to_value_along_pitch(self, value: float):
        return value / np.cos(np.radians(self.pitch))

    def get_number_of_panels_from_polygons(self) -> int:
        print(self.roof_area)
        numbers = []
        for polygon in self.polygons:
            if len(polygon.dimensions) != 4:  # if not roughly rectangular
                print("Calculated based on area")
                number_this_polygon = self.get_number_of_panels_from_polygon_area(polygon)
            else:
                print("Calculated based on side lengths")
                number_this_polygon = self.max_number_of_panels_in_a_rectangle(polygon)
            numbers.append(number_this_polygon)
        print(f"number this polygon: {number_this_polygon}")
        all_panels = sum(numbers)
        print(f"number all polygons: {all_panels}")
        print(f"number based on area: {self.get_number_of_panels_from_polygon_area(polygon)}")
        return all_panels

    def get_number_of_panels_from_polygon_area(self, polygon: Polygon) -> int:
        """ Very simplified assumptions to fall back on when shape not roughly rectangular"""
        area = self.convert_plan_value_to_value_along_pitch(polygon.area)
        usable_area = area * SolarConstants.PERCENT_SQUARE_USABLE
        number_of_panels = floor(usable_area / SolarConstants.PANEL_AREA)
        return number_of_panels

    def max_number_of_panels_in_a_rectangle(self, polygon) -> int:
        """ Assume shape is rectangular. Try panels in either orientation"""
        roof_height = polygon.average_plan_height / np.cos(np.radians(self.pitch))
        print(f"roof height = {roof_height}, roof_width = {polygon.average_width}")
        # Typically installers leave a bigger border on big roofs. Increase border if fit more than 2 rows heightwise
        if roof_height >= 2 * (SolarConstants.SMALL_PANEL_BORDER_M + SolarConstants.PANEL_HEIGHT_M):
            border_to_use = SolarConstants.BIG_PANEL_BORDER_M
        else:
            border_to_use = SolarConstants.SMALL_PANEL_BORDER_M
        print("long side up roof")
        option_1 = self.number_of_panels_in_rectangle(side_1=polygon.average_width, side_2=roof_height,
                                                      border=border_to_use)
        print("short side up roof")
        option_2 = self.number_of_panels_in_rectangle(side_1=roof_height, side_2=polygon.average_width,
                                                      border=border_to_use)
        number = max(option_1, option_2)
        return number

    @staticmethod
    def number_of_panels_in_rectangle(side_1: float, side_2: float, border: float) -> int:
        if side_1 < SolarConstants.SMALL_PANEL_BORDER_M or side_2 < SolarConstants.SMALL_PANEL_BORDER_M:
            number = 0
        else:
            rows_axis_1 = floor((side_1 - border) / SolarConstants.PANEL_WIDTH_M)
            rows_axis_2 = floor((side_2 - border) / SolarConstants.PANEL_HEIGHT_M)
            number = rows_axis_1 * rows_axis_2
            print(f"{rows_axis_1} by {rows_axis_2}")
        return number

    @property
    def number_of_panels_has_been_overwritten(self):
        return self.number_of_panels != self.get_number_of_panels_from_polygons()

    @property
    def peak_capacity_kw_out_per_kw_in_per_m2(self):
        """ The nominal output capacity of the system when there is 1kW/m2 of irradiance on the panel"""
        return self.number_of_panels * self.kwp_per_panel

    @property
    def generation(self):
        if self.peak_capacity_kw_out_per_kw_in_per_m2 > 0:
            profile_kwh = self.get_hourly_radiation_from_eu_api()
            profile_kwh.index = constants.BASE_YEAR_HOURLY_INDEX
        else:
            profile_kwh = pd.Series(index=constants.BASE_YEAR_HOURLY_INDEX, data=0)
        # set negative as generation not consumption
        profile_kwh_negative = profile_kwh * -1
        generation = Consumption(hourly_profile_kwh=profile_kwh_negative, fuel=constants.ELECTRICITY)
        return generation

    @cache
    def get_hourly_radiation_from_eu_api(self) -> pd.Series:
        """ Returns series of 8760 of average solar pv power for that hour in kW. Index 0 to 8759"""
        # API Documentation here: https://joint-research-centre.ec.europa.eu/
        #   pvgis-photovoltaic-geographical-information-system/getting-started-pvgis/api-non-interactive-service_en
        # Limit of 30 calls per second

        tool_name = 'seriescalc'
        api_url = f'https://re.jrc.ec.europa.eu/api/v5_2/{tool_name}'

        params = {'lat': self.latitude,
                  'lon': self.longitude,
                  'startyear': SolarConstants.API_YEAR,  # just take one year for now
                  'endyear': SolarConstants.API_YEAR,
                  'pvcalculation': 1,  # estimate hourly PV production
                  'peakpower': self.peak_capacity_kw_out_per_kw_in_per_m2,  # installed capacity
                  'mountingplace': "building",
                  'loss': SolarConstants.SYSTEM_LOSS,
                  'angle': self.pitch,
                  'aspect': self.orientation.azimuth_degrees,
                  'outputformat': "json"
                  }
        print("making api call")
        response = requests.get(api_url, params=params)

        if response.status_code == 200:
            dictr = response.json()
            df = pd.DataFrame(dictr['outputs']['hourly'])
            # can add timeseries as index later if needed
            pv_power_kw = df['P'] / 1000  # source data in W so convert to kW
            pv_power_kw.index = constants.BASE_YEAR_HOURLY_INDEX
        else:
            print(response.status_code)
            print(response.text)
            raise requests.ConnectionError

        return pv_power_kw
