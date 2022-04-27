from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Tuple, Union

libs = __import__('sys').modules['libs'] # import ..models

__all__ = ['MountInterface']


class MountInterface(metaclass=ABCMeta):

    _mount: Union[libs.SynScanObject, None]

    @abstractmethod
    def get_coordinates(self) -> Tuple[str, str]:
        ...

    @abstractmethod
    def start_slew(self, data: dict) -> None:
        ...

    @abstractmethod
    def stop_slew(self) -> None:
        ...

    @abstractmethod
    def goto_coordinates(self, data: dict) -> None:
        ...
