import json
import os

import requests
from scrapers.craigslScraper import scrape_craigslist_v2
from scrapers.fbMarketScraper import fbMarketScraper 
from scrapers.offerUpScraper import offerUpScraper
from kbb_valuator import process_scraped_data
from selenium import webdriver
from selenium import *
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

# This setup creates 'live_scraper.log' with timestamped messages
log_handler = logging.FileHandler('live_scraper.log')
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
live_logger = logging.getLogger('live_logger')
live_logger.setLevel(logging.INFO)
live_logger.addHandler(log_handler)

# Use this instead of print() in your scraper logic
live_logger.info("This is a message from the server-side scraper.")


service = Service()
opts = webdriver.ChromeOptions()
PROXY = '45.90.219.12:4444'
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'

webdriver.DesiredCapabilities.CHROME['proxy'] = {
    "httpProxy": PROXY,
    "ftpProxy": PROXY,
    "sslProxy": PROXY,
    "proxyType": "MANUAL",

}

webdriver.DesiredCapabilities.CHROME['acceptSslCerts'] = True
opts.add_argument("user-agent="+user_agent)
opts.add_argument('--headless')
print(webdriver.DesiredCapabilities.CHROME)
driver = webdriver.Chrome(service=service, options=opts)

# --- Constants for shared database and index files ---
DATABASE_FILE = "scraped_listings.jsonl"
SEEN_URLS_FILE = "seen_urls.txt"


def load_seen_urls():
    """Loads the set of previously seen URLs from the index file."""
    if not os.path.exists(SEEN_URLS_FILE):
        return set()
    with open(SEEN_URLS_FILE, 'r', encoding='utf-8') as f:
        # Use a set for efficient O(1) lookups
        return set(line.strip() for line in f)

def save_new_listings(new_listings):
    """
    Appends truly new listings to the database and their URLs to the index.
    This function performs two atomic append operations.
    """
    if not new_listings:
        print("No new listings to save.")
        return

    # Open both files in append mode to add new data
    with open(DATABASE_FILE, 'a', encoding='utf-8') as db_f, \
         open(SEEN_URLS_FILE, 'a', encoding='utf-8') as urls_f:
        for listing in new_listings:
            # Write the full JSON object to the database
            db_f.write(json.dumps(listing, ensure_ascii=False) + '\n')
            # Write just the unique URL to the index
            urls_f.write(listing['link'] + '\n')
            
    print(f"Appended {len(new_listings)} new listings to database.")



    
if __name__ == "__main__":
    scrapedLinks = load_seen_urls()
    # global driver
    # https://wyoming.craigslist.org/search/farson-wy/cta?lat=42.17&lon=-109.3557&postal=78741&search_distance=1000#search=2~gallery~15 
    # https://westky.craigslist.org/search/cadiz-ky/cta?lat=36.8168&lon=-87.8614&postal=78741&search_distance=1000#search=2~gallery~0
    # https://saguenay.craigslist.org/search/baie-comeau-northeast-qc/cta?lat=51.3981&lon=-69.4177&postal=78741&search_distance=1000&lang=en&cc=us#search=2~gallery~0
    
    # new fb market links 
    # https://www.facebook.com/marketplace/la/vehicles/?sortBy=creation_time_descend&exact=true&radius_in_km=804
    # https://www.facebook.com/marketplace/nyc/vehicles/?sortBy=creation_time_descend&exact=true&radius_in_km=804
    
    # will do each location setting twice, 1 for car/truck, another for boats
    
    # craigslist cars/trucks
    # listings = scrape_craigslist_v2(city="elpaso", query="car")
    # save_new_listings(listings)
    link = "https://westky.craigslist.org/search/cadiz-ky/cta?lat=36.8168&lon=-87.8614&postal=78741&search_distance=1000#search=2~gallery~0"
    listings = scrape_craigslist_v2(driver, scrapedLinks, link)
    save_new_listings(listings)

    link = "https://saguenay.craigslist.org/search/baie-comeau-northeast-qc/cta?lat=51.3981&lon=-69.4177&postal=78741&search_distance=1000&lang=en&cc=us#search=2~gallery~0"
    listings = scrape_craigslist_v2(driver, scrapedLinks, link)
    save_new_listings(listings)

    # fb market cars/trucks
    link = "https://www.facebook.com/marketplace/la/vehicles/?sortBy=creation_time_descend&exact=true&radius_in_km=804"
    listings = fbMarketScraper(driver, scrapedLinks, link)
    save_new_listings(listings)
    
    link = "https://www.facebook.com/marketplace/nyc/vehicles/?sortBy=creation_time_descend&exact=true&radius_in_km=804"
    listings = fbMarketScraper(driver, scrapedLinks, link)
    save_new_listings(listings)

    # offer up cars/trucks
    
    listings = offerUpScraper(driver, scrapedLinks)
    save_new_listings(listings)
    process_scraped_data(driver, opts, service)

