from __future__ import annotations
# pylint: disable=R0801
from abc import ABCMeta, abstractmethod
from typing import Type, Union
from threading import Thread
from socketio import Client

models = __import__('sys').modules['models'] # import ..models

__all__ = ['TelescopeInterface']


class TelescopeInterface(metaclass=ABCMeta):

    telescope_id: str
    server: dict
    _frame: dict
    camera: Type[models.camera.BaseCamera]
    mount: Type[models.mount.BaseMount]
    hardware_thread: Union[Thread, None]
    sio: Client

    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def disconnect(self) -> None:
        ...

    @abstractmethod
    def get_frame(self) -> None:
        ...

    @abstractmethod
    def camera_settings_changed(self, data: dict) -> None:
        ...

    @abstractmethod
    def mount_settings_changed(self, data: dict) -> None:
        ...

    @abstractmethod
    def start_slew(self, data: dict) -> None:
        ...

    @abstractmethod
    def stop_slew(self) -> None:
        ...

    @abstractmethod
    def stop_actions(self) -> None:
        ...

    @abstractmethod
    def take_photo(self) -> None:
        ...
