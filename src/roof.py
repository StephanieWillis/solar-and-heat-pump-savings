from dataclasses import dataclass
from typing import List, Tuple, Optional

import folium
import leafmap.foliumap as leafmap
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium
import numpy as np
from place_search import place_search


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
    points: List[Tuple]

    @property
    def area(self):
        return shoelace(self.points)


DEFAULT_LOCATION = dict(lat=0, lng=0, address="")


def roof_mapper(width: int, height: int) -> Optional[List[Polygon]]:
    """
    Render a map, returning co-ordinates of any shapes drawn upon the map
    """

    selected_location = place_search(my_input_value="yeehaa")

    centre = [selected_location["lat"], selected_location["lng"]] if selected_location else [50, 0]
    m = leafmap.Map(google_map="SATELLITE", location=centre,
                    zoom_start=22 if selected_location else 2)
    if selected_location:
        marker = folium.Marker(
            [selected_location["lat"], selected_location["lng"]], popup=selected_location["address"]
        ).add_to(m)

    map = st_folium(m, width=width, height=height)
    st.write(map)
    if map["all_drawings"]:
        return [Polygon(points=drawing["geometry"]["coordinates"]) for drawing in map["all_drawings"]]
