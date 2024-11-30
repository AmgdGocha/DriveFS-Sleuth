# Google Drive For Desktop - What is it?
Google Drive for Desktop (formerly known as Google Drive File Stream) works as a file-syncing application, facilitating the synchronization of files and photos with Google Drive and Google Photos services. The nomenclature "file stream" is attributed to its capability to stream files on demand, thereby avoiding the need to occupy disk space by downloading all files preemptively. Upon installation and login, users can promptly access all previously synced files through Windows Explorer, without the necessity of storing an offline version.

# 🕵️ DriveFS Sleuth

![This is how Bing creator imagined a logo for the DriveFS Sleuth Tool.](https://raw.githubusercontent.com/AmgdGocha/DriveFS-Sleuth/main/assets/DriveFS%20Sleuth%20Logo.jpg)


DriveFS Sleuth is a Python tool that automates investigating Google Drive File Stream disk artifacts, the tool has been developed based on research that has been performed by mounting different scenarios and noting down the changes in the Google Drive File Stream disk artifacts.

## 🚀 DriveFS Sleuth is capable of:
* Parsing the disk artifacts and building a filesystem tree-like structure enumerating the synchronized files along with their respective properties. 
* Detecting synchronized items and items that have been shared with the account under investigation.
* Compiling information on mirroring folders.
* Providing insights into connected device configurations.
* Supports searching functionality to facilitate the investigations.
* Recovering the synced items from the cache. The recovered items can be filtered based on the searching criteria.
* Recovering the cached thumbnails of the synced items if available. The recovered thumbnails can be filtered based on the searching criteria.
* Generating HTML and CSV reports of the analysis results.

For the underlying research, refer to: 
* [(BlackHat Presentation Slides) DriveFS Sleuth — Your Ultimate Google Drive File Stream Investigator!](https://github.com/AmgdGocha/DriveFS-Sleuth/blob/main/assets/DriveFS-Sleuth_Amged-Wageh.pdf)
* [DriveFS Sleuth — Your Ultimate Google Drive File Stream Investigator!](https://amgedwageh.medium.com/drivefs-sleuth-investigating-google-drive-file-streams-disk-artifacts-0b5ea637c980)
* [DriveFS Sleuth — Revealing The Hidden Intelligence](https://amgedwageh.medium.com/drivefs-sleuth-revealing-the-hidden-intelligence-82f043c452e4)
* [DriveFS Sleuth — Recovery Made Possible!](https://amgedwageh.medium.com/drivefs-sleuth-recovery-made-possible-f3847c0b0ac9)

## 🔍 Artifacts Collection Made Easy
For those who are fans of Velociraptor, like myself, here is a Velociraptor offline collector ready to be used for triaging Google Drive File Stream artifacts to investigate them. The collector can be found here https://github.com/AmgdGocha/DriveFS-Sleuth/tree/main/collectors.

You can also use this Kape target to gather the same artifacts: https://github.com/EricZimmerman/KapeFiles/blob/master/Targets/Apps/GoogleDrive_Metadata.tkape

## ⚙️ Installation
DriveFS Sleuth can be easily installed using pip. https://pypi.org/project/drivefs-sleuth/
```commandline
pip install drivefs-sleuth
```
It also can be directly used from the source code by:
1. Clone the repo
  ```commandline
  git clone https://github.com/AmgdGocha/DriveFS-Sleuth.git
  ```
2. Optionally, Inside the downloaded folder, create a new virtual environment
  ```commandline
  python -m venv drivefs_sleuth
  ```
* Activate the virtual environment:
  * On windows:
  ```commandline
  .\drivefs_sleuth\Scripts\activate
  ```
  * On Linux and macOS
  ```commandline
  source drivefs_sleuth/bin/activate
  ```
3. Install Dependencies
```commandline
pip install -r requirements.txt
```

## 🧑‍💻 DriveFS Sleuth Usage
```commandline
usage: DriveFS Sleuth [-h] -o OUTPUT [--accounts ACCOUNTS [ACCOUNTS ...]]
                      [--regex REGEX [REGEX ...]]
                      [-q QUERY_BY_NAME [QUERY_BY_NAME ...]]
                      [--md5 MD5 [MD5 ...]] [--url-id URL_ID [URL_ID ...]]
                      [--search-csv SEARCH_CSV] [--exact]
                      [--dont-list-sub-items] [--csv] [--html]
                      [--recover-from-cache | --recover-search-results]
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
  -o OUTPUT, --output OUTPUT
                        A path to a directory to save the output.
  --accounts ACCOUNTS [ACCOUNTS ...]
                        Specifies account id/s or emails separated by space to be processed, defaults to all the accounts.

Searching Arguments:
  --regex REGEX [REGEX ...]
                        Searches for files or folders by regular expressions. Multiple regex can be passed separated by spaces.
  -q QUERY_BY_NAME [QUERY_BY_NAME ...], --query-by-name QUERY_BY_NAME [QUERY_BY_NAME ...]
                        Searches for files or folders by name. The search will be case insensitive. Multiple file names can be passed separated by spaces.
  --md5 MD5 [MD5 ...]   Searches for files by the MD5 hash. Multiple hashes can be passed separated by spaces.
  --url-id URL_ID [URL_ID ...]
                        Searches for files by the URL ID. Multiple hashes can be passed separated by spaces.
  --search-csv SEARCH_CSV
                        Searches for files or folders that satisfies the searching conditions in the provided CSV file.
  --exact               If selected, only files or folders with exact file names will be returned. The --query_by_name argument has to be passed. Defaults to False.
  --dont-list-sub-items
                        By default, if a folder matches the search criteria, the results will contain all of it's sub-items. This argument suppresses this feature to only return the folder without listing it's sub-items.

Output Formats:
  --csv                 Generates a CSV report. The CSV report will only contain information about the files and folders. Either --csv or --html should be specified.
  --html                Generates an HTML report. The HTML report contains comprehensive information about the analyzed artifacts.  Either --csv or --html should be specified.

Recovery Options:
  --recover-from-cache  Recover the cached items from the content cache.
  --recover-search-results
                        Recover the search results items that are cached.
```
### Automated Investigation
Easily automate the examination of Google Drive File Stream artifacts by providing the tool with the path to the DriveFS triaged folder.

### Targeted Analysis
Utilize the `--accounts` argument to specify the email or account ID of the targeted account, allowing the tool to process specific accounts of interest. Multiple accounts can be specified, separated by spaces. Defaults to all available accounts.

### Flexible Search Functionality
DriveFS Sleuth supports various search functionalities to meet your investigative needs:
* **Regular Expressions:** Use the `--regex` parameter to employ regular expressions for searching. Multiple expressions can be specified separated by spaces.
* **Simple Text Search:** Perform a simple text search using the `[-q|--query-by-name]` optional parameter. Input single or multiple texts separated by spaces. The tool searches for files or folders with names containing the provided text. Toggle the `--exact` parameter for an exact name search.
* **MD5 Search:** Use the `--md5` parameter to search by the MD5 hash of the files. Multiple MD5s can be specified separated by spaces.
* **URL ID:** Use the `--url-id` parameter to search by the URL ID of the item. Multiple MD5s can be specified separated by spaces. _URL ID is the ID of the item when it's being accessed by HTTP requests._

### Customization Options
Tailor the tool's behavior with additional parameters:
* **Listing Control:** Use the `--dont-list-sub-items` parameter to suppress listing sub-items and only display matching folders.
* **Complex Criteria:** Enable a more complex combination of search criteria by providing a CSV file through the `--search-csv parameter`. The CSV file includes case-sensitive headers: `TARGET`, `TYPE`, `CONTAINS`, and `LIST_SUB_ITEMS`.
    * **TARGET:** Holds the searching regex or simple text.
    * **TYPE:** Classifies the search type as either `FILENAME`, `REGEX`, `MD5`, or `urlid`.
    * **CONTAINS:** Use `FALSE` for an exact search or `TRUE` to search for any filename containing the specified target.
    * `LIST_SUB_ITEMS:` Enable or disable the listing of sub-items for matching folders, indicated by `TRUE` or `FALSE`, respectively.

### Recovery From Cache
Drive Sleuth can parse and recover the cached synced items and their thumbnails if available, the recovery path will be under a subdirectory with the account name/email that will be created under the output path passed via the `[-o|--output]` argument. Only the search results will be recovered if the argument `--recover-search-results` is set.

### Output Options
DriveFS Sleuth provides support for two types of outputs:
1. **CSV Files:** Can be specified via the `--csv` argument to instruct DriveFS Sleuth to generate two CSV files. The first CSV file includes a comprehensive list of all processed files, while the second CSV file specifically enumerates files and folders that match the search criteria if provided by the analyst.
2. **HTML Report:** Can be specified via the `--html` argument to instruct DriveFS Sleuth to generate an HTML report summarizing the analysis results.
The reports will be created under the output directory passed via the `[-o|--output]` argument.

### Examples
The following are some examples of the tool usage, change the paths and the searching criteria to match yours.
* Processing a triage and outputting an HTML report.
```commandline
python3 drivefs_sleuth.py C:\triage_path\DriveFS --html -o C:\analysis_results
```
* Processing a triage and outputting a CSV report.
```commandline
python3 drivefs_sleuth.py C:\triage_path\DriveFS --csv -o C:\analysis_results
```
* Processing a triage, searching for all files or folders with filenames containing the word 'DFIR', and outputting both CSV and HTML reports.
```commandline
python3 drivefs_sleuth.py C:\triage_path\DriveFS -q DFIR --html --csv --output C:\analysis_results
```
* Processing a triage, searching for all files or folders with the exact filename 'DFIR', and outputting both CSV and HTML reports.
```commandline
python3 drivefs_sleuth.py C:\triage_path\DriveFS -q DFIR --exact --html --csv --output C:\analysis_results
```
* Processing a triage, searching for all files or folders with filenames that match the regex `*dfir_\d+*`, and outputting an HTML report with listing sub-items suppressed.
```commandline
python3 drivefs_sleuth.py C:\triage_path\DriveFS --regex "*dfir_\d+" --html --dont-list-sub-items -o C:\analysis_results
```
* Processing a triage, searching for files by multiple md5 hashes, and outputting an HTML report.
```commandline
python3 drivefs_sleuth.py C:\triage_path\DriveFS --md5 e03d35c4792f1e2b773c1c03d71d96ef	8018f9c57bb40ed5f42dfac859dd7405 --html -o C:\analysis_results
```
* Processing a triage passing a CSV file that contains the searching criteria, and outputting a CSV report.
```commandline
python3 drivefs_sleuth.py C:\triage_path\DriveFS --search-csv search_conditions.csv --csv --outputo C:\analysis_results
```
* Processing a triage , and recover the cached synced items from the content cache.
```commandline
python3 drivefs_sleuth.py C:\triage_path\DriveFS --search-csv search_conditions.csv --csv --recover-from-cache -o C:\analysis_results
```
* Processing a triage passing a CSV file that contains the searching criteria, outputting a CSV report, and recover the search results from the content cache.
```commandline
python3 drivefs_sleuth.py C:\triage_path\DriveFS --search-csv search_conditions.csv --recover-search-results --csv -o C:\analysis_results
```

# 📰 Featured At:
* [SANS FOR500: Windows Forensic Analysis Course - Feb 21, 2024 Update](https://www.sans.org/blog/whats-new-in-for500-windows-forensic-analysis/)
* [This Week In 4N6 - Week 52 - 2023](https://thisweekin4n6.com/2023/12/24/week-52-2023/)
* [This Week In 4N6 - Week 01 - 2024](https://thisweekin4n6.com/2024/01/07/week-01-2024/)
* [This Week In 4N6 - Week 22 – 2024](https://thisweekin4n6.com/2024/06/02/week-22-2024/)
* [DFIR Diva](https://dfirdiva.com/free-affordable-training-news-monthly-dec-2023-jan-2024)
* [Help Net Security](https://www.helpnetsecurity.com/2024/01/04/drivefs-sleuth-investigating-google-drive-file-stream/)
* [AboutDFIR](https://aboutdfir.com/toolsandartifacts/google-workspace/)
* [Digital Forensics Now Podcast - Episode 9](https://www.youtube.com/live/m_fP7qf3Pok?si=YVaqruW_NlMgpEpg&t=547)
* [Forensic Focus Round-Up - Jan 11, 2024](https://www.forensicfocus.com/news/digital-forensics-round-up-january-11-2024/)

# 🌟 Your Feedback Matters:
I'm eager to hear your thoughts! Share your feedback and suggestions, or report issues on our GitHub repository. Your input is crucial in making DriveFS Sleuth even more robust. Consider starring the repo if you found it useful. 😉
