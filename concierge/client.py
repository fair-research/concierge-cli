import os
import sys
import click
import json
import requests
from functools import reduce
from urllib.parse import urlencode
from concierge.globus_login import login as glogin
from concierge.globus_login import get_info
from concierge.api import create_bag, stage_bag
from concierge.exc import ConciergeException

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


@main.command(help='Create a BDBag with a Remote File Manifest')
@click.option('--ro-metadata', type=click.File('r'), nargs=1)
@click.option('--metadata', '-m', type=click.File('r'), nargs=1)
@click.option('--server', '-s', help='Concierge server to use',
              default=DEFAULT_CONCIERGE_SERVER)
@click.argument('remote_file_manifest', type=click.File('r'))
@click.argument('title')
def create(remote_file_manifest, title, server, metadata, ro_metadata):
    try:
        # this should take an optional metadata
        info = get_info()
        access_token = info['tokens'][CONCIERGE_SCOPE_NAME]['access_token']
        rfm_file = json.loads(remote_file_manifest.read())
        bag_metadata, ro_bag_metadata = {}, {}
        if metadata:
            bag_metadata = json.loads(metadata.read())
        if ro_metadata:
            ro_bag_metadata = json.loads(ro_metadata.read())
        if any([isinstance(v, dict) for v in bag_metadata.values()]):
            click.echo('Warning: Metadata contains complex objects.', err=True)
        bag = create_bag(rfm_file, info['name'],
                         info['email'], title, access_token,
                         metadata=bag_metadata,
                         ro_metadata=ro_bag_metadata,
                         server=server)
        click.echo('{}'.format(bag['minid_id']))
    except ConciergeException as ce:
        click.echo('Error Creating Bag: {}'.format(ce.message), err=True)
    except requests.exceptions.ConnectionError as ce:
        click.echo(str(ce), err=True)


def update(path, minid):
    pass


def get(minid):
    pass


@main.command(help='Stage a BDBag with a Minid')
@click.option('--server', '-s', help='Concierge server to use',
              default=DEFAULT_CONCIERGE_SERVER)
@click.argument('minids')
@click.argument('destination_endpoint')
@click.argument('path')
def stage(minids, destination_endpoint, path, server):
    try:
        info = get_info()
        # this should take an optional metadata
        bearer_token = info['tokens'][CONCIERGE_SCOPE_NAME]['access_token']
        result = stage_bag(minids, destination_endpoint, bearer_token,
                           prefix=path, server=server)
        stats = {
            'transferred': len(reduce(lambda x, y: len(x) + len(y),
                               result['transfer_catalog'].values())),
            'source_eps': len(result['transfer_catalog']),
            'dest': GLOBUS_WEB_TRANSFER.format(
                urlencode({'origin_id': result['destination_endpoint'],
                           'origin_path': result['destination_path_prefix']})),
            'catalog': result['url'],
            'transfer_tasks': ','.join([GLOBUS_WEB_TASK.format(s) for s in
                                        result['transfer_task_ids']]),
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


@click.command()
def usage():
    click.echo('Use "cbag" for the Concierge CLI.')
