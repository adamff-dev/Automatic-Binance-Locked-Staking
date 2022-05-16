import os
import json
import requests
import time
import ctypes
from datetime import timedelta
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

# Constants
SEARCH_BAR_ID = "savings-search-coin"
STAKE_BTN_ID = "pos-stake"
MAX_BTN_CLASS = "css-joha13"
ACCEPT_TERMS_XPATH = "//label[@class='css-bfef9a']"
CONFIRM_BTN_ID = "pos-confirm"
LOCK_AMO_CLASS = "css-16fg16t"
AVAILABLE_AMO_CLASS = "css-87q6r1"
ACCEPT_COOKIES_BTN_ID = "onetrust-accept-btn-handler"
LABEL_HELPER_CLASS = "bn-input-helper-text"
API_URL = "https://www.binance.com/gateway-api/v1/friendly/pos/union?pageSize=200&pageIndex=1&status=ALL"


def startStaking(driver, assetName, assetPeriod):
    while True:
        driver.refresh()

        time.sleep(1.5)

        searchBar = driver.find_element(By.ID, SEARCH_BAR_ID)

        searchBar.send_keys(assetName)  # write asset name on search bar

        time.sleep(2)

        # select period (days)
        driver.find_element(
            By.XPATH, '//button[contains(text(), ' + str(assetPeriod) + ')]').click()

        time.sleep(0.1)

        if driver.find_elements(By.ID, STAKE_BTN_ID) == 0:
            writeToLog("Asset sold out. Retrying...",
                       assetName, assetPeriod, True)
            continue
        else:
            print("Asset available")
            break

    print("Starting subscription...")

    try:
        time.sleep(0.3)

        driver.find_element(By.ID, STAKE_BTN_ID).click()  # open stake panel

        time.sleep(1)

        # select max quantity
        driver.find_element(By.CLASS_NAME, MAX_BTN_CLASS).click()

        time.sleep(0.2)

        if len(driver.find_elements(By.CLASS_NAME, LABEL_HELPER_CLASS)) != 0:
            writeToLog(driver.find_element(By.CLASS_NAME, LABEL_HELPER_CLASS).get_attribute(
            "innerText"), assetName, assetPeriod)
            return

        lockAmount = driver.find_element(
            By.CLASS_NAME, LOCK_AMO_CLASS).get_attribute("value")
        availableAmount = driver.find_element(
            By.CLASS_NAME, AVAILABLE_AMO_CLASS).get_attribute("innerText").split()[-2].rstrip("0")

        if lockAmount != availableAmount:
            writeToLog(
                "Lock amount (" + lockAmount + ") and available amount (" + availableAmount + ") are not matching. Retrying...", assetName, assetPeriod)
            startStaking(driver, assetName, assetPeriod)

        # accept terms and conditions
        driver.find_element(By.XPATH, ACCEPT_TERMS_XPATH).click()

        time.sleep(0.2)

        driver.find_element(By.ID, CONFIRM_BTN_ID).click()  # confirm

        writeToLog("Subscription completed successfully!",
                   assetName, assetPeriod)

    except Exception as e:
        print(e)
        writeToLog("Something went wrong. Retrying...", assetName, assetPeriod)
        startStaking(driver, assetName, assetPeriod)


def writeToLog(text, assetName, assetPeriod):
    now = datetime.now()
    dateTime = now.strftime("%d/%m/%Y, %H:%M:%S")

    print(text)

    f = open("abs_log.txt", "a")
    f.write(assetName + assetPeriod + "\t" + dateTime + "\t" + text + "\n")
    f.close()


def initWebDriver():
    print("--------------------------------------------")
    print(" Starting web driver...")
    print("--------------------------------------------")

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
                    print("Error: web driver not found.")
                    print(
                        "Please, download the web driver and place it in the same forlder of this script")
                    print(
                        "https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/")
                    print("Press enter when you are done")
                    input(">")

    driver.maximize_window()

    return driver


