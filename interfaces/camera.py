from __future__ import annotations

from abc import ABCMeta, abstractmethod
from zwoasi import Camera
from typing import Union
import numpy as np

__all__ = ['CameraInterface']


class CameraInterface(metaclass=ABCMeta):

    _changed: bool
    _running: bool
    _camera: Union[Camera, None]

    @abstractmethod
    def capture_video_frame(self) -> np.ndarray:
        ...

    @abstractmethod
    def start_video_capture(self) -> None:
        ...

    @abstractmethod
    def stop_video_capture(self) -> None:
        ...

    @abstractmethod
    def update_paramerers(self, parameters: dict) -> None:
        ...

    @abstractmethod
    def _capture(self, filename: str) -> None:
        ...
