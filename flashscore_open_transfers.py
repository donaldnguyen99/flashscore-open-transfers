import webbrowser
import calendar
import datetime
import os
import re
import zipfile
import sys
from sys import platform
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service


# To run this script, you need to have Python 3 installed.
# You also need to install the following packages:
#   requests
#   selenium


# To detect Chrome automatically (32-bit version will be detected if both 
# 32-bit and 64-bit are installed), use 
#   'CHROME_VERSION': None 
#   'CHROME_PATH': None
DEFAULT_PARAMS = {
    'ASK_FOR_DAY': False,
    'CHROME_VERSION': '115.0.5790.102',
    'CHROME_PATH': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'DEPARTING_ONLY': True,
    'LOOP': False,
}

def show_exception_and_exit(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    input("Press Enter to exit.\n")
    sys.exit(-1)

def correct_year(year, month, day, now=datetime.datetime.now()):
    # if day and month are after now, set year to previous year
    if month > now.month:
        year = year - 1
    elif month == now.month and day > now.day:
        year = year - 1
    else:
        year = year
    return year

def get_user_input(request_day=DEFAULT_PARAMS['ASK_FOR_DAY']):
    
    # Request user input for the team transfer page URL
    #   Example
    # url = 'https://www.flashscore.com/team/medyk-konin/2couPXCh/transfers/'
    url = input('Enter the team transfers page URL: ')
    req = requests.get(url)
    while req.status_code != 200:
        print('Page Not Found, or Invalid URL')
        url = input('Enter the team transfers page URL: ')
        req = requests.get(url)

    now = datetime.datetime.now()
    year = int(input(f'Select transfers on and after year (up to {now.year}): '))
    while year > now.year:
        year = int(input(f'Enter a valid year (up to {now.year}): '))

    # Request user input for the month
    max_month = 12 if year < now.year else now.month
    month = int(input(f'Select transfers on and after month (1 - {max_month}): '))
    while month not in range(1, max_month + 1):
        month = int(input(f'Enter a valid month (1 - {max_month}): '))

    # Request user input for the day
    day = 1
    if not request_day:
        print(f'    *If you want to select transfers on and after a specific day,')
        print(f'     set ASK_FOR_DAY to True in the .py script*\n')
        print(f'Your selection: {calendar.month_name[month]} {day}, {year}')
    else:
        max_day = now.day if year == now.year and month == now.month else calendar.monthrange(year, month)[1]
        if max_day > 1: 
            day = int(input('Enter the day ' + f'(1 - {max_day}): '))
            while day not in range(1, max_day + 1):
                days_in_month = calendar.monthrange(year, month)[1]
                if day > days_in_month:
                    print(f'Invalid day for {calendar.month_name[month]} of {year}')
                day = int(input(f'Enter a valid day (1 - {max_day}): '))
    
    try:
        input('Press Enter to continue (Ctrl+C to exit) ... ')
    except KeyboardInterrupt:
        print('\nExiting...')
        exit()
    return url, year, month, day

def open_pages(urls):
    for url in urls:
        webbrowser.open(url)


#
# Programmatically detect the version of the Chrome web browser installed on the PC.
# Compatible with Windows, Mac, Linux.
# Written in Python.
# Uses native OS detection. Does not require Selenium nor the Chrome web driver.
#

def extract_version_registry(output):
    try:
        google_version = ''
        for letter in output[output.rindex('DisplayVersion    REG_SZ') + 24:]:
            if letter != '\n':
                google_version += letter
            else:
                break
        return(google_version.strip())
    except TypeError:
        return

def extract_version_install_path(output):
    try: 
        install_path = ''
        start = output.rindex('InstallLocation    REG_SZ')
        end = output.rindex('DisplayIcon')
        for letter in output[start + 25: end + 1]:
            if letter != '\n':
                install_path += letter
            else:
                break
        return(install_path.strip())
    except TypeError:
        return

def extract_version_folder():
    # Check if the Chrome folder exists in the x32 or x64 Program Files folders.
    for i in range(2):
        path = 'C:\\Program Files' + (' (x86)' if i else '') +'\\Google\\Chrome\\Application'
        if os.path.isdir(path):
            paths = [f.path for f in os.scandir(path) if f.is_dir()]
            for path in paths:
                filename = os.path.basename(path)
                pattern = '\d+\.\d+\.\d+\.\d+'
                match = re.search(pattern, filename)
                if match and match.group():
                    # Found a Chrome version.
                    return match.group(0), path

    return None

def get_chrome_version_and_path():
    version = None
    install_path = None

    if DEFAULT_PARAMS['CHROME_VERSION'] and DEFAULT_PARAMS['CHROME_PATH']:
        return DEFAULT_PARAMS['CHROME_VERSION'], DEFAULT_PARAMS['CHROME_PATH']

    try:
        if platform == "linux" or platform == "linux2":
            # linux
            install_path = "/usr/bin/google-chrome"
        elif platform == "darwin":
            # OS X
            install_path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"
        elif platform == "win32":
            # Windows...
            try:
                # Try registry key.
                stream = os.popen('reg query "HKLM\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Google Chrome"')
                output = stream.read()
                version = extract_version_registry(output)
                full_install_path = extract_version_install_path(output)
            except Exception as ex:
                # Try folder path.
                version, full_install_path = extract_version_folder()
    except Exception as ex:
        print(ex)
    version = os.popen(f"{install_path} --version").read().strip('Google Chrome ').strip() if install_path else version

    return version, full_install_path

def get_chrome_driver():
    chrome_version, chrome_path = get_chrome_version_and_path()
    chrome_architecture = '32' if 'x86' in chrome_path else '64'
    chrome_milestone = chrome_version.split('.')[0]
    print(f'Your Google Chrome version: {chrome_version}')
    chrome_driver_file = 'chromedriver.exe'
    chrome_driver_path = os.path.join(os.getcwd(), chrome_driver_file)
    chrome_driver_exists = os.path.isfile(chrome_driver_path)
    print(f'External Chrome driver exists? {chrome_driver_exists}')
    chrome_driver_compatible = False
    if chrome_driver_exists:
        chrome_driver_version = os.popen(f'\"{chrome_driver_path}\" --version').read().split(' ')[1]
        chrome_driver_compatible = chrome_version.split('.')[:3] == chrome_driver_version.split('.')[:3]
        print(f'Existing Chrome driver path: {os.path.join(chrome_driver_path, chrome_driver_file)}')
        print(f'Existing Chrome driver version: {chrome_driver_version}')
        print(f'Existing Chrome driver compatible? {chrome_driver_compatible}')
        print()

    if not chrome_driver_exists or not chrome_driver_compatible:
        # Downloads the chromedriver.exe file from the links 
        # provided by the Chrome for Testing project:
        # https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json
        # and places it in the same directory as this script.
        chrome_for_testing_url = 'https://googlechromelabs.github.io/chrome-for-testing/'
        chrome_for_testing_json_endpoint = 'latest-versions-per-milestone-with-downloads.json'
        chrome_for_testing = requests.get(
            chrome_for_testing_url + chrome_for_testing_json_endpoint).json()
        chrome_driver_downloads = chrome_for_testing['milestones'][chrome_milestone]['downloads']['chromedriver']
        chrome_driver_zip_url = None
        for download in chrome_driver_downloads:
            if download['platform'] == 'win' + chrome_architecture:
                chrome_driver_zip_url = download['url']
                break
        # Download, replacing the existing chromedriver.exe if it exists.
        print(f'Downloading {"latest " if chrome_driver_exists else ""}Chrome driver...')
        if chrome_driver_exists: os.remove(chrome_driver_path)
        chrome_driver_zip = requests.get(chrome_driver_zip_url)
        chrome_driver_zip_folder = f'chromedriver-win{chrome_architecture}'
        if os.path.isdir(chrome_driver_zip_folder):
            os.rename(chrome_driver_zip_folder, chrome_driver_zip_folder + '_old')
        with open(chrome_driver_zip_folder + '.zip', 'wb') as f:
            f.write(chrome_driver_zip.content)
        with zipfile.ZipFile(chrome_driver_zip_folder + '.zip', 'r') as zip_ref:
            zip_ref.extract(chrome_driver_zip_folder + '/chromedriver.exe', os.getcwd())
        os.rename(chrome_driver_zip_folder + '/chromedriver.exe', 'chromedriver.exe')
        os.remove(chrome_driver_zip_folder + '.zip')
        os.removedirs(chrome_driver_zip_folder)
        if os.path.isdir(chrome_driver_zip_folder + '_old'):
            os.removedirs(chrome_driver_zip_folder + '_old')

        print('Chrome driver downloaded.')
        chrome_driver_compatible = True
    
    return os.path.isfile(chrome_driver_path), chrome_driver_path

def main():
    
    sys.excepthook = show_exception_and_exit

    print('\nStarting... (Ctrl+C anytime to quit)\n')
    chrome_driver_exists, chrome_driver_path = get_chrome_driver()
    service = Service(executable_path=chrome_driver_path)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)

    
    # Example
    # url = 'https://www.flashscore.com/team/medyk-konin/2couPXCh/transfers/'
    # year = 2023
    # month = 6
    # day = 29

    while True:
        try:
            url, year, month, day = get_user_input()
            earliest_date_included = datetime.datetime(year, month, day)


            print('\nSearching for transfers...')
            driver.get(url)
            driver.find_element(By.ID, 'onetrust-accept-btn-handler').click()
            time.sleep(3)
            while True:
                try:
                    driver.find_element(By.CSS_SELECTOR, 'div.transferTab__more > a').click()
                    time.sleep(0.2)
                except Exception as e:
                    break


            elements = driver.find_elements(By.CSS_SELECTOR, 'div.transferTab__row.transferTab__row--team')[1:]
            print(f'Found {len(elements)} total transfers')
            print(f'Selecting transfers on and after {calendar.month_name[month]} {day}, {year}...\n')
            urls = []
            players = []
            for element in elements:
                date_text = element.find_element(By.CSS_SELECTOR, 'div.transferTab__date').text
                date = datetime.datetime.strptime(date_text, '%d.%m.%Y')
                departing = element.find_element(By.CSS_SELECTOR, 'div.transferTab__team--to > svg.arrow').get_attribute('class')
                isDeparting = 'transferTab__typeIcon--out' in departing.split(' ')
                if date >= earliest_date_included and (not DEFAULT_PARAMS['DEPARTING_ONLY'] or isDeparting):
                    name_ele = element.find_element(By.CSS_SELECTOR, 'div.transferTab__player > div.transferTab__teamName > a')
                    players.append(f'{date.strftime("%d.%m.%Y")} - {name_ele.text}')
                    urls.append(name_ele.get_attribute('href'))
            for player in players:
                print(player)
            print(f'\nFound {len(urls)} {"departing " if DEFAULT_PARAMS["DEPARTING_ONLY"] else ""}transfers on and after {calendar.month_name[month]} {day}, {year}\n')

            open_pages(urls)
        except KeyboardInterrupt as e:
            print('\nExiting...')
            driver.quit()
            break
        if not DEFAULT_PARAMS['LOOP']:
            driver.quit()
            break

if __name__ == '__main__':
    main()