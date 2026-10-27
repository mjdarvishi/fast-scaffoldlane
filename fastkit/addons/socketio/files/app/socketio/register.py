"""Register application event handlers with the shared Socket.IO server."""

import socketio


def register_all_events(sio: socketio.AsyncServer) -> None:
    # To enable the bundled example:
    # from app.socketio.events.example import register_example_events
    # register_example_events(sio)
    # Add imports and calls for your own event modules here.
    pass
