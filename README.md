# Google Drive File Stream - What is it?
Google Drive File Stream works as a file-syncing application, facilitating the synchronization of files and photos with Google Drive and Google Photos services. The nomenclature "file stream" is attributed to its capability to stream files on demand, thereby avoiding the need to occupy disk space by downloading all files preemptively. Upon installation and login, users can promptly access all previously synced files through Windows Explorer, without the necessity of storing an offline version.

# DriveFS Sleuth

![](/assets/DriveFS Sleuth Logo.jpg)

DriveFS Sleuth is a Python tool that automates investigating Google Drive File Stream disk artifacts, the tool has been developed based on research that has been performed by mounting different scenarios and noting down the changes in the Google Drive File Stream disk artifacts.

DriveFS Sleuth is capable of parsing the disk artifacts and building a filesystem tree-like structure enumerating the synchronized files along with their respective properties. DriveFS Sleuth detects some deleted synchronized items and items that have been shared with the user, compiles information on mirroring folders, and provides insights into connected device configurations along with searching functionality to facilitate the investigations. Additionally, DriveFS Sleuth offers the functionality to generate reports in HTML or CSV formats.

Refer to: https://amgedwageh.medium.com/drivefs-sleuth-investigating-google-drive-file-streams-disk-artifacts-0b5ea637c980 for more information about the underlying research.

## Artifacts Collection
For those who are fans of Velociraptor, like myself, here is a Velociraptor offline collector ready to be used for triaging Google Drive File Stream artifacts to investigate them. The collector can be found here https://github.com/AmgdGocha/DriveFS-Sleuth/tree/main/collectors.

You can also use this Kape target to gather the same artifacts: https://github.com/EricZimmerman/KapeFiles/blob/master/Targets/Apps/GoogleDrive_Metadata.tkape

## DriveFS Sleuth Usage
```
usage: DriveFS Sleuth [-h] [--accounts ACCOUNTS [ACCOUNTS ...]] [--regex REGEX [REGEX ...]] [-q QUERY_BY_NAME [QUERY_BY_NAME ...]] [--exact]
                      [--search-csv SEARCH_CSV] [--dont-list-sub-items] [--csv CSV] [--html HTML]
                      path

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


positional arguments:
  path                  A path to the DriveFS folder. By default on a live system, it should exist in %LocalAppData%\Google\DriveFS.

optional arguments:
  -h, --help            show this help message and exit
  --accounts ACCOUNTS [ACCOUNTS ...]
                        Specifies account id/s or emails separated by space to be processed, defaults to all the accounts.
  --regex REGEX [REGEX ...]
                        Searches for files or folders by regular expressions. Multiple regex can be passed separated by spaces.
  -q QUERY_BY_NAME [QUERY_BY_NAME ...], --query_by_name QUERY_BY_NAME [QUERY_BY_NAME ...]
                        Searches for files or folders by name. The search will be case insensitive. Multiple file names can be passed separated by spaces.
  --exact               If selected, only files or folders with exact file names will be returned. The --query_by_name argument has to be passed. Defaults to False.
  --search-csv SEARCH_CSV
                        Searches for files or folders that satisfies the searching conditions in the provided CSV file.
  --dont-list-sub-items
                        By default, if a folder matches the search criteria, the results will contain all of it's sub-items. This argument suppresses this feature to only return the folder without listing it's sub-items.
  --csv CSV             Generates an HTML report. The CSV report will only contain information regarding the queried files.
  --html HTML           Generates an HTML report. The HTML report contains comprehensive information about the analyzed artifacts.
```
DriveFS Sleuth has been developed following research results, aiming to automate the investigation of disk forensic artifacts associated with the Google Drive File Stream Application. The tool's usage is straightforward: the analyst provides a path to the DriveFS triaged folder. Additionally, by utilizing the `--accounts` argument, the analyst can specify the email or account ID of the targeted account, allowing the tool to process the interesting accounts. Multiple accounts can be specified, separated by spaces.

DriveFS Sleuth supports searching functionalities, allowing the analyst to employ regular expressions by passing a regex to the `--regex` parameter. Multiple expressions can be specified, separated by spaces. Furthermore, a simple text search is facilitated through the `-q|--query-by-name` optional parameter, where the analyst can input single or multiple texts separated by spaces. By default, the tool searches for files or folders with names containing the provided simple text. The `--exact` parameter can be toggled to enforce an exact name search.

While the default behavior involves listing all sub-items of a folder meeting the search criteria, the analyst can use the `--dont-list-sub-items` parameter to suppress this feature and only list the matching folder.

DriveFS Sleuth facilitates a more complex combination of search criteria by enabling the analyst to pass a CSV file containing the search conditions through the `--search-csv` parameter. The CSV file utilized for searching includes case-sensitive headers: `TARGET`, `TYPE`, `CONTAINS`, and `LIST_SUB_ITEMS`. The `TARGET` field holds the searching regex or simple text, while the `TYPE` field classifies the search type as either `FILENAME` or `REGEX`. The `CONTAINS` field employs `FALSE` for an exact search or `TRUE` to search for any filename containing the specified `TARGET`. Additionally, `LIST_SUB_ITEMS` is utilized to enable or disable the listing of sub-items for matching folders, indicated by `TRUE` or `FALSE`, respectively.

DriveFS Sleuth supports two types of outputs:
1. A CSV File/s.
2. An HTML Report.

A path can be passed to the `--csv` arguments so DriveFS Sleuth outputs 2 CSV files, the first file contains a list of all the processed files while the second CSV file lists the files and folders that match the search if the analyst provided any. Similarly, a path can be provided to the `--html` argument to generate an HTML report with the analysis results.

