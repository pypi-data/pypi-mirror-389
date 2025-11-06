"""Very small localhost message-passing helpers.

Note: `send(msg)` opens a listener socket and writes to the first client.
Use `receive()` to connect as a client and read the message. Run the sender
first so the listener is available.
"""

import pickle
import socket
from contextlib import closing
from threading import Lock

__lock = Lock()
_HOST = "127.0.0.1"
_PORT = 3011
_HEADER_SIZE = 4  # 4 bytes to store payload length


def _send_with_size(conn: socket.socket, payload: bytes) -> None:
    """Send payload prefixed with its length."""
    conn.sendall(len(payload).to_bytes(_HEADER_SIZE, "big"))
    conn.sendall(payload)


def _recv_exact(conn: socket.socket, size: int) -> bytes:
    """Read exactly `size` bytes from the socket."""
    chunks = []
    remaining = size
    while remaining:
        chunk = conn.recv(remaining)
        if not chunk:
            raise ConnectionResetError("Socket connection closed unexpectedly")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def send(msg):
    payload = pickle.dumps(msg, protocol=pickle.HIGHEST_PROTOCOL)
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((_HOST, _PORT))
        listener.listen(1)
        conn, _ = listener.accept()
        with closing(conn):
            _send_with_size(conn, payload)


def receive():
    with __lock:
        try:
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as conn:
                conn.connect((_HOST, _PORT))
                length = int.from_bytes(_recv_exact(conn, _HEADER_SIZE), "big")
                data = _recv_exact(conn, length)
                return pickle.loads(data)
        except ConnectionRefusedError:
            raise ConnectionRefusedError("Run the sender first")
