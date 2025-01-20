from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastcs import launch
from fastcs.attributes import AttrR, AttrW, Sender, Updater
from fastcs.connections import (
    SerialConnection,
    SerialConnectionSettings,
)
from fastcs.controller import Controller
from fastcs.datatypes import Bool, Int, String
from fastcs.wrappers import command

__version__ = "0.0.1"

@dataclass
class ThorlabsMFFSettings:
    serial_settings: SerialConnectionSettings


class ThorlabsAPTProtocol:
    def set_identify(self) -> bytes:
        return b"\x23\x02\x00\x00\x50\x01"

    def set_position(self, desired: bool) -> bytes:
        if desired:
            return b"\x6a\x04\x00\x02\x50\x01"
        else:
            return b"\x6a\x04\x00\x01\x50\x01"

    def get_position(self) -> bytes:
        return b"\x29\x04\x00\x00\x50\x01"

    def get_info(self) -> bytes:
        return b"\x05\x00\x00\x00\x50\x01"

    def read_position(self, response: bytes) -> bool:
        return bool(int(response[8]) - 1)

    def read_model(self, response: bytes) -> str:
        return response[10:18].decode("ascii")

    def read_serial_no(self, response: bytes) -> int:
        return int.from_bytes(response[6:10], byteorder="little")



protocol = ThorlabsAPTProtocol()


@dataclass
class ThorlabsMFFHandlerW(Sender):
    cmd: Callable

    async def put(
        self,
        controller: ThorlabsMFF,
        attr: AttrW,
        value: Any,
    ) -> None:
        await controller.conn.send_command(
            self.cmd(value),
        )


@dataclass
class ThorlabsMFFHandlerR(Updater):
    cmd: Callable
    response_size: int
    process_response: Callable
    update_period: float | None = 0.2

    async def update(
        self,
        controller: ThorlabsMFF,
        attr: AttrR,
    ) -> None:
        response = await controller.conn.send_query(
            self.cmd(),
            self.response_size,
        )
        response = self.process_response(response)
        await attr.set(response)


class ThorlabsMFF(Controller):
    readback_position = AttrR(
        Bool(znam="Disabled", onam="Enabled"),
        handler=ThorlabsMFFHandlerR(
            protocol.get_position,
            12,
            protocol.read_position,
            update_period=0.2,
        ),
    )
    desired_position = AttrW(
        Bool(znam="Disabled", onam="Enabled"),
        handler=ThorlabsMFFHandlerW(
            protocol.set_position,
        ),
    )
    model = AttrR(
        String(),
        handler=ThorlabsMFFHandlerR(
            protocol.get_info,
            90,
            protocol.read_model,
            update_period=10,
        ),
        group="Information",
    )
    serial_no = AttrR(
        Int(),
        handler=ThorlabsMFFHandlerR(
            protocol.get_info,
            90,
            protocol.read_serial_no,
            update_period=10,
        ),
        group="Information",
    )

    def __init__(self, settings: ThorlabsMFFSettings):
        super().__init__()

        self.suffix = ""
        self._settings = settings
        self.conn = SerialConnection()

    async def connect(self) -> None:
        await self.conn.connect(self._settings.serial_settings)

    async def close(self) -> None:
        await self.conn.close()

    @command()
    async def blink_led(self) -> None:
        await self.conn.send_command(
            protocol.set_identify(),
        )

if __name__ == "__main__":
    launch(ThorlabsMFF, version=__version__)
