from .tikzcode import Tex
from .options import OptionsMixin
from .formatting import format_options


class Style(Tex, OptionsMixin):

    def __init__(self, name: str, **options):
        self.name = name
        self.init_options(**options)

    def get_code(self) -> str:
        return f"{self.name}/.style={{ {format_options(with_brackets=False, **self.options)} }}"
