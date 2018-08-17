import sys
import os
import json
import globus_sdk
from globus_sdk.exc import TransferAPIError
from six.moves import input
import webbrowser
from concierge.exc import LoginRequired
from concierge import CONCIERGE_SCOPE

CLIENT_ID = 'd686ffce-63be-4dd4-9094-42008f754d0c'
INFO_FILE = os.path.join(os.getenv('HOME'), '.concierge_client_tokens.json')
REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code'
SCOPES = (CONCIERGE_SCOPE,)


def login():
    tokens = do_native_app_authentication(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        requested_scopes=SCOPES)
    save_info_to_file(INFO_FILE, tokens)


def get_info():
    try:
        # if we already have tokens, load and use them
        return load_info_from_file(INFO_FILE)
    except:
        raise LoginRequired()


def load_info_from_file(filepath):
    """Load a set of saved tokens."""
    with open(filepath, 'r') as f:
        tokens = json.load(f)

    return tokens


def save_info_to_file(filepath, tokens):
    """Save a set of tokens for later use."""
    with open(filepath, 'w') as f:
        json.dump(tokens, f)


def do_native_app_authentication(client_id, redirect_uri,
                                 requested_scopes=None):
    """
    Does a Native App authentication flow and returns a
    dict of tokens keyed by service name.
    """
    client = globus_sdk.NativeAppAuthClient(client_id=client_id)
    # pass refresh_tokens=True to request refresh tokens
    client.oauth2_start_flow(
            requested_scopes=requested_scopes,
            redirect_uri=redirect_uri,
            refresh_tokens=True)

    url = client.oauth2_get_authorize_url()

    print('Native App Authorization URL: \n{}'.format(url))

    if not is_remote_session():
        # There was a bug in webbrowser recently that this fixes:
        # https://bugs.python.org/issue30392
        if sys.platform == 'darwin':
            webbrowser.get('safari').open(url, new=1)
        else:
            webbrowser.open(url, new=1)

    auth_code = input('Enter the auth code: ').strip()

    token_response = client.oauth2_exchange_code_for_tokens(auth_code)
    tokens = token_response.by_resource_server
    return tokens


def is_remote_session():
    """
    Check if this is a remote session, in which case we can't open a browser
    on the users computer. This is required for Native App Authentication (but
    not a Client Credentials Grant).
    Returns True on remote session, False otherwise.
    """
    return os.environ.get('SSH_TTY', os.environ.get('SSH_CONNECTION'))
