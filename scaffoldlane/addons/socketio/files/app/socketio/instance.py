"""Shared Socket.IO server instance."""

import socketio


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
