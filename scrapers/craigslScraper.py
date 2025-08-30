import os
import sys
import traceback
from inputimeout import inputimeout, TimeoutOccurred
import requests
from bs4 import BeautifulSoup
import json # Python's built-in library for handling JSON
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from uszipcode.search import SearchEngine

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

# def scrape_craigslist_v2(scrapedLinks, city, query):
def scrape_craigslist_v2(driver, scrapedLinks, url, category):

    """
    Scrapes Craigslist using the superior JSON-LD data method.
    """
    print(f" Starting Craigslist Scrape V2 for '{url}...")
    # --- Setup the WebDriver ---
    # Make sure you have chromedriver installed and in your PATH,
    # or specify the path to it.

    driver.get(url)

    print(f"Successfully navigated to {url}")
    
    scraped_data = []

    try:
        # --- Wait for the listings to be present on the page ---
        # We target the container for all search results to ensure the page is loaded.
        container = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "search-results-1"))
        )
        print("s: " + str(container))
        print("Search results container found. Proceeding to scrape listings.")
        listings = WebDriverWait(driver, 1000).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "cl-search-result"))
        )
        # --- Find all individual listing containers ---
        # listings = driver.find_elements(By.CLASS_NAME, 'cl-search-result cl-search-view-mode-gallery')
        
        if not listings:
            print("No listings found on the page with the selector 'div.cl-search-result'.")
            driver.quit()
            return []
            
        print(f"Found {len(listings)} listings to process.")

        # --- Loop through each listing to extract data ---
        for listing in listings:
            print("list: " + str(listing.get('title')))
            try:
                # --- Extract Title and Link ---
                title_element = listing.find_element(By.CSS_SELECTOR, 'a.posting-title')
                title = title_element.text
                link = title_element.get_attribute('href')

                # --- Extract Price ---
                try:
                    price = listing.find_element(By.CSS_SELECTOR, 'span.priceinfo').text
                except NoSuchElementException:
                    price = 'N/A' # Handle listings with no price

                # --- Extract Mileage and Location ---
                mileage = 'N/A'
                location = 'N/A'
                try:
                    # # The meta-line contains mileage and location
                    # meta_line_text = listing.find_element(By.CSS_SELECTOR, 'div.meta').text
                    # print("met1:" + str(meta_line_text))
                    # # Split the text to better isolate parts. The separator is usually a '•' or similar.
                    # # Selenium's .text property often uses spaces as separators. We can split by space.
                    # parts = [part.strip() for part in meta_line_text.split()]
                    
                    # # Find mileage (usually contains 'k mi')
                    # for part in parts:
                    #     if 'k mi' in part:
                    #         mileage = part
                    #         break
                    
                    # # Location is often the last part of the meta string
                    meta_div_full_text = listing.find_element(By.CSS_SELECTOR, 'div.meta-line .meta').text
                    # print("met2:" + str(meta_div_full_text))

                    if meta_div_full_text:
                        # Split by newline which often separates timestamp/mileage from location
                        location_parts = meta_div_full_text.split('\n')
                        if len(location_parts) == 3:
                           mileage = location_parts[1]
                           # The last element after splitting is typically the location.
                           location = location_parts[2]
                        elif len(location_parts) == 2:
                            mileage = location_parts[1]



                except NoSuchElementException:
                    mileage = 'N/A'
                    location = 'N/A'

                listing_data = {
                    'title': title,
                    'price': price,
                    'mileage': mileage,
                    'location': location,
                    'link': link,
                    'source': "Craigslist",
                    'priceChecked': False,
                    
                }
                # --- Compile the data for this listing ---
                if category == 'car':
                    listing_data = {
                    'title': title,
                    'price': price,
                    'mileage': mileage,
                    'location': location,
                    'link': link,
                    'source': "Craigslist",
                    'priceChecked': False,
                    'category': category
                    
                }
                else:
                    listing_data = {
                    'title': title,
                    'price': price,
                    'mileage': mileage,
                    'location': location,
                    'link': link,
                    'source': "Craigslist",
                    'priceChecked': False,
                    'category': category
                }
                print("list: " + str(listing.get('title')))

                # scraped_data.append(listing_data)
                scraped_data.insert(0,listing_data)

            except Exception as e:
                print(f"Could not process a listing. Error: {e}")
                continue # Move to the next listing
        return scraped_data
    except Exception as e:
        print(f"Error CL: {e}")
        traceback.print_exc()
    # try:
    #     # url = f"https://{city}.craigslist.org/d/cars-trucks/search/cta?query={query}"
    #     # url = "https://elpaso.craigslist.org/search/cta?query=car"
    #     # headers = {
    #     #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    #     # }
    #     # https_proxy = "http://45.90.219.12:4444"
    #     # proxies = {
    #     #     "http": https_proxy
    #     # }
    #     try:
    #         # response = requests.get(url, headers=headers, proxies=proxies)
    #         # response.raise_for_status()
    #         driver.get(link)
    #     except Exception as e:
    #     # except requests.exceptions.RequestException as e:
    #         print(f" Error fetching Craigslist page: {e}")
    #         return []
        
    #     page_source = driver.page_source
    #     soup = BeautifulSoup(page_source, 'html.parser')
    #     waitFuncSpecified(5)
    #     print("saa: " + str(soup))
    #     # --- OUR NEW STRATEGY ---
    #     # 1. Find the specific script tag with the data
    #     data_script = soup.find('script', id='ld_searchpage_results')
    #     # print("souce0: " + str(soup))
    #     # If the script tag isn't found, we can't proceed
    #     if not data_script:
    #         print(" Could not find the JSON-LD data script on the page. The site structure may have changed.")
    #         return []
    #     # print("souce1: " + str(data_script))
            
    #     # 2. Extract the JSON content from the script tag
    #     json_data = json.loads(data_script.string)
    #     # print("souce2: " + str(json_data))
    #     # --- The Hybrid Approach to get Links ---
    #     # The JSON data is missing the URL for each post, so we still need to grab those from the page.
    #     # We find all the listing containers and extract the `href` from the `<a>` tag inside each.
    #     # Note: The class 'cl-static-search-result' is what I see now, this might need updating again in the future.
    #     listing_elements = soup.find_all('li', class_='cl-static-search-result')
    #     links = [el.find('a')['href'] for el in listing_elements if el.find('a')]

    #     results = []
    #     # 3. Loop through the clean data
    #     # We use enumerate to get an index 'i' which we can use to retrieve the corresponding link.
    #     for i, item in enumerate(json_data['itemListElement']):
    #         item_details = item.get('item', {})
            
    #         title = item_details.get('name', 'N/A')
            
    #         # Price is nested inside 'offers'
    #         offers = item_details.get('offers', {})
    #         price = offers.get('price', '0.00')
            
    #         # Location is also nested
    #         location_info = offers.get('availableAtOrFrom', {}).get('address', {})
    #         location = location_info.get('addressLocality', 'N/A')
            
    #         # Add the link we scraped separately
    #         link = links[i] if i < len(links) else "N/A"
            
    #         if link in scrapedLinks:
    #             continue
    #         # Data Cleaning: Let's ignore listings with no price or a placeholder price
    #         try:
    #             if float(price) > 100: # Filter out $1 placeholders, etc.
    #                 results.append({
    #                     'title': title,
    #                     'price': f"${price}", # Format the price nicely
    #                     'location': location,
    #                     'link': link,
    #                     'source': 'Craigslist',
    #                     'priceChecked' : True
    #                 })
    #         except (ValueError, TypeError):
    #             # This handles cases where price isn't a valid number
    #             continue
                
    #     print(f" Found {len(results)} valid results from Craigslist.")
    #     # driver.quit()
    #     return results
    # except Exception as e:
    #     print(f"Error CL: {e}")
    #     traceback.print_exc()

