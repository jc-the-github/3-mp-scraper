import json
import os

import requests
from scrapers.craigslScraper import scrape_craigslist_v2
from scrapers.fbMarketScraper import fbMarketScraper 
from scrapers.offerUpScraper import offerUpScraper
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
import logging
import sys # Import the sys module to access standard output
from boat_valuator import process_scraped_data_boat
from kbb_valuator import process_scraped_data

# --- Basic logger setup (as before) ---
log_formatter = logging.Formatter('%(asctime)s - %(message)s')
live_logger = logging.getLogger('live_logger')
live_logger.setLevel(logging.INFO)

# --- Handler 1: The File (for the web UI) ---
file_handler = logging.FileHandler('live_scraper.log')
file_handler.setFormatter(log_formatter)
live_logger.addHandler(file_handler)

# --- Handler 2: The Console (for journalctl debugging) ---
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_formatter)
live_logger.addHandler(stream_handler)


# --- Example Usage ---
# Now, any message sent with this logger goes to BOTH the file and the console.
live_logger.info("This message will appear in live_scraper.log AND in the systemd journal.")

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
# opts.add_argument('--headless')
print(webdriver.DesiredCapabilities.CHROME)
driver = webdriver.Chrome(service=service, options=opts)

# --- Constants for shared database and index files ---
DATABASE_FILE = "scraped_listings.jsonl"
BOATS_DATABASE_FILE = "boats_scraped_listings.jsonl"

SEEN_URLS_FILE = "seen_urls.txt"

def load_and_prepare_listings(database_file):
    try:
        with open(database_file, 'r', encoding='utf-8') as f:
            listings = [json.loads(line) for line in f]
            listings
            # listings.reverse()
            return listings
    except FileNotFoundError:
        return []
    
def interweave_listings_directly(array2d):
    """
    Interweaves listings from a fixed number of sources.
    """
    # # 1. Fetch all the data upfront
    # listings_c1 = getListingsCity1()
    # listings_c2 = getListingsCity2()
    # listings_c3 = getListingsCity3()
    max = 0
    for element in array2d:
        print("sss: " + str(len(element)))
        if len(element) > max:
            max = len(element)
    # 2. Prepare the final list and find the length of the longest list
    interwoven = []
    # max_length = max(len(listings_c1), len(listings_c2), len(listings_c3))

    
    # 3. Loop up to the max length
    for i in range(max):
        # Add from city 1 if an item exists at this index
        for element in array2d:
            if i < len(element):
                interwoven.append(element[i])
        # if i < len(listings_c1):
        #     interwoven.append(listings_c1[i])
# 3. Loop up to the max length
    # for i in range(max):
    #     # Add from city 1 if an item exists at this index
    #     for element in array2d:
    #         index = 0
    #         for elem in element:
    #             if i < len(element) and index == i:
    #                 interwoven.append(elem)
    #             index += 1
            
    return interwoven

def separate_listings(all_listings):
    """Splits a master list into categorized queues."""
    queues = {
        'cl_car': [],
        'cl_boat': [],
        'fbm_car': [],
        'fbm_boat': [],
        'offerup_car': [],
        'offerup_boat': []
    }
    
    for listing in all_listings:
        source = listing.get('source') # e.g., 'craigslist', 'fbm', 'offerup'
        category = listing.get('category') # e.g., 'car', 'boat'
        
        if source == 'Craigslist' and category == 'car':
            queues['cl_car'].append(listing)
        elif source == 'Craigslist' and category == 'boat':
            queues['cl_boat'].append(listing)
        elif source == 'Facebook' and category == 'car':
            queues['fbm_car'].append(listing)
        elif source == 'Facebook' and category == 'boat':
            queues['fbm_boat'].append(listing)        
        elif source == 'OfferUp' and category == 'car':
            queues['offerup_car'].append(listing)        
        elif source == 'OfferUp' and category == 'boat':
            queues['offerup_boat'].append(listing)
        # ... add elif for fbm_car, fbm_boat, offerup_car, offerup_boat
        
    return queues

