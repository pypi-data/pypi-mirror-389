from .tikzcode import Tex
from .options import OptionsMixin
from itertools import product


class Label(Tex, OptionsMixin):
    """Class to represent an inline label"""

    def __init__(self, contents: str, **options):
        super().__init__(contents)
        self.init_options(**options)

    def get_code(self) -> str:
        return f"{{{self.options.format()}:{self.code}}}"

    def set_location(self, loc) -> str:
        topbot = ("", "above", "below")
        leftright = ("", "left", "right")
        allowed = [" ".join([vert, hor]).strip() for vert, hor in product(topbot, leftright)]

        if loc not in allowed:
            raise ValueError(f"Label location {loc} is not a valid position. Expected one of `{allowed}`.")
        self.set_option(loc, True)

    def contains_position_setting(self, options: dict) -> bool:
        positions = ("above", "below", "left", "right")
        return any((k.startswith(pos)) for k, pos in product(self._label_opts, positions))
