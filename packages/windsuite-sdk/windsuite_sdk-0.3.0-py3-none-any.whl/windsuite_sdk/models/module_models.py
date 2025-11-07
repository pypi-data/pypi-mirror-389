from typing import NamedTuple


class ModuleUpdate(NamedTuple):
    mac: str
    ip: str
    type: dict[str, str]
    rpms: dict[int, list[int]]
    is_connected: bool
    is_blinking: bool
    is_psu: bool
    lifepoints: int
    pwms: dict[int, list[int]]
    blink_command: bool
    psu_command: bool
