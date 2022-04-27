from __future__ import annotations

from serial.tools.list_ports import comports as _avalable_ports
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Tuple, List
from threading import Thread, main_thread
from itertools import groupby
from serial import Serial
from time import sleep
from enum import Enum

utils = __import__('sys').modules['utils'] # import ..utils


__all__ = [
    'TrackMode', 'SynScanGetter', 'SynScanObject',
    'SynScanNotAvailableError', 'SynScanExecutor',
    'SynScanCommander', 'SynScanFormatter',
    # 'SynScanDEPRECATED'
]


class TrackMode(Enum):
    OFF = 0
    ALT_AZ = 1
    EQATORIAL = 2
    PEC = 3

def _reveal_digits(string: str) -> List[int]:
    return [int(''.join(x[1])) for x in groupby(string, key=str.isdigit) if x[0]]

class SynScanNotAvailableError(TimeoutError):
    ...

class SynScanExecutor:

    def __init__(self,
            port: str, baudrate: Optional[int] = 9600,
            timeout: Optional[Union[int, float]] = 0.01
        ) -> None:
        self.port = port
        self.timeout = timeout
        self.commands = {}
        self.cid = 0
        Thread(target=self.command_loop, daemon=True).start()
        self.serial_tunnel = Serial(self.port, baudrate=baudrate, timeout=self.timeout)

    def command_loop(self) -> None:
        try:
            while True:
                if self.commands:
                    for cid in sorted(self.commands):
                        try:
                            if not self.commands[cid]['done']:
                                min_cid = cid
                                break
                        except KeyError:
                            pass
                    else:
                        continue
                    command = self.commands[min_cid]['command'].encode() + b'\r'
                    result = self._execute(command)
                    self.commands[min_cid]['result'] = result
                    self.commands[min_cid]['done'] = True
                else:
                    sleep(self.timeout)
        except: #pylint: disable=bare-except
            self._stop_all_hardend()

    @staticmethod
    def _stop_all_hardend() -> None:
        utils.kill_thread(
            thread=main_thread(),
            exception=SynScanNotAvailableError
            )
        raise SynScanNotAvailableError

    def _execute(self, command: bytes) -> bytes:
        self.serial_tunnel.write(command)
        return self.serial_tunnel.read_until('#')

    def execute(self, command: str) -> str:
        self.cid += 1
        current_cid = self.cid
        self.commands[current_cid] = {'command': command, 'done': False}
        while not self.commands[current_cid]['done']:
            sleep(self.timeout)
        result = self.commands[current_cid]['result']
        del self.commands[current_cid]
        return result.decode()[:-1]

    def _echo(self, message: str) -> str:
        return self.execute('K' + message)


class SynScanFormatter:

    @staticmethod
    def _decode_coordinate(coordinate: str) -> Tuple[float, float]:
        if len(coordinate) == 9:
            return tuple(int(coord, base=16) / 65536 for coord in coordinate.split(','))
        if len(coordinate) == 17:
            return tuple(int(coord[:-2], base=16) / 16777216 for coord in coordinate.split(','))
        raise ValueError(f"Invalid coordinate length: {len(coordinate)}")

    @staticmethod
    def _encode_coordinate(coordinate: Tuple[float, float], precise: bool) -> str:
        if precise:
            return ','.join(hex(int(coord * 16777216))[2:].upper() + '00' for coord in coordinate)
        return ','.join(hex(int(coord * 65536))[2:].upper() for coord in coordinate)

    @staticmethod
    def _format_clock(value: float) -> str:
        _hours = value * 24
        hours = int(_hours)
        _minutes = 60 * (_hours - hours)
        minutes = int(_minutes)
        _seconds = 60 * (_minutes - minutes)
        seconds = round(_seconds)
        return f'{hours}h {minutes}m {seconds}s'

    @staticmethod
    def _format_degrees(value: float) -> str:
        _deg = value * 360
        deg = int(_deg)
        _minutes = 60 * (_deg - deg)
        minutes = int(_minutes)
        _seconds = 60 * (_minutes - minutes)
        seconds = int(_seconds)
        return f'{deg}° {minutes}’ {seconds}”'

    @staticmethod
    def _from_degrees(value: Tuple[float, float, float]) -> float:
        return ((value[2] / 60 + value[1]) / 60 + value[0]) / 360

    @staticmethod
    def _from_clock(value: Tuple[float, float, float]) -> float:
        return ((value[2] / 60 + value[1]) / 60 + value[0]) / 24

    @classmethod
    def format_ra_dec(cls, ra: float, dec: float) -> Tuple[str, str]:
        return cls._format_clock(ra), cls._format_degrees(dec)

    @classmethod
    def format_azm_alt(cls, azm: float, alt: float) -> Tuple[str, str]:
        return cls._format_degrees(azm), cls._format_degrees(alt)

    @staticmethod
    def format_datetime(time: List[int]) -> str:
        if time[6] < 128:
            currnet_timezone = timedelta(hours=time[6])
        else:
            currnet_timezone = timedelta(hours=time[6] - 256)

        current_datetime = datetime(
            year=2000+time[5], month=time[3], day=time[4],
            hour=time[0], minute=time[1], second=time[2],
            tzinfo=timezone(currnet_timezone), fold=time[7]
        )
        return f'{current_datetime :%I:%M:%S%p %B %d, %Y %Z}'

    @staticmethod
    def format_version(version: List[int]) -> str:
        return f'{version[0]}{version[1]}.{version[2]}{version[3]}.{version[4]}{version[5]}'

    @staticmethod
    def format_location(location: List[int]) -> str:
        longitude = 'WE'[location[3]]
        latitude = 'SN'[location[7]]
        return f'{location[4]}°{location[5]}’{location[6]}” {longitude}, ' \
            f'{location[0]}°{location[1]}’{location[2]}” {latitude}'


