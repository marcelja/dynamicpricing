import requests

"""
    Singleton request adapter

    All APIs should use the same adapter in order for connection pools to work
    This also covers an API wide authorization header
"""

request_session = requests.Session()

'''
    Setup connection pools

    otherwise, requests is going to open a new connection for each request,
    leaving resources on the destination allocated.
'''
adapter = requests.adapters.HTTPAdapter(pool_connections=300, pool_maxsize=300)
request_session.mount('http://', adapter)


def add_api_token(token):
    global request_session
    request_session.headers.update({'Authorization': 'Token {:s}'.format(token)})
