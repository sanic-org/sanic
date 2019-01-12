__all__ = ["ConnectionClosed", "InvalidHandshake"]


def __getattr__(name):
    if name == "ConnectionClosed":
        from websockets import ConnectionClosed
        return ConnectionClosed
    if name == "InvalidHandshake":
        from websockets import InvalidHandshake
        return InvalidHandshake