class SynScanGetter(SynScanExecutor, SynScanFormatter):

    models = {
        0: 'EQ6 GOTO Series',
        1: 'HEQ5 GOTO Series',
        2: 'EQ5 GOTO Series',
        3: 'EQ3 GOTO Series',
        4: 'EQ8 GOTO Series',
        5: 'AZ-EQ6 GOTO Series',
        6: 'AZ-EQ5 GOTO Series',
        160: 'AllView GOTO Series'
    }
    models.update({id: 'AZ GOTO Series' for id in range(128, 144)})
    models.update({id: 'DOB GOTO Series' for id in range(144, 160)})

    def get_ra_dec(self, precise: Optional[bool] = True) -> Tuple[float, float]:
        coordinate = self.execute('e' if precise else 'E')
        return self._decode_coordinate(coordinate)

    def get_azm_alt(self, precise: Optional[bool] = True) -> Tuple[float, float]:
        coordinate = self.execute('z' if precise else 'Z')
        return self._decode_coordinate(coordinate)

    def get_tracking(self) -> TrackMode:
        track_mode = ord(self.execute('t'))
        return TrackMode(track_mode)

    def get_location(self) -> List[int]:
        location = list(map(ord, self.execute('w')))
        return location

    def get_version(self) -> str:
        version = map(lambda x: int(x, base=16), self.execute('V'))
        return self.format_version(version)

    def get_model(self) -> str:
        return self.models[ord(self.execute('m'))]

    def get_datetime(self) -> List[int]:
        time = list(map(ord, self.execute('h')))
        return self.format_datetime(time)

    def get_mount_state(self) -> str:
        return self.execute('p')


class SynScanCommander(SynScanExecutor, SynScanFormatter):

    def slew_positive_ra(self, speed: int) -> str:
        return self.execute(f'P\x02\x10${speed:c}\x00\x00\x00')

    def slew_negative_ra(self, speed: int) -> str:
        return self.execute(f'P\x02\x10%{speed:c}\x00\x00\x00')

    def slew_positive_dec(self, speed: int) -> str:
        return self.execute(f'P\x02\x11${speed:c}\x00\x00\x00')

    def slew_negative_dec(self, speed: int) -> str:
        return self.execute(f'P\x02\x11%{speed:c}\x00\x00\x00')

    def is_alignment_complete(self) -> bool:
        return self.execute('J') == '\x01'

    def is_goto_in_progress(self) -> bool:
        return self.execute('J') == '1'

    def cancel_goto(self) -> str:
        return self.execute('M')

    def goto_ra_dec(self, ra: float, dec: float, precise: Optional[bool] = True) -> str:
        coordinate = self._encode_coordinate((ra, dec), precise=precise)
        return self.execute(('r' if precise else 'R') + coordinate)


class SynScanObject(SynScanCommander, SynScanGetter):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        Thread(target=self._ping_pong_loop).start()

    def _ping_pong_loop(self,
            timeout: Optional[Union[int, float]] = 1,
            delay: Optional[Union[int, float]] = 10
        ) -> None:
        while True:
            thread = Thread(target=self._echo, args=('ping',))
            thread.start()
            sleep(timeout)
            if thread.is_alive():
                self._stop_all_hardend()
            sleep(delay)

    def slew_ra(self, speed: int) -> str:
        if speed >= 0:
            return self.slew_positive_ra(speed)
        return self.slew_negative_ra(speed)

    def slew_dec(self, speed: int) -> str:
        if speed >= 0:
            return self.slew_positive_dec(speed)
        return self.slew_negative_dec(speed)

    def stop_slew(self) -> None:
        self.slew_ra(0)
        self.slew_dec(0)

    @staticmethod
    def get_avalable_ports() -> List[str]:
        return [port.device for port in _avalable_ports()]

    @classmethod
    def parse_ra_dec(cls, ra: str, dec: str) -> Tuple[float, float]:
        ra, dec = _reveal_digits(ra), _reveal_digits(dec)
        return cls._from_clock(ra), cls._from_degrees(dec)


class SynScanDEPRECATED(SynScanObject, SynScanFormatter):

    def set_tracking(self, mode: TrackMode) -> str:
        return self.execute('T' + chr(mode.value))

    def sync_ra_dec(self, ra: float, dec: float, precise: Optional[bool] = True) -> str:
        coordinate = self._encode_coordinate((ra, dec), precise=precise)
        return self.execute(('s' if precise else 'S') + coordinate)

    def set_location(self, location: List[int]) -> str:
        return self.execute('W' + bytes(location).decode())

    def set_datetime(self, time: List[int]) -> str:
        return self.execute('H' + bytes(time).decode())

    def goto_azm_alt(self, azm: float, alt: float, precise: Optional[bool] = True) -> str:
        coordinate = self._encode_coordinate((azm, alt), precise=precise)
        return self.execute(('b' if precise else 'B') + coordinate)

    @classmethod
    def find_mount(cls):
        list_ports = cls.get_avalable_ports()
        assert len(list_ports) == 1
        return cls(list_ports[0])
