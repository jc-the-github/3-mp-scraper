import json
import os
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
        print("[Offer Up] No new listings to save.")
        return

    # Open both files in append mode to add new data
    with open(DATABASE_FILE, 'a', encoding='utf-8') as db_f, \
         open(SEEN_URLS_FILE, 'a', encoding='utf-8') as urls_f:
        for listing in new_listings:
            # Write the full JSON object to the database
            db_f.write(json.dumps(listing, ensure_ascii=False) + '\n')
            # Write just the unique URL to the index
            urls_f.write(listing['link'] + '\n')
            
    print(f"[Offer Up] Appended {len(new_listings)} new listings to database.")

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


# def saveHTML():
    # global categories
    # fileName = categories[categoryIndex]
    # fileName = 'unsorted HTML Data/' + \
    #     str(categories[categoryIndex]) + 'PawnHTML.txt'

    # waitFuncSpecified(1)
    # newPawnListingsHTML = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
    #     (By.XPATH, "/html/body/div[1]/div/div/div[2]/div/div[2]/div[1]"))).get_attribute('outerHTML')

    # # save to file
    # # first read contents
    # pawnListingsHTMLFile = open(
    #     fileName, 'r', encoding="utf8")
    # pawnListingsHTML = pawnListingsHTMLFile.read()
    # pawnListingsHTMLFile.close()

    # # add to contents
    # pawnListingsHTML += "\n"
    # pawnListingsHTML += str(newPawnListingsHTML)
    # print("huh " + pawnListingsHTML)

    # # write to contents
    # pawnListingsHTMLFile = open(fileName, 'w', encoding="utf8")
    # pawnListingsHTMLFile.write(str(pawnListingsHTML))
    # pawnListingsHTMLFile.close()