def openLoginAndPos(driver):
    openWebsite(driver, "https://accounts.binance.com/es/login")

    time.sleep(2)

    driver.find_element(By.ID, ACCEPT_COOKIES_BTN_ID).click()  # Accept cookies

    print(" Please, log in to your Binance account")
    print("--------------------------------------------")
    print(" Press enter to continue...")
    print("--------------------------------------------")
    input(">")

    openWebsite(driver, "https://www.binance.com/es/pos")


def openWebsite(driver, website):
    while True:
        try:
            driver.get(website)
            break
        except:
            showNetworkError()
            continue


def showNetworkError():
    print("Error: we weren't able to open the website")
    print("Please, check your internet connection")
    print("Press enter to retry")
    input(">")


def checkAssetAvailability(assetName, assetPeriod, checkInterval):
    ctypes.windll.kernel32.SetConsoleTitleW(
        "Searching for: " + assetName + " " + assetPeriod + " days")

    showAssetInfo(assetName, assetPeriod, checkInterval)

    while True:
        # Request data from binance
        try:
            response = json.loads(requests.get(API_URL).text)["data"]
        except:
            # Couldn't get json data. Sleep and retry
            time.sleep(1000)
            continue

        # Unpacking results
        avaliables = unpackResponse(response)

        for item in avaliables:
            if assetName == item["asset"] and assetPeriod == item["duration"]:
                print(" Asset found:")
                print(
                    f" {item['asset']} for {item['duration']}d / {item['APY']}% APY")
                print("--------------------------------------------")
                return True

        # time loop waiting
        time.sleep(timedelta(seconds=checkInterval).total_seconds())


def unpackResponse(response):
    avaliables = []

    for item in response:
        for asset in item["projects"]:
            if not asset["sellOut"]:
                # Asset available, adding a dictionary with asset name, duration and APY to the result list
                avaliables.append({
                    "asset": asset["asset"],
                    "duration": asset["duration"],
                    "APY": str(round(float(asset["config"]["annualInterestRate"]) * 100, 2))
                })

    return avaliables


def showAssetInfo(assetName, assetPeriod, checkInterval):
    print("--------------------------------------------")
    print(" Automatic Binance Locked staking")
    print("--------------------------------------------")
    print(" Searching for...")
    print(" Asset: " + assetName)
    print(" Period: " + assetPeriod + " days")
    print("--------------------------------------------")
    print(" Checking every " + str(checkInterval) + " seconds")
    print("--------------------------------------------")


def end(shutdown):
    print("Bye!")
    if shutdown:
        os.system('shutdown -s -t 30')
    exit()


def main():
    ctypes.windll.kernel32.SetConsoleTitleW("Automatic Binance Locked Staking")

    try:
        print("--------------------------------------------")
        print(" Automatic Binance Locked Staking")
        print("--------------------------------------------")
        print(" Please, type the target asset")
        print(" Examples: 'LUNA 90', 'AXS 60'...")
        print("--------------------------------------------")

        while True:
            target_asset = input(">")
            assetName, assetPeriod = target_asset.split(" ")

            if assetPeriod in ["15", "30", "60", "90", "120"]:
                break
            else:
                print("Wrong duration")

        while True:
            print("--------------------------------------------")
            print(" Please, enter check interval in seconds")
            print("--------------------------------------------")
            checkInterval = int(input(">"))
            if checkInterval >= 0:
                break
            else:
                print("Wrong check interval")

        print("--------------------------------------------")
        print(" Do you want to shutdown your computer")
        print(" after subscripion? (y/n)")
        print("--------------------------------------------")
        shutdown = True if input(">").lower == 'y' else False

        driver = initWebDriver()

        openLoginAndPos(driver)

        if checkAssetAvailability(assetName, assetPeriod, checkInterval):
            startStaking(driver, assetName, assetPeriod)

        end(shutdown)

    except:
        exit()


if __name__ == "__main__":
    main()
