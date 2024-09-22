import os
import re
import sys
import time
import http
import signal
import shutil
import unicodedata
from bs4 import BeautifulSoup
from requestium import Session
import requests.exceptions
from deep_translator import GoogleTranslator, MyMemoryTranslator, LibreTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

downloads_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "Temporary Archives"
)

# Get the username input from user
username = sys.argv[1]

# Create options object and disable logging of warning messages
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--disable-logging")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-ssl-false-start")
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--allow-running-insecure-content")

# Add experimental options to download zip files
chrome_options.add_experimental_option(
    "prefs",
    {
        "download.default_directory": downloads_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    },
)

chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])


# # Create webdriver object and pass options to it
# chrome_driver = webdriver.Chrome(
#     ChromeDriverManager().install(), options=chrome_options
# )

chrome_driver = webdriver.Chrome(options=chrome_options)

latest_dir = ""


def cleanup(signum, frame):
    global latest_dir
    if latest_dir and os.path.isdir(latest_dir):
        shutil.rmtree(latest_dir)

# define a custom expected condition to check if the first img element has loaded
def wait_for_image(driver):
    return driver.execute_script("return document.images[0].complete")

def is_english(text):
    # Check if text contains only English characters (using regular expressions)
    return bool(re.match('^[a-zA-Z0-9]+$', text))

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

print(f"\nParsing File Table For [REDACTED] User : {username}\n")

# Initialize the data arrays
links = []
filenames = []
position_numbers = []
pure_filenames = []
titles = []
genres = []
restrictions = []
modified_dates = []

# Start on page 1
offset = 0
url = f"https://[REDACTED].com/upld-index.php?uname={username}&dorder_by=time_disp.DESC&doffset={offset}"

# Navigate to the page
chrome_driver.get(url)

# Wait for the checkboxes to be loaded
checkboxes = WebDriverWait(chrome_driver, 10).until(
    EC.presence_of_all_elements_located((By.XPATH, "//input[@name='restriction[]']"))
)

# Check all checkboxes
for checkbox in checkboxes:
    checkbox.click()

# Submit the form
submit_button = chrome_driver.find_element(By.XPATH, "//button[@type='submit']")
submit_button.click()

# Wait for the page to load after submitting the form
WebDriverWait(chrome_driver, 10).until(
    EC.presence_of_element_located((By.TAG_NAME, "h1"))
)

# Wait for 5 seconds to ensure that the page has fully loaded
time.sleep(5)


while True:

    chrome_driver.get(url)

    # Get the webpage source and parse with BeautifulSoup
    page_source = chrome_driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    # Find the table in the parsed HTML
    table = soup.find("table")

    # Parse the table rows and extract the data
    rows = table.find_all("tr", class_=lambda x: x == "white" or x == "gray")

    for row in rows:
        tds = row.select("td")
        position_numbers.append(unicodedata.normalize("NFKD", tds[0].text))
        links.append(tds[1].find("a").get("href"))
        filenames.append(unicodedata.normalize("NFKD", tds[1].find("a").text))
        titles.append(unicodedata.normalize("NFKD", tds[2].text))
        genres.append(unicodedata.normalize("NFKD", tds[8].text))
        restrictions.append(unicodedata.normalize("NFKD", tds[9].text))
        modified_dates.append(unicodedata.normalize("NFKD", tds[7].text))

    # Look for the "Next 15 file(s) ->" link to see if there is another page
    next_link = soup.find("a", string="Next 15 file(s) ->")
    if next_link is None:
        # If the "Next 15 file(s) ->" link is not found, we have reached the last page
        break
    else:
        # If the "Next 15 file(s) ->" link is found, go to the next page
        offset += 15
        url = f"https://[REDACTED].com/upld-index.php?uname={username}&dorder_by=time_disp.DESC&doffset={offset}"

pure_filenames = [filename.split(".")[0] for filename in filenames]


print(f"\nParsing Complete. Downloading Files From [REDACTED] by {username}\n")


# Print the extracted data
# print("Links:", links)

