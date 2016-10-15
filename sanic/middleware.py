class Middleware:
    def __init__(self, process_request=None, process_response=None):
        self.process_request = process_request
        self.process_response = process_response
