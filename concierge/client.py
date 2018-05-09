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
@click.option('--server', '-s', help='Concierge server to use',
              default='https://concierge.fair-research.org')
@click.argument('remote_file_manifest')
@click.argument('title')
def create(remote_file_manifest, title, server):
    if not os.path.exists(remote_file_manifest):
        click.echo('Remote File Manifest "{}" '
                   'does not exist'.format(remote_file_manifest))
        sys.exit(2)
    with open(remote_file_manifest) as f:
        try:
            # this should take an optional metadata
            info = get_info()
            access_token = info['tokens']['auth.globus.org']['access_token']
            rfm_file = json.loads(f.read())
            bag = create_bag(server, rfm_file, info['name'],
                             info['email'], title, access_token)
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
