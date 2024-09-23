# GSUP-File-Downloader
A personal file downloader for the website [REDACTED]. I might unredact the website name someday for public use. This Python script automates the process of downloading files from a specific user page on a website. It utilizes Selenium for web automation, BeautifulSoup for parsing HTML, and various translation libraries to handle non-English titles.

## Features

- Automatically checks filter boxes using Selenium.
- Downloads various file types (HTML, PDF, images, archives).
- Creates a structured directory for downloaded files.
- Checks directories for validating file & folder names.
- Translates non-English titles to English.
- Cleans up temporary directories after execution.
- Creates a Details.txt file next to the download for information retention.

## Prerequisites

- Python 3.x
- Chrome WebDriver (make sure it's in your PATH)

## Installation

1. Clone this repository

2. Next, install the required packages with:
   ```bash
   pip install -r requirements.txt

## Usage

To run the script, execute it from the command line with the username as an argument:
   ```bash
   python GSUP-dl.py <username>
   ```
Replace <username> with the username you want to download files for.

## Important Notes

Make sure to replace the [REDACTED] placeholder in the code URL with the actual website domain. (IYKYK)

## License

This project is licensed under the GPL License. See the LICENSE file for details.
