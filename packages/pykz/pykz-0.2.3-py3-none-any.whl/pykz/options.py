from collections.abc import Mapping
from collections import OrderedDict


class Options(Mapping):

    def __init__(self, **options):
        self._opt_dict = OrderedDict(**{key.replace("_", " "): value
                                        for (key, value) in options.items()
                                        if value is not None})

    def format(self, include_brackets: bool = True) -> str:
        from .formatting import format_options
        return format_options(with_brackets=include_brackets, **self._opt_dict)

    def set_option(self, name: str, value: str):
        self._opt_dict[name.replace("_", " ")] = value

    def set_options(self, **options):
        for k, v in options.items():
            self.set_option(k, v)

    # Dict-like methods

    def __getitem__(self, key):
        return self._opt_dict[key]

    def __setitem__(self, key, value):
        self._opt_dict[key] = value

    def __delitem__(self, key):
        del self._opt_dict[key]

    def __iter__(self):
        return iter(self._opt_dict)

    def __len__(self):
        return len(self._opt_dict)

    def __dict__(self):
        return self._opt_dict


class OptionsMixin:

    @property
    def options(self) -> Options:
        return self._options

    def init_options(self, **options):
        self._options = Options(**options)

    def set_option(self, key: str, value: str):
        self._options.set_option(key, value)

    def set_options(self, **options):
        self._options.set_options(**options)

    def update_option(self, name: str, inner_key: str, value: str):
        suboption = self.options.get(name, Options())
        if not isinstance(suboption, Options):
            raise TypeError(f"Cannot update sub-options. Option {suboption} is a string.")
        suboption.set_option(inner_key, value)
        self.options[name] = suboption
