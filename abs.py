import os
import json
import requests
import time
import ctypes
from datetime import timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By

def start(driver, asset_name, asset_period):
    while True:
        driver.refresh()

        time.sleep(1.5)

        search_bar = driver.find_element(By.ID, "savings-search-coin")

        search_bar.send_keys(asset_name)

        time.sleep(2)

        driver.find_element(By.XPATH, '//button[contains(text(), ' + str(asset_period) + ')]').click() # select period (days)

        time.sleep(0.1)

        if driver.find_elements(By.CLASS_NAME, 'css-ercebf') == 0:
            print("Asset sold out. Retrying...")
            continue
        else:
            print("Asset available")
            break

    print("Starting subscription...")

    try:
        time.sleep(0.3)

        driver.find_element(By.ID, 'pos-stake').click() # open stake panel

        time.sleep(1)

        driver.find_element(By.CLASS_NAME, 'css-lw7eev').click() # select max quantity

        time.sleep(0.2)

        driver.find_element(By.XPATH, "//label[@class='css-bfef9a']").click() # accept terms and conditions
        
        time.sleep(0.2)

        driver.find_element(By.ID, 'pos-confirm').click() # confirm

        print("Subscription completed successfully!")

    except:
        print("Something went wrong. Retrying...")
        start(driver, asset_name, asset_period)

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
                    print("Please, download the web driver and place it in the same forlder of this script")
                    print("https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/")
                    print("Press enter when you are done")
                    input(">")

    while True:
        try:
            driver.get("https://accounts.binance.com/es/login")
            break
        except:
            networkConnectionError()
            continue

    driver.maximize_window()

    print(" Please, log in to your Binance account")
    print("--------------------------------------------")
    print(" Press enter to continue...")
    print("--------------------------------------------")
    input(">")

    while True:
        try:
            driver.get("https://www.binance.com/es/pos")
            break
        except:
            networkConnectionError()
            continue

    return driver

def networkConnectionError():
    print("Error: we weren't able to open the website")
    print("Please, check your internet connection")
    print("Press enter to retry")
    input(">")

def listener(asset_name, asset_period, check_every):
    ctypes.windll.kernel32.SetConsoleTitleW("Searching for: " + asset_name + " " + asset_period + " days")
    # baseline url request
    friendly_url = "https://www.binance.com/gateway-api/v1/friendly/pos/"\
                "union?pageSize=200&pageIndex=1&status=ALL"
    
    print("--------------------------------------------")
    print(" Automatic Binance Locked staking" )
    print("--------------------------------------------")
    print(" Searching for...")
    print(" Asset: " + asset_name)
    print(" Period: " + asset_period + " days")
    print("--------------------------------------------")
    print(" Checking every " + str(check_every) + " seconds")
    print("--------------------------------------------")

    while True:
        # Request data from binance
        response = json.loads(requests.get(friendly_url).text)["data"]

        # Unpacking results
        avaliables = []
        for item in response:
            for asset in item["projects"]:
                if not asset["sellOut"]:
                    # Asset available, adding a dictionary with asset name, duration and APY to the result list
                    avaliables.append({
                        "asset": asset["asset"],
                        "duration": asset["duration"],
                        "APY": str(round(float(asset["config"]["annualInterestRate"])*100, 2))
                    })

        for item in avaliables:
            if asset_name == item["asset"] and asset_period == item["duration"]:
                print(" Asset found:")
                print(f" {item['asset']} for {item['duration']}d / {item['APY']}% APY")
                print("--------------------------------------------")
                return

        # time loop waiting
        time.sleep(timedelta(seconds=check_every).total_seconds())

def end(shutdown):
    print("Bye!")
    if shutdown == 'y':
        os.system('shutdown -s -t 30')
    exit()

def main():
    ctypes.windll.kernel32.SetConsoleTitleW("Automatic Binance Locked staking")
    try:
        print("--------------------------------------------")
        print(" Automatic Binance Locked staking" )
        print("--------------------------------------------")
        print(" Please, type the target asset")
        print(" Examples: 'LUNA 90', 'AXS 60'...")
        print("--------------------------------------------")
        target_asset = input(">")
        print("--------------------------------------------")
        print(" Please, enter check interval in seconds")
        print("--------------------------------------------")
        check_every = int(input(">"))
        print("--------------------------------------------")
        print(" Do you want to shutdown your computer")
        print(" after subscripion? (y/n)")
        print("--------------------------------------------")
        shutdown = input(">")
        
        asset_name, asset_period = target_asset.split(" ")
        driver = initWebDriver()
        listener(asset_name, asset_period, check_every)
        start(driver, asset_name, asset_period)
        end(shutdown)
    except:
        exit()

if __name__ == "__main__":
    main()