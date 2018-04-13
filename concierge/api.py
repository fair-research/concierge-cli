import requests
from concierge.exc import ConciergeException


def create_bag(server, remote_file_manifest, name, email, title, bearer_token):
    """
    :param remote_file_manifest: The BDBag remote file manifest for the bag.
    Docs can be found here:
    https://github.com/fair-research/bdbag/blob/master/doc/config.md#remote-file-manifest  # noqa
    :param name: The name that will be under on the Minid Service
    :param email: The email that will be used (Must be a
                    globus-linked-identity)
    :param title: The title of the minid
    :param bearer_token: A User Globus access token
    :return: Creates a BDBag from the manifest, registers it and returns
     the resulting Minid
    """
    headers = {'Authorization': 'Bearer {}'.format(bearer_token)}
    data = {
      'minid_user': name, 'minid_email': email, 'minid_title': title,
      'remote_files_manifest': remote_file_manifest
    }
    url = '{}/api/bags/'.format(server)
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()
    else:
        raise ConciergeException()


def update_bag():
    pass


def get_bag():
    pass
