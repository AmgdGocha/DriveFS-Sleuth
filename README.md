# Google Drive File Stream - What is it?
Google Drive File Stream works as a file-syncing application, facilitating the synchronization of files and photos with Google Drive and Google Photos services. The nomenclature "file stream" is attributed to its capability to stream files on demand, thereby avoiding the need to occupy disk space by downloading all files preemptively. Upon installation and login, users can promptly access all previously synced files through Windows Explorer, without the necessity of storing an offline version.

# 🕵️ DriveFS Sleuth

![This is how Bing creator imagined a logo for the DriveFS Sleuth Tool.](https://raw.githubusercontent.com/AmgdGocha/DriveFS-Sleuth/main/assets/DriveFS%20Sleuth%20Logo.jpg)


DriveFS Sleuth is a Python tool that automates investigating Google Drive File Stream disk artifacts, the tool has been developed based on research that has been performed by mounting different scenarios and noting down the changes in the Google Drive File Stream disk artifacts.

## 🚀 DriveFS Sleuth is capable of:
* Parsing the disk artifacts and building a filesystem tree-like structure enumerating the synchronized files along with their respective properties. 
* Detecting synchronized items and items that have been shared with the user.
* Compiling information on mirroring folders.
* Providing insights into connected device configurations.
* Supports searching functionality to facilitate the investigations.
* Generating HTML and CSV reports of the analysis results.

For the underlying research, refer to: 
* [DriveFS Sleuth — Your Ultimate Google Drive File Stream Investigator!](https://amgedwageh.medium.com/drivefs-sleuth-investigating-google-drive-file-streams-disk-artifacts-0b5ea637c980)
* [DriveFS Sleuth — Revealing The Hidden Intelligence](https://amgedwageh.medium.com/drivefs-sleuth-revealing-the-hidden-intelligence-82f043c452e4)

## 🔍 Artifacts Collection Made Easy
For those who are fans of Velociraptor, like myself, here is a Velociraptor offline collector ready to be used for triaging Google Drive File Stream artifacts to investigate them. The collector can be found here https://github.com/AmgdGocha/DriveFS-Sleuth/tree/main/collectors.

You can also use this Kape target to gather the same artifacts: https://github.com/EricZimmerman/KapeFiles/blob/master/Targets/Apps/GoogleDrive_Metadata.tkape

## 🧑‍💻 DriveFS Sleuth Usage
```
usage: DriveFS Sleuth [-h] [--accounts ACCOUNTS [ACCOUNTS ...]]
                      [--regex REGEX [REGEX ...]]
                      [-q QUERY_BY_NAME [QUERY_BY_NAME ...]]
                      [--search-csv SEARCH_CSV] [--exact]
                      [--dont-list-sub-items] [--csv CSV] [--html HTML]
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

options:
  -h, --help            show this help message and exit
  --accounts ACCOUNTS [ACCOUNTS ...]
                        Specifies account id/s or emails separated by space to be processed, defaults to all the accounts.

Searching Arguments:
  --regex REGEX [REGEX ...]
                        Searches for files or folders by regular expressions. Multiple regex can be passed separated by spaces.
  -q QUERY_BY_NAME [QUERY_BY_NAME ...], --query-by-name QUERY_BY_NAME [QUERY_BY_NAME ...]
                        Searches for files or folders by name. The search will be case insensitive. Multiple file names can be passed separated by spaces.
  --search-csv SEARCH_CSV
                        Searches for files or folders that satisfies the searching conditions in the provided CSV file.
  --exact               If selected, only files or folders with exact file names will be returned. The --query_by_name argument has to be passed. Defaults to False.
  --dont-list-sub-items
                        By default, if a folder matches the search criteria, the results will contain all of it's sub-items. This argument suppresses this feature to only return the folder without listing it's sub-items.

Output Formats:
  --csv CSV             Generates an HTML report. The CSV report will only contain information regarding the queried files. Either --csv or --html should be specified.
  --html HTML           Generates an HTML report. The HTML report contains comprehensive information about the analyzed artifacts.  Either --csv or --html should be specified.
```
### Automated Investigation
Easily automate the examination of Google Drive File Stream artifacts by providing the tool with the path to the DriveFS triaged folder.

### Targeted Analysis
Utilize the `--accounts` argument to specify the email or account ID of the targeted account, allowing the tool to process specific accounts of interest. Multiple accounts can be specified, separated by spaces. Defaults to all available accounts.

### Flexible Search Functionality
DriveFS Sleuth supports various search functionalities to meet your investigative needs:
* **Regular Expressions:** Use the `--regex` parameter to employ regular expressions for searching. Multiple expressions can be specified, separated by spaces.
* **Simple Text Search:** Perform a simple text search using the `[-q|--query-by-name]` optional parameter. Input single or multiple texts separated by spaces. The tool searches for files or folders with names containing the provided text. Toggle the `--exact` parameter for an exact name search.

### Customization Options
Tailor the tool's behavior with additional parameters:
* **Listing Control:** Use the `--dont-list-sub-items` parameter to suppress listing sub-items and only display matching folders.
* **Complex Criteria:** Enable a more complex combination of search criteria by providing a CSV file through the `--search-csv parameter`. The CSV file includes case-sensitive headers: `TARGET`, `TYPE`, `CONTAINS`, and `LIST_SUB_ITEMS`.
    * **TARGET:** Holds the searching regex or simple text.
    * **TYPE:** Classifies the search type as either `FILENAME` or `REGEX`.
    * **CONTAINS:** Use `FALSE` for an exact search or `TRUE` to search for any filename containing the specified target.
    * `LIST_SUB_ITEMS:` Enable or disable the listing of sub-items for matching folders, indicated by `TRUE` or `FALSE`, respectively.

### Output Options
DriveFS Sleuth provides support for two types of outputs:
1. **CSV Files:** You can specify a path using the `--csv` argument to instruct DriveFS Sleuth to generate two CSV files. The first CSV file includes a comprehensive list of all processed files, while the second CSV file specifically enumerates files and folders that match the search criteria if provided by the analyst.
2. **HTML Report:** By supplying a path to the `--html` argument, you can trigger DriveFS Sleuth to create an HTML report summarizing the analysis results.

### Examples
The following are some examples of the tool usage, change the paths and the searching criteria to match yours.
* Processing a triage and outputting an HTML report.
```
python3 drivefs_sleuth.py C:\triage_path\DriveFS --html C:\analysis_results\drivefs_report.html
```
* Processing a triage and outputting a CSV report.
```
python3 drivefs_sleuth.py C:\triage_path\DriveFS --csv C:\analysis_results\drivefs_report.csv
```
* Processing a triage, searching for all files or folders with filenames containing the word 'DFIR', and outputting both CSV and HTML reports.
```
python3 drivefs_sleuth.py C:\triage_path\DriveFS -q DFIR --html C:\analysis_results\drivefs_report.html --csv C:\analysis_results\drivefs_report.csv
```
* Processing a triage, searching for all files or folders with the exact filename 'DFIR', and outputting both CSV and HTML reports.
```
python3 drivefs_sleuth.py C:\triage_path\DriveFS -q DFIR --exact --html C:\analysis_results\drivefs_report.html --csv C:\analysis_results\drivefs_report.csv
```
* Processing a triage, searching for all files or folders with filenames that match the regex `*dfir_\d+*`, and outputting an HTML report with listing sub-items suppressed.
```
python3 drivefs_sleuth.py C:\triage_path\DriveFS --regex '*dfir_\d+' --html C:\analysis_results\drivefs_report.html --dont-list-sub-items
```
* Processing a triage passing a CSV file that contains the searching criteria, and outputting a CSV report.
```
python3 drivefs_sleuth.py C:\triage_path\DriveFS --search-csv search_conditions.csv --csv C:\analysis_results\drivefs_report.csv
```

# 📰 Referenced At:
* [This Week In 4N6 - Week 52 - 2023](https://thisweekin4n6.com/2023/12/24/week-52-2023/)
* [This Week In 4N6 - Week 01 - 2024](https://thisweekin4n6.com/2024/01/07/week-01-2024/)
* [Help Net Security](https://www.helpnetsecurity.com/2024/01/04/drivefs-sleuth-investigating-google-drive-file-stream/)
* [AboutDFIR](https://aboutdfir.com/toolsandartifacts/google-workspace/)
* [Digital Forensics Now Podcast - Episode 9](https://www.youtube.com/live/m_fP7qf3Pok?si=YVaqruW_NlMgpEpg&t=547)

# 🌟 Your Feedback Matters:
I'm eager to hear your thoughts! Share your feedback and suggestions, or report issues on our GitHub repository. Your input is crucial in making DriveFS Sleuth even more robust. Consider starring the repo if you found it useful. 😉
