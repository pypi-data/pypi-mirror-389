from requests_futures.sessions import FuturesSession as UnmodifiedFuturesSession
from concurrent.futures import Future
from requestr.api import parse_response

class ParsedFuture(Future):
    def __init__(self, original_future):
        super().__init__()
        self._original_future = original_future

    def result(self, timeout=None):
        response = self._original_future.result(timeout)
        return parse_response(response)

class FuturesSession(UnmodifiedFuturesSession):
    def request(self, *args, **kwargs):
        original_future = super().request(*args, **kwargs)
        return ParsedFuture(original_future)