from dataclasses import dataclass
from math import pi
from typing import List, Tuple, Optional

import folium
import leafmap.foliumap as leafmap
import streamlit as st
from streamlit_folium import st_folium
import numpy as np
from place_search import place_search

KM_TO_M = 1e3


def shoelace(x_y):
    """https://stackoverflow.com/questions/41077185/fastest-way-to-shoelace-formula"""
    x_y = np.array(x_y)
    x_y = x_y.reshape(-1, 2)

    x = x_y[:, 0]
    y = x_y[:, 1]

    S1 = np.sum(x * np.roll(y, -1))
    S2 = np.sum(y * np.roll(x, -1))

    area = 0.5 * np.absolute(S1 - S2)

    return area


@dataclass
class Polygon:
    _points: List[Tuple[float]]


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

        return points_in_relative_metres

    @property
    def area(self) -> float:
        return shoelace(self.points)

    @property
    def largest_rectangle(self):
        if len(self.dimensions) !=5:
            raise ValueError("Only able to deal with 4 sided shapes for now - please redraw")


    @staticmethod
    def convert_points_to_be_relative_to_first(points: List[Tuple]):
        first = points.copy().pop()
        return [(p[0] - first[0], p[1] - first[1]) for p in points]

    @staticmethod
    def lat_lng_to_metres(start_lat_lng, lat_lng: Tuple) -> Tuple:
        """https://stackoverflow.com/questions/7477003/calculating-new-longitude-latitude-from-old-n-meters"""
        start_lat, _ = start_lat_lng
        st.write(start_lat_lng)
        lat, lng = lat_lng
        r_earth_in_km = 6378
        km_per_degree_lng = (pi / 180) * r_earth_in_km * np.cos(start_lat * pi / 180)  # Depend upon latitude
        km_per_degree_lat = 111  # constant

        return lat * km_per_degree_lat * KM_TO_M, lng * km_per_degree_lng * KM_TO_M


def roof_mapper(width: int, height: int) -> Optional[List[Polygon]]:
    """
    Render a map, returning co-ordinates of any shapes drawn upon the map
    """

    selected_location = place_search()

    centre = [selected_location["lat"], selected_location["lng"]] if selected_location else [55, 0]
    m = leafmap.Map(google_map="SATELLITE", location=centre, zoom_start=21 if selected_location else 4)
    if selected_location:
        _ = folium.Marker(
            [selected_location["lat"], selected_location["lng"]], popup=selected_location["address"]
        ).add_to(m)
    # also return selected_location['lat'] and selected_location['lng']
    map = st_folium(m, width=width, height=height)
    # st.write(map)
    if map["all_drawings"]:  # map["all_drawings"] is none until somebody clicks
        # Figure out if actually possible to produce more than one drawing
        polygons = []
        for drawing in map['all_drawings']:
            drawing_type = drawing['geometry']['type']
            if not(drawing_type == 'Polygon'):
                raise KeyError(f"User selected the {drawing_type} tool")
            # coordinates is list of list of lists: e.g. [[[lng, lat], [lng, lat], [lng, lat], [lng, lat]]]
            polygon = Polygon(_points=drawing["geometry"]["coordinates"][0])
            polygons.append(polygon)
        return polygons
