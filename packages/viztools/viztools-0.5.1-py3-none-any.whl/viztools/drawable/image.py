from typing import Union

import numpy as np
import pygame as pg
from PIL import Image as PilImage

from viztools.coordinate_system import CoordinateSystem
from viztools.drawable import Drawable
from viztools.drawable.draw_utils import AnkerType


class Image(Drawable):
    def __init__(
            self, image: Union[np.ndarray, PilImage.Image], position: np.ndarray, size: Union[np.ndarray, float] = 0.01,
            anker_type: AnkerType = AnkerType.CENTER
    ):
        """
        Initializes a list of lines.

        :param image: Numpy array of shape [h, w, 3] or pillow image.
        :param position: The position of the image as numpy array of shape [2].
        :param size: The size of the image as numpy array of shape [2] or scale factor to original size.
        """
        if isinstance(image, PilImage.Image):
            image = np.array(image)
        self.image: np.ndarray = image.swapaxes(0, 1)
        self.image_surface = pg.surfarray.make_surface(self.image)
        self.position = position
        self.anker_type = anker_type
        if isinstance(size, float):
            size = np.array(self.image.shape[:2]) * size
        self.size = size
        self.last_size = None
        self.scaled_surface = None

    def draw(self, screen: pg.Surface, coordinate_system: CoordinateSystem):
        screen_points = coordinate_system.space_to_screen_t(self.position).flatten().astype(int)
        size = np.abs(coordinate_system.space_to_screen_t(self.size, translate=False).flatten().astype(int))
        if self.last_size is None or np.any(size != self.last_size):
            self.scaled_surface = pg.transform.scale(self.image_surface, size)
            self.last_size = size
        target_rect = self.anker_type.arrange_rect(self.scaled_surface.get_rect(), screen_points)
        screen.blit(self.scaled_surface, target_rect)
