from dataclasses import dataclass
import math
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
        points_in_relative_metres = points_in_relative_metres[:-1]  # drop the 5th point which closes the shape
        return points_in_relative_metres

    @property
    def side_lengths(self):
        side_lengths = self.calculate_side_lengths(self.dimensions)
        return side_lengths

    @property
    def x_aligned_dimensions(self) -> List[Tuple[float]]:
        """ Rotate dimensions so the longest side is along the horizontal (x--x)"""
        # Identify longest side and put first
        # TODO: something isn't working here - not ordering as I'd expect
        longest_side_idx = self.side_lengths.index(max(self.side_lengths))
        points_longest_first = list(np.roll(self.dimensions, 1-longest_side_idx, axis=0))
        points_longest_first = [array.tolist() for array in points_longest_first]
        # recalculate lengths to check
        side_lengths = self.calculate_side_lengths(points_longest_first)
        assert set(side_lengths) == set(self.side_lengths)
        assert side_lengths.index(max(side_lengths)) == 0

        # shift so stars at origin with new order
        points_longest_starting_at_origin = self.convert_points_to_be_relative_to_first(points_longest_first)
        side_lengths = self.calculate_side_lengths(points_longest_starting_at_origin)
        assert set(side_lengths) == set(self.side_lengths)
        assert side_lengths.index(max(side_lengths)) == 0
        assert points_longest_starting_at_origin[0] == (0, 0)

        # rotate so first side is along x axis
        angle = self.calculate_angle_to_rotate_point_to_horizontal(points_longest_starting_at_origin[1])
        x_aligned_dimensions = [self.rotate_point_by_angle(point, angle) for point in points_longest_starting_at_origin]
        side_lengths = self.calculate_side_lengths(x_aligned_dimensions)
        assert set(side_lengths) == set(self.side_lengths)
        assert side_lengths.index(max(side_lengths)) == 0
        assert x_aligned_dimensions[0] == (0, 0)
        assert x_aligned_dimensions[1] == (max(self.side_lengths),0)
        return x_aligned_dimensions

    @property
    def area(self) -> float:
        return shoelace(self.points)

    @staticmethod
    def convert_points_to_be_relative_to_first(points: List[Tuple]):
        first = points.copy()[0]
        return [(p[0] - first[0], p[1] - first[1]) for p in points]

    @staticmethod
    def lat_lng_to_metres(start_lat_lng, lat_lng: Tuple) -> Tuple:
        """https://stackoverflow.com/questions/7477003/calculating-new-longitude-latitude-from-old-n-meters"""
        start_lat, _ = start_lat_lng
        st.write(start_lat_lng)
        lat, lng = lat_lng
        r_earth_in_km = 6378
        km_per_degree_lng = (math.pi / 180) * r_earth_in_km * np.cos(start_lat * math.pi / 180)  # Depend upon latitude
        km_per_degree_lat = 111  # constant

        return lat * km_per_degree_lat * KM_TO_M, lng * km_per_degree_lng * KM_TO_M

    def calculate_side_lengths(self, dimensions: List[Tuple[float]]) -> List[float]:
        side_lengths = []
        for i in range(len(dimensions)):
            next_dimension = dimensions[i+1] if i+1 < len(dimensions) else dimensions[0]
            side_length = self.calculate_side_length(dimensions[i], next_dimension)
            side_lengths.append(side_length)
        side_lengths = [self.calculate_side_length(dimensions[i], dimensions[i+1]) for i in range(-1, (len(dimensions) - 1))]
        return side_lengths

    @staticmethod
    def calculate_side_length(point_1: Tuple[float], point_2) -> float:
        (x1, y1) = point_1
        (x2, y2) = point_2
        length = math.sqrt((x2-x1) ** 2 + (y2-y1) ** 2)
        return length

    @staticmethod
    def calculate_angle_to_rotate_point_to_horizontal(point: Tuple[float]) -> float:
        """ Calculate angle of rotation (anticlockwise in radians) needed to get a point onto the x axis """
        (x, y) = point
        return - math.atan(y / x)

    @staticmethod
    def rotate_point_by_angle(point: Tuple[float], angle: float) -> Tuple[float]:
        """ Rotates a point by angle in radians around the origin in an anticlockwise direction """
        # https://stackoverflow.com/questions/14842090/rotate-line-around-center-point-given-two-vertices/14842362#14842362
        (x1, y1) = point
        x2 = x1 * math.cos(angle) - y1 * math.sin(angle)
        y2 = x1 * math.sin(angle) + y1 * math.cos(angle)
        print(x1,y1)
        print(x2, y2)
        return x2, y2





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
