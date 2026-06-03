import json
import socket
import threading
from typing import Any

DISCOVERY_PORT = 5554
ENCODING = "utf-8"
BROADCAST_ADDRESS = "<broadcast>"


def _EnableBroadcast(Socket: socket.socket) -> None:
    Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    Socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


def ParseRoomNumber(Text: str) -> int | None:
    """Room number is the campaign TCP port (digits only)."""
    Raw = Text.strip()
    if not Raw.isdigit():
        return None
    Room = int(Raw)
    if Room < 1 or Room > 65535:
        return None
    return Room


class RoomDiscoveryHost:
    """UDP listener: answers room lookups on the local network."""

    def __init__(self, RoomNumber: int, HostIp: str, HostUsername: str) -> None:
        self._RoomNumber = RoomNumber
        self._HostIp = HostIp
        self._HostUsername = HostUsername
        self._Socket: socket.socket | None = None
        self._Running = False
        self._Thread: threading.Thread | None = None

    def Start(self) -> None:
        self._Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _EnableBroadcast(self._Socket)
        self._Socket.bind(("", DISCOVERY_PORT))
        self._Running = True
        self._Thread = threading.Thread(target=self._Serve, daemon=True)
        self._Thread.start()

    def _Reply(self, Address: tuple[str, int]) -> None:
        if not self._Socket:
            return
        Payload = {
            "Type": "ROOM_REPLY",
            "Room": self._RoomNumber,
            "HostIp": self._HostIp,
            "Port": self._RoomNumber,
            "Host": self._HostUsername,
        }
        try:
            self._Socket.sendto(
                json.dumps(Payload).encode(ENCODING),
                Address,
            )
        except OSError:
            pass

    def _Serve(self) -> None:
        assert self._Socket is not None
        self._Socket.settimeout(1.0)

        while self._Running:
            try:
                Data, Address = self._Socket.recvfrom(4096)
            except TimeoutError:
                continue
            except OSError:
                break

            try:
                Message = json.loads(Data.decode(ENCODING))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            if Message.get("Type") != "FIND_ROOM":
                continue
            if int(Message.get("Room", -1)) != self._RoomNumber:
                continue

            self._Reply(Address)

    def Stop(self) -> None:
        self._Running = False
        if self._Socket:
            try:
                self._Socket.close()
            except OSError:
                pass
            self._Socket = None


def FindRoomOnLan(RoomNumber: int, Timeout: float = 3.0) -> str | None:
    """Broadcast a room lookup and return the host IPv4 address, if found."""
    Query = json.dumps({"Type": "FIND_ROOM", "Room": RoomNumber}).encode(ENCODING)
    Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    _EnableBroadcast(Socket)
    Socket.settimeout(Timeout)

    try:
        Socket.sendto(Query, (BROADCAST_ADDRESS, DISCOVERY_PORT))
        while True:
            try:
                Data, _ = Socket.recvfrom(4096)
            except TimeoutError:
                return None

            try:
                Message: dict[str, Any] = json.loads(Data.decode(ENCODING))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            if Message.get("Type") != "ROOM_REPLY":
                continue
            if int(Message.get("Room", -1)) != RoomNumber:
                continue

            HostIp = str(Message.get("HostIp", "")).strip()
            if HostIp:
                return HostIp
    except OSError:
        return None
    finally:
        Socket.close()

    return None
