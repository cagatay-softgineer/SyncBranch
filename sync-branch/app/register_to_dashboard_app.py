from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os 
from dotenv import load_dotenv

load_dotenv()

MAIL = os.getenv("MAIL")
PASSWORD = os.getenv("PASSWORD")

def get_form_selectors(html_content):
    """Extract form field IDs for 'Full Name' and 'Email' using BeautifulSoup."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the input fields for name and email
    name_input = soup.find("input", {"name": "name"})
    email_input = soup.find("input", {"name": "email"})
    
    # Check if elements are found
    name_id = name_input.get("id", None) if name_input else None
    email_id = email_input.get("id", None) if email_input else None
    
    # Return the IDs (could be None if elements were not found)
    return name_id, email_id

def add_spotify_dashboard_user(fullname, email):
    # Initialize WebDriver using ChromeDriverManager
    driver = webdriver.Chrome(ChromeDriverManager().install())
    
    try:
        # Step 1: Open the Spotify Developer Dashboard login page
        driver.get("https://accounts.spotify.com/en/login")
        
        # Step 2: Log in using the provided selectors
        username_field = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "login-username")))
        password_field = driver.find_element(By.ID, "login-password")
        login_button = driver.find_element(By.ID, "login-button")
        
        # Enter your login credentials
        username_field.send_keys(MAIL)
        password_field.send_keys(PASSWORD)
        login_button.click()

        # Step 3: Verify that the login was successful and check the redirected URL
        WebDriverWait(driver, 10).until(EC.url_contains("https://accounts.spotify.com/en/status"))

        # Check if redirected to the status page, which indicates successful login
        current_url = driver.current_url
        if "status" in current_url:
            print("Login successful. Redirecting to the dashboard...")
            driver.get("https://developer.spotify.com/dashboard/d863b0ec1be24fafa4f4dc4696ea26b1/users")
        else:
            print("Login unsuccessful or unexpected redirect. Exiting.")
            return

        # Step 4: Wait until the form fields are loaded
        name_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "name")))
        email_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))

        # Fill in the form fields with provided fullname and email
        name_field.send_keys(fullname)
        email_field.send_keys(email)
        
        # Submit the form by clicking the "Add user" button
        add_user_button = driver.find_element(By.XPATH, "//button[@type='submit' and contains(@class, 'Button-sc-qlcn5g-0')]")
        add_user_button.click()
        
        # Optional: Wait to confirm user is added
        time.sleep(5)

    finally:
        # Close the WebDriver
        driver.quit()
        
# Example usage with arguments
add_spotify_dashboard_user("username", "example123@mail.com")
