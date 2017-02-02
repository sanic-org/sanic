import uvloop

_policy = uvloop.EventLoopPolicy()

def get_event_loop():
    return _policy.get_event_loop()

def new_event_loop():
    return _policy.new_event_loop()

def set_event_loop(loop):
    _policy.set_event_loop(loop)

