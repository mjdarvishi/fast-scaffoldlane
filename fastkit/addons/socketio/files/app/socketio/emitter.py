"""Generic helpers for emitting Socket.IO events."""

from typing import Any

from fastapi.encoders import jsonable_encoder

from app.socketio.instance import sio


async def emit_to_room(room: str, event: str, data: Any) -> None:
    await sio.emit(event, jsonable_encoder(data), room=room)


async def broadcast_event(event: str, data: Any) -> None:
    await sio.emit(event, jsonable_encoder(data))
