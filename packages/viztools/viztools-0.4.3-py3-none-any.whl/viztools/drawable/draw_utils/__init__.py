from typing import Tuple

import numpy as np


Color = np.ndarray | Tuple[int, int, int, int] | Tuple[int, int, int]


def normalize_color(color: Color) -> np.ndarray:
    if len(color) == 3:
        return np.array([*color, 255], dtype=np.float32)
    if len(color) != 4:
        raise ValueError(f'color must be of length 3 or 4, not {len(color)}.')
    return np.array(color, dtype=np.float32)
