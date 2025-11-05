import argparse as agp
from pchime.helpers.help_menu import get_app_version
from pchime.local_data_instances.load_data_files.load_csv_file import load_csv_file

from pchime.initiate_federated_learning.server.server_node import establish_server
from pchime.initiate_federated_learning.client.client_node import start_client

from pchime.helpers.help_menu import return_package_name





def create_parser():
    parser = agp.ArgumentParser(prog='pchime')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # help_parser = subparsers.add_parser('help', help="returns help options")
    # help_parser.add_argument('--parquet', required=True)
    # help_parser.set_defaults(func=help_menu)

    load_data_parser = subparsers.add_parser('load', help="load and add data to pchime storage blob to perform FML.")
    load_data_parser.add_argument('--csv', required=True)
    load_data_parser.add_argument('--project', required=True)
    load_data_parser.set_defaults(func=load_csv_file)

    enable_superlink_parser = subparsers.add_parser('server', help="perform server related federated learning operartions")
    enable_superlink_parser.add_argument('--start', required=True)
    enable_superlink_parser.add_argument('--federatedRounds', required=True)
    enable_superlink_parser.add_argument("--n_count", required=True)
    enable_superlink_parser.add_argument("--outDirectory", required=True)
    enable_superlink_parser.set_defaults(func=establish_server)


    run_client_process_parser = subparsers.add_parser('client', help="peforms client related activites such as computing local results")
    run_client_process_parser.add_argument("--start", required=True)
    run_client_process_parser.add_argument("--project", required=True)
    run_client_process_parser.set_defaults(func=start_client)

    pchime_help_parser = subparsers.add_parser('version', help="returns version of the current application")
    # pchime_help_parser.add_argument("--version", required=True)

    pchime_help_parser.set_defaults(func=return_package_name)
    







    return parser
