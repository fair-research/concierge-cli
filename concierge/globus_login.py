import sys
import os
import json
import globus_sdk
from globus_sdk.exc import TransferAPIError
import webbrowser
from concierge.exc import LoginRequired

CLIENT_ID = 'd686ffce-63be-4dd4-9094-42008f754d0c'
INFO_FILE = os.path.join(os.getenv('HOME'), '.concierge_client_tokens.json')
REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code'
SCOPES = ('openid email profile '
          'urn:globus:auth:scope:transfer.api.globus.org:all')


# Input function for either python2 or python3
get_input = getattr(__builtins__, 'raw_input', input)


def login(browser=True):
    tokens = do_native_app_authentication(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        requested_scopes=SCOPES,
        browser=browser)
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
                                 requested_scopes=None, browser=False):
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

    if not is_remote_session() and browser:
        # There was a bug in webbrowser recently that this fixes:
        # https://bugs.python.org/issue30392
        if sys.platform == 'darwin':
            webbrowser.get('safari').open(url, new=1)
        else:
            webbrowser.open(url, new=1)

    auth_code = get_input('Enter the auth code: ').strip()

    token_response = client.oauth2_exchange_code_for_tokens(auth_code)
    tokens = token_response.by_resource_server
    access_token = tokens['auth.globus.org']['access_token']
    atclient = globus_sdk.AuthClient(
        authorizer=globus_sdk.AccessTokenAuthorizer(access_token))
    info = atclient.oauth2_userinfo()
    user_info = {
        'tokens': tokens,
        'name': info['name'],
        'email': info['email'],
        'sub': info['sub']
    }
    return user_info


def is_remote_session():
    """
    Check if this is a remote session, in which case we can't open a browser
    on the users computer. This is required for Native App Authentication (but
    not a Client Credentials Grant).
    Returns True on remote session, False otherwise.
    """
    return os.environ.get('SSH_TTY', os.environ.get('SSH_CONNECTION'))
