import Logger
import configs.Switches as Switches
from argparse import ArgumentParser, Namespace
import OAuth2Connector

def create_arg_parser() -> Namespace:
    parser = ArgumentParser(description='Create dnd npcs easily.')
    parser.add_argument('-ct',"--createtoken", action="store_true")
    parser.add_argument('-cc',"--createcharacterpage", action="store_true")
    parser.add_argument('-vb',"--verbose", action="store_true")
    args, _ = parser.parse_known_args()
    
    return args

def handle_create_token(args: Namespace, auth_connector: OAuth2Connector):
    if args.verbose:
        Switches.verbose = True

    if args.createtoken == True:
        Logger.info("A new OneNote API token will be created..")
        auth_connector.create_token()
    else:
        Logger.info("Loading token..")
        auth_connector.token_is_expired()

def process(auth_connector: OAuth2Connector) -> Namespace:
    """
    Handles the creation and processing of the cmd-arguments.
    """
    args = create_arg_parser()
    handle_create_token(args, auth_connector)

    return args


