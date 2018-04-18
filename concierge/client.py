import os
import sys
import click
import json
from concierge.globus_login import login as glogin
from concierge.globus_login import get_info
from concierge.api import create_bag
from concierge.exc import ConciergeException


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
@click.option('--metadata', '-m', type=click.File('r'), nargs=1)
@click.option('--server', '-s', help='Concierge server to use',
              default='https://concierge.fair-research.org')
@click.argument('remote_file_manifest', type=click.File('r'))
@click.argument('title')
def create(remote_file_manifest, title, server, metadata):
    try:
        # this should take an optional metadata
        info = get_info()
        access_token = info['tokens']['auth.globus.org']['access_token']
        rfm_file = json.loads(remote_file_manifest.read())
        bag_metadata = {}
        if metadata:
            bag_metadata = json.loads(metadata.read())
        bag = create_bag(server, rfm_file, info['name'],
                         info['email'], title, access_token,
                         metadata=bag_metadata)
        click.echo('{}'.format(bag['minid_id']))
    except ConciergeException as ce:
        click.echo('Error Creating Bag: {}'.format(ce.message))


def update(path, minid):
    pass


def get(minid):
    pass


@click.command()
def usage():
    click.echo('Use "cbag" for the Concierge CLI.')
