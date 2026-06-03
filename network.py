import json
import queue
import socket
import threading
from typing import Any


DEFAULT_PORT = 5555
ENCODING = "utf-8"
JOIN_ANNOUNCEMENT_SUFFIX = "Adventurer Joined To Campaign"
URL_SCHEME = "dnd"
AUTO_PORT = 0
DM_DISPLAY_NAME = "Dungeon Master"


class NetworkProtocol:
    """Line-delimited JSON messages for host/player communication."""

    @staticmethod
    def BuildJoinAnnouncement(Username: str) -> str:
        """Campaign-wide text when a new adventurer connects."""
        return f"{Username}: {JOIN_ANNOUNCEMENT_SUFFIX}"

    @staticmethod
    def Encode(Message: dict[str, Any]) -> bytes:
        return (json.dumps(Message, ensure_ascii=False) + "\n").encode(ENCODING)

    @staticmethod
    def Parse(Line: str) -> dict[str, Any] | None:
        try:
            return json.loads(Line)
        except json.JSONDecodeError:
            return None


class ConnectedPlayer:
    """One player connection on the host."""

    def __init__(self, Socket: socket.socket, Address: tuple[str, int], Username: str) -> None:
        self.Socket = Socket
        self.Address = Address
        self.Username = Username


def BuildInviteUrl(LanIp: str, Port: int) -> str:
    """Shareable LAN invite link for players on the same network."""
    return f"{URL_SCHEME}://{LanIp}:{Port}"


def NormalizeAddressInput(Address: str) -> str:
    """Strip invite URL scheme and whitespace."""
    Text = Address.strip()
    Lower = Text.lower()
    Prefix = f"{URL_SCHEME}://"
    if Lower.startswith(Prefix):
        Text = Text[len(Prefix) :]
    return Text.strip().strip("/")


def ParseHostAddress(
    Address: str,
    DefaultPort: int = DEFAULT_PORT,
) -> tuple[str, int] | None:
    """Parse invite URL, 'host:port', or 'host'. Return None if invalid."""
    Text = NormalizeAddressInput(Address)
    if not Text:
        return None

    if ":" in Text:
        Host, _, PortText = Text.rpartition(":")
        if not Host or not PortText:
            return None
        try:
            Port = int(PortText)
            if Port < 1 or Port > 65535:
                return None
        except ValueError:
            return None
        return Host.strip(), Port

    return Text, DefaultPort


def ResolveCampaignConnection(
    Input: str,
    HostIp: str,
    DefaultPort: int = DEFAULT_PORT,
) -> tuple[str, int] | None:
    """Port-only on LAN, or full dnd:// / host:port when needed."""
    Text = Input.strip()
    if not Text:
        return None

    if Text.isdigit():
        if not HostIp:
            return None
        Port = int(Text)
        if Port < 1 or Port > 65535:
            return None
        return HostIp, Port

    return ParseHostAddress(Text, DefaultPort)


def GetLanIp() -> str:
    """Best-effort LAN IPv4 address for other machines to connect."""
    Probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        Probe.connect(("8.8.8.8", 80))
        return Probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        Probe.close()


def ParseIpv4(Text: str) -> str | None:
    """Return normalized IPv4 text, or None if invalid."""
    Text = Text.strip()
    if not Text:
        return None

    Parts = Text.split(".")
    if len(Parts) != 4:
        return None

    try:
        Octets = [int(Part) for Part in Parts]
    except ValueError:
        return None

    if any(Octet < 0 or Octet > 255 for Octet in Octets):
        return None

    return ".".join(str(Octet) for Octet in Octets)


