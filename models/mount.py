from __future__ import annotations

from typing import Type, Tuple
from math import sin, cos
from time import time


interfaces = __import__('sys').modules['interfaces'] # import ..interfaces
utils = __import__('sys').modules['utils'] # import ..utils
libs = __import__('sys').modules['libs'] # import ..libs

__all__ = [
    'BaseMount', 'MockMount',
    'RealMount', 'mount_factory'
]

BaseMount = interfaces.mount.MountInterface


class MockMount(BaseMount):

    @staticmethod
    def start_slew(data: dict) -> None:
        print(
            '[MOUNT] Called `start_slew` method ' \
            'with args ' + utils.json_stringify(data)
        )

    @staticmethod
    def stop_slew() -> None:
        print('[MOUNT] Called `stop_slew` method')

    @staticmethod
    def _random_ra_dec() -> Tuple[float, float]:
        delta_t = time() * 0.00002
        return sin(delta_t) ** 2, cos(delta_t) ** 2

    def get_coordinates(self) -> Tuple[str, str]:
        print('[MOUNT] Called `get_coordinates` method')
        coordinates = self._random_ra_dec()
        return libs.synscan.SynScanFormatter.format_ra_dec(*coordinates)

    @staticmethod
    def goto_coordinates(data: dict) -> None:
        print(
            '[MOUNT] Called `goto_coordinates` method ' \
            'with args ' + utils.json_stringify(data)
        )


class RealMount(BaseMount):

    def __init__(self, com_port: str) -> None:
        self._mount = libs.synscan.SynScanObject(com_port)

    def start_slew(self, data: dict) -> None:
        assert data['speed'] in [-7, -2, 2, 7]
        if data['direction'] == 'RA':
            self._mount.slew_ra(data['speed'])
        else:
            self._mount.slew_dec(data['speed'])

    def stop_slew(self) -> None:
        self._mount.stop_slew()

    def get_coordinates(self) -> Tuple[str, str]:
        numeric_ra, numeric_dec = self._mount.get_ra_dec()
        return self._mount.format_ra_dec(numeric_ra, numeric_dec)

    def goto_coordinates(self, data: dict) -> None:
        ra, dec = self._mount.parse_ra_dec(data['ra'], data['dec'])
        self._mount.goto_ra_dec(ra, dec)



def mount_factory(workmode: str) -> Type[BaseMount]:
    if workmode == 'real':
        ports = libs.synscan.SynScanObject.get_avalable_ports()
        if len(ports) == 0:
            raise SystemError('No telescope found')
        if len(ports) == 1:
            mount = ports[0]
        else:
            mount = libs.pynquirer.select('selct port', ports)
        mount = RealMount(com_port=mount)
    elif workmode == 'mock':
        mount = MockMount()
    else:
        raise ValueError(f'Workmode {workmode!r} is not defined')
    return mount
