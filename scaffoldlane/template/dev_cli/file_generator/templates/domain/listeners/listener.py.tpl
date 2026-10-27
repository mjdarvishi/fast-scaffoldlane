from app.core.event_bus import BaseListener
{event_import}


class {listener_class}(BaseListener[{event_class}]):
    event_type = {event_class}

    async def handle(self, event: {event_class}) -> None:
        pass
