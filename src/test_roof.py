import streamlit as st
import math

import roof


def test_roof():
    polygons = roof.roof_mapper(800, 400)

    if polygons:
        print([p.dimensions for p in polygons])


def test_polygons():
    test_points = [[-6.526265, 58.072384],
                    [-6.523862, 58.072725],
                    [-6.52281, 58.071647],
                    [-6.525664, 58.071919],
                    [-6.526265, 58.072384]]
    polygon = roof.Polygon(test_points)
    assert math.sqrt(polygon.dimensions[1][0]**2 + polygon.dimensions[1][1]**2) == polygon.side_lengths[1]
    assert polygon.x_aligned_dimensions[0] == (0, 0)
    assert polygon.x_aligned_dimensions[1] == (0, 0)
    lengths_from_x_aligned_dimensions = [polygon.calculate_side_length(polygon.x_aligned_dimensions[i],
                                                                       polygon.x_aligned_dimensions[i+1])
                                         for i in range((len(polygon.x_aligned_dimensions) - 1))]


# test_roof()
test_polygons()
