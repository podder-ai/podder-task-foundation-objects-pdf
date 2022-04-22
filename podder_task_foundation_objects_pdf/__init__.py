__version__ = '0.1.0'

from typing import Type

from .pdf import PDF


def get_class() -> Type[PDF]:
    return PDF
