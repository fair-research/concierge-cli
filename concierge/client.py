import os
import sys
import click
import json
import requests
from concierge.globus_login import login as glogin
from concierge.globus_login import get_info
from concierge.api import create_bag, stage_bag
from concierge.exc import ConciergeException

from concierge import DEFAULT_CONCIERGE_SERVER


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
        access_token = info['tokens']['auth.globus.org']['access_token']
        rfm_file = json.loads(remote_file_manifest.read())
        bag_metadata, ro_bag_metadata = {}, {}
        if metadata:
            bag_metadata = json.loads(metadata.read())
        if ro_metadata:
            ro_bag_metadata = json.loads(ro_metadata.read())
        if any([isinstance(v, dict) for v in bag_metadata.values()]):
            click.echo('Warning: Metadata contains complex objects.', err=True)
        bag = create_bag(server, rfm_file, info['name'],
                         info['email'], title, access_token,
                         metadata=bag_metadata,
                         ro_metadata=ro_bag_metadata)
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
        auth_token = info['tokens']['auth.globus.org']['access_token']
        transfer_token = \
            info['tokens']['transfer.api.globus.org']['access_token']
        result = stage_bag(minids, destination_endpoint, auth_token,
                           transfer_token=transfer_token,
                           prefix=path, server=server)
        click.echo('{}'.format(result))
    except ConciergeException as ce:
        click.echo('Error Creating Bag: {}'.format(ce.message), err=True)
    except requests.exceptions.ConnectionError as ce:
        click.echo(str(ce), err=True)


@click.command()
def usage():
    click.echo('Use "cbag" for the Concierge CLI.')
