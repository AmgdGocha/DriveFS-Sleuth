import argparse
from argparse import RawTextHelpFormatter

if __name__ == '__main__':
    description = """

██████╗ ██████╗ ██╗██╗   ██╗███████╗███████╗███████╗    ███████╗██╗     ███████╗██╗   ██╗████████╗██╗  ██╗
██╔══██╗██╔══██╗██║██║   ██║██╔════╝██╔════╝██╔════╝    ██╔════╝██║     ██╔════╝██║   ██║╚══██╔══╝██║  ██║
██║  ██║██████╔╝██║██║   ██║█████╗  █████╗  ███████╗    ███████╗██║     █████╗  ██║   ██║   ██║   ███████║
██║  ██║██╔══██╗██║╚██╗ ██╔╝██╔══╝  ██╔══╝  ╚════██║    ╚════██║██║     ██╔══╝  ██║   ██║   ██║   ██╔══██║
██████╔╝██║  ██║██║ ╚████╔╝ ███████╗██║     ███████║    ███████║███████╗███████╗╚██████╔╝   ██║   ██║  ██║
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝╚═╝     ╚══════╝    ╚══════╝╚══════╝╚══════╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝
                 A tool for investigating Google Drive File Stream's forensic artifacts.
                 
                                           By: Amged Wageh
                                         Twitter: @amgdgocha
                                   GitHub: https://github.com/AmgdGocha
                                  Medium: https://medium.com/@amgedwageh
                             Linked In: https://www.linkedin.com/in/amgedwageh
    """

    arg_parser = argparse.ArgumentParser(prog="DriveFS Sleuth", formatter_class=RawTextHelpFormatter,
                                         description=description)

    arg_parser.add_argument(
        'path',
        type=str,
        help='A path to the DriveFS folder. By default on a live system, it should exist in '
             '%%LocalAppData%%\\Google\\DriveFS.'
    )

    search_group = arg_parser.add_mutually_exclusive_group()

    search_group.add_argument(
        '--regex',
        type=str,
        help='Searches for files or folders by regular expressions.'
    )

    search_group.add_argument(
        '-q',
        '--query_by_name',
        type=str,
        dest='query_by_name',
        help='Searches for files or folders by name. The search will be case insensitive.'
    )

    # TODO if -q or --regex are being specified
    arg_parser.add_argument(
        '--exact',
        action='store_true',
        dest='contains',
        help='If selected, only files or folders with exact file names will be returned. '
             'The --query_by_name argument has to be passed. Defaults to False.'
    )

    # TODO if -q or --regex are being specified
    arg_parser.add_argument(
        '--no-list-sub-items',
        action='store_true',
        dest='list_sub_items',
        help='By default, if a folder matches the search criteria, the results will contain all of it\'s sub-items. '
             'This argument suppresses this feature to only return the folder without listing it\'s sub-items.'
    )

    arg_parser.add_argument(
        '--csv',
        type=str,
        dest='html_report_location',
        help='Generates an HTML report. The CSV report will only contain information regarding the queried files.'
    )

    arg_parser.add_argument(
        '--html',
        type=str,
        dest='html_report_location',
        help='Generates an HTML report. The HTML report contains comprehensive information about the analyzed '
             'artifacts.'
    )

    arg_parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Prints the output to the console.'
    )

    # TODO add an argument to specify an email or account id to be analyzed

    args = arg_parser.parse_args()
