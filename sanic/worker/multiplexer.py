class WorkerMultiplexer:
    def __init__(self, publisher):
        self._publisher = publisher

    def restart(self):
        self._publisher.send(1)
