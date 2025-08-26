import json
import os
import re
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium import *
from time import time
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.support.wait import WebDriverWait
from inputimeout import inputimeout, TimeoutOccurred
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import traceback

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

def waitFuncSpecified(waitAmount):
    try:
        time_over = inputimeout(
            prompt='End code? (Input y)', timeout=waitAmount)
        if str(time_over) == "y":
            print("Ending code...")
            exitTime = True
            sys.exit()

    except TimeoutOccurred:
        print("cont")

def sanitize_for_console(text):
    """
    Sanitizes text to prevent UnicodeEncodeError on some terminals.
    """
    return text.encode('cp1252', 'ignore').decode('cp1252')

def fbMarketScraper(driver, scrapedLinks, link):
    
    # Vars
    # service = Service()

    # opts = webdriver.ChromeOptions()
    # PROXY = '45.90.219.12:4444'
    # user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'

    # webdriver.DesiredCapabilities.CHROME['proxy'] = {
    #     "httpProxy": PROXY,
    #     "ftpProxy": PROXY,
    #     "sslProxy": PROXY,
    #     "proxyType": "MANUAL",

    # }

    # webdriver.DesiredCapabilities.CHROME['acceptSslCerts'] = True
    # opts.add_argument("user-agent="+user_agent)
    # print(webdriver.DesiredCapabilities.CHROME)
    # driver = webdriver.Chrome(service=service, options=opts)
    zip_code = 66045
    results = []

    try:
        # Step 1: Go to the initial page
        print("1. Navigating to fb page...")
        driver.get(link)
        # driver.get("https://offerup.com/search?q=car&DISTANCE=5000&SORT=-posted")
        # waitFuncSpecified(20)
        print("4. Parsing HTML for listings...")
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # The Anchor Selector: Find all 'a' tags where the href starts with '/marketplace/item/'
        # This is the most reliable way to identify listing cards.
        listing_cards = soup.select('a[href^="/marketplace/item/"]')
        
        for card in listing_cards:
            link = "https://www.facebook.com" + card.get('href', '')
            if link in scrapedLinks:
                continue
            # Initialize data points
            title, location, price, mileage = "N/A", "N/A", "N/A", "N/A"

            # Primary Data Extraction from img 'alt' attribute
            img_tag = card.find('img')
            if img_tag and img_tag.get('alt'):
                alt_text = sanitize_for_console(img_tag['alt'])
                if ' in ' in alt_text:
                    parts = alt_text.split(' in ', 1)
                    title = parts[0]
                    location = parts[1]
                else:
                    title = alt_text

            # Secondary Data Extraction from all spans within the card
            span_texts = [span.get_text(strip=True) for span in card.find_all('span') if span.get_text(strip=True)]
            
            for text in span_texts:
                if text.startswith('$'):
                    price = text
                # Regex to find mileage, e.g., "169K miles" or "10,000 miles"
                elif re.search(r'\d[\d,.]*K?\s*miles', text, re.IGNORECASE):
                    mileage = text

            # Add to results only if essential data is found
            if title != "N/A" and price != "N/A":
                results.append({
                    'title': title,
                    'price': price,
                    'location': location,
                    'mileage': mileage,
                    'link': link,
                    'source': 'Facebook',
                    'priceChecked': True
                })

        print(f"5. Found {len(results)} valid listings.")
        return results

    finally:
        print("6. Closing WebDriver.")
        driver.quit()

# if __name__ == "__main__":
#     # You can change these values to whatever you need
#     target_zip = "78741" 
#     target_query = "car"
    
#     offerup_deals = fbMarketScraper()
#         # offerup_deals = offerUpScraper(zip_code=target_zip, search_query=target_query)

#     if offerup_deals:
#         df = pd.DataFrame(offerup_deals)
#         print(df)
