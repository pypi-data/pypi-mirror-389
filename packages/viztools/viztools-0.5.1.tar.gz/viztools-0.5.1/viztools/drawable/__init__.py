from abc import ABC, abstractmethod

import pygame as pg

from viztools.coordinate_system import CoordinateSystem


class Drawable(ABC):
    @abstractmethod
    def draw(self, screen: pg.Surface, coordinate_system: CoordinateSystem):
        pass

    def update(self, screen: pg.Surface, coordinate_system: CoordinateSystem) -> bool:
        return False
