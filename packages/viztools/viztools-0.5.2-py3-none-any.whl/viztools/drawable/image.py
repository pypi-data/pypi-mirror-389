from typing import Union, Optional

import numpy as np
import pygame as pg
from PIL import Image as PilImage

from viztools.coordinate_system import CoordinateSystem
from viztools.drawable import Drawable
from viztools.drawable.draw_utils import AnkerType


class Image(Drawable):
    def __init__(
            self, image: Union[np.ndarray, PilImage.Image], position: np.ndarray, size: Union[np.ndarray, float] = 0.01,
            anker_type: AnkerType = AnkerType.CENTER, offset: Optional[np.ndarray] = None,
            offset_color: Optional[np.ndarray] = None
    ):
        """
        Initializes a list of lines.

        :param image: Numpy array of shape [h, w, 3] or pillow image.
        :param position: The position of the image as numpy array of shape [2].
        :param size: The size of the image as numpy array of shape [2] or scale factor to original size.
        :param anker_type: The type of anker to use.
        :param offset: The offset of the image as numpy array of shape [2].
        :param offset_color: The color of the offset as numpy array of shape [3] or [4] (with alpha).
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
        self.offset = offset
        self.offset_color = offset_color

    def draw(self, screen: pg.Surface, coordinate_system: CoordinateSystem):
        anchor_point = coordinate_system.space_to_screen_t(self.position).flatten().astype(int)
        pos = self.position + self.offset if self.offset is not None else self.position
        screen_points = coordinate_system.space_to_screen_t(pos).flatten().astype(int)
        size = np.abs(coordinate_system.space_to_screen_t(self.size, translate=False).flatten().astype(int))
        if self.last_size is None or np.any(size != self.last_size):
            self.scaled_surface = pg.transform.scale(self.image_surface, size)
            self.last_size = size
        target_rect = self.anker_type.arrange_rect(self.scaled_surface.get_rect(), screen_points)

        if self.offset_color is not None:
            pg.draw.line(screen, self.offset_color, anchor_point, screen_points, 2)
        screen.blit(self.scaled_surface, target_rect)
