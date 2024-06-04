import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import sqlite3 

def load_accounts(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def setup_driver(proxy=None):
    chrome_options = Options()
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def login(account):
    driver = setup_driver(account.get("proxy"))
    driver.get("https://www.edominacy.com/en/login")

    email_field = driver.find_element(By.NAME, "email")
    email_field.send_keys(account["email"])

    password_field = driver.find_element(By.NAME, "password")
    password_field.send_keys(account["password"])

    remember_me_checkbox = driver.find_element(By.ID, "remember-me")
    if not remember_me_checkbox.is_selected():
        remember_me_checkbox.click()

    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()

    time.sleep(5)

    work(driver)
    train(driver)
    driver.quit()

def work(driver):
    driver.get("https://www.edominacy.com/en/companies")
    time.sleep(5)

    try:
        if click_button(driver, "button.buttonT.wHelperRest", "Rest button clicked"):
            driver.refresh() 
            print("Page refreshed after resting")
            time.sleep(5)  
            if not click_button(driver, "button.buttonT.wHelperWork", "Work button clicked again"):
                print("You have already worked for today after resting.")
        elif click_button(driver, "button.buttonT.wHelperWork", "Work button clicked"):
            time.sleep(5)  
            calculate_days_left(driver)
        else:
            print("You have already worked for today.")
    except Exception as e:
        print(f"An error occurred: {e}")

def click_button(driver, selector, success_message):
    try:
        button = driver.find_element(By.CSS_SELECTOR, selector)
        if "disabled" not in button.get_attribute("class"):
            button.click()
            print(success_message)
            return True
    except Exception as e:
        print(f"An error occurred while clicking button: {e}")
    return False

def calculate_days_left(driver):
    try:
        parent_div = driver.find_element(By.CSS_SELECTOR, ".vs685")
        title_attribute = parent_div.get_attribute("title")

        progress_element = driver.find_element(By.CSS_SELECTOR, ".vs685-4")
        current_progress = progress_element.text.strip().split(" / ")
        current_days = int(current_progress[0])
        total_days = int(current_progress[1])
        days_left = total_days - current_days

        print(f"{title_attribute}: {days_left}")
    except Exception as e:
        print(f"An error occurred while calculating days left: {e}")

def train(driver):
    driver.get("https://www.edominacy.com/en/training-grounds")
    time.sleep(5)

    try:
        train_button = driver.find_element(By.CSS_SELECTOR, ".buttonT.wHelperTrain")
        if "disabled" in train_button.get_attribute("class"):
            print("You have already trained for today.")
        else:
            train_button.click()
            print("Train button clicked.")
            time.sleep(5) 
            calculate_training_progress(driver)
    except Exception as e:
        print(f"An error occurred while training: {e}")

def calculate_training_progress(driver):
    try:
        parent_div = driver.find_element(By.CSS_SELECTOR, ".vs685")
        title_attribute = parent_div.get_attribute("title")

        progress_element = driver.find_element(By.CSS_SELECTOR, ".vs685-4")
        current_progress = progress_element.text.strip().split(" / ")
        current_value = int(current_progress[0])
        total_value = int(current_progress[1])
        progress_left = total_value - current_value

        print(f"{title_attribute}: {progress_left}")
    except Exception as e:
        print(f"An error occurred while calculating training progress: {e}")

if __name__ == "__main__":
    accounts = load_accounts('accounts.json')
    for account in accounts:
        login(account)
