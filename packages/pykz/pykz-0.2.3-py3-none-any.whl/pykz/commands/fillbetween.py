from ..command import Command


class FillBetween(Command):

    def __init__(self, name1: str,
                 name2: str,
                 **options,
                 ):
        self.curve_name1 = name1
        self.curve_name2 = name2
        super().__init__("addplot", **options)

    # def customize_label(self, **options):
    #     """Customize the options of the inline label"""
    #     self._label_opts.set_options(**options)

    def get_code(self) -> str:
        result = f"\\addplot{self._options.format()} fill between[\n"
        result += f"of = {self.curve_name1} and {self.curve_name2},\n"
        result += "];\n"
        return result
