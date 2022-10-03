import streamlit as st
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


# test_roof()
test_polygons()
