from requests import *
from requestr.sessions import Session, parse_response
from requestr.api import get, options, head, post, put, patch, delete
from requestr.futures_session import FuturesSession
import requestr.futures_api as requestr_futures