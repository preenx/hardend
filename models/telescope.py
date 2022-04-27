from __future__ import annotations

from typing import Any, Type, Optional
from threading import Thread
from socketio import Client
from time import sleep
from time import time
import numpy as np
import cv2
import os

interfaces = __import__('sys').modules['interfaces'] # import ..interfaces
models = __import__('sys').modules['models'] # import ..models
utils = __import__('sys').modules['utils'] # import ..utils

__all__ = [
    'BaseTelescope', 'MockTelescope',
    'RealTelescope', 'telescope_factory'
]


class BaseTelescope(interfaces.telescope.TelescopeInterface):

    def __init__(self,
            telescope_id: str,
            server: dict,
            camera: Type[models.camera.BaseCamera],
            mount: Type[models.mount.BaseMount],
            **kwargs: Optional[Any]
        ) -> None:
        self.telescope_id = telescope_id
        self.server = server
        self._frame = {'sent': None, 'last': None}
        self.camera = camera
        self.mount = mount
        self.hardware_thread = None
        self.load_constants(**kwargs)

    def _hardware_loop(self) -> None:
        while True:
            image = self.camera.capture_video_frame()
            coordinates = self.mount.get_coordinates()
            Thread(target=self._process_image, args=(
                image, coordinates
            ), daemon=True).start()

    def _start_video_capture(self) -> None:
        self.camera.start_video_capture()
        self.hardware_thread = Thread(target=self._hardware_loop, daemon=True)
        self.hardware_thread.start()

    def _stop_video_capture(self) -> None:
        self.camera.stop_video_capture()
        utils.kill_thread(thread=self.hardware_thread)
        self.hardware_thread = None

    def load_constants(self, **kwargs: Optional[Any]) -> None:
        self._path = os.path.join(os.path.expanduser("~"), "Desktop", "Uniscope_photos")
        width, height, quality = utils.get_kwargs_or_dotenv_values(
            variables=[
                'WEBP_IMAGE_WIDTH', 'WEBP_IMAGE_HEIGHT',
                'WEBP_IMAGE_QUALITY'
            ], kwargs=kwargs
        )
        self._webp_size = int(width), int(height)
        self._quality = [cv2.IMWRITE_WEBP_QUALITY, int(quality)]

    def _process_image(self, raw_image: np.ndarray, position: dict) -> None:
        resized_image = cv2.resize(raw_image, self._webp_size)
        _, buffer = cv2.imencode('.webp', resized_image, self._quality)
        final_image = buffer.tobytes()
        self._frame['last'] = {'data': final_image, 'position': position}


    def _get_photo_filename(self) -> None:
        filename = utils.random_hash() + '.png'
        return os.path.join(self._path, filename)

    def serve(self) -> None:
        self.sio.connect(
            self.server['path'],
            socketio_path=self.server['subpath'] + '/socket.io/',
            wait=False, auth={
            'clientType': 'hardend',
            'telescopeId': self.telescope_id
        })
        try:
            while True:
                sleep(10)
        except KeyboardInterrupt:
            self.sio.disconnect()
        except Exception as exception:
            self.sio.disconnect()
            raise exception


class InterfacedTelescopeMixin(BaseTelescope):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_socketio_hook()

    def _set_socketio_hook(self) -> None:
        self.sio = Client(handle_sigint=True)
        for name, method in utils.get_methods_by_class_instance(self):
            if name in interfaces.telescope.TelescopeInterface.__dict__:
                self.sio.on(name)(method)

    def connect(self) -> None:
        self._start_video_capture()

    def disconnect(self) -> None:
        self.stop_actions()

    def get_frame(self) -> dict:
        # FIXME: Create new event called 'initialize' # pylint: disable=fixme
        if not self.camera._running: # pylint: disable=protected-access
            self._start_video_capture()
        while self._frame['sent'] == self._frame['last']:
            sleep(0.1)
        self._frame['sent'] = self._frame['last']
        currnet_frame = dict(self._frame['sent'])
        currnet_frame['timestamps'] = {
            'hardend': int(time() * 1e3)
        }
        return currnet_frame

    def camera_settings_changed(self, data: dict) -> None:
        self.camera.update_paramerers(data)

    def mount_settings_changed(self, data: dict) -> None:
        self.mount.goto_coordinates(data)

    def start_slew(self, data: dict) -> None:
        self.mount.start_slew(data)

    def stop_slew(self) -> None:
        self.mount.stop_slew()

    def stop_actions(self) -> None:
        self.stop_slew()
        self._stop_video_capture()

    def take_photo(self) -> None:
        filename = self._get_photo_filename()
        self.camera.capture(filename)


class MockTelescope(InterfacedTelescopeMixin):

    def connect(self) -> None:
        print('[HARDEND] Connected')
        super().connect()

    def disconnect(self) -> None:
        print('[HARDEND] Disconnected')
        super().disconnect()

    def get_frame(self) -> dict:
        print('[HARDEND] Called `get_frame` method')
        return super().get_frame()

    def camera_settings_changed(self, data: dict) -> None:
        print('[HARDEND] Called `camera_settings_changed` method')
        super().camera_settings_changed(data)

    def mount_settings_changed(self, data: dict) -> None:
        print('[HARDEND] Called `mount_settings_changed` method')
        super().mount_settings_changed(data)

    def start_slew(self, data: dict) -> None:
        print('[HARDEND] Called `start_slew` method')
        super().start_slew(data)

    def stop_slew(self) -> None:
        print('[HARDEND] Called `stop_slew` method')
        super().stop_slew()

    def stop_actions(self) -> None:
        print('[HARDEND] Called `stop_actions` method')
        super().stop_actions()

    def take_photo(self) -> None:
        print('[HARDEND] Called `take_photo` method')
        super().take_photo()


class RealTelescope(InterfacedTelescopeMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        utils.create_folder_if_not_exist(self._path)


def telescope_factory(workmode: str, server: dict, **kwargs: Optional[Any]) -> Type[BaseTelescope]:
    telescope_id = utils.get_kwargs_or_dotenv_values('TELESCOPE_ID', kwargs=kwargs)
    camera =  models.camera.camera_factory(workmode=workmode)
    mount =  models.mount.mount_factory(workmode=workmode)
    if workmode == 'real':
        telescope = RealTelescope(
            telescope_id=telescope_id, server=server,
            camera=camera, mount=mount
        )
    elif workmode == 'mock':
        telescope = MockTelescope(
            telescope_id=telescope_id, server=server,
            camera=camera, mount=mount
        )
    else:
        raise ValueError(f'Workmode {workmode!r} is not defined')
    return telescope
