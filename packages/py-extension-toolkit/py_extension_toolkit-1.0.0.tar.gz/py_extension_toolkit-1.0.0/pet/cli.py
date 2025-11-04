#!/usr/bin/env python3
"""
Python Extension Toolkit (PET) CLI
A Python equivalent of the Zoho Extension Toolkit (zet)
"""

import click
from pet.commands.init_command import init
from pet.commands.run_command import run
from pet.commands.login_command import login
from pet.commands.validate_command import validate
from pet.commands.pack_command import pack
from pet.commands.push_command import push
from pet.commands.pull_command import pull
from pet.commands.list_workspace_command import list_workspace


@click.group()
@click.version_option(version="1.1.0")
def cli():
    """Python Extension Toolkit (PET) - A CLI tool for extension development."""
    pass


# Add all commands to the CLI
cli.add_command(init)
cli.add_command(run)
cli.add_command(login)
cli.add_command(validate)
cli.add_command(pack)
cli.add_command(push)
cli.add_command(pull)
cli.add_command(list_workspace)


if __name__ == "__main__":
    cli()