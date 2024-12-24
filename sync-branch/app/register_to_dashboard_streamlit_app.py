import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MAIL = os.getenv("MAIL")
PASSWORD = os.getenv("PASSWORD")

def add_spotify_dashboard_user(fullname, email):
    """Automates the process of adding a user to the Spotify Developer Dashboard."""

    # Initialize WebDriver using ChromeDriverManager
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    try:
        # Step 1: Open the Spotify login page
        with st.spinner("Opening Spotify login page..."):
            driver.get("https://accounts.spotify.com/en/login")

        # Step 2: Log in
        with st.spinner("Logging in..."):
            username_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "login-username"))
            )
            password_field = driver.find_element(By.ID, "login-password")
            login_button = driver.find_element(By.ID, "login-button")

            # Enter credentials from environment variables
            username_field.send_keys(MAIL)
            password_field.send_keys(PASSWORD)
            login_button.click()

            # Wait for login to complete (URL check)
            WebDriverWait(driver, 10).until(
                EC.url_contains("https://accounts.spotify.com/en/status")
            )

            if "status" in driver.current_url:
                st.write("Login successful. Redirecting to the dashboard...")
                driver.get("https://developer.spotify.com/dashboard/d863b0ec1be24fafa4f4dc4696ea26b1/users")
            else:
                st.error("Login unsuccessful or unexpected redirect.")
                return

        # Step 3: Wait for the user addition form and fill it
        with st.spinner("Loading user addition form..."):
            name_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "name"))
            )
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )

            # Fill in the form
            name_field.send_keys(fullname)
            email_field.send_keys(email)

            # Click "Add user" button
            with st.spinner("Submitting the form..."):
                add_user_button = driver.find_element(
                    By.XPATH, "//button[@type='submit' and contains(@class, 'Button-sc-qlcn5g-0')]"
                )
                add_user_button.click()

            # Wait a bit for confirmation
            time.sleep(5)
            st.success("User added successfully!")

    except Exception as e:
        st.error(f"An error occurred: {e}")

    finally:
        with st.spinner("Closing the browser..."):
            driver.quit()


def main():
    st.title("Spotify Dashboard User Adder")

    # Input fields
    fullname = st.text_input("Full Name")
    email = st.text_input("Email")

    if st.button("Add User"):
        if not (fullname and email):
            st.warning("Please provide both Full Name and Email!")
        else:
            add_spotify_dashboard_user(fullname, email)


if __name__ == "__main__":
    main()
