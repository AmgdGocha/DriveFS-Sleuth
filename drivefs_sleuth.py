import os
import csv
import argparse
from argparse import RawTextHelpFormatter

from drivefs_sleuth.setup import Setup

from drivefs_sleuth.tasks import generate_csv_report
from drivefs_sleuth.tasks import generate_html_report
from drivefs_sleuth.tasks import recover_from_content_cache


if __name__ == '__main__':
    description = """

██████╗ ██████╗ ██╗██╗   ██╗███████╗███████╗███████╗    ███████╗██╗     ███████╗██╗   ██╗████████╗██╗  ██╗
██╔══██╗██╔══██╗██║██║   ██║██╔════╝██╔════╝██╔════╝    ██╔════╝██║     ██╔════╝██║   ██║╚══██╔══╝██║  ██║
██║  ██║██████╔╝██║██║   ██║█████╗  █████╗  ███████╗    ███████╗██║     █████╗  ██║   ██║   ██║   ███████║
██║  ██║██╔══██╗██║╚██╗ ██╔╝██╔══╝  ██╔══╝  ╚════██║    ╚════██║██║     ██╔══╝  ██║   ██║   ██║   ██╔══██║
██████╔╝██║  ██║██║ ╚████╔╝ ███████╗██║     ███████║    ███████║███████╗███████╗╚██████╔╝   ██║   ██║  ██║
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝╚═╝     ╚══════╝    ╚══════╝╚══════╝╚══════╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝
               A tool for investigating Google Drive File Stream's disk forensic artifacts.
                 
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

    arg_parser.add_argument(
        '--accounts',
        nargs='+',
        type=str,
        help='Specifies account id/s or emails separated by space to be processed, defaults to all the accounts.')

    searching_args = arg_parser.add_argument_group('Searching Arguments')

    searching_args.add_argument(
        '--regex',
        nargs='+',
        type=str,
        help='Searches for files or folders by regular expressions. Multiple regex can be passed separated by spaces.'
    )

    searching_args.add_argument(
        '-q',
        '--query-by-name',
        type=str,
        nargs='+',
        dest='query_by_name',
        help='Searches for files or folders by name. The search will be case insensitive. '
             'Multiple file names can be passed separated by spaces.'
    )

    searching_args.add_argument(
        '--search-csv',
        type=str,
        dest="search_csv",
        help='Searches for files or folders that satisfies the searching conditions in the provided CSV file.'
    )

    searching_args.add_argument(
        '--exact',
        action='store_false',
        dest='exact',
        help='If selected, only files or folders with exact file names will be returned. '
             'The --query_by_name argument has to be passed. Defaults to False.'
    )

    searching_args.add_argument(
        '--dont-list-sub-items',
        action='store_false',
        dest='list_sub_items',
        help='By default, if a folder matches the search criteria, the results will contain all of it\'s sub-items. '
             'This argument suppresses this feature to only return the folder without listing it\'s sub-items.'
    )

    output_formats_group = arg_parser.add_argument_group('Output Formats')

    output_formats_group.add_argument(
        '--csv',
        type=str,
        help='Generates an HTML report. The CSV report will only contain information regarding the queried files.'
             ' Either --csv or --html should be specified.'
    )

    output_formats_group.add_argument(
        '--html',
        type=str,
        help='Generates an HTML report. The HTML report contains comprehensive information about the analyzed '
             'artifacts.  Either --csv or --html should be specified.'
    )

    recovery_group = arg_parser.add_mutually_exclusive_group()

    recovery_group.add_argument(
        '--recover-from-cache',
        dest='recover_from_cache',
        type=str,
        help='Recover the cached items from the content cache. The recovery will be in the passed location.'
    )

    recovery_group.add_argument(
        '--recover-search-results',
        dest='recover_search_results',
        type=str,
        help='Recover the search results items that are cached. The recovery will be in the passed location.'
    )

    args = arg_parser.parse_args()

    drivefs_path = args.path
    if not args.exact and not args.query_by_name:
        arg_parser.print_usage()
        print('DriveFS Sleuth: error: [--exact] can only be specified  with [-q QUERY_BY_NAME [QUERY_BY_NAME ...]]')
        arg_parser.exit()

    if not args.csv and not args.html:
        arg_parser.print_usage()
        print('DriveFS Sleuth: error: Either --csv or --html should be specified.')
        arg_parser.exit()

    if args.recover_search_results and not (args.query_by_name or args.regex or args.search_csv):
        arg_parser.print_usage()
        print('DriveFS Sleuth: error: --recover-search-results option can\'t be specified without specifying searching '
              'criteria via [--regex REGEX [REGEX ...]] or [-q QUERY_BY_NAME [QUERY_BY_NAME ...]] or '
              '[--search-csv SEARCH_CSV]')
        arg_parser.exit()

    print(f'[+] Processing {drivefs_path}...')
    setup = Setup(drivefs_path, args.accounts)

    search_results = {}
    if args.search_csv:
        print(f'[+] Searching the provided CSV searching criteria: {args.search_csv}...')
        searching_criteria = {
            'exact-listing': [],
            'exact-no-listing': [],
            'contains-listing': [],
            'contains-no-listing': [],
            'regex-listing': [],
            'regex-no-listing': []
        }
        with open(args.search_csv, 'r', encoding='utf-8') as search_csv_file:
            for criteria in csv.DictReader(search_csv_file):
                if criteria['TYPE'].lower() == 'regex':
                    if criteria['LIST_SUB_ITEMS'].lower() == 'false':
                        searching_criteria['regex-no-listing'].append(criteria['TARGET'])
                    else:
                        searching_criteria['regex-listing'].append(criteria['TARGET'])
                else:
                    if criteria['CONTAINS'].lower() == 'false':
                        if criteria['LIST_SUB_ITEMS'].lower() == 'false':
                            searching_criteria['exact-no-listing'].append(criteria['TARGET'])
                        else:
                            searching_criteria['exact-listing'].append(criteria['TARGET'])
                    else:
                        if criteria['LIST_SUB_ITEMS'].lower() == 'false':
                            searching_criteria['contains-no-listing'].append(criteria['TARGET'])
                        else:
                            searching_criteria['contains-listing'].append(criteria['TARGET'])

        for account in setup.get_accounts():
            if account.is_logged_in():
                if searching_criteria['exact-listing']:
                    result = account.get_synced_files_tree().search_item_by_name(
                        filenames=searching_criteria['exact-listing'],
                        contains=False
                    )
                    if result:
                        if not search_results.get((account.get_account_id(), account.get_account_email()), None):
                            search_results[(account.get_account_id(), account.get_account_email())] = []
                    search_results[(account.get_account_id(), account.get_account_email())] += result

                if searching_criteria['exact-no-listing']:
                    result = account.get_synced_files_tree().search_item_by_name(
                        filenames=searching_criteria['exact-no-listing'],
                        contains=False,
                        list_sub_items=False
                    )
                    if result:
                        if not search_results.get((account.get_account_id(), account.get_account_email()), None):
                            search_results[(account.get_account_id(), account.get_account_email())] = []
                    search_results[(account.get_account_id(), account.get_account_email())] += result

                if searching_criteria['contains-listing']:
                    result = account.get_synced_files_tree().search_item_by_name(
                        filenames=searching_criteria['contains-listing']
                    )
                    if result:
                        if not search_results.get((account.get_account_id(), account.get_account_email()), None):
                            search_results[(account.get_account_id(), account.get_account_email())] = []
                    search_results[(account.get_account_id(), account.get_account_email())] += result

                if searching_criteria['contains-no-listing']:
                    result = account.get_synced_files_tree().search_item_by_name(
                        filenames=searching_criteria['contains-no-listing'],
                        list_sub_items=False
                    )
                    if result:
                        if not search_results.get((account.get_account_id(), account.get_account_email()), None):
                            search_results[(account.get_account_id(), account.get_account_email())] = []
                    search_results[(account.get_account_id(), account.get_account_email())] += result

                if searching_criteria['regex-listing']:
                    result = account.get_synced_files_tree().search_item_by_name(
                        regex=searching_criteria['regex-listing']
                    )
                    if result:
                        if not search_results.get((account.get_account_id(), account.get_account_email()), None):
                            search_results[(account.get_account_id(), account.get_account_email())] = []
                    search_results[(account.get_account_id(), account.get_account_email())] += result

                if searching_criteria['regex-no-listing']:
                    result = account.get_synced_files_tree().search_item_by_name(
                        regex=searching_criteria['regex-no-listing'],
                        list_sub_items=False
                    )
                    if result:
                        if not search_results.get((account.get_account_id(), account.get_account_email()), None):
                            search_results[(account.get_account_id(), account.get_account_email())] = []
                    search_results[(account.get_account_id(), account.get_account_email())] += result

    for account in setup.get_accounts():
        if account.is_logged_in():
            result = account.get_synced_files_tree().search_item_by_name(
                filenames=args.query_by_name,
                regex=args.regex,
                contains=args.exact,
                list_sub_items=args.list_sub_items
            )

            if result:
                if not search_results.get((account.get_account_id(), account.get_account_email()), None):
                    search_results[(account.get_account_id(), account.get_account_email())] = []
                search_results[(account.get_account_id(), account.get_account_email())] += result

    if args.html:
        if os.path.isdir(args.html):
            output_file = os.path.join(args.html, 'html_report.html')
        else:
            output_file = args.html
        print(f'[+] Generating an HTML report: {output_file}...')
        generate_html_report(setup, output_file, search_results)

    if args.csv:
        if os.path.isdir(args.csv):
            output_file = os.path.join(args.csv, 'items_listing.csv')
        else:
            output_file = args.csv
        print(f'[+] Generating a CSV report: {output_file}...')
        generate_csv_report(setup, output_file, search_results)

    if args.recover_from_cache:
        print(f'[+] Recovering from cache into: {args.recover_from_cache}...')
        for account in setup.get_accounts():
            if account.is_logged_in():
                synced_files_tree = account.get_synced_files_tree()
                recover_from_content_cache(
                    synced_files_tree.get_recoverable_items_from_cache(), args.recover_from_cache)
    elif args.recover_search_results:
        if not search_results.values():
            print('[+] Can\'t recover any items as there is no results available, you may need to consider modifying'
                  ' the searching criteria or using the --recover-from-cache option to recover all the cached items.')
        else:
            print(f'[+] Recovering search results from cache into: {args.recover_search_results}...')
            recoverable_items = []
            for results in search_results.values():
                recoverable_items += results
            recover_from_content_cache(recoverable_items, args.recover_search_results)

    print('[+] DriveFS Sleuth completed the process.')
