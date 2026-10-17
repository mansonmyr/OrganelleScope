"""Linear black-to-colour display LUTs; never used by measurement functions."""
import numpy as np
from organelle_scope.image_io import ImageError
LUTS = {
    'rose': (1., .12, .25), 'mint': (.1, 1., .65), 'ocean': (.2, .45, 1.), 'silver': (.8, .8, .8),
    'red': (1., 0., 0.), 'green': (0., 1., 0.), 'blue': (0., 0., 1.),
    'cyan': (0., 1., 1.), 'magenta': (1., 0., 1.), 'yellow': (1., 1., 0.),
    'gray': (1., 1., 1.), 'orange': (1., .49, 0.),
}
DEFAULTS = ('rose', 'mint', 'ocean', 'silver')
def display_colors(luts: str | None, count: int) -> np.ndarray:
    names = DEFAULTS[:count] if luts is None else luts.split(',')
    if len(names) != count or any(n not in LUTS for n in names):
        raise ImageError('Choose one supported display LUT per source channel. LUTs change display only.')
    return np.asarray([LUTS[n] for n in names], dtype=np.float32)
