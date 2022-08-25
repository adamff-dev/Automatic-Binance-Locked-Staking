import os
import platform
import json
import requests
import time
import re
from datetime import timedelta
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchWindowException

# Globals
global driver
global assetName
global assetPeriod

# Constants
# Regex
REGEX_ASSET = "\w{3,} (15|30|60|90|120)"
# Elements
SEARCH_BAR_ID = "savings-search-coin"
ASSET_TITLE_CLASS = "css-1onbf4e"
STAKE_BTN_ID = "pos-stake"
MAX_BTN_CLASS = "css-joha13"
AUTO_STAKE_SWITCH_CLASS = "css-1bbf0ma"
ACCEPT_TERMS_XPATH = "//div[4]/div/div[4]/label/div"
MODAL_TITLE_CLASS = "modal-title"
CHECKBOXES_autoStaking_CLASS = "css-pf8gn9"
ACCEPT_autoStaking_BTN_CLASS = "css-d1jly6"
CONFIRM_BTN_ID = "pos-confirm"
LOCK_AMO_CLASS = "css-16fg16t"
AVAILABLE_AMO_CLASS = "css-87q6r1"
ACCEPT_COOKIES_BTN_ID = "onetrust-accept-btn-handler"
LABEL_HELPER_CLASS = "bn-input-helper-text"
# URLs
API_URL = "https://www.binance.com/gateway-api/v1/friendly/pos/union?pageSize=200&pageIndex=1&status=ALL"
LOGIN_URL = "https://accounts.binance.com/es/login"
POS_URL = "https://www.binance.com/es/pos"
POST_LOGIN_URL = "https://www.binance.com/es/my/dashboard"


def scrollAndClick(element):
    driver.execute_script("arguments[0].scrollIntoView();", element)
    element.click()


def waitForElement(strategy, locator, timeout):
    if timeout == None:
        timeout = 20
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((strategy, locator)))


def waitAndClick(strategy, locator, timeout):
    waitForElement(strategy, locator, timeout).click()


def searchAsset():
    while True:
        driver.refresh()

        searchBar = driver.find_element(By.ID, SEARCH_BAR_ID)

        searchBar.send_keys(assetName)  # write asset name on search bar

        # wait for the asset to show up
        while len(driver.find_elements(By.CLASS_NAME, ASSET_TITLE_CLASS)) != 1:
            time.sleep(0.2)
            len(driver.find_elements(By.CLASS_NAME, ASSET_TITLE_CLASS))

        # select period (days)
        driver.find_element(
            By.XPATH, '//button[contains(text(), ' + str(assetPeriod) + ')]').click()

        time.sleep(0.1)

        if driver.find_elements(By.ID, STAKE_BTN_ID) == 0:
            writeToLog("Asset sold out. Retrying…")
            continue
        else:
            print("  Asset available")
            break


def compareLockAndAvailableAmount():
    """Checks if lock amount equals available amount"""

    lockAmount = driver.find_element(
        By.CLASS_NAME, LOCK_AMO_CLASS).get_attribute("value")
    availableAmount = driver.find_element(
        By.CLASS_NAME, AVAILABLE_AMO_CLASS).get_attribute("innerText").split()[-2].rstrip("0")

    if lockAmount != availableAmount:
        writeToLog(
            "Lock amount (" + lockAmount + ") and available amount (" + availableAmount + ") are not matching. Retrying…")
        return False

    return True


def autoStakingAcceptTerms():
    """Accepts terms of auto stake and accepts subscription"""

    waitForElement(By.CLASS_NAME, MODAL_TITLE_CLASS, None)
    checkboxes = driver.find_elements(
        By.CLASS_NAME, CHECKBOXES_autoStaking_CLASS)
    for checkbox in checkboxes:
        checkbox.click()
    driver.find_element(By.CLASS_NAME, ACCEPT_autoStaking_BTN_CLASS).click()

def acceptCookies():
    try:
        waitAndClick(By.ID, ACCEPT_COOKIES_BTN_ID, 15)
        return True
    except:
        return False

def startStaking(autoStaking):
    while True:
        searchAsset()
        print("  Starting subscription…")

        try:
            time.sleep(0.3)

            # open stake panel
            driver.find_element(By.ID, STAKE_BTN_ID).click()

            # select max quantity
            waitAndClick(By.CLASS_NAME, MAX_BTN_CLASS)

            time.sleep(0.2)

            # if there's an error, in helper labal, write it to the log
            if len(driver.find_elements(By.CLASS_NAME, LABEL_HELPER_CLASS)) != 0:
                writeToLog(driver.find_element(By.CLASS_NAME, LABEL_HELPER_CLASS).get_attribute(
                    "innerText"))
                return

            if not compareLockAndAvailableAmount():
                continue

            if not autoStaking:
                scrollAndClick(driver.find_element(
                    By.CLASS_NAME, AUTO_STAKE_SWITCH_CLASS))

            # accept terms and conditions
            driver.find_element(By.XPATH, ACCEPT_TERMS_XPATH).click()

            time.sleep(0.2)

            # driver.find_element(By.ID, CONFIRM_BTN_ID).click()  # confirm

            if autoStaking:
                autoStakingAcceptTerms()

            writeToLog("Subscription completed successfully!")

            break

        except Exception as e:
            writeToLog("Something went wrong.\nException:\n" + e)
            print("  Retrying…")


