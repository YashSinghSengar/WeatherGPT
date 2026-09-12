"""Offline guard: MAUSAM_OFFLINE=1 blocks all real sockets during tests."""
import os
import socket

if os.environ.get("MAUSAM_OFFLINE") == "1":
    def _blocked(*a, **k):
        raise OSError("network disabled (MAUSAM_OFFLINE=1)")
    socket.create_connection = _blocked
    socket.socket.connect = _blocked
