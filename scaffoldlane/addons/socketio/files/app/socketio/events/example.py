"""Example event registration. Copy and adapt this in your own event module."""

import socketio


def register_example_events(sio: socketio.AsyncServer) -> None:
    @sio.on("example")
    async def on_example(sid: str, data: dict) -> dict:
        return {"received": data}
