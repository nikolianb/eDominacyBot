import json
import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def create_database():
    conn = sqlite3.connect('database/user_activities.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            day INTEGER,
            has_worked INTEGER,
            has_rested INTEGER,
            has_worked_twice INTEGER,
            has_trained INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    print("Database and table created if not exists.")

def load_accounts(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def setup_driver(proxy=None):
    chrome_options = Options()
    chrome_options.add_argument('--headless')  
    chrome_options.add_argument('--no-sandbox') 
    chrome_options.add_argument('--disable-dev-shm-usage')  
    chrome_options.add_argument('--disable-gpu')  
    chrome_options.add_argument('--disable-software-rasterizer') 
    chrome_options.add_argument('--window-size=1920,1080')  

    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.geolocation": 2,
        "profile.default_content_setting_values.cookies": 2,
        "profile.managed_default_content_settings.third_party_cookies": 2,
        "profile.managed_default_content_setting_values.javascript": 1,
        "profile.managed_default_content_settings.plugins": 2,
        "profile.managed_default_content_setting_values.popups": 2,
        "profile.managed_default_content_setting_values.ads": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--log-level=3")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def save_page_source(driver, file_name):
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(driver.page_source)

def extract_day_from_index(driver):
    driver.get("https://www.edominacy.com/en/index")
    time.sleep(2)
    try:
        day_element = driver.find_element(By.XPATH, "//div[@class='vs596-1']/span[contains(text(), 'Day')]")
        day_text = day_element.text.strip()
        print(f"'{day_text}'")  # Debugging statement
        if not day_text:
            raise ValueError("Day text is empty")
        day_number = int(day_text.split()[1])
        return day_number
    except Exception as e:
        print(f"An error occurred while getting the current day: {e}")
        raise

def login(account, day):
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

    user_id = account["email"]

    print(f"Logged in as {user_id}.")
    print(f"Current day: {day}")

    if not user_has_activity(user_id, day):
        add_user_activity(user_id, day)
        print(f"Activity initialized for user {user_id} on day {day}.")

    work_and_rest_sequence(driver, user_id)

    if not user_has_done_action(user_id, 'has_trained'):
        train_performed = train(driver, user_id)
        if train_performed:
            print(f"Train action recorded for user {user_id}.")
        else:
            print(f"Train button not available for user {user_id}.")
    else:
        print(f"User {user_id} has already trained today.")

    driver.quit()

def work_and_rest_sequence(driver, user_id):
    driver.get("https://www.edominacy.com/en/companies")
    time.sleep(5)

    has_worked = user_has_done_action(user_id, 'has_worked')
    has_rested = user_has_done_action(user_id, 'has_rested')
    has_worked_twice = user_has_done_action(user_id, 'has_worked_twice')

    print(f"User status: has_worked={has_worked}, has_rested={has_rested}, has_worked_twice={has_worked_twice}")

    try:
        # Work first if not already done
        if not has_worked:
            perform_work_action(driver, user_id, 'has_worked')

        # Rest if not already done
        if not has_rested:
            perform_rest_action(driver, user_id)

        # Work again if not already done twice
        if has_worked and has_rested and not has_worked_twice:
            perform_work_action(driver, user_id, 'has_worked_twice')

        calculate_days_left(driver)
    except Exception as e:
        print(f"An error occurred: {e}")

def perform_work_action(driver, user_id, action):
    work_button = driver.find_element(By.CSS_SELECTOR, "button.buttonT.wHelperWork")
    if "disabled" not in work_button.get_attribute("class"):
        work_button.find_element(By.XPATH, "..").submit()
        set_user_action_done(user_id, action)
        print(f"Work action recorded for user {user_id} as {action}.")
        time.sleep(5)
        driver.refresh()
        time.sleep(5)
    else:
        print(f"Work button not available for user {user_id}.")

def perform_rest_action(driver, user_id):
    rest_button = driver.find_element(By.CSS_SELECTOR, "button.buttonT.wHelperRest")
    if "disabled" not in rest_button.get_attribute("class"):
        rest_button.click()
        set_user_action_done(user_id, 'has_rested')
        print(f"Rest action recorded for user {user_id}.")
        time.sleep(5)
        driver.refresh()
        time.sleep(5)
    else:
        print(f"Rest button not available for user {user_id}.")

def user_has_activity(user_id, day):
    conn = sqlite3.connect('database/user_activities.db')
    c = conn.cursor()
    c.execute('SELECT 1 FROM activities WHERE user_id = ? AND day = ?', (user_id, day))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def add_user_activity(user_id, day):
    conn = sqlite3.connect('database/user_activities.db')
    c = conn.cursor()
    c.execute('INSERT INTO activities (user_id, day, has_worked, has_rested, has_worked_twice, has_trained) VALUES (?, ?, 0, 0, 0, 0)', (user_id, day))
    conn.commit()
    conn.close()

def user_has_done_action(user_id, action):
    conn = sqlite3.connect('database/user_activities.db')
    c = conn.cursor()
    c.execute(f'SELECT {action} FROM activities WHERE user_id = ? ORDER BY day DESC LIMIT 1', (user_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def set_user_action_done(user_id, action):
    conn = sqlite3.connect('database/user_activities.db')
    c = conn.cursor()
    c.execute(f'UPDATE activities SET {action} = 1 WHERE user_id = ? AND day = (SELECT MAX(day) FROM activities WHERE user_id = ?)', (user_id, user_id))
    conn.commit()
    conn.close()
    print(f"Set {action} for user {user_id}.")

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

def train(driver, user_id):
    driver.get("https://www.edominacy.com/en/training-grounds")
    time.sleep(5)
    train_performed = False

    try:
        train_button = driver.find_element(By.CSS_SELECTOR, ".buttonT.wHelperTrain")
        if "disabled" in train_button.get_attribute("class"):
            print("You have already trained for today.")
        else:
            train_button.click()
            set_user_action_done(user_id, 'has_trained')
            train_performed = True
            time.sleep(5)
            calculate_training_progress(driver)
    except Exception as e:
        print(f"An error occurred while training: {e}")

    return train_performed

def calculate_training_progress(driver):
    try:
        parent_div = driver.find_element(By.CSS_SELECTOR, ".vs685")
        title_attribute = parent_div.get_attribute("title")

        progress_element = driver.find_element(By.CSS_SELECTOR, ".vs685-4")
        current_progress = progress_element.text.strip().split(" / ")
        current_days = int(current_progress[0])
        total_days = int(current_progress[1])
        days_left = total_days - current_days

        print(f"{title_attribute}: {days_left}/250")
    except Exception as e:
        print(f"An error occurred while calculating days left: {e}")

if __name__ == "__main__":
    create_database()
    accounts = load_accounts("accounts.json")
    for account in accounts:
        driver = setup_driver(account.get("proxy"))
        day = extract_day_from_index(driver)
        driver.quit()
        login(account, day)
