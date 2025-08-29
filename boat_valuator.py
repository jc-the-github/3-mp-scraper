import json
import re
import os
import sys
import time
from bs4 import BeautifulSoup
from thefuzz import process
import requests
from inputimeout import inputimeout, TimeoutOccurred

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from uszipcode.search import SearchEngine
from urllib.parse import urlencode

# --- Constants ---
DATABASE_FILE = "boats_scraped_listings.jsonl"
MATCH_SCORE_THRESHOLD = 80 # Confidence threshold for fuzzy matching search results

def save_data(data):
    """Writes a list of dictionaries to a .jsonl file, overwriting it."""
    with open(DATABASE_FILE, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

def sendTelegramNotif(listing, updates):
    """Sends a Telegram notification if a good deal is found."""
    # --- CONFIGURE YOUR TELEGRAM BOT ---
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    CHAT_ID = "YOUR_CHAT_ID"
    # -----------------------------------

    try:
        # Clean the listing price
        price_str = listing.get('price', 'notfound').replace("$", "").replace(",", "").strip()
        if not price_str.isdigit():
            print(f"[Telegram] Invalid listing price: {listing.get('price')}")
            return
        price = int(price_str)

        # Clean the JD Power trade-in value
        jd_power_value_str = updates.get('jd_power_trade_in', 'notfound').replace("$", "").replace(",", "").strip()
        print("s: " + jd_power_value_str)
        if not jd_power_value_str.isdigit():
            print(f"[Telegram] Invalid JD Power value: {updates.get('jd_power_trade_in')}")
            return
        jd_power_value = int(jd_power_value_str)

        message = ""
        # A good deal is if the listing price is near or below the trade-in value
        if price <= jd_power_value:
            price_diff = jd_power_value - price
            percentage_below = (price_diff / jd_power_value) * 100 if jd_power_value > 0 else 0
            message_prefix = (
                f"🔥 Excellent Deal Alert! 🔥\n"
                f"Price is ${price_diff:,.2f} ({percentage_below:.2f}%) BELOW Trade-In Value!\n\n"
            )
            message = (
                f"{message_prefix}"
                f"Vehicle: {listing.get('title', 'N/A')}\n"
                f"Listed Price: ${price:,.2f}\n"
                f"JD Power Trade-In: ${jd_power_value:,.2f}\n"
                f"Location: {listing.get('location', 'N/A')}\n"
                f"Link: {listing.get('link', 'N/A')}"
            )

        if message:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
            response = requests.get(url)
            print(f"[Telegram] Notification sent. Status: {response.status_code}")
        else:
            print("[Telegram] Deal did not meet notification criteria.")

    except (ValueError, TypeError) as e:
        print(f"[Telegram] Error processing values for notification: {e}")

def update_listing_data(data, identifier_link, updates):
    """Finds a listing by its link, applies updates, and saves."""
    found = False
    for listing in data:
        if listing.get('link') == identifier_link:
            print(f"[DB] Found matching listing, updating with: {updates}")
            listing.update(updates)
            sendTelegramNotif(listing, updates)
            found = True
            break
    if found:
        save_data(data)
    else:
        print(f"[DB] Could not find listing with link {identifier_link} to update.")
    return data, found


def get_jdpower_valuation(driver, listing_title):
    """
    Searches for a vehicle on DuckDuckGo, finds the best JD Power link using
    fuzzy matching, navigates to it, and extracts the trade-in value.
    """
    print(f"\n[JD Power] Starting valuation for: {listing_title}")
    wait = WebDriverWait(driver, 20)
    
    try:
        # Step 1: Search on DuckDuckGo for JD Power links
        query = listing_title.replace(" ", "+") + "+jd+power+values"
        search_url = f"https://duckduckgo.com/?q={query}"
        print(f"[Search] Navigating to: {search_url}")
        driver.get(search_url)

        # Step 2: Gather all JD Power links from the search results
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ol.react-results--main > li")))
        
        # Use a dictionary to store link text and href, avoiding duplicates
        jd_power_links = {}
        link_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='jdpower.com']")
        for link in link_elements:
            href = link.get_attribute('href')
            text = link.text
            if href and text and "..." not in text: # Filter out incomplete link text
                if 'values' in text:
                    jd_power_links[text] = href
        
        if not jd_power_links:
            print("[Search] ERROR: No valid jdpower.com links found on search results page.")
            return None
        
        print(f"[Search] Found {len(jd_power_links)} potential JD Power links.")

        fuzzyStringToCheck = listing_title 
        # fuzzyStringToCheck = listing_title + "values"
        # Step 3: Use fuzzy matching to find the best link
        best_match = process.extractOne(fuzzyStringToCheck, jd_power_links.keys())
        if not best_match or best_match[1] < MATCH_SCORE_THRESHOLD:
            print(f"[Fuzzy] No good match found. Best was '{best_match[0]}' with score {best_match[1]}. Aborting.")
            return None
            
        target_title, score = best_match
        target_url = jd_power_links[target_title]
        print(f"[Fuzzy] Best match found with score {score}: '{target_title}'")
        print(f"[Navigate] Going to best match URL: {target_url}")

        # Step 4: Go to the best matching link
        driver.get(target_url)

        # Step 5: Find and click the "Values" heading
        # Using XPath with text is more reliable than class names which can change
        # print("[Action] Looking for 'Values' button...")
        # values_button = wait.until(EC.element_to_be_clickable(
        #     (By.XPATH, "//h2[normalize-space()='Values']")
        # ))
        # values_button = wait.until(EC.element_to_be_clickable(
        #     (By.CLASS_NAME, "bh-l MuiBox-root mui-0")
        # ))
        # values_button.click()
        # print("[Action] Clicked 'Values'. Waiting for price to load...")

        # A brief pause allows the UI to update after the click
        # time.sleep(2)

        # Step 6: Get the price from the specified span
        price_element = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "span.tradeToDealer_line-before-total__mJ89F")
        ))
        price = price_element.text
        print(f"[SUCCESS] Extracted Trade-In Value: {price}")
        
        return {"jd_power_trade_in": price, "priceChecked": True}

    except (TimeoutException, NoSuchElementException) as e:
        print(f"[JD Power] ERROR: A step in the process failed. The website structure may have changed.")
        print(f"Details: {e}")
        return None
    except Exception as e:
        print(f"[JD Power] An unexpected error occurred: {e}")
        return None


