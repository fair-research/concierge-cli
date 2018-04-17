# Concierge Client

The Concierge Client is used to easily create BDBags and track them by Minids using the Concierge Service.

## Installation

Install using pip:

    pip install git+https://github.com/fair-research/concierge-cli#egg=concierge_cli

This will give you a client you can use to access the Concierge Service

    cbag --help

Creating a bag is fast and easy, point the client at a Remote File Manifest
and it will create it along with a minid.

    cbag login globus
    cbag create my_remote_file_manifest.json concierge-test

The result is a valid minid identifier that can be queried with the minid client:

    minid ark:/99999/fk4hq54x0r