class CampaignHost:
    """TCP server: accepts players and tracks who is connected."""

    def __init__(self, Port: int) -> None:
        # Port 0 lets the OS pick a free local port on the LAN.
        self._Port = Port
        self._LanIp = ""
        self._HostUsername = DM_DISPLAY_NAME
        self._ServerSocket: socket.socket | None = None
        self._Players: list[ConnectedPlayer] = []
        self._Lock = threading.Lock()
        self._Running = False
        self._AcceptThread: threading.Thread | None = None
        self._EventQueue: queue.Queue[str] = queue.Queue()
        self._Discovery = None

    @property
    def Port(self) -> int:
        return self._Port

    @property
    def RoomNumber(self) -> int:
        """Public room code (same as the TCP port on the LAN)."""
        return self._Port

    @property
    def LanIp(self) -> str:
        return self._LanIp or GetLanIp()

    @property
    def PlayerCount(self) -> int:
        with self._Lock:
            return len(self._Players)

    def _Log(self, Message: str) -> None:
        self._EventQueue.put(Message)

    def _Send(self, Target: ConnectedPlayer, Message: dict[str, Any]) -> None:
        try:
            Target.Socket.sendall(NetworkProtocol.Encode(Message))
        except OSError:
            self._Disconnect(Target)

    def _Broadcast(self, Message: dict[str, Any], Skip: ConnectedPlayer | None = None) -> None:
        Payload = NetworkProtocol.Encode(Message)
        with self._Lock:
            Active = list(self._Players)

        for Player in Active:
            if Skip is not None and Player is Skip:
                continue
            try:
                Player.Socket.sendall(Payload)
            except OSError:
                self._Disconnect(Player)

    def _RosterUsernames(self) -> list[str]:
        with self._Lock:
            return [Player.Username for Player in self._Players]

    def _Disconnect(self, Player: ConnectedPlayer) -> None:
        RemovedName = Player.Username
        with self._Lock:
            if Player in self._Players:
                self._Players.remove(Player)
        try:
            Player.Socket.close()
        except OSError:
            pass
        self._Broadcast({"Type": "PLAYER_LEFT", "Username": RemovedName})
        self._Log(f"Player left: {RemovedName}")

    def _FormatChatLine(self, Username: str, Text: str) -> str:
        return f"[{Username}] {Text}"

    def _LogChat(self, Username: str, Text: str) -> None:
        if Text:
            self._Log(self._FormatChatLine(Username, Text))

    def _RelayChat(self, Username: str, Text: str, Skip: ConnectedPlayer | None = None) -> None:
        """Broadcast chat to all players and show it on the host screen."""
        Text = Text.strip()
        if not Text:
            return
        Payload = {"Type": "CHAT", "Username": Username, "Text": Text}
        self._Broadcast(Payload, Skip=Skip)
        self._LogChat(Username, Text)

    def _HandlePlayerMessage(self, Player: ConnectedPlayer, Message: dict[str, Any]) -> None:
        MsgType = Message.get("Type")
        if MsgType == "CHAT":
            Username = str(Message.get("Username", Player.Username)).strip() or Player.Username
            Text = str(Message.get("Text", ""))
            self._RelayChat(Username, Text, Skip=Player)
        elif MsgType == "PING":
            self._Send(Player, {"Type": "PONG"})

    def _ListenPlayer(self, Player: ConnectedPlayer, InitialBuffer: bytes = b"") -> None:
        """Keep the connection open until the player disconnects."""
        Buffer = InitialBuffer
        try:
            while self._Running:
                Chunk = Player.Socket.recv(4096)
                if not Chunk:
                    break
                Buffer += Chunk
                while b"\n" in Buffer:
                    Line, Buffer = Buffer.split(b"\n", 1)
                    Message = NetworkProtocol.Parse(Line.decode(ENCODING))
                    if Message:
                        self._HandlePlayerMessage(Player, Message)
        except OSError:
            pass
        finally:
            self._Disconnect(Player)

    def SendChat(self, Text: str) -> None:
        """Host message to every connected player."""
        self._RelayChat(self._HostUsername, Text)

    def _AcceptLoop(self) -> None:
        assert self._ServerSocket is not None
        self._ServerSocket.settimeout(1.0)

        while self._Running:
            try:
                Connection, Address = self._ServerSocket.accept()
            except TimeoutError:
                continue
            except OSError:
                break

            threading.Thread(
                target=self._RegisterPlayer,
                args=(Connection, Address),
                daemon=True,
            ).start()

    def _RegisterPlayer(self, Connection: socket.socket, Address: tuple[str, int]) -> None:
        Buffer = b""
        Username = ""

        try:
            Connection.settimeout(30.0)
            while b"\n" not in Buffer:
                Chunk = Connection.recv(4096)
                if not Chunk:
                    Connection.close()
                    return
                Buffer += Chunk

            Line, Remainder = Buffer.split(b"\n", 1)
            Message = NetworkProtocol.Parse(Line.decode(ENCODING))
            if not Message or Message.get("Type") != "JOIN":
                Connection.close()
                return

            Username = str(Message.get("Username", "")).strip()
            if not Username:
                Connection.close()
                return

            Player = ConnectedPlayer(Connection, Address, Username)
            Connection.settimeout(None)

            with self._Lock:
                self._Players.append(Player)

            Welcome = {
                "Type": "WELCOME",
                "Role": "PLAYER",
                "Host": self._HostUsername,
                "Message": f"Welcome to the {self._HostUsername}'s campaign!",
            }
            self._Send(Player, Welcome)
            self._Send(Player, {"Type": "ROSTER", "Players": self._RosterUsernames()})

            Announcement = NetworkProtocol.BuildJoinAnnouncement(Username)
            self._Broadcast(
                {
                    "Type": "PLAYER_JOINED",
                    "Username": Username,
                    "Message": Announcement,
                },
            )
            self._Log(Announcement)

            threading.Thread(
                target=self._ListenPlayer,
                args=(Player, Remainder),
                daemon=True,
            ).start()
        except OSError:
            try:
                Connection.close()
            except OSError:
                pass

    def Start(self) -> None:
        """Bind to a free port on the LAN and listen for players."""
        self._LanIp = GetLanIp()
        self._ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._ServerSocket.bind(("0.0.0.0", self._Port))
        self._Port = self._ServerSocket.getsockname()[1]
        self._ServerSocket.listen(8)
        self._Running = True
        self._AcceptThread = threading.Thread(target=self._AcceptLoop, daemon=True)
        self._AcceptThread.start()

        self._Discovery = RoomDiscoveryHost(
            self._Port,
            self._LanIp,
            self._HostUsername,
        )
        self._Discovery.Start()
        self._Log("Room is open on your local network.")

    def Stop(self) -> None:
        """Shut down the server and disconnect all players."""
        self._Running = False

        with self._Lock:
            Players = list(self._Players)
            self._Players.clear()

        for Player in Players:
            try:
                Player.Socket.close()
            except OSError:
                pass

        if self._ServerSocket:
            try:
                self._ServerSocket.close()
            except OSError:
                pass
            self._ServerSocket = None

        if self._Discovery:
            self._Discovery.Stop()
            self._Discovery = None

        self._Log("Campaign host stopped.")

    def RunSession(self) -> None:
        """Host lobby: share room number, then open chat until the window closes."""
        from ui import AppUI

        RoomText = str(self.RoomNumber)
        HeaderLines = [f"Room Number: {RoomText}"]

        AppUI.OpenChatWindow(
            Title="Campaign Host Chat",
            Username=self._HostUsername,
            EventQueue=self._EventQueue,
            SendMessage=self.SendChat,
            HeaderLines=HeaderLines,
            OnLeave=self.Stop,
            ShouldContinue=lambda: self._Running,
            ShowLocalEcho=False,
            PrivateDiceRolls=True,
        )