def process_scraped_data_boat(driver):
    """Main loop to process listings from the database file."""
    print("--- Starting JD Power Valuation Processor ---")
    
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            listings = [json.loads(line) for line in f]
        print(f"Loaded {len(listings)} listings from '{DATABASE_FILE}'.")
    except FileNotFoundError:
        print(f"ERROR: Database file '{DATABASE_FILE}' not found. Run a scraper first.")
        return
        
    # service = Service(ChromeDriverManager().install())
    # opts = webdriver.ChromeOptions()
    # # To run headless (without a visible browser window), uncomment the next line
    # # opts.add_argument("--headless")
    # opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    # opts.add_argument("--disable-blink-features=AutomationControlled") # Helps avoid bot detection

    for i, listing in enumerate(listings):
        print(f"\n--- Processing Listing {i+1}/{len(listings)}: {listing.get('title', 'N/A')} ---")

        if listing.get('priceChecked'):
            print("This listing has already been processed. Skipping.")
            continue
        
        if listing.get('title', 'N/A') == 'N/A':
            print("Listing has no title. Skipping.")
            continue

        # driver = None # Ensure driver is defined in this scope
        try:
            # driver = webdriver.Chrome(service=service, options=opts)
            valuation_data = get_jdpower_valuation(
                driver=driver,
                listing_title=listing['title']
            )
            
            if valuation_data:
                print(f"JD POWER VALUATION FOUND: {valuation_data}")
                listings, found = update_listing_data(listings, listing.get('link'), valuation_data)
            else:
                print("JD POWER VALUATION FAILED for this vehicle.")
                # Mark as checked to avoid retrying a known failure
                listings, found = update_listing_data(listings, listing.get('link'), {"priceChecked": True})

        except Exception as e:
            print(f"An error occurred in the main processing loop for a listing: {e}")
        # finally:
        #     if driver:
        #         driver.quit()

# if __name__ == "__main__":
#     process_scraped_data()