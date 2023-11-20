# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
from __future__ import annotations
import sys
import queue
import socket
import os
from typing import Generic, TypeVar, Any
if sys.version_info >= (3, 9):
    from types import GenericAlias

_T = TypeVar('_T')

class TypedQueue(Generic[_T]):
    maxsize: int
    def __init__(self, maxsize: int = 0) -> None: ...
    def _init(self, maxsize: int) -> None: ...
    def empty(self) -> bool: ...
    def full(self) -> bool: ...
    def get(self, block: bool = True, timeout: float | None = None) -> _T: ...
    def get_nowait(self) -> _T: ...
    def _get(self) -> _T: ...
    def put(self, item: _T, block: bool = True, timeout: float | None = None) -> None: ...
    def put_nowait(self, item: _T) -> None: ...
    def _put(self, item: _T) -> None: ...
    def join(self) -> None: ...
    def qsize(self) -> int: ...
    def _qsize(self) -> int: ...
    def task_done(self) -> None: ...
    if sys.version_info >= (3, 9):
        def __class_getitem__(cls, item: Any) -> GenericAlias: ...


class SocketQueue(queue.Queue, TypedQueue[_T]):
    """
    This is a queue.Queue that's also a socket so it works with the select() call
    to await both a queue item and a network packet.
    """
    _putsocket: socket.socket
    _getsocket: socket.socket
    def __init__(self):
        super().__init__()

        if os.name == 'posix':
            self._putsocket, self._getsocket = socket.socketpair()
        else:
            # Compatibility on non-POSIX systems
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('127.0.0.1', 0))
            server.listen(1)
            self._putsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._putsocket.connect(server.getsockname())
            self._getsocket, _ = server.accept()
            server.close()

    def fileno(self):
        return self._getsocket.fileno()

    def put(self, item: _T, **kwargs):
        super().put(item, **kwargs)
        self._putsocket.send(b'x')

    def get(self, **kwargs) -> _T:
        self._getsocket.recv(1)
        return super().get(**kwargs)