class CampaignClient:
    """TCP client: joins a host campaign."""

    def __init__(self, HostIp: str, Port: int, Username: str) -> None:
        self._HostIp = HostIp
        self._Port = Port
        self._Username = Username
        self._Socket: socket.socket | None = None
        self._Running = False
        self._EventQueue: queue.Queue[str] = queue.Queue()
        self._ListenThread: threading.Thread | None = None
        self._SendLock = threading.Lock()

    def _Log(self, Message: str) -> None:
        self._EventQueue.put(Message)

    def _ListenLoop(self) -> None:
        assert self._Socket is not None
        Buffer = b""

        try:
            while self._Running:
                Chunk = self._Socket.recv(4096)
                if not Chunk:
                    self._Log("Disconnected from host.")
                    self._Running = False
                    break
                Buffer += Chunk
                while b"\n" in Buffer:
                    Line, Buffer = Buffer.split(b"\n", 1)
                    self._HandleMessage(NetworkProtocol.Parse(Line.decode(ENCODING)))
        except OSError:
            if self._Running:
                self._Log("Connection lost.")
            self._Running = False

    def _HandleMessage(self, Message: dict[str, Any] | None) -> None:
        if not Message:
            return

        MsgType = Message.get("Type")
        if MsgType == "WELCOME":
            Text = Message.get("Message", "Connected!")
            self._Log(Text)
        elif MsgType == "ROSTER":
            Names = Message.get("Players", [])
            self._Log(f"Players online: {', '.join(Names) if Names else '(none)'}")
        elif MsgType == "PLAYER_JOINED":
            self._Log(
                Message.get("Message")
                or NetworkProtocol.BuildJoinAnnouncement(
                    str(Message.get("Username", "Someone"))
                )
            )
        elif MsgType == "PLAYER_LEFT":
            self._Log(f"{Message.get('Username')} left the campaign.")
        elif MsgType == "CHAT":
            Username = str(Message.get("Username", "?"))
            Text = str(Message.get("Text", ""))
            self._Log(f"[{Username}] {Text}")
        elif MsgType == "PONG":
            pass

    def Connect(self) -> bool:
        """Connect and send JOIN. Return False on failure."""
        try:
            self._Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._Socket.settimeout(10.0)
            self._Socket.connect((self._HostIp, self._Port))
            self._Socket.settimeout(None)
            Join = {"Type": "JOIN", "Username": self._Username}
            self._Socket.sendall(NetworkProtocol.Encode(Join))
            self._Running = True
            self._ListenThread = threading.Thread(target=self._ListenLoop, daemon=True)
            self._ListenThread.start()
            return True
        except OSError as Error:
            self._Log(f"Could not connect: {Error}")
            self._Disconnect()
            return False

    def SendChat(self, Text: str) -> None:
        """Send a chat line to the host (host relays to everyone)."""
        if not self._Socket or not self._Running:
            return
        Text = Text.strip()
        if not Text:
            return
        try:
            Message = {"Type": "CHAT", "Username": self._Username, "Text": Text}
            Payload = NetworkProtocol.Encode(Message)
            with self._SendLock:
                self._Socket.sendall(Payload)
        except OSError:
            self._Log("Connection lost.")
            self._Running = False

    def _Disconnect(self) -> None:
        self._Running = False
        if self._Socket:
            try:
                self._Socket.close()
            except OSError:
                pass
            self._Socket = None

    def RunSession(self) -> None:
        """Join the campaign chat room until the window closes."""
        from ui import AppUI

        if not self.Connect():
            AppUI.ShowError("Could not connect to the room.")
            return

        AppUI.OpenChatWindow(
            Title="Campaign Chat",
            Username=self._Username,
            EventQueue=self._EventQueue,
            SendMessage=self.SendChat,
            HeaderLines=[
                f"Host IP: {self._HostIp}",
                f"Room Number: {self._Port}",
            ],
            OnLeave=self._Disconnect,
            ShouldContinue=lambda: self._Running,
        )


# ---------------------------------------------------------------------------
# UDP room discovery
# ---------------------------------------------------------------------------

DISCOVERY_PORT = 5554
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
            self._Socket.sendto(json.dumps(Payload).encode(ENCODING), Address)
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
