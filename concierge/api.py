import os
from minid import MinidClient
import globus_sdk
import fair_research_login

import concierge.exc


class ConciergeClient(globus_sdk.base.BaseClient):
    CLIENT_ID = 'd686ffce-63be-4dd4-9094-42008f754d0c'
    CONCIERGE_SCOPE = (
        'https://auth.globus.org/scopes/'
        '524361f2-e4a9-4bd0-a3a6-03e365cac8a9/concierge'
    )
    APP_NAME = 'Concierge Client'
    ENVIRONMENTS = {
        'production': 'https://concierge.fair-research.org/api/',
        'local': 'http://localhost:8000/api/',
    }
    error_class = concierge.exc.ConciergeException

    def __init__(self, *args, **kwargs):
        self.SCOPES = [self.CONCIERGE_SCOPE]
        env = os.getenv('CONCIERGE_ENV', 'production')
        kwargs['base_url'] = kwargs.get('base_url', self.ENVIRONMENTS[env])
        kwargs.update(dict(client_id=self.CLIENT_ID, app_name=self.APP_NAME))
        super().__init__('Concierge Client App', *args, **kwargs)
        self.native_client = fair_research_login.NativeClient(
            app_name=self.app_name, client_id=self.CLIENT_ID,
            default_scopes=self.SCOPES,
        )

    @property
    def authorizer(self):
        if self._authorizer is not None:
            return self._authorizer
        try:
            scopes = self.native_client.get_authorizers_by_scope()
            return scopes[self.CONCIERGE_SCOPE]
        except fair_research_login.LoadError:
            return None

    @authorizer.setter
    def authorizer(self, value):
        self._authorizer = value

    def is_logged_in(self):
        return bool(self.authorizer)

    def login(self, refresh_tokens=False, no_local_server=False,
              no_browser=False, force=False):
        """
        Authenticate with Globus for tokens to talk to the concierge service
        **Parameters**
        ``no_local_server`` (*bool*)
          Disable spinning up a local server to automatically copy-paste the
          auth code. THIS IS REQUIRED if you are on a remote server, as this
          package isn't able to determine the domain of a remote service. When
          used locally with no_local_server=False, the domain is localhost with
          a randomly chosen open port number. Typically not used when calling
          directly into a client.
        ``no_browser`` (*string*)
          Do not automatically open the browser for the Globus Auth URL.
          Display the URL instead and let the user navigate to that location.
          This usually isn't desired if calling from a jupyter notebook or from
          a remote server.
        ``refresh_tokens`` (*bool*)
          Ask for Globus Refresh Tokens to extend login time.
        ``force`` (*bool*)
          Force a login flow, even if loaded tokens are valid.
        """
        self.native_client.login(refresh_tokens=refresh_tokens,
                                 no_local_server=no_local_server,
                                 no_browser=no_browser,
                                 force=force)

    def logout(self):
        """
        Revoke local tokens and clear the token cache.
        """
        try:
            self.native_client.load_tokens()
            self.native_client.logout()
            return True
        except fair_research_login.LoadError:
            return False

    def get_bag(self, minids):
        mc = MinidClient()
        return [mc.check(mc.to_minid(m)).data for m in minids]

    def create_bag(self, remote_file_manifest, minid_metadata=None,
                   bag_metadata=None, bag_ro_metadata=None,
                   bag_name=None, minid_test=False):
        """
        :param remote_file_manifest: The BDBag remote file manifest for the bag.
        Docs can be found here:
        https://github.com/fair-research/bdbag/blob/master/doc/config.md#remote-file-manifest  # noqa
        :param minid_metadata: Metadata to include for the minid
        :param minid_test: Create the minid as a test or real production minid
        :param minid_visible_to: Control who can view the minid
        :param bag_metadata: Optional metadata for the bdbag. Must be a dict of the
                         format:
                         {"bag_metadata": {...}, "ro_metadata": {...} }
        :param bag_ro_metadata: Research Object metadata, see BDBag docs for more info
                            on usage and file syntax:
                            https://github.com/fair-research/bdbag/tree/ro-metadata-enhancements/examples/metamanifests  # noqa
        :param verify_remote_files
        :return: Creates a BDBag from the manifest, registers it and returns
         the resulting Minid
        """
        data = dict(remote_file_manifest=remote_file_manifest,
                    minid_metadata=minid_metadata or {},
                    bag_metadata=bag_metadata or {},
                    bag_ro_metadata=bag_ro_metadata or {},
                    bag_name=bag_name,
                    minid_test=minid_test)
        return self.post("/bags/", json_body=data)

    def stage_bag(self, minids, destination_endpoint, path=None,
                  bag_dirs=False, transfer_label='Concierge Transfer'):
        data = dict(minids=minids, destination_endpoint=destination_endpoint,
                    destination_path_prefix=path, bag_dirs=bag_dirs,
                    transfer_label=transfer_label)
        return self.post("/stagebag/", json_body=data)
