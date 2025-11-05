from ..command import Command


class Connector(Command):

    def __init__(self, desc: str, **options):
        super().__init__(f" {desc} ", **options)
        self._endline = False
        self._escape = False