def process_listings_round_robin(queues, driver, opts, service, boatListings, carListings):
    """
    Processes listings from all queues in a round-robin fashion
    until all queues are empty.
    """
    # Continue as long as at least one queue has items in it
    from boat_valuator import process_scraped_data_boat
    from kbb_valuator import process_scraped_data
    while any(queues.values()):
        # The round-robin sequence
        if queues['cl_car']:
            listing = queues['cl_car'].pop(0)
            print(f"Evaluating Craigslist Car: {listing.get('title')}")
            process_scraped_data(driver,opts,service,listing,carListings)
            
        if queues['fbm_boat']:
            listing = queues['fbm_boat'].pop(0)
            print(f"Evaluating FBM Boat: {listing.get('title')}")
            process_scraped_data_boat(driver, listing, boatListings)

        if queues['offerup_car']:
            listing = queues['offerup_car'].pop(0)
            print(f"Evaluating OfferUp Car: {listing.get('title')}")
            process_scraped_data(driver,opts,service,listing,carListings)

        if queues['cl_boat']:
            listing = queues['cl_boat'].pop(0)
            print(f"Evaluating Craigslist Boat: {listing.get('title')}")
            process_scraped_data_boat(driver, listing, boatListings)

        if queues['fbm_car']:
            listing = queues['fbm_car'].pop(0)
            print(f"Evaluating FBM Car: {listing.get('title')}")
            process_scraped_data(driver,opts,service,listing,carListings)

        if queues['offerup_boat']:
            listing = queues['offerup_boat'].pop(0)
            print(f"Evaluating OfferUp Boat: {listing.get('title')}")
            process_scraped_data_boat(driver, listing, boatListings)

def load_seen_urls():
    """Loads the set of previously seen URLs from the index file."""
    if not os.path.exists(SEEN_URLS_FILE):
        return set()
    with open(SEEN_URLS_FILE, 'r', encoding='utf-8') as f:
        # Use a set for efficient O(1) lookups
        return set(line.strip() for line in f)

def save_new_listings(new_listings):
    global scrapedLinks
    """
    Appends truly new listings to the database and their URLs to the index.
    This function performs two atomic append operations.
    """
    if not new_listings:
        print("No new listings to save.")
        return
    new_listings_num = 0
    # Open both files in append mode to add new data
    with open(DATABASE_FILE, 'w', encoding='utf-8') as db_f, \
         open(SEEN_URLS_FILE, 'w', encoding='utf-8') as urls_f:
        for listing in new_listings:
            if listing.get('link', '') not in scrapedLinks:
                # Write the full JSON object to the database
                db_f.write(json.dumps(listing, ensure_ascii=False) + '\n')
                # Write just the unique URL to the index
                urls_f.write(listing['link'] + '\n')
                new_listings_num = new_listings_num + 1

            
    print(f"Appended {str(new_listings_num)} new listings to cars/trucks database.")
    # print(f"Appended {len(new_listings)} new listings to database.")

def save_new_listings_boat(new_listings):
    """
    Appends truly new listings to the database and their URLs to the index.
    This function performs two atomic append operations.
    """
    if not new_listings:
        print("No new listings to save.")
        return
    new_listings_num = 0
    # Open both files in write mode replace, data
    with open(BOATS_DATABASE_FILE, 'w', encoding='utf-8') as db_f, \
         open(SEEN_URLS_FILE, 'w', encoding='utf-8') as urls_f:
        for listing in new_listings:
            if listing.get('link', '') not in scrapedLinks:
                # Write the full JSON object to the database
                db_f.write(json.dumps(listing, ensure_ascii=False) + '\n')
                # Write just the unique URL to the index
                urls_f.write(listing['link'] + '\n')
                new_listings_num = new_listings_num + 1

            
    print(f"Appended {str(new_listings_num)} new listings to boats database.")
    # print(f"Appended {len(new_listings)} new listings to database.")


def deduplicate_listings_by_key(listings, key='link'):
    """
    Removes duplicate dictionaries from a list based on a unique key, 
    preserving the order of the first occurrence.

    Args:
        listings (list): The list of listing dictionaries to process.
        key (str): The dictionary key to use for checking uniqueness (e.g., 'link').

    Returns:
        list: A new list of unique listings, in their original order.
    """
    seen_keys = set()
    unique_listings = []
    # print('key: ' + str(seen_keys))
    for listing in listings:
        key_value = listing.get(key)
        # print('list: ' + str(listing))
        # print('key: ' + str(key_value))
        if key_value and key_value not in seen_keys:
            seen_keys.add(key_value)
            # print('add ')
            unique_listings.append(listing)
    # print('key: ' + str(unique_listings))
    return unique_listings
    
