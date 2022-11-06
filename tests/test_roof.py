import math

from .context import src
from src import roof


def test_polygon_calculate_side_lengths():
    assert roof.Polygon.calculate_side_length([0, 0], [0, 0]) == 0
    assert roof.Polygon.calculate_side_length([-2.31, 4.5], [-2.31, 4.5]) == 0
    assert roof.Polygon.calculate_side_length([-2.31, 4.5], [-2.31, 5.5]) == 1

    test_points = [[-6.526265, 58.072384],
                   [-6.523862, 58.072725],
                   [-6.52281, 58.071647],
                   [-6.525664, 58.071919],
                   [-6.526265, 58.072384]]
    polygon = roof.Polygon(test_points)
    assert math.sqrt(polygon.dimensions[1][0] ** 2 + polygon.dimensions[1][1] ** 2) == polygon.side_lengths[1]


def test_polygon_brockwell_lido_average_height_and_width():

    brockwell_lido_points = [(-0.106671, 51.453278),
                             (-0.106848, 51.453054),
                             (-0.106194, 51.452852),
                             (-0.106014, 51.453074),
                             (-0.106671, 51.453278)]
    lido_polygon = roof.Polygon(brockwell_lido_points)

    assert lido_polygon.average_plan_height == 27.67757085605215  # code defines 'height' as smaller of the two dims
    assert lido_polygon.average_width == 50.747397116375595


def test_make_zero_area_instance():
    no_area = roof.Polygon.make_zero_area_instance()
    assert no_area.area == 0
    assert no_area.average_width == 0
    assert no_area.average_plan_height == 0