def offerUpScraper(driver, scrapedLinks):
    
    # # Vars
    # service = Service()

    # opts = webdriver.ChromeOptions()
    # PROXY = '45.90.219.12:4444'
    # user_agent = 'Mozilla/5.0 CK={} (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'

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
    
    scraped_data = []
    try:
        driver.get("https://offerup.com/explore/k/5/1?DISTANCE=5000&SORT=-posted")
        # --- Wait for the list of items to be present ---
        # We target the main <ul> container for all listings
        # WebDriverWait(driver, 20).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[class*="jss"]'))
        # )
        # print("Listings container found. Proceeding to scrape.")

        # # --- Find all individual listing containers ---
        # # The class names like 'jss603' are dynamic. We find a list item 'li'
        # # that contains a link 'a' with '/item/detail/' in its href.
        # # listings = driver.find_elements(By.CSS_SELECTOR, 'li a[href*="/item/detail/"]')
        # listings = WebDriverWait(driver, 1000).until(
        #     EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[5]/div[2]/main/div[4]/div/div[1]/ul/li[3]'))
        # )
        listings = WebDriverWait(driver, 1000).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'jss254'))
        )
        if not listings:
            print("No listings found on the page.")
            driver.quit()
            return []
            
        print(f"OFFUP Found {len(listings)} listings to process.")
        
        # --- Loop through each listing to extract data ---
        for listing in listings:
            print("listing: " + str(listing))
            try:
                # --- Extract Title ---
                # The title is in a span with a class like 'jss605'
                listing_string = listing.get_attribute("aria-label")
                # title = listing.find_element(By.CSS_SELECTOR, 'span[class*="jss605"]').text
            
                # --- Extract Link ---
                # Combine the relative href with the base URL
                relative_link = listing.get_attribute('href')
                link = f"https://offerup.com{relative_link}" if relative_link.startswith('/') else relative_link
                # 1. Execute your first split. The '1' ensures it only splits on the first '$'.
                title, remaining_details = listing_string.split(' $', 1)

                # 2. Split the rest by the unique phrase " miles in ".
                price_and_miles, location = remaining_details.split(' miles in ', 1)

                # 3. Now split the price_and_miles part by the space between them.
                price, miles_raw = price_and_miles.split(' ', 1)

                # 4. Combine the mileage number and the word "miles" for the final variable.
                mileage = f"{miles_raw} miles"
                # # --- Extract Price and Mileage ---
                # price = 'N/A'
                # mileage = 'N/A'
                # try:
                #     # Both price and mileage are in spans inside a parent span with a class like 'jss602'
                #     price_mileage_elements = listing.find_elements(By.CLASS_NAME, 'jss254')

                #     # price_mileage_elements = listing.find_elements(By.CSS_SELECTOR, 'span[class*="jss602"] > span')
                #     print("hi" + price_mileage_elements.text)
                #     if len(price_mileage_elements) >= 1:
                #         price = price_mileage_elements[0].text
                #     if len(price_mileage_elements) >= 2:
                #         mileage = price_mileage_elements[1].text
                # except Exception as e:
                #     print("Error OfferUp: " + str(e))
                #     traceback.print_exc()

                # # --- Extract Location ---
                # try:
                #     # The location is in a span with Typography 'body2'
                #     location = listing.find_element(By.CSS_SELECTOR, 'span.MuiTypography-body2').text
                # except Exception as e:
                #     print("Error OfferUp: " + str(e))
                #     traceback.print_exc()
                #     location = 'N/A'
                
                # --- Compile the data for this listing ---
                # Filter out non-vehicle items that might get scraped by mistake
                if "miles" in mileage or mileage == 'N/A':
                    listing_data = {
                        'title': title,
                        'price': price,
                        'mileage': mileage,
                        'location': location,
                        'link': link,
                        'priceChecked': False
                    }
                    scraped_data.append(listing_data)

            except Exception as e:
                print("Error OfferUp: " + str(e))
                traceback.print_exc()
                continue
        return scraped_data           
    except Exception as e:
        print("Error OfferUp: " + str(e))
        traceback.print_exc()
    # zip_code = 66045
    # try:
    #         # Step 1: Go to the initial page
    #         print("1. Navigating to OfferUp homepage...")
    #         driver.get("https://offerup.com/explore/k/5/1?DISTANCE=5000&SORT=-posted")
    #         # driver.get("https://offerup.com/search?q=car&DISTANCE=5000&SORT=-posted")

    #         # # Now we grab the HTML of the results list, just like you identified
    #         page_source = driver.page_source
    #         soup = BeautifulSoup(page_source, 'html.parser')
            
    #         # # You correctly identified the <ul> as the container. Let's find all the list items.
    #         # # The class name "jss369" from your example might change, but the list item tag <li> is stable.
    #         # # We will target the link `<a>` inside each list item as it contains all the data we need.
    #         listings = soup.find_all('a', class_='jss254') # Using a class from your example that seems specific to listings
            
    #         results = []
    #         for listing in listings:
    #             title = listing.get('title', 'N/A')
    #             link = "https://offerup.com" + listing.get('href', 'N/A')
    #             if link in scrapedLinks:
    #                 continue
    #             # Extracting price and location is trickier due to complex classes
    #             # We find all text elements and piece it together
    #             text_spans = listing.find_all('span')
                
    #             price = "N/A"
    #             location = "N/A"
                
    #             # This logic assumes a consistent structure within the listing card
    #             if len(text_spans) >= 4:
    #                 price = text_spans[2].text.strip()
    #                 location = text_spans[3].text.strip()

    #             results.append({
    #                 'title': title,
    #                 'price': price,
    #                 'location': location,
    #                 'link': link,
    #                 'source': 'OfferUp',
    #                 'priceChecked': True
    #             })
                
    #         print(f" Found {len(results)} results from OfferUp.")
    #         # driver.quit()
    #         return results
    # except Exception as e:
    #     print("Error OfferUp: " + str(e))
    #     traceback.print_exc()
    # finally:
    #     driver.quit() # Always close the browser`

# if __name__ == "__main__":
#     # You can change these values to whatever you need
#     target_zip = "78741" 
#     target_query = "car"
    
#     offerup_deals = offerUpScraper()
#         # offerup_deals = offerUpScraper(zip_code=target_zip, search_query=target_query)

#     if offerup_deals:
#         df = pd.DataFrame(offerup_deals)
#         print(df)