def writeToLog(message):
    """Writes a message to the log and prints it"""

    now = datetime.now()
    dateTime = now.strftime("%d/%m/%Y, %H:%M:%S")

    print("  " + message)

    f = open("abs_log.txt", "a")
    f.write(f"{assetName} {assetPeriod} days\t{dateTime}\t{message}\n")
    f.close()


def initWebDriver():
    print(" --------------------------------------------")
    print("  Starting web driver…")
    print(" --------------------------------------------")

    while True:
        try:
            driver = webdriver.Firefox()
            break
        except:
            try:
                driver = webdriver.Chrome()
                break
            except:
                try:
                    driver = webdriver.Safari()
                    break
                except:
                    input('''
  Error: web driver not found.
  Please, download the web driver
  https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
  Press enter when you are done
  >''')

    driver.maximize_window()

    return driver


def openLoginAndPos():
    """Opens the login page and redirects to POS page after user logs-in"""

    openWebsite(LOGIN_URL)

    print('''
 --------------------------------------------
  Please, log into your Binance account
 --------------------------------------------''')
    
    cookiesAccepted = acceptCookies()

    while driver.current_url != POST_LOGIN_URL:
        time.sleep(0.2)

    openWebsite(POS_URL)
    
    if not cookiesAccepted:
        acceptCookies()


def openWebsite(website):
    while True:
        try:
            driver.get(website)
            break
        except:
            showNetworkError()
            continue


def showNetworkError():
    input('''
  Error: we weren't able to open the website
  Please, check your internet connection and
  press enter to retry
  >''')


def getAssetAvailability(checkingInterval):
    while True:
        # Request data from binance
        try:
            response = json.loads(requests.get(API_URL).text)["data"]
        except:
            # Couldn't get json data. Sleep and retry
            time.sleep(1000)
            continue

        # Unpacking results
        avaliableAssets = unpackResponse(response)

        for item in avaliableAssets:
            if assetName == item["asset"] and assetPeriod == item["duration"]:
                print(" Asset found:")
                print(
                    f" {item['asset']} for {item['duration']} days / {item['APY']}% APY")
                print("--------------------------------------------")
                return True

        # time loop waiting
        time.sleep(timedelta(seconds=checkingInterval).total_seconds())


def unpackResponse(response):
    """Unpacks API response"""

    avaliableAssets = []

    for item in response:
        for asset in item["projects"]:
            if not asset["sellOut"]:
                # Asset available, adding a dictionary with asset name, duration and APY to the result list
                avaliableAssets.append({
                    "asset": asset["asset"],
                    "duration": asset["duration"],
                    "APY": str(round(float(asset["config"]["annualInterestRate"]) * 100, 2))
                })

    return avaliableAssets


def getYesNo(condition):
    return "yes" if condition else "no"


def showSessionInfo(checkingInterval, autoStaking, shutdown):
    print("""
 --------------------------------------------
       Automatic Binance Locked Staking
 --------------------------------------------
  Searching for…
  Asset: %s
  Period: %s days
 --------------------------------------------
  Checking every %s seconds
  Auto-Staking: %s
  Shutdown after subscription: %s
 --------------------------------------------
""" % (assetName,
        assetPeriod,
        str(checkingInterval),
        getYesNo(autoStaking),
        getYesNo(shutdown)))


def end(shutdown):
    """Shutdowns the computer if specified"""

    driver.close()
    print("Bye!")
    osName = platform.system()

    if shutdown:
        if osName == 'Linux':
            os.system('systemctl poweroff')
        elif osName == 'Darwin':
            os.system('shutdown -h now')
        elif osName == 'Windows':
            os.system('shutdown -s -t 0')

    exit()


def main():
    global driver
    global assetName
    global assetPeriod

    print("""
 --------------------------------------------
       Automatic Binance Locked Staking
 --------------------------------------------
  Please, type the asset and period you
  want to subscribe.

  Examples: 'ADA 120', 'DOT 30'…
 --------------------------------------------""")

    while True:
        assetNamePeriod = input("  >")

        if re.search(REGEX_ASSET, assetNamePeriod):
            assetName, assetPeriod = assetNamePeriod.split(" ")
            assetName = assetName.upper()
            break
        else:
            print("\n  Wrong asset-period format")
            print("  Check the examples and try again\n")

    while True:
        print(" --------------------------------------------")
        print("  Type checking interval (in seconds)")
        print(" --------------------------------------------")
        checkingInterval = input("  >")

        if checkingInterval.isnumeric():
            checkingInterval = int(checkingInterval)
            if checkingInterval >= 0:
                break
        else:
            print("\n  Wrong checking interval\n")

    print(" --------------------------------------------")
    print("  Do you want to enable Auto-Staking? (y/n)")
    print(" --------------------------------------------")
    autoStaking = True if input("  >").lower() == 'y' else False

    print(" --------------------------------------------")
    print("  Do you want to shutdown your computer")
    print("  after subscripion? (y/n)")
    print(" --------------------------------------------")
    shutdown = True if input("  >").lower() == 'y' else False

    driver = initWebDriver()

    openLoginAndPos()

    showSessionInfo(checkingInterval, autoStaking, shutdown)

    if getAssetAvailability(checkingInterval):
        startStaking(autoStaking)

    end(shutdown)


if __name__ == "__main__":
    try:
        main()
    except NoSuchWindowException:
        print("  Error: web driver was closed!")
    finally:
        exit()
