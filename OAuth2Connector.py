from pprint import pp
from oauthlib.oauth2.rfc6749.endpoints import token
from oauthlib.oauth2.rfc6749.tokens import get_token_from_header
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from rich.console import Console
import configparser
import json
import os
import sys
import Logger

class OAuth2Connector:
    console = Console()
    token = ""
    onenote = ""
    token_file_name = "token.json"
    configs = "configs/configs.ini"
    authorization_base_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
    token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
    scope = [
        'Notes.Read.All',
        'Notes.Read',
        'Notes.ReadWrite',
        'offline_access'
        ]
    redirect_uri = 'https://localhost:8000/callback'
    client_id= ""
    client_secret = ""
    refresh_url = 'https://login.live.com/oauth20_token.srf'
    protected_url = 'https://graph.microsoft.com/v1.0/me/onenote/notebooks'

    def __init__(self) -> None:
        config = configparser.ConfigParser()
        config.read(self.configs)
        auth_config = config['oauth']

        if 'client_id' not in auth_config or 'PLACEHOLDER' == auth_config['client_id']:
            Logger.error("Please set the \"client_id\" in the corresponding ini file found here: " + self.configs)
            sys.exit()
        else:
            self.client_id = auth_config['client_id']
            
        if 'client_secret' not in auth_config:
            Logger.error("Please set the \"client_secret\" in the corresponding ini file found here: " + self.configs)
            sys.exit()
        else:
            self.client_secret = auth_config['client_secret']

    def create_token(self):
        """
        This Method has to be used once to create a token and a refresh token.
        These will be stored in a local file. Another token will not have to be created this way unless the refresh token expires.
        Use OAuth2Connector.load_token after you created a token.
        """
        #self.check_token()
        os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
        one_note = OAuth2Session(self.client_id, scope=self.scope, redirect_uri=self.redirect_uri)

        # authorisation url
        authorization_url, state = one_note.authorization_url(self.authorization_base_url)
        print('Please go here and authorize: \n', authorization_url)

        # get verification url
        redirect_response = input('Paste the full redirect URL here:')

        # fetch token
        self.token = one_note.fetch_token(self.token_url,client_secret=self.client_secret,authorization_response=redirect_response)
        self.onenote = one_note

    def save_token(self):
        with open(self.token_file_name, 'w', encoding='utf-8') as f:
            json.dump(self.token, f, ensure_ascii=False, indent=4)

    def token_is_expired(self):
        self.load_token()
        one_note = OAuth2Session(client_id = self.client_id, token=self.token)

        try:
            Logger.info('Trying to use saved token..')
            r = one_note.get(self.protected_url)
        except TokenExpiredError as e:
            Logger.info("Saved token expired. Trying to refresh the token..")
            extra = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }
            self.token = one_note.refresh_token(self.refresh_url, **extra)
            self.save_token()
        r = one_note.get(self.protected_url)
        self.onenote = one_note

    def load_token(self):
        with open(self.token_file_name) as json_file:
            self.token = json.load(json_file)
        
        self.onenote = OAuth2Session(self.client_id, token=self.token)

    def get_onenote_session(self):
        return self.onenote