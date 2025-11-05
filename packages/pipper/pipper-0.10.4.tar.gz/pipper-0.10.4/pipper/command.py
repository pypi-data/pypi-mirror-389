import sys

import pipper
from pipper import authorizer
from pipper import bundler
from pipper import downloader
from pipper import info
from pipper import installer
from pipper import parser
from pipper import publisher
from pipper import repository
from pipper.environment import Environment
from typing import Optional

ACTIONS = dict(
    authorize=authorizer.run,
    download=downloader.run,
    install=installer.run,
    bundle=bundler.run,
    publish=publisher.run,
    info=info.run,
    repository=repository.run,
)


def show_version(env: Environment):
    """Shows the pipper version information and then exits"""
    if env.quiet:
        print(pipper.__version__)
    else:
        print("Version: {}".format(pipper.__version__))


def run(cli_args: Optional[list] = None):
    """Executes the command based on command line arguments."""
    args = parser.parse(cli_args)
    env = Environment(args)

    if args.get("version"):
        show_version(env)
        sys.exit(0)

    action = ACTIONS.get(env.action)
    if action is None:
        message = 'Unrecognized command action "{}"'.format(env.action)
        print("[ERROR]: {}".format(message))
        args["parser"].print_help()
        raise ValueError(message)

    if not env.quiet:
        print("\n\n=== {} ===\n".format(env.action.upper()))

    try:
        action(env)
    except Exception as err:
        print("[ERROR]: Unable to complete action. {}\n".format(err))
        raise

    if not env.quiet:
        print("\n")
