import json
import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

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

    day = get_current_day(driver)
    user_id = account["email"]

    if not user_has_activity(user_id, day):
        update_user_activity(user_id, day)

    if not user_has_done_action(user_id, 'has_worked'):
        work(driver, user_id)
    if not user_has_done_action(user_id, 'has_trained'):
        train(driver, user_id)

    driver.quit()

def get_current_day(driver):
    day_element = driver.find_element(By.CSS_SELECTOR, ".nav-header .vs104-3")
    day_text = day_element.text.strip()
    day_number = int(day_text.split()[1])
    return day_number

def user_has_activity(user_id, day):
    conn = sqlite3.connect('user_activities.db')
    c = conn.cursor()
    c.execute('SELECT 1 FROM activities WHERE user_id = ? AND day = ?', (user_id, day))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def update_user_activity(user_id, day):
    conn = sqlite3.connect('user_activities.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO activities (user_id, day, has_worked, has_rested, has_worked_twice, has_trained) VALUES (?, ?, 0, 0, 0, 0)', (user_id, day))
    conn.commit()
    conn.close()

def user_has_done_action(user_id, action):
    conn = sqlite3.connect('user_activities.db')
    c = conn.cursor()
    c.execute(f'SELECT {action} FROM activities WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def set_user_action_done(user_id, action):
    conn = sqlite3.connect('user_activities.db')
    c = conn.cursor()
    c.execute(f'UPDATE activities SET {action} = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def work(driver, user_id):
    driver.get("https://www.edominacy.com/en/companies")
    time.sleep(5)

    try:
        # Check and click either the rest button or the work button
        if click_button(driver, "button.buttonT.wHelperRest", "Rest button clicked"):
            set_user_action_done(user_id, 'has_rested')
            driver.refresh()  # Refresh the page immediately after clicking the rest button
            print("Page refreshed after resting")
            time.sleep(5)  # Wait for the page to refresh
            if click_button(driver, "button.buttonT.wHelperWork", "Work button clicked again"):
                set_user_action_done(user_id, 'has_worked_twice')
            else:
                print("You have already worked for today after resting.")
        elif click_button(driver, "button.buttonT.wHelperWork", "Work button clicked"):
            set_user_action_done(user_id, 'has_worked')
            time.sleep(5)  # Wait for the page to refresh after clicking the work button
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
        # Locate the parent div and get its title attribute
        parent_div = driver.find_element(By.CSS_SELECTOR, ".vs685")
        title_attribute = parent_div.get_attribute("title")
        # print(f"Title of the parent div: {title_attribute}")

        # Extract current and total days from the progress span
        progress_element = driver.find_element(By.CSS_SELECTOR, ".vs685-4")
        current_progress = progress_element.text.strip().split(" / ")
        current_days = int(current_progress[0])
        total_days = int(current_progress[1])
        days_left = total_days - current_days

        print(f"{title_attribute}: {days_left}")
    except Exception as e:
        print(f"An error occurred while calculating days left: {e}")

def train(driver, user_id):
    driver.get("https://www.edominacy.com/en/training-grounds")
    time.sleep(5)

    try:
        train_button = driver.find_element(By.CSS_SELECTOR, ".buttonT.wHelperTrain")
        if "disabled" in train_button.get_attribute("class"):
            print("You have already trained for today.")
        else:
            train_button.click()
            print("Train button clicked.")
            set_user_action_done(user_id, 'has_trained')
            time.sleep(5)  # Wait for the page to refresh after clicking the button
            calculate_training_progress(driver)
    except Exception as e:
        print(f"An error occurred while training: {e}")

def calculate_training_progress(driver):
    try:
        # Locate the parent div and get its title attribute
        parent_div = driver.find_element(By.CSS_SELECTOR, ".vs685")
        title_attribute = parent_div.get_attribute("title")

        # Extract current and total progress from the progress span
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