if __name__ == "__main__":
    
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


    
    # link = "https://westky.craigslist.org/search/cadiz-ky/cta?lat=36.8168&lon=-87.8614&postal=78741&search_distance=1000#search=2~gallery~0"
    # listings = scrape_craigslist_v2(driver, scrapedLinks, link, 'car')
    # save_new_listings(listings)
    
    # boats
    # link = "https://westky.craigslist.org/search/cadiz-ky/boo?lat=36.8168&lon=-87.8614&search_distance=1000#search=2~gallery~0"
    # listings = scrape_craigslist_v2(driver, scrapedLinks, link, 'car')
    # save_new_listings_boat(listings)

    # link = "https://saguenay.craigslist.org/search/baie-comeau-northeast-qc/cta?lat=51.3981&lon=-69.4177&postal=78741&search_distance=1000&lang=en&cc=us#search=2~gallery~0"
    # listings = scrape_craigslist_v2(driver, scrapedLinks, link, 'car')
    # save_new_listings(listings)

        # # offer up cars/trucks
    # listings = offerUpScraper(driver, scrapedLinks, 'car')
    # save_new_listings(listings)

    scrapedLinks = load_seen_urls()
    
    carListings = []
    carListings2d = []
    boatListings = []
    boatListings2d = []
    # fb market cars/trucks
    link = "https://www.facebook.com/marketplace/la/vehicles/?sortBy=creation_time_descend&exact=true&radius_in_km=804"
    # carListings.append(fbMarketScraper(driver, scrapedLinks, link, 'car'))
    carListings = fbMarketScraper(driver, scrapedLinks, link, 'car')
    carListings2d.append(carListings)
    
    link = "https://www.facebook.com/marketplace/nyc/vehicles/?sortBy=creation_time_descend&exact=true&radius_in_km=804"
    carListings = fbMarketScraper(driver, scrapedLinks, link, 'car')
    carListings2d.append(carListings)

    flattenedCarListings = []
    flattenedBoatListings = []

    flattenedCarListings = interweave_listings_directly(carListings2d)
    flattenedBoatListings = interweave_listings_directly(boatListings2d)

    # for elem in carListings2d:
    #     for listing in elem:
    #         flattenedCarListings.append(listing)
    # for elem in boatListings2d:
    #     for listing in elem:
    #         flattenedBoatListings.append(listing)

    # print("boat: " + str(flattenedBoatListings))
    # print("car: " + str(flattenedCarListings))
   
    # flattenedBoatListings = deduplicate_listings_by_key(flattenedBoatListings, 'link')
    # flattenedCarListings = deduplicate_listings_by_key(flattenedCarListings, 'link')

    # print("boat: " + str(flattenedBoatListings))
    # print("car: " + str(flattenedCarListings))

    # flattenedCarListings = list(set(flattenedCarListings))
    # flattenedBoatListings = list(set(flattenedBoatListings))

    flattenedCarListings.reverse()
    flattenedBoatListings.reverse()

    previousBoatListings = load_and_prepare_listings('boats_scraped_listings.jsonl')
    previousCarListings = load_and_prepare_listings('scraped_listings.jsonl')
    # if not previousBoatListings:

    totalListingsCars = flattenedCarListings + previousCarListings
    totalListingsBoats = flattenedBoatListings + previousBoatListings

    totalListingsCars = deduplicate_listings_by_key(totalListingsCars, 'link')
    totalListingsBoats = deduplicate_listings_by_key(totalListingsBoats, 'link')

    save_new_listings(totalListingsCars)
    save_new_listings_boat(totalListingsBoats)
    
    actualTotalListings = totalListingsBoats + totalListingsCars

    if not flattenedCarListings and not flattenedBoatListings:
        print("No new listings found to process. Cycle complete.")
        # return

    print(f"Found {flattenedCarListings + flattenedBoatListings} total new listings to process.")
    
    # 3. Segregate the master list into the six processing queues
    processing_queues = separate_listings(actualTotalListings)
    
    # 4. Execute the single, unified round-robin evaluation
    process_listings_round_robin(processing_queues, driver, opts, service, totalListingsBoats, totalListingsCars)



    # process_scraped_data_boat(driver)
    # process_scraped_data(driver, opts, service)

    # would want to do:
    # every 30 min scrape listings from 3 sites
    # evaluate listings but going:
    # 1 cl car, 1cl boat, 1 fbm car, 1 fbm boat, 1 offerup car, 1 offerup boat
    # and repeat until any of the car/boat listings no longer has any left, so then
    # it may be 1 cl car, 1cl boat, 1 offer up car, because thers no more boats and fbm listings
    # then after 30 minutes of processing these, it would again scrape from all 3 sites, then
    # do valuations again from newest to oldest
    # 

