# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: LGPL-3.0-only
from __future__ import annotations
import hashlib
import struct

from pyatem.media import rle_encode


class TransferTask:
    tid: int|None
    state: int|None
    upload: bool
    store: int
    slot: int
    data: bytes
    data_length: int|None
    hash: bytes|None
    send_length: int|None
    send_done: int
    name: str|None
    description: str|None
    def __init__(self, store: int, slot: int, upload=False):
        self.tid = None
        self.state = None
        self.upload = upload

        self.store = store
        self.slot = slot

        # self.data = None
        self.data_length = None
        self.hash = None

        self.send_length = None
        self.send_done = 0

        self.name = None
        self.description = None

    def calculate_hash(self):
        hasher = hashlib.md5(self.data)
        self.hash = hasher.digest()
        self.data_length = len(self.data)

    def compress(self):
        compressed = rle_encode(self.data)
        self.data = compressed
        self.send_length = len(self.data)

    def __repr__(self):
        direction = 'upload' if self.upload else 'download'
        return f'<TransferTask {direction} store={self.store} slot={self.slot}>'

    def to_tcp(self) -> list[tuple[bytes, bytes]]:
        name = self.name.encode() if self.name else b''
        description = self.description.encode() if self.description else b''
        header = struct.pack('>HH Hx? 64s 128s 16s II', self.tid or 0, self.store, self.slot, self.upload,
                             name, description, self.hash, self.send_length, self.data_length)

        # Large packets, let TCP fragmentation deal with it
        chunksize = 16000
        buffer = self.data
        packets: list[tuple[bytes, bytes]] = []
        while True:
            chunk = buffer[0:chunksize]
            buffer = buffer[chunksize:]
            packet = header + chunk
            packets.append((b'*XFR', packet))
            if len(buffer) == 0:
                break
        return packets

    @classmethod
    def from_tcp(cls, packet: bytes):
        header = struct.unpack_from('>HH Hx? 64s 128s 16s II', packet, 8)
        store, slot = header[1], header[2]
        self = TransferTask(store, slot)
        self.tid = header[0]
        self.upload = header[3]
        self.name = header[4].split(b'\x00')[0].decode()
        self.description = header[5].split(b'\x00')[0].decode()
        self.hash = header[6]
        self.send_length = header[7]
        self.data_length = header[8]
        self.data = packet[232:]
        return self


class TransferQueueFlushed:
    def __init__(self):
        pass
