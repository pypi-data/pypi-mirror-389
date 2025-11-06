from requestr import FuturesSession

def get(url, **kwargs):
    r'''
    Sends a GET request. Returns :class:`Future` object.

    :param url: URL for the new :class:`Request` object.
    :param **kwargs: Optional arguments that ``request`` takes.
    :rtype : concurrent.futures.Future
    '''
    session = FuturesSession()
    return session.get(url, **kwargs)

def options(url, **kwargs):
    r'''
    Sends an OPTIONS request. Returns :class:`Future` object.

    :param url: URL for the new :class:`Request` object.
    :param **kwargs: Optional arguments that ``request`` takes.
    :rtype : concurrent.futures.Future
    '''
    session = FuturesSession()
    return session.options(url, **kwargs)

def head(url, **kwargs):
    r'''
    Sends a HEAD request. Returns :class:`Future` object.

    :param url: URL for the new :class:`Request` object.
    :param **kwargs: Optional arguments that ``request`` takes.
    :rtype : concurrent.futures.Future
    '''
    session = FuturesSession()
    return session.head(url, **kwargs)

def post(url, data=None, json=None, **kwargs):
    r'''
    Sends a POST request. Returns :class:`Future` object.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
    :param json: (optional) json to send in the body of the :class:`Request`.
    :param **kwargs: Optional arguments that ``request`` takes.
    :rtype : concurrent.futures.Future
    '''
    session = FuturesSession()
    return session.post(url, data=data, json=json, **kwargs)

def put(url, data=None, **kwargs):
    r'''
    Sends a PUT request. Returns :class:`Future` object.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
    :param **kwargs: Optional arguments that ``request`` takes.
    :rtype : concurrent.futures.Future
    '''
    session = FuturesSession()
    return session.put(url, data=data, **kwargs)

def patch(url, data=None, **kwargs):
    r'''
    Sends a PATCH request. Returns :class:`Future` object.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
    :param **kwargs: Optional arguments that ``request`` takes.
    :rtype : concurrent.futures.Future
    '''
    session = FuturesSession()
    return session.patch(url, data=data, **kwargs)

def delete(url, **kwargs):
    r'''
    Sends a DELETE request. Returns :class:`Future` object.

    :param url: URL for the new :class:`Request` object.
    :param **kwargs: Optional arguments that ``request`` takes.
    :rtype : concurrent.futures.Future
    '''
    session = FuturesSession()
    return session.delete(url, **kwargs)