import click
import json
from concierge.globus_login import login as glogin
from concierge.globus_login import get_info
from concierge.api import create_bag
from concierge.exc import ConciergeException


@click.group()
def main():
    pass


@main.command(help='Login with Globus')
def globus_login():
    glogin()


@main.command(help='Create a BDBag with a Remote File Manifest')
@click.option('--server', help='Concierge server',
              default='https://concierge.nick.globuscs.info')
@click.argument('remote_file_manifest')
@click.argument('title')
def create(remote_file_manifest, title, server):
    info = get_info()
    access_token = info['tokens']['auth.globus.org']['access_token']
    with open(remote_file_manifest) as f:
        try:
            rfm_file = json.loads(f.read())
            bag = create_bag(server, rfm_file, info['name'],
                             info['email'], title, access_token)
            click.echo('{} created at {}'.format(bag['minid_id'],
                                                 bag['location']))
        except ConciergeException as ce:
            click.echo('Error Creating Bag: {}'.format(ce.message))


@click.command()
def usage():
    click.echo('Use "cbag" for the Concierge CLI.')
