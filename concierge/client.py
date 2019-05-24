from pprint import pprint
import click
import json
import requests
from functools import reduce
from urllib.parse import urlencode
from concierge.globus_login import login as glogin
from concierge.globus_login import get_info
from concierge.api import bag_create, bag_stage, bag_info
from concierge.exc import ConciergeException
from concierge.version import __version__

from concierge import DEFAULT_CONCIERGE_SERVER, CONCIERGE_SCOPE_NAME

GLOBUS_WEB_TASK = 'https://app.globus.org/activity/{}/overview'
GLOBUS_WEB_TRANSFER = 'https://app.globus.org/file-manager?{}'


@click.group()
def main():
    pass


@main.group(help='Login for authorization with the Concierge '
                 'and Minid services')
def login():
    pass


@login.command(help='Login with Globus')
def globus():
    glogin()


@main.command(help='Get info on a Minid')
@click.option('--server', '-s', help='Concierge server to use',
              default=DEFAULT_CONCIERGE_SERVER)
@click.argument('minid')
def info(minid, server):
    try:
        pprint(bag_info([minid])[0])
    except ConciergeException as ce:
        click.echo('{}: {}'.format(ce.code, ce.message))


@main.command(help='Create a Minid-Referenced BDBag with a '
                   'Remote File Manifest')
@click.option('--minid-metadata', type=click.File('r'), nargs=1)
@click.option('--minid-test/--no-minid-test', default=False)
@click.option('--bag-name', help='Filename for the bdbag')
@click.option('--bag-ro-metadata', type=click.File('r'), nargs=1)
@click.option('--bag-metadata', '-m', type=click.File('r'), nargs=1)
@click.option('--server', '-s', help='Concierge server to use',
              default=DEFAULT_CONCIERGE_SERVER)
@click.argument('remote_file_manifest', type=click.File('r'))
def create(remote_file_manifest, server, bag_metadata,
           bag_ro_metadata, bag_name, minid_test, minid_metadata):
    try:
        # this should take an optional metadata
        info = get_info()
        bearer_token = info[CONCIERGE_SCOPE_NAME]['access_token']
        rfm_file = json.loads(remote_file_manifest.read())
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
        bag = bag_create(rfm_file, bearer_token,
                         minid_metadata=minid_metadata_dict,
                         bag_metadata=bag_metadata_dict,
                         bag_ro_metadata=bag_ro_metadata_dict,
                         bag_name=bag_name,
                         server=server,
                         minid_test=minid_test)
        click.echo('{}'.format(bag['minid']))
    except ConciergeException as ce:
        click.echo('Error Creating Bag: {}'.format(ce.message), err=True)
    except requests.exceptions.ConnectionError as ce:
        click.echo(str(ce), err=True)


def update(path, minid):
    pass


def get(minid):
    pass


@main.command(help='Stage a BDBag referred to by a Minid. Specify multiple '
                   'minids by commas.')
@click.option('--server', '-s', help='Concierge server to use',
              default=DEFAULT_CONCIERGE_SERVER)
@click.argument('minids')
@click.argument('destination_endpoint')
@click.argument('path', default='')
def stage(minids, destination_endpoint, path, server):
    try:
        minids = minids.split(',')
        info = get_info()
        # this should take an optional metadata
        bearer_token = info[CONCIERGE_SCOPE_NAME]['access_token']
        result = bag_stage(minids, destination_endpoint, bearer_token,
                           prefix=path, server=server)
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
        click.echo('Error Creating Bag: {}'.format(ce.message), err=True)
    except requests.exceptions.ConnectionError as ce:
        click.echo(str(ce), err=True)


@main.command(help='Show current version of the Concierge Client')
def version():
    click.echo(__version__)


@click.command()
def usage():
    click.echo('Use "cbag" for the Concierge CLI.')
