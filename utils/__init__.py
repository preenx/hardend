from __future__ import annotations

from typing import Tuple, Iterator, Union, Any, Optional, List, Callable
from threading import Thread, main_thread, enumerate as avalable_threads
from uuid import uuid4 as _random_hash

from pygit2.errors import GitError
from dotenv import dotenv_values
from pygit2 import Repository # pylint: disable=ungrouped-imports
from json import dumps
from math import ceil
import inspect
import ctypes
import zwoasi
import os

__all__ = [
    'get_kwargs_or_dotenv_values', 'kill_all_threads',
    'get_methods_by_class_instance', 'random_hash',
    'create_folder_if_not_exist', 'kill_thread',
    'installation_warning', 'json_stringify',
    'init_zwoasi_drivers', 'get_project_url'
]

def kill_thread(thread: Thread, exception: Exception = SystemExit) -> None:
    if thread is not None and thread.is_alive():
        exc = ctypes.py_object(exception)
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread.ident), exc
        )


def kill_all_threads() -> None:
    for thread in avalable_threads():
        if thread != main_thread():
            kill_thread(thread)


def installation_warning() -> None:
    print('[WARN] Dont forget to install new dependencies !!!')
    print('[WARN] pip install -r requirements.txt')


def get_project_url() -> Iterator[str]:
    branches = list(map(
        str.strip, get_kwargs_or_dotenv_values('PROJECT_BRANCHES').split(',')
    ))
    try:
        branches.append(Repository('.').head.shorthand)
    except GitError:
        pass
    for branch in sorted(set(branches)):
        if branch == 'main':
            yield 'https://uniscope.space/'
        else:
            yield f'https://{branch}.uniscope.space/'


def get_kwargs_or_dotenv_values(
        variables: Union[Iterator[str], str],
        kwargs: Optional[dict] = None
    ) -> Union[List[Any], Any]:
    if kwargs is None:
        kwargs = {}
    values = { **dotenv_values(), **os.environ, **kwargs }
    if isinstance(variables, str):
        return values[variables]
    return [values[variable] for variable in variables]


def random_hash(length: Optional[int] = None) -> str:
    if length is None:
        length = int(
            get_kwargs_or_dotenv_values('FILENAME_HASH_LENGTH')
        )
    return ''.join(
        _random_hash().hex for i in range(ceil(length / 32))
    )[:length]


def create_folder_if_not_exist(path: str) -> None:
    try:
        os.mkdir(path)
    except FileExistsError:
        pass


def get_methods_by_class_instance(intance: Any) -> List[Callable]:
    return inspect.getmembers(intance, predicate=inspect.ismethod)


def json_stringify(data: dict) -> str:
    return dumps(data, indent=4)


def init_zwoasi_drivers() -> None:
    driver = os.path.join(os.getcwd(), 'drivers', 'windows_x86.dll')
    zwoasi.init(library_file=driver)
