from itertools import pairwise

import numpy as np
import pygame as pg

from viztools.coordinate_system import CoordinateSystem
from viztools.drawable import Drawable


class Lines(Drawable):
    def __init__(self, points: np.ndarray, color: np.ndarray = None):
        """
        Initializes a list of lines.

        :param points: Numpy array of shape [N, 2] where N is the number of points.
        :param color: The color of the lines as numpy array of shape [3] or [4] (with alpha).
        """
        self.points = points
        self.color = color

    def draw(self, screen: pg.Surface, coordinate_system: CoordinateSystem):
        screen_points = coordinate_system.space_to_screen_t(self.points)
        for p1, p2 in pairwise(screen_points):
            pg.draw.line(screen, self.color, p1, p2)
