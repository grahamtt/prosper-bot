import requests

from prosper_api.auth_token_manager import AuthTokenManager
from prosper_api.config import Config

class Client:
    def __init__(self):
        AuthTokenManager(Config()).get_token()

Client()