import enum
from typing import Tuple, Union

import pygame as pg
import numpy as np


Color = Union[np.ndarray, Tuple[int, int, int, int], Tuple[int, int, int]]


def normalize_color(color: Color) -> np.ndarray:
    if len(color) == 3:
        return np.array([*color, 255], dtype=np.float32)
    if len(color) != 4:
        raise ValueError(f'color must be of length 3 or 4, not {len(color)}.')
    return np.array(color, dtype=np.float32)


class AnkerType(enum.StrEnum):
    CENTER = 'center'
    LEFT = 'left'
    RIGHT = 'right'
    TOP = 'top'
    BOTTOM = 'bottom'
    TOP_LEFT = 'top_left'
    TOP_RIGHT = 'top_right'
    BOTTOM_LEFT = 'bottom_left'
    BOTTOM_RIGHT = 'bottom_right'
    
    def arrange_rect(self, rect: pg.Rect, position: Union[np.ndarray, Tuple[int, int]]) -> pg.Rect:
        new_rect = rect.copy()

        if self == AnkerType.CENTER:
            new_rect.center = position
        elif self == AnkerType.LEFT:
            new_rect.midleft = position
        elif self == AnkerType.RIGHT:
            new_rect.midright = position
        elif self == AnkerType.TOP:
            new_rect.midtop = position
        elif self == AnkerType.BOTTOM:
            new_rect.midbottom = position
        elif self == AnkerType.TOP_LEFT:
            new_rect.topleft = position
        elif self == AnkerType.TOP_RIGHT:
            new_rect.topright = position
        elif self == AnkerType.BOTTOM_LEFT:
            new_rect.bottomleft = position
        elif self == AnkerType.BOTTOM_RIGHT:
            new_rect.bottomright = position
        else:
            raise ValueError(f'unknown anker type: {self}')

        return new_rect
