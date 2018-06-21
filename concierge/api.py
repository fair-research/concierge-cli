import requests
from requests import codes
from concierge.exc import ConciergeException, LoginRequired
from concierge import DEFAULT_CONCIERGE_SERVER


def _concierge_response(response):
    try:
        rjson = response.json()
    except ValueError:
        raise ConciergeException(message='')
    err_code = rjson.get('code', '')
    messages = ','.join(
        ['{}: {}'.format(k, ','.join(v) if isinstance(v, list) else v)
         for k, v in rjson.items() if k != 'code'])

    err_map = {
        codes.BAD_REQUEST: ConciergeException(code=err_code, message=messages),
        codes.UNAUTHORIZED: LoginRequired(),
        codes.SERVER_ERROR: ConciergeException(code=err_code, message=messages)
    }
    concern = err_map.get(response.status_code)
    if concern:
        raise concern
    elif response.status_code in [codes.ALL_GOOD, codes.ACCEPTED,
                                  codes.CREATED]:
        return rjson
    else:
        raise ConciergeException(**rjson)


def create_bag(server, remote_file_manifest, name, email, title, bearer_token,
               metadata={}, ro_metadata={}):
    """
    :param remote_file_manifest: The BDBag remote file manifest for the bag.
    Docs can be found here:
    https://github.com/fair-research/bdbag/blob/master/doc/config.md#remote-file-manifest  # noqa
    :param name: The name that will be under on the Minid Service
    :param email: The email that will be used (Must be a
                    globus-linked-identity)
    :param title: The title of the minid
    :param bearer_token: A User Globus access token
    :param metadata: Optional metadata for the bdbag. Must be a dict of the
                     format:
                     {"bag_metadata": {...}, "ro_metadata": {...} }
    :param ro_metadata: Research Object metadata, see BDBag docs for more info
                        on usage and file syntax:
                        https://github.com/fair-research/bdbag/tree/ro-metadata-enhancements/examples/metamanifests  # noqa
    :return: Creates a BDBag from the manifest, registers it and returns
     the resulting Minid
    """
    headers = {'Authorization': 'Bearer {}'.format(bearer_token)}
    data = {
      'minid_user': name, 'minid_email': email, 'minid_title': title,
      'remote_files_manifest': remote_file_manifest, 'metadata': metadata,
      'ro_metadata': ro_metadata
    }
    url = '{}/api/bags/'.format(server)
    response = requests.post(url, headers=headers, json=data)
    return _concierge_response(response)


def update_bag():
    pass


def get_bag():
    pass


def stage_bag(minids, endpoint, bearer_token, prefix='',
              server=DEFAULT_CONCIERGE_SERVER,
              transfer_token=None):
    headers = {'Authorization': 'Bearer {}'.format(bearer_token)}
    data = {'bag_minids': [minids], 'destination_endpoint': endpoint,
            'transfer_token': transfer_token,
            'destination_path_prefix': prefix}
    url = '{}/api/stagebag/'.format(server)
    response = requests.post(url, headers=headers, json=data)
    return _concierge_response(response)
