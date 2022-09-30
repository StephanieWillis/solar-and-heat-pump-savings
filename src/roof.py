from dataclasses import dataclass
from typing import List, Tuple

import leafmap.foliumap as leafmap
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium
import numpy as np

m = leafmap.Map(google_map="SATELLITE")


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


def roof_mapper(width: int, height: int) -> List[Polygon]:
    """
    Render a map, returning co-ordinates of any shapes drawn upon the map
    """

    map = st_folium(m, width=width, height=height)
    st.write(map)

    return [Polygon(points=drawing['geometry']['coordinates']) for drawing in map['all_drawings']]
