from dataclasses import dataclass
import math
from typing import List, Tuple, Optional

import folium
import leafmap.foliumap as leafmap
import streamlit as st
from streamlit_folium import st_folium
import numpy as np

from constants import SolarConstants
from place_search import place_search

KM_TO_M = 1e3


def shoelace(x_y) -> float:
    """Calculate the area of an array of x,y points which form an arbitrary polygon"""

    """https://stackoverflow.com/questions/41077185/fastest-way-to-shoelace-formula"""
    x_y = np.array(x_y)
    x_y = x_y.reshape(-1, 2)

    x = x_y[:, 0]
    y = x_y[:, 1]

    s1 = np.sum(x * np.roll(y, -1))
    s2 = np.sum(y * np.roll(x, -1))

    area = 0.5 * np.absolute(s1 - s2)

    return area


@dataclass
class Polygon:
    _points: List[List[float]]

    @classmethod
    def make_zero_area_instance(cls):
        default_point = [SolarConstants.DEFAULT_LONG, SolarConstants.DEFAULT_LAT]
        _points = [default_point, default_point, default_point, default_point, default_point]
        return Polygon(_points)

    @property
    def points(self) -> List[Tuple[float]]:
        """map returns lng lat for some reason, rather than lat long - so switch around here"""
        return [(lat, lng) for (lng, lat) in self._points]

    @property
    def dimensions(self) -> List[Tuple[float]]:
        """Formats points as metres"""
        points_in_relative_lat_lng = self.convert_points_to_be_relative_to_first(self.points)
        points_in_relative_metres = [
            self.lat_lng_to_metres(start_lat_lng=self.points[0], lat_lng=p) for p in points_in_relative_lat_lng
        ]
        points_in_relative_metres = points_in_relative_metres[:-1]  # drop the 5th point which closes the shape
        return points_in_relative_metres

    @property
    def area(self) -> float:
        return shoelace(self.dimensions)

    @property
    def side_lengths(self):
        side_lengths = []
        for i in range(len(self.dimensions)):
            next_dimension = self.dimensions[i + 1] if i + 1 < len(self.dimensions) else self.dimensions[0]
            side_length = self.calculate_side_length(self.dimensions[i], next_dimension)
            side_lengths.append(side_length)
        side_lengths = [self.calculate_side_length(self.dimensions[i], self.dimensions[i + 1]) for i in
                        range(-1, (len(self.dimensions) - 1))]
        return side_lengths

    @property
    def average_plan_height(self):
        """ Assume polygon is rectangular and is wider that it is tall. 'plan' because doesn't account for pitch"""
        average_length_1 = (self.side_lengths[0] + self.side_lengths[2])/2
        average_length_2 = (self.side_lengths[1] + self.side_lengths[3])/2
        return min(average_length_1, average_length_2)

    @property
    def average_width(self):
        """ Assume polygon is rectangular and is wider that it is tall."""
        average_length_1 = (self.side_lengths[0] + self.side_lengths[2])/2
        average_length_2 = (self.side_lengths[1] + self.side_lengths[3])/2
        return max(average_length_1, average_length_2)

    @staticmethod
    def convert_points_to_be_relative_to_first(points: List[Tuple]):
        first = points.copy()[0]
        return [(p[0] - first[0], p[1] - first[1]) for p in points]

    @staticmethod
    def lat_lng_to_metres(start_lat_lng, lat_lng: Tuple) -> Tuple:
        """https://stackoverflow.com/questions/7477003/calculating-new-longitude-latitude-from-old-n-meters"""
        start_lat, _ = start_lat_lng

        lat, lng = lat_lng
        r_earth_in_km = 6378
        km_per_degree_lng = (math.pi / 180) * r_earth_in_km * np.cos(start_lat * math.pi / 180)  # Depend upon latitude
        km_per_degree_lat = 111  # constant

        return lat * km_per_degree_lat * KM_TO_M, lng * km_per_degree_lng * KM_TO_M

    def calculate_side_lengths(self, dimensions: List[Tuple[float]]) -> List[float]:
        side_lengths = []
        for i in range(len(dimensions)):
            next_dimension = dimensions[i + 1] if i + 1 < len(dimensions) else dimensions[0]
            side_length = self.calculate_side_length(dimensions[i], next_dimension)
            side_lengths.append(side_length)
        side_lengths = [self.calculate_side_length(dimensions[i], dimensions[i + 1]) for i in
                        range(-1, (len(dimensions) - 1))]
        return side_lengths

    @staticmethod
    def calculate_side_length(point_1: Tuple[float], point_2: Tuple[float]) -> float:
        (x1, y1) = point_1
        (x2, y2) = point_2
        length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return length


def roof_mapper(width: int, height: int) -> Optional[List[Polygon]]:
    """
    Render a map, returning co-ordinates of the most recently drawn shape
    """
    selected_location = place_search()

    map_styling = ".leaflet-draw-draw-polyline {" \
                  "display: none;" \
                  "}"
    st.markdown(f"<style><{map_styling}/style>", unsafe_allow_html=True)

    centre = [selected_location["lat"], selected_location["lng"]] if selected_location else [55, 0]

    st.write("""
        - Now use the tool with the ⭓ icon to draw the biggest rectangle that fits on your most south facing roof
            - Make sure you 'close' the rectangle by clicking back on the first point at the end
            - You can draw multiple rectangles if needed
        - Enter the orientation of the side of the roof you have drawn on
    """)

    m = leafmap.Map(google_map="SATELLITE", location=centre, zoom_start=21 if selected_location else 4,
                    measure_control=False,
                    search_control=False,
                    layers_control=False,
                    fullscreen_control=False)

    if selected_location:
        _ = folium.Marker(
            [selected_location["lat"], selected_location["lng"]], popup=selected_location["address"]
        ).add_to(m)

    map = st_folium(m, width=width, height=height)

    if map["all_drawings"]:  # map["all_drawings"] is none until somebody clicks
        polygons = []
        for drawing in map["all_drawings"]:
            drawing_type = drawing["geometry"]["type"]
            if not (drawing_type == "Polygon" or drawing_type == "Square"):
                raise KeyError(f"User selected the {drawing_type} tool")
            # coordinates is list of list of lists: e.g. [[[lng, lat], [lng, lat], [lng, lat], [lng, lat]]]
            polygon = Polygon(_points=drawing["geometry"]["coordinates"][0])
            polygons.append(polygon)

        return polygons
