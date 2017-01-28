from blinker import Namespace

__all__ = ('request_started', 'request_finished')

_signals = Namespace()
signal = _signals.signal


request_started = signal('request-started')
request_finished = signal('request-finished')