# print("Filenames:", filenames)
# print("Pure Filenames:", pure_filenames)
# print("Titles:", titles)
# print("Genres:", genres)
# print("Restrictions:", restrictions)
# print("Modified Dates:", modified_dates)

# print(f"Total number of links: {len(links)}")
# print(f"Total number of filenames: {len(filenames)}")
# print("Total number of Pure Filenames:", {len(pure_filenames)})
# print(f"Total number of titles: {len(titles)}")
# print(f"Total number of genres: {len(genres)}")
# print(f"Total number of restrictions: {len(restrictions)}")
# print(f"Total number of dates: {len(modified_dates)}")


# Visit the URL for each link in the links array

requests_session = Session(driver=chrome_driver)
requests_session.transfer_driver_cookies_to_session()

lastfile = 0

try:
    for i, link in enumerate(links):

        lastfile = i
        
        # if i != 237:
        #     print("Skipping")
        #     continue

        url = f"https://[REDACTED].com{link}"

        # print("URL:", url)

        chrome_driver.get(url)

        # Find the href link associated with the filename
        filename = filenames[links.index(link)]
        wait = WebDriverWait(
            chrome_driver, 10
        )  # Wait for up to 10 seconds for the element to be found
        href_link = wait.until(
            EC.presence_of_element_located((By.XPATH, f"//a[text()='{filename}']"))
        ).get_attribute("href")

        dir_path = None

        # Check if the filename ends with .htm
        if filename.endswith((".htm", ".pdf")):

            # Create the directory if it doesn't exist
            dir_path = (
                f"./Downloads/{username}/Texts/{pure_filenames[links.index(link)]}/"
            )
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                latest_dir = dir_path
            else:
                print(
                    f"Skipping {pure_filenames[links.index(link)]} ({i+1}/{len(links)})"
                )
                continue
            
            if filename.endswith(".htm"):
                    
                # Visit the href link and print the response
                chrome_driver.get(href_link)

                # Parse the HTML content using BeautifulSoup
                soup = BeautifulSoup(chrome_driver.page_source, "html.parser")

                # Remove any script and style tags
                for script in soup(["script", "style"]):
                    script.extract()

                # Save the HTML file
                with open(f"{dir_path}/{pure_filenames[links.index(link)]}.htm", "wb") as f:
                    f.write(chrome_driver.page_source.encode("utf-8"))

                # Get the text from the HTML
                text = soup.get_text()

                # Save the text as a file with the same name as the original filename
                with open(
                    f"{dir_path}/{pure_filenames[links.index(link)]}.txt",
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(text)

            if filename.endswith(".pdf"):

                # Get the pdf URL
                pdf_link = href_link
                print(f"Link: {pdf_link}")
                file_path = f"{dir_path}/{pure_filenames[links.index(link)]}.pdf"

                # Download the pdf file and save it to the directory
                response = requests_session.get(pdf_link)
                with open(file_path, "wb") as f:
                    f.write(response.content)

                while not os.path.exists(file_path):  # Wait for the file to be downloaded
                    time.sleep(2)      

            time.sleep(2)          
                

        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):

            # Create the directory if it doesn't exist
            dir_path = (
                f"./Downloads/{username}/Images/{pure_filenames[links.index(link)]}/"
            )
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                latest_dir = dir_path
            else:
                print(
                    f"Skipping {pure_filenames[links.index(link)]} ({i+1}/{len(links)})"
                )
                continue

            max_retries = 10
            retry_delay = 480

            wait = WebDriverWait(chrome_driver, 60)
            chrome_driver.get(href_link)

            for k in range(max_retries):
                try:
                    
                    # Visit the href link and print the response
                    chrome_driver.get(href_link)
                    requests_session = Session(driver=chrome_driver)
                    requests_session.transfer_driver_cookies_to_session()
                    
                    # Wait for the image to load
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "img")))
                    wait.until(wait_for_image)

                    img_tag = chrome_driver.find_element(By.TAG_NAME, "img")

                    # do something with the img element
                    # print("Image loaded successfully!")

                    image_url = img_tag.get_attribute("src")

                    #print(f"Image URL FOUND: {image_url}")

                    requests_session.transfer_driver_cookies_to_session()
                    response = requests_session.get(image_url, stream=True)
                    response.raise_for_status()

                    with open(os.path.join(dir_path, filename), "wb") as f:
                        response.raw.decode_content = True
                        shutil.copyfileobj(response.raw, f)
                    break

                except (requests.exceptions.RequestException, http.client.RemoteDisconnected, TimeoutException) as e:
                    print(f"Failed to download image, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
            else:
                print(f"Could not download image after {max_retries} retries.")
                cleanup(None, None)
                continue
                        
            time.sleep(1)

        if filename.endswith((".zip", ".tar", ".tar.gz", ".tar.bz2", ".7z")):
            # Download archive files
            dir_path = (
                f"./Downloads/{username}/Archives/{pure_filenames[links.index(link)]}/"
            )
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                latest_dir = dir_path
            else:
                print(
                    f"Skipping {pure_filenames[links.index(link)]} ({i+1}/{len(links)})"
                )
                continue

            file_path = os.path.join(dir_path, f"{filename}")

            # Get the archive URL
            archive_link = href_link
            # print(f"Link: {archive_link}")

            # Download the archive file and save it to the directory
            response = requests_session.get(archive_link)
            with open(file_path, "wb") as f:
                f.write(response.content)

            while not os.path.exists(file_path):  # Wait for the file to be downloaded
                time.sleep(2)

        """ [ARCHIVE DOWNLOADER w/o USING REQUESTIUM]  
            
            if filename.endswith((".zip", ".tar", ".tar.gz", ".tar.bz2", ".7z")):
                # Download archive files
                dir_path = f"./Downloads/{username}/Archives/{pure_filenames[links.index(link)]}/"
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                else:
                    print(f"Skipping {pure_filenames[links.index(link)]} ({i+1}/{len(links)})")
                    continue

                file_path = os.path.join(downloads_dir, f"{filename}")

                # Get the archive URL
                archive_link = href_link
                # print(f"Link: {archive_link}")

                # Download the archive file and save it to the directory
                download_button = chrome_driver.find_element(By.XPATH, f"//a[contains(@href, '{filename}')]")
                download_button.click()

                while not os.path.exists(file_path): # Wait for the file to be downloaded
                    time.sleep(2)

                shutil.move(file_path, dir_path) # Move the file to the destination folder
        """

        # Add the details to the Details.txt file
        with open(f"{dir_path}/Details.txt", "w", encoding="utf-8") as f:
            f.write(f"File Position: {position_numbers[links.index(link)]}\n\n")
            f.write(f"File Name: {filenames[links.index(link)]}\n\n")
            f.write(f"Pure File Names: {pure_filenames[links.index(link)]}\n\n")
            f.write(f"Title: {titles[links.index(link)]}\n\n")

            # Translate the title to English if it's not already in English
            title = titles[links.index(link)]

            if not is_english(title):
                try:
                    title_en = GoogleTranslator(source="auto", target="en").translate(title)
                except:
                    try:
                        title_en = MyMemoryTranslator(source="auto", target="en").translate(
                            title
                        )
                    except:
                        title_en = LibreTranslator(source="auto", target="en").translate(
                            title
                        )
            else:
                title_en = title

            f.write(f"English Title: {title_en.title()}\n\n")

            f.write(f"Genre: {genres[links.index(link)]}\n\n")
            f.write(f"Restrictions: {restrictions[links.index(link)]}\n\n")
            f.write(f"Modification Date: {modified_dates[links.index(link)]}\n\n")
            f.write(f"Link: {'https://[REDACTED].com'+link}\n\n")

        print(f"Saved {pure_filenames[links.index(link)]} ({i+1}/{len(links)})")

    # Close the driver
    chrome_driver.quit()

except Exception as e:
    print("Error:", e)
    print(f"Potential Error ; Filetype Not Supported: {filenames[lastfile]}")
    cleanup(None, None)