# --- Let's run it! ---
# if __name__ == "__main__":
#     el_paso_deals = scrape_craigslist_v2(city="elpaso", query="car")
#     # links:
#     # https://wyoming.craigslist.org/search/farson-wy/cta?lat=42.17&lon=-109.3557&postal=78741&search_distance=1000#search=2~gallery~15 
#     # https://westky.craigslist.org/search/cadiz-ky/cta?lat=36.8168&lon=-87.8614&postal=78741&search_distance=1000#search=2~gallery~0
#     # https://saguenay.craigslist.org/search/baie-comeau-northeast-qc/cta?lat=51.3981&lon=-69.4177&postal=78741&search_distance=1000&lang=en&cc=us#search=2~gallery~0
    
#     # fb market zips:
#     # 97620, 85341, 82431, 79527, 55060, 71423, 30828, 13310, 33037
#     # https://www.facebook.com/marketplace/104040289631632/vehicles?sortBy=creation_time_descend&exact=true&radius_in_km=804
#     # https://www.facebook.com/marketplace/104068782961733/vehicles?sortBy=creation_time_descend&exact=true&radius_in_km=804
    
#     # new fb market links 
#     # https://www.facebook.com/marketplace/la/vehicles/?sortBy=creation_time_descend&exact=true&radius_in_km=804
#     # https://www.facebook.com/marketplace/nyc/vehicles/?sortBy=creation_time_descend&exact=true&radius_in_km=804
#     if el_paso_deals:
#         df = pd.DataFrame(el_paso_deals)
#         print(df)
#         save_new_listings(el_paso_deals)