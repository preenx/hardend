from __future__ import annotations

from requests import get as http_get
from typing import Type
from time import sleep
from io import BytesIO
from PIL import Image
import numpy as np
import zwoasi
import cv2

interfaces = __import__('sys').modules['interfaces'] # import ..interfaces
utils = __import__('sys').modules['utils'] # import ..utils
libs = __import__('sys').modules['libs'] # import ..libs

__all__ = [
    'BaseCamera', 'MockCamera',
    'RealCamera', 'camera_factory'
]


class BaseCamera(interfaces.camera.CameraInterface):

    def __init__(self) -> None:
        self._changed = False
        self._running = False
        self._camera = None

    def _update_paramerers(self) -> None:
        self._changed = True

    def capture_video_frame(self) -> None:
        while not self._running:
            sleep(0.1)

    def start_video_capture(self) -> None:
        while not self._changed:
            sleep(0.1)
        self._start_video_capture()
        self._running = True

    def stop_video_capture(self) -> None:
        self._running = False

    def capture(self, filename: str) -> None:
        self.stop_video_capture()
        self._capture(self, filename)
        self.start_video_capture()


class MockCamera(BaseCamera):

    def __init__(self):
        super().__init__()
        self._mock_delay = 0

    @staticmethod
    def _get_random_image() -> np.ndarray:
        width, height = utils.get_kwargs_or_dotenv_values(
            variables=['WEBP_IMAGE_WIDTH', 'WEBP_IMAGE_HEIGHT']
        )
        raw = http_get(f'https://picsum.photos/{width}/{height}').content
        image = cv2.cvtColor(np.array(Image.open(BytesIO(raw))), cv2.COLOR_BGR2RGB)
        return image

    def capture_video_frame(self) -> np.ndarray:
        print('[CAMERA] Called `capture_video_frame` method')
        super().capture_video_frame()
        sleep(self._mock_delay)
        return self._get_random_image()

    @staticmethod
    def _start_video_capture() -> None:
        print('[CAMERA] Called `start_video_capture` method')

    def stop_video_capture(self) -> None:
        print('[CAMERA] Called `stop_video_capture` method')
        super().stop_video_capture()

    def update_paramerers(self, parameters: dict) -> None:
        print(
            '[CAMERA] Called `update_paramerers` method ' \
            'with args ' + utils.json_stringify(parameters)
        )
        self._mock_delay = parameters['exposition'] * 0.000001
        super()._update_paramerers()

    def _capture(self, filename: str) -> None:
        print(
            '[CAMERA] Called `capture` method ' \
            'with args ' + utils.json_stringify(filename)
        )
        sleep(self._mock_delay)


class RealCamera(BaseCamera):

    def __init__(self, camera_id: int) -> None:
        super().__init__()
        self._camera = zwoasi.Camera(camera_id)

    def capture_video_frame(self) -> np.ndarray:
        super().capture_video_frame()
        return self._camera.capture_video_frame()

    def _start_video_capture(self) -> None:
        self._camera.start_video_capture()

    def stop_video_capture(self) -> None:
        self._camera.start_video_capture()
        super().start_video_capture()

    def update_paramerers(self, data: dict) -> None:
        self._camera.set_control_value(zwoasi.ASI_BRIGHTNESS, data['brightness'])
        self._camera.set_control_value(zwoasi.ASI_EXPOSURE, data['exposition'])
        self._camera.set_control_value(zwoasi.ASI_GAMMA, data['gamma'])
        self._camera.set_control_value(zwoasi.ASI_GAIN, data['gain'])
        self._camera.set_control_value(zwoasi.ASI_WB_B, data['wb_B'])
        self._camera.set_control_value(zwoasi.ASI_WB_R, data['wb_R'])
        flip = 2 * int(data['flip_x']) + int(data['flip_y'])
        self._camera.set_control_value(zwoasi.ASI_FLIP, flip)
        color_format = {
            'RGB24': zwoasi.ASI_IMG_RGB24,
            'RAW8': zwoasi.ASI_IMG_RAW8,
            'RAW16': zwoasi.ASI_IMG_RAW16,
            'Y8': zwoasi.ASI_IMG_Y8
        }[data['colorFormat']]
        self._camera.set_image_type(color_format)
        super()._update_paramerers()

    def _capture(self, filename: str) -> None:
        self._camera.capture(filename=filename)


def camera_factory(workmode: str) -> Type[BaseCamera]:
    if workmode == 'real':
        utils.init_zwoasi_drivers()
        cameras = zwoasi.list_cameras()
        if len(cameras) == 0:
            raise SystemError('No camera found')
        if len(cameras) == 1:
            camera_id = cameras[0]
        else:
            camera_id = libs.pynquirer.select('selct camera', cameras)
        camera = RealCamera(camera_id=camera_id)
    elif workmode == 'mock':
        camera = MockCamera()
    else:
        raise ValueError(f'Workmode {workmode!r} is not defined')
    return camera
