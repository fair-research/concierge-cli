import click


@click.command()
def main():
    click.echo('Welcome to the Concierge Client! We are still in early stages '
               'of development, check back soon!')


@click.command()
def usage():
    click.echo('Use "cbag" for the Concierge CLI.')
