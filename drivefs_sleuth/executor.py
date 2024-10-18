"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: this module contains the main function.
"""

import os
import sys
import csv
import argparse
from argparse import RawTextHelpFormatter

from drivefs_sleuth.setup import Setup

from drivefs_sleuth.tasks import recover_thumbnail
from drivefs_sleuth.tasks import generate_csv_report
from drivefs_sleuth.tasks import generate_html_report
from drivefs_sleuth.tasks import recover_from_content_cache

USE_EMOJI = True if 'utf-8' in sys.stdout.encoding.lower() else False


def __get_status_emoji(emoji, fallback):
    return emoji if USE_EMOJI else fallback


def execute():
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
        '-o',
        '--output',
        required=True,
        type=str,
        help='A path to a directory to save the output.')

    arg_parser.add_argument(
        '--accounts',
        nargs='+',
        type=str,
        help='Specifies account id/s or emails separated by space to be processed, defaults to all the accounts.')

    searching_group = arg_parser.add_argument_group('Searching Arguments')

    searching_group.add_argument(
        '--regex',
        nargs='+',
        type=str,
        default=[],
        help='Searches for files or folders by regular expressions. Multiple regex can be passed separated by spaces.'
    )

    searching_group.add_argument(
        '-q',
        '--query-by-name',
        type=str,
        nargs='+',
        default=[],
        dest='query_by_name',
        help='Searches for files or folders by name. The search will be case insensitive. '
             'Multiple file names can be passed separated by spaces.'
    )

    searching_group.add_argument(
        '--md5',
        type=str,
        nargs='+',
        default=[],
        help='Searches for files by the MD5 hash. Multiple hashes can be passed separated by spaces.'
    )

    searching_group.add_argument(
        '--url-id',
        type=str,
        nargs='+',
        default=[],
        dest='url_id',
        help='Searches for files by the URL ID. Multiple hashes can be passed separated by spaces.'
    )

    searching_group.add_argument(
        '--search-csv',
        type=str,
        dest="search_csv",
        help='Searches for files or folders that satisfies the searching conditions in the provided CSV file.'
    )

    searching_group.add_argument(
        '--exact',
        action='store_false',
        dest='exact',
        help='If selected, only files or folders with exact file names will be returned. '
             'The --query_by_name argument has to be passed. Defaults to False.'
    )

    searching_group.add_argument(
        '--dont-list-sub-items',
        action='store_false',
        dest='list_sub_items',
        help='By default, if a folder matches the search criteria, the results will contain all of it\'s sub-items. '
             'This argument suppresses this feature to only return the folder without listing it\'s sub-items.'
    )

    output_formats_group = arg_parser.add_argument_group('Output Formats')

    output_formats_group.add_argument(
        '--csv',
        action='store_true',
        help='Generates a CSV report. The CSV report will only contain information about the files and folders.'
             ' Either --csv or --html should be specified.'
    )

    output_formats_group.add_argument(
        '--html',
        action='store_true',
        help='Generates an HTML report. The HTML report contains comprehensive information about the analyzed '
             'artifacts.  Either --csv or --html should be specified.'
    )

    recovery_group = arg_parser.add_argument_group('Recovery Options')
    recovery_exclusive_group = recovery_group.add_mutually_exclusive_group()

    recovery_exclusive_group.add_argument(
        '--recover-from-cache',
        dest='recover_from_cache',
        action='store_true',
        help='Recover the cached items from the content cache.'
    )

    recovery_exclusive_group.add_argument(
        '--recover-search-results',
        dest='recover_search_results',
        action='store_true',
        help='Recover the search results items that are cached.'
    )

    args = arg_parser.parse_args()

    drivefs_path = os.path.abspath(args.path)
    if not args.exact and not args.query_by_name:
        arg_parser.print_usage()
        print('DriveFS Sleuth: error: [--exact] can only be specified  with [-q QUERY_BY_NAME [QUERY_BY_NAME ...]]')
        arg_parser.exit()

    if not args.csv and not args.html:
        arg_parser.print_usage()
        print('DriveFS Sleuth: error: Either --csv or --html should be specified.')
        arg_parser.exit()

    if args.recover_search_results and not (args.query_by_name or args.regex or args.search_csv or args.md5):
        arg_parser.print_usage()
        print('DriveFS Sleuth: error: --recover-search-results option can\'t be specified without specifying searching '
              'criteria via [--regex REGEX [REGEX ...]] or [-q QUERY_BY_NAME [QUERY_BY_NAME ...]] or '
              '[--search-csv SEARCH_CSV]')
        arg_parser.exit()

    if os.path.isfile(args.output):
        arg_parser.print_usage()
        print('DriveFS Sleuth: error: -o/--output should contain a path to a file.')
        arg_parser.exit()
    else:
        if not os.path.exists(args.output):
            try:
                os.mkdir(args.output)
            except OSError as e:
                print(f'DriveFS Sleuth: error: couldn\'t create output directory {args.output}\n Error Message: {e}')

    print(f'{__get_status_emoji("🚀", "[START]")} Starting DriveFS Sleuth...')
    print(f'\n{__get_status_emoji("🔄", "[...]")} Processing Path: {drivefs_path}... [IN PROGRESS]')

    setup = Setup(drivefs_path, args.accounts)

    search_results = {}
    searching_criteria = []
    if args.search_csv:
        print(
            f'\n{__get_status_emoji("📂", "[LOADING]")} Loading searching criteria from CSV: {args.search_csv}... [LOADED {__get_status_emoji("✅", "✔")}]')

        try:
            with open(args.search_csv, 'r', encoding='utf-8') as search_csv_file:
                for criteria in csv.DictReader(search_csv_file):
                    if criteria['TYPE'].lower() == 'md5':
                        searching_criteria.append({
                            "TYPE": "md5",
                            "TARGET": [criteria['TARGET']]
                        })
                    elif criteria['TYPE'].lower() == 'urlid':
                        if (criteria['LIST_SUB_ITEMS'] or 'true').lower() == 'false':
                            searching_criteria.append({
                                "TYPE": "urlid",
                                "TARGET": [criteria['TARGET']],
                                "LIST_SUB_ITEMS": False
                            })
                        else:
                            searching_criteria.append({
                                "TYPE": "urlid",
                                "TARGET": [criteria['TARGET']],
                                "LIST_SUB_ITEMS": True
                            })
                    elif criteria['TYPE'].lower() == 'regex':
                        if (criteria['LIST_SUB_ITEMS'] or 'true').lower() == 'false':
                            searching_criteria.append({
                                "TYPE": "regex",
                                "TARGET": [criteria['TARGET']],
                                "LIST_SUB_ITEMS": False
                            })
                        else:
                            searching_criteria.append({
                                "TYPE": "regex",
                                "TARGET": [criteria['TARGET']],
                                "LIST_SUB_ITEMS": True
                            })
                    else:
                        if (criteria['CONTAINS'] or 'true').lower() == 'false':
                            if (criteria['LIST_SUB_ITEMS'] or 'true').lower() == 'false':
                                searching_criteria.append({
                                    "TYPE": "filename",
                                    "TARGET": [criteria['TARGET']],
                                    "CONTAINS": False,
                                    "LIST_SUB_ITEMS": False
                                })
                            else:
                                searching_criteria.append({
                                    "TYPE": "filename",
                                    "TARGET": [criteria['TARGET']],
                                    "CONTAINS": False,
                                    "LIST_SUB_ITEMS": True
                                })
                        else:
                            if (criteria['LIST_SUB_ITEMS'] or 'true').lower() == 'false':
                                searching_criteria.append({
                                    "TYPE": "filename",
                                    "TARGET": [criteria['TARGET']],
                                    "CONTAINS": True,
                                    "LIST_SUB_ITEMS": False
                                })
                            else:
                                searching_criteria.append({
                                    "TYPE": "filename",
                                    "TARGET": [criteria['TARGET']],
                                    "CONTAINS": True,
                                    "LIST_SUB_ITEMS": True
                                })
        except AttributeError:
            print(
                'Searching CSV file should be formated as follows:\n'
                '\t- The Head should be TYPE,TARGET,CONTAINS,LIST_SUB_ITEMS (case sensitive), '
                'where the values should be as follows:\n'
                '\t- TYPE: [md5|filename|regex|urlid] (case insensitive)\n'
                '\t- TARGET: the value to be searched. (case sensitive for regex only)\n'
                '\t- CONTAINS: [True|False] (case insensitive)\n'
                '\t- LIST_SUB_ITEMS: [True|False] (case insensitive)')
            arg_parser.exit()

    if args.query_by_name:
        if args.exact:
            if args.list_sub_items:
                searching_criteria.append({
                    "TYPE": "filename",
                    "TARGET": args.query_by_name,
                    "CONTAINS": False,
                    "LIST_SUB_ITEMS": True
                })
            else:
                searching_criteria.append({
                    "TYPE": "filename",
                    "TARGET": args.query_by_name,
                    "CONTAINS": False,
                    "LIST_SUB_ITEMS": False
                })
        else:
            if args.list_sub_items:
                searching_criteria.append({
                    "TYPE": "filename",
                    "TARGET": args.query_by_name,
                    "CONTAINS": True,
                    "LIST_SUB_ITEMS": True
                })
            else:
                searching_criteria.append({
                    "TYPE": "filename",
                    "TARGET": args.query_by_name,
                    "CONTAINS": True,
                    "LIST_SUB_ITEMS": False
                })

    if args.regex:
        if args.list_sub_items:
            searching_criteria.append({
                "TYPE": "regex",
                "TARGET": args.regex,
                "LIST_SUB_ITEMS": True
            })
        else:
            searching_criteria.append({
                "TYPE": "regex",
                "TARGET": args.regex,
                "LIST_SUB_ITEMS": False
            })

    if args.md5:
        searching_criteria.append({
            "TYPE": "md5",
            "TARGET": args.md5
        })

    if args.url_id:
        if args.list_sub_items:
            searching_criteria.append({
                "TYPE": "urlid",
                "TARGET": args.url_id,
                "LIST_SUB_ITEMS": True
            })
        else:
            searching_criteria.append({
                "TYPE": "urlid",
                "TARGET": args.url_id,
                "LIST_SUB_ITEMS": False
            })

    print(f'{__get_status_emoji("🔍", "[SEARCHING]")} Searching... [IN PROGRESS]')

    if searching_criteria:
        for account in setup.get_accounts():
            if account.is_logged_in():
                result = account.get_synced_files_tree().search(searching_criteria)
                if result:
                    if not search_results.get((account.get_account_id(), account.get_account_email()), None):
                        search_results[(account.get_account_id(), account.get_account_email())] = []
                    search_results[(account.get_account_id(), account.get_account_email())] += result

    print(f"\n{__get_status_emoji('🛠️', '[GENERATING]')} Generating reports:")
    if args.html:
        html_output_path = os.path.join(args.output, 'html_report.html')
        print(
            f'    {__get_status_emoji("📝", "[HTML]")} Generating HTML report: {html_output_path}... [DONE {__get_status_emoji("✅", "✔")}]')
        generate_html_report(setup, html_output_path, search_results)

    if args.csv:
        csv_output_path = os.path.join(args.output, 'csv_report.csv')
        print(
            f'    {__get_status_emoji("📊", "[CSV]")} Generating a CSV report: {csv_output_path}... [DONE {__get_status_emoji("✅", "✔")}]')
        generate_csv_report(setup, csv_output_path, search_results)

    if args.recover_from_cache:
        recovery_from_cache_path = os.path.join(args.output, 'recovery')
        if not os.path.exists(recovery_from_cache_path):
            os.mkdir(recovery_from_cache_path)
        print(
            f'\n{__get_status_emoji("♻️", "[RECOVERY]")} Recovering from cache into: {recovery_from_cache_path}... [IN PROGRESS]')
        for account in setup.get_accounts():
            if account.is_logged_in():
                acc_recovery_from_cache_path = os.path.join(recovery_from_cache_path, account.get_name())
                acc_thumbnails_path = os.path.join(acc_recovery_from_cache_path, 'thumbnails')
                if not os.path.exists(acc_recovery_from_cache_path):
                    os.mkdir(acc_recovery_from_cache_path)
                if not os.path.exists(acc_thumbnails_path):
                    os.mkdir(acc_thumbnails_path)
                synced_files_tree = account.get_synced_files_tree()
                recover_from_content_cache(
                    synced_files_tree.get_recoverable_items_from_cache(), acc_recovery_from_cache_path)
                recover_thumbnail(
                    synced_files_tree.get_thumbnail_items(), acc_thumbnails_path)
    elif args.recover_search_results:
        if not search_results.values():
            print('[+] Can\'t recover any items as there is no results available, you may need to consider modifying'
                  ' the searching criteria or using the --recover-from-cache option to recover all the cached items.')
        else:
            search_recovery_results_path = os.path.join(args.output, 'search_results_recovery')
            if not os.path.exists(search_recovery_results_path):
                os.mkdir(search_recovery_results_path)
            print(
                f'\n{__get_status_emoji("♻️", "[RECOVERY]")} Recovering search results from cache into: {search_recovery_results_path}... [IN PROGRESS]')
            for account in search_results:
                acc_search_recovery_results_path = os.path.join(search_recovery_results_path, account[1])
                acc_thumbnails_path = os.path.join(acc_search_recovery_results_path, 'thumbnails')
                if not os.path.exists(acc_search_recovery_results_path):
                    os.mkdir(acc_search_recovery_results_path)
                if not os.path.exists(acc_thumbnails_path):
                    os.mkdir(acc_thumbnails_path)
                recover_from_content_cache(search_results[account], acc_search_recovery_results_path)
                recover_thumbnail(search_results[account], acc_thumbnails_path)

    print(f'\n{__get_status_emoji("🎉", "[FINISH]")} DriveFS Sleuth completed the process.')
