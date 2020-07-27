from pprint import pprint
import click
import json
import requests
from functools import reduce
from urllib.parse import urlencode

from concierge import api
from concierge.exc import ConciergeException
from concierge.version import __version__

GLOBUS_WEB_TASK = 'https://app.globus.org/activity/{}/overview'
GLOBUS_WEB_TRANSFER = 'https://app.globus.org/file-manager?{}'
DEFAULT_CONCIERGE_SERVER = api.ConciergeClient.CONCIERGE_API


def get_concierge_client(server=None):
    return api.ConciergeClient(base_url=server)


@click.group()
def main():
    pass


@main.command(help='Login with Globus')
@click.option('--refresh-tokens/--no-refresh-tokens', default=False,
              help='Request a refresh token to login indefinitely')
@click.option('--force/--no-force', default=False,
              help='Do a fresh login, ignoring any existing credentials')
@click.option('--local-server/--no-local-server', default=True,
              help='Start a local TCP server to handle the auth code')
@click.option('--browser/--no-browser', default=True,
              help='Automatically open the browser to login')
def login(refresh_tokens, force, local_server, browser):
    cc = get_concierge_client()
    if cc.is_logged_in() and not force:
        click.echo('You are already logged in.')
        return

    cc.login(refresh_tokens=refresh_tokens,
             no_local_server=not local_server,
             no_browser=not browser,
             force=force)
    click.secho('You have been logged in.', fg='green')


@main.command(help='Revoke local tokens')
def logout():
    cc = get_concierge_client()
    if cc.is_logged_in():
        cc.logout()
        click.secho('You have been logged out.', fg='green')
    else:
        click.echo('No user logged in, no logout necessary.')


@main.command(help='Get info on a Minid')
@click.option('--server', '-s', help='Concierge server to use',
              default=DEFAULT_CONCIERGE_SERVER)
@click.argument('minid')
def info(minid, server):
    cc = get_concierge_client(server)
    try:
        pprint(cc.get_bag([minid])[0])
    except ConciergeException as ce:
        click.echo(json.dumps(ce.message, indent=4), err=True)


@main.command(help='Create a Minid-Referenced BDBag with a '
                   'Remote File Manifest')
@click.option('--minid-metadata', type=click.File('r'), nargs=1)
@click.option('--minid-test/--no-minid-test', default=False)
@click.option('--bag-name', default='', help='Filename for the bdbag')
@click.option('--bag-ro-metadata', type=click.File('r'), nargs=1)
@click.option('--bag-metadata', '-m', type=click.File('r'), nargs=1)
@click.option('--server', '-s', help='Concierge server to use',
              default=DEFAULT_CONCIERGE_SERVER)
@click.argument('remote_file_manifest', type=click.File('r'))
def create(remote_file_manifest, server, bag_metadata,
           bag_ro_metadata, bag_name, minid_test, minid_metadata):
    cc = get_concierge_client(server)
    if not cc.is_logged_in():
        click.secho('You are not logged in', fg='red')
        return

    try:
        # this should take an optional metadata
        rfm = json.loads(remote_file_manifest.read())
        bag_metadata_dict, bag_ro_metadata_dict = {}, {}
        minid_metadata_dict = {}
        if bag_metadata:
            bag_metadata_dict = json.loads(bag_metadata.read())
        if bag_ro_metadata:
            bag_ro_metadata_dict = json.loads(bag_ro_metadata.read())
        if minid_metadata:
            minid_metadata_dict = json.loads(minid_metadata.read())
        if any([isinstance(v, dict) for v in bag_metadata_dict.values()]):
            click.echo('Warning: Metadata contains complex objects.', err=True)
        bag = cc.create_bag(rfm, minid_metadata=minid_metadata_dict,
                            bag_metadata=bag_metadata_dict,
                            bag_ro_metadata=bag_ro_metadata_dict,
                            bag_name=bag_name, minid_test=minid_test)
        click.echo('{}'.format(bag['minid']))
    except ConciergeException as ce:
        click.echo(f'Error Creating Bag: \n {json.dumps(ce.errors, indent=4)}',
                   err=True)
    except requests.exceptions.ConnectionError as ce:
        click.echo(str(ce), err=True)


def update(path, minid):
    pass


def get(minid):
    pass


@main.command(help='Stage a BDBag referred to by a Minid. Specify multiple '
                   'minids by commas.')
@click.argument('minids')
@click.argument('destination_endpoint')
@click.argument('path', default='')
@click.option('--server', '-s', help='Concierge server to use',
              default=DEFAULT_CONCIERGE_SERVER)
@click.option('--bag-dirs', default=False, is_flag=True,
              help='Use dirs within the bag instead of source path')
@click.option('--transfer-label', default='Concierge Bag Transfer',
              help='Label for the concierge transfer')
def stage(minids, destination_endpoint, path, server, bag_dirs,
          transfer_label):

    cc = get_concierge_client(server)
    if not cc.is_logged_in():
        click.secho('You are not logged in', fg='red')
        return
    try:
        minids = minids.split(',')
        result = cc.stage_bag(minids, destination_endpoint, path=path,
                              bag_dirs=bag_dirs, transfer_label=transfer_label)
        transferred = result['transfer_catalog'].values()
        if len(transferred) == 1:
            num_transferred = len(list(transferred)[0])
        else:
            num_transferred = reduce(lambda x, y: len(x) + len(y), transferred)
        stats = {
            'transferred': num_transferred,
            'source_eps': len(result['transfer_catalog']),
            'dest': GLOBUS_WEB_TRANSFER.format(
                urlencode({'origin_id': result['destination_endpoint'],
                           'origin_path': result['destination_path_prefix']})),
            'catalog': result['url'],
            'transfer_tasks': ('\n\t\t\t'.join([GLOBUS_WEB_TASK.format(s)
                               for s in result['transfer_task_ids']])),
            'transfer_errors': len(result['error_catalog'])
        }
        report = (
            'Files Transferred: \t{transferred}\n'
            'Source Endpoints: \t{source_eps}\n'
            'Destination Path: \t{dest}\n'
            'Transfer Catalog: \t{catalog}\n'
            'Transfer Tasks: \t{transfer_tasks}\n'
            'Transfer Errors: \t{transfer_errors}'.format(**stats)
        )
        click.echo('{}'.format(report))
    except ConciergeException as ce:
        click.echo(f'Error Staging Bag: \n {json.dumps(ce.errors, indent=4)}',
                   err=True)
    except requests.exceptions.ConnectionError as ce:
        click.echo(str(ce), err=True)


@main.command(help='Show current version of the Concierge Client')
def version():
    click.echo(__version__)


@click.command()
def usage():
    click.echo('Use "cbag" for the Concierge CLI.')
