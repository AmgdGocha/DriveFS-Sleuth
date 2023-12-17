# Google Drive File Stream - What is it?
Google Drive File Stream works as a file-syncing application, facilitating the synchronization of files and photos with Google Drive and Google Photos services. The nomenclature "file stream" is attributed to its capability to stream files on demand, thereby avoiding the need to occupy disk space by downloading all files preemptively. Upon installation and login, users can promptly access all previously synced files through Windows Explorer, without the necessity of storing an offline version.

# DriveFS Sleuth
[//]: # (Bing creator photo)

DriveFS Sleuth is a Python tool that automates investigating Google Drive File Stream disk artifacts, the tool has been developed based on research that has been performed by mounting different scenarios and noting down the changes in the Google Drive File Stream disk artifacts.

DriveFS Sleuth is capable of parsing the disk artifacts and building a filesystem tree-like structure enumerating the synchronized files along with their respective properties. DriveFS Sleuth detects some deleted synchronized items and items that have been shared with the user, compiles information on mirroring folders, and provides insights into connected device configurations along with searching functionality to facilitate the investigations. Additionally, DriveFS Sleuth offers the functionality to generate reports in HTML or CSV formats.

Refer to [//]: # (Medium story link) for more information about the underlying research.

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