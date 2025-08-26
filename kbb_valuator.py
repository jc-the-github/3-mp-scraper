import json
import re
import os
import sys
import time
from bs4 import BeautifulSoup
# import inputimeout
import pgeocode
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
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
MAX_NAVIGATION_STEPS = 4
# --- Constants ---
DATABASE_FILE = "scraped_listings.jsonl"

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

def save_data(data):
    """Writes a list of dictionaries to a .jsonl file, overwriting it."""
    with open("scraped_listings.jsonl", 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

def sendTelegramNotif(listing, updates):
    TOKEN = "YOUR TELEGRAM BOT TOKEN"
    chat_id = "YOUR CHAT ID"
    price = listing.get('price', 'notfound')
    privateValue = updates.get('private_party_value', 'notfound')
    if price != "notfound" and privateValue != 'notfound':
        cleaned_parts = privateValue.replace('$', '').replace(',', '').split(' - ')

        # Convert the string parts to integers
        min_value = int(cleaned_parts[0])
        max_value = int(cleaned_parts[1])
        average_value = (max_value - min_value) / 2  + min_value
        message = f"Car Deal Alert: \n {listing.get('title', ' ')} \n {listing.get('link', ' ')} \n {listing.get('location', ' ')}"
        percentage = priceDiff / average_value

        if price < min_value:
            priceDiff = min_value - price
            messPrefix = "Good Deal!"
            messSuff = "Difference: " + str(priceDiff) + " Percentage: " + str(percentage)
            message = messPrefix + message + messSuff
        elif price < average_value:
            messPrefix = "Possible Deal!"
            messSuff = "Difference: " + str(priceDiff) + " Percentage: " + str(percentage)
            message = messPrefix + message + messSuff
        if price < min_value or price < average_value:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"

    print(requests.get(url).json())

def update_listing(data, identifier_link, updates):
    """
    Finds a listing by its link and applies updates.
    'updates' is a dictionary of new key-value pairs to set.
    Returns the modified data list and a flag indicating if found.
    """
    print("update listing dbug")
    found = False
    # listing.get('')
    for listing in data:
        if listing.get('link') == identifier_link:
            print("found link")
            # The .update() method merges the dictionaries,
            # overwriting existing keys and adding new ones.
            listing.update(updates)
            sendTelegramNotif(listing, updates)

            found = True
            break # Stop searching once found

    save_data(data)
    return data, found

# --- KBB Manager & Utilities ---
def get_zip_from_city_state(city, state_abbr):
    print(f"[Geo] Looking up zip for {city}, {state_abbr}...")
    try:
        search = SearchEngine(
            simple_or_comprehensive=SearchEngine.SimpleOrComprehensiveArgEnum.simple,
        )
        res = search.by_city_and_state(str(city), str(state_abbr), returns=1)
        if res is not None:
            zipcode = res[0].zipcode
            print("got this zip: " + str(zipcode))
            return zipcode
        else:
            print("[Geo] Lookup failed: No zip codes found from: " + str(city) + ", " + str(state_abbr) + ". Using default.")
            return "97620"
    except Exception as e:
        print(f"[Geo] Lookup failed: {e}. Using default.")
    return "97620" # Default zip

def get_kbb_valuation_via_search(driver, opts, service, listing_title, mileage, city, state):
    # --- DISCLAIMER ---
    # This function uses absolute XPaths as requested. This is not a recommended
    # practice for production systems as it is extremely brittle. Any minor
    # change to the KBB website's HTML structure will break these selectors.
    # A more robust solution would use relative selectors based on stable
    # attributes like 'data-testid', 'id', or functional class names.
    
    print(f"\n[KBB Search] Starting valuation for: {listing_title}")
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
    # proxies = {
    #     'http': 'http://45.90.219.12:4444'
    # }
    
    # # webdriver.DesiredCapabilities.CHROME['acceptSslCerts'] = True
    # opts.add_argument("user-agent="+user_agent)
    # # opts.accept_insecure_certs = True
    # print(webdriver.DesiredCapabilities.CHROME)
    # driver = webdriver.Chrome(service=service, options=opts)
    wait = WebDriverWait(driver, 25)
    
    valuation_results = {"trade_in_value": "N/A", "private_party_value": "N/A"}

    try:
        zip_code = get_zip_from_city_state(city, state)
        # query_title = listing_title.replace(" ", "+")
        # Step 1: DuckDuckGo Search
        fullLink = "https://duckduckgo.com/" + listing_title + " kelly blue book"
        driver.get(fullLink)
        # search_input = wait.until(EC.visibility_of_element_located((By.ID, "search_form_input_homepage")))
        # search_input.send_keys(f"{listing_title} site:kbb.com")
        # search_input.send_keys(Keys.ENTER)

        # Step 2: Find and click the first KBB link
        # Find all result list items, including ads and organic results
        all_results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ol.react-results--main > li")))
        kbb_link = ""
        kbb_link_found = False
        for result in all_results:
            # Check if the result is organic and contains a kbb.com link
            if result.get_attribute("data-layout") == "organic":
                try:
                    # Find the link within this specific organic result
                    link_element = result.find_element(By.CSS_SELECTOR, "a[data-testid='result-title-a'][href*='kbb.com']")
                    print(f"[DDG] Found organic link: {link_element.get_attribute('href')}")
                    # link_element.click()
                    kbb_link = str(link_element.get_attribute('href'))
                    print("klink: ")
                    kbb_link_found = True
                    break # Exit the loop once the first organic link is clicked
                except NoSuchElementException:
                    # This organic result was not a kbb link, continue to the next one
                    continue

        if not kbb_link_found:
            print("[DDG] ERROR: No organic kbb.com link found on the first page of results.")
            return None
        params = {
            "intent": "buy-used",
            "mileage": re.sub(r'\D', '', str(mileage)),
            "zipcode": zip_code
        }
        # initial_url = f"https://www.kbb.com/{make_fmt}/{model_fmt}/{year}/styles/?{urlencode(params)}"
        current_url = kbb_link + f"styles/?{urlencode(params)}"
        print(f"[KBB Direct] Fetching initial URL: {current_url}")
        initial_styles_url = current_url
        try:
            # --- Step 1: Go to the link and check for style selection ---
            driver.get(initial_styles_url)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Check if the style selection box exists on the page
            style_selection_box = soup.find(id='box-style')

            if style_selection_box:
                # --- Scenario A: No Redirect, Style Selection is Required ---
                print("[KBB] Style selection page detected. Building new link with the first style.")
                
                # Find the first radio button to get the style name
                first_style_radio = style_selection_box.find('input', {'type': 'radio'})
                if not first_style_radio or not first_style_radio.get('name'):
                    raise ValueError("Could not find a valid style radio button on the page.")
                    
                style_name = first_style_radio.get('name')
                print(f"[KBB] Found first style: '{style_name}'")

                # Format the style name for the URL path (e.g., "LE Sedan 4D" -> "le-sedan-4d")
                style_slug = style_name.lower().replace(' ', '-')
                
                # Deconstruct the initial URL to rebuild it with the new style path
                parsed_url = urlparse(initial_styles_url)
                path_parts = parsed_url.path.strip('/').split('/') # e.g., ['toyota', 'camry', '2010', 'styles']
                
                if len(path_parts) < 3:
                    raise ValueError("Initial URL format is incorrect. Could not extract make/model/year.")

                make, model, year = path_parts[0], path_parts[1], path_parts[2]
                new_path = f"/{make}/{model}/{year}/{style_slug}/"
                
                # Get original mileage from the initial URL's query string to carry it over
                initial_query_params = parse_qs(parsed_url.query)
                mileage = initial_query_params.get('mileage', ['null'])[0]

                # Build the new URL with the specified parameters
                new_params = {
                    "condition": "good",
                    "intent": "buy-used",
                    "mileage": mileage, # Carry over the original mileage
                    "pricetype": "private-party",
                }
                
                final_valuation_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    new_path,
                    '',
                    urlencode(new_params),
                    ''
                ))
                
                print(f"[KBB] Navigating to newly constructed URL: {final_valuation_url}")
                driver.quit()
                
                # service = Service()
                # opts = webdriver.ChromeOptions()
                driver = webdriver.Chrome(service=service, options=opts)
                container_locator = (By.XPATH, "/html/body/div[2]/div/div/div[1]/div[5]/div/div/div/div/div[1]/div/div[1]/div[1]/div/div[1]/object")
                driver.get(final_valuation_url)
                wait = WebDriverWait(driver, 15) 
                # finallyPrice = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div/div[1]/div[5]/div/div/div/div/div[1]/div/div[1]/div[1]/div/div[1]/object")))
                # finallyPrice = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div/div[1]/div[5]/div/div/div/div/div[1]/div/div[1]/div[1]/div/div[1]/object/svg/g[1]/g/text[2]")))
                

            else:
                # --- Scenario B: Redirect Occurred, Already on Valuation Page ---
                print("[KBB] Redirect detected or already on a final valuation page.")
                # The driver is already on the correct page, so we just proceed.
                new_params = '?condition=good&intent=buy-used&mileage=0&pricetype=private-party'
                # Split the link at 'options/' and take the first part, which is the base URL you want.
                base_url = driver.current_url.split('options/')[0]
                # Combine the base URL with your new parameters.
                final_valuation_url = base_url + new_params

                print(f"[KBB] Navigating to newly constructed URL: {final_valuation_url}")
                driver.quit()
                
                # service = Service()
                # opts = webdriver.ChromeOptions()
                driver = webdriver.Chrome(service=service, options=opts)
                container_locator = (By.XPATH, "/html/body/div[2]/div/div/div[1]/div[5]/div/div/div/div/div[1]/div/div[1]/div[1]/div/div[1]/object")
                driver.get(final_valuation_url)
                wait = WebDriverWait(driver, 15) 
                # pass
            wait.until(EC.frame_to_be_available_and_switch_to_it(container_locator))
        
            # Step 2: Now inside the object, pinpoint the specific text element.
            # This XPath is now running inside the SVG document.
            target_text_locator = (By.XPATH, "/*[local-name()='svg']/*[local-name()='g'][1]/*[local-name()='g'][@id='RangeBox']/*[local-name()='text'][2]")
            print(f"[ACTION] Switched focus. Locating target text with XPath: {target_text_locator[1]}")
            # print("d: " + str(driver.page_source))
            target_element = wait.until(EC.visibility_of_element_located(target_text_locator))
            
            price = target_element.text 

            # print("d: " + str(price))
            # --- Step 2: Get the price values from the final page ---
            print("[KBB] Extracting price from SVG chart...")

            driver.quit()
            # print(f"[SUCCESS] Extracted Private Party Value: {private_party_value}")
            return {"private_party_value": price, "zipCode": zip_code, "priceChecked": True}
            # return {"private_party_value": price, "all_svg_values": values}


            
        except Exception as e:
            print(f"[KBB] ERROR: An unexpected error occurred. {e}")
            return None
        finally:
            print("[KBB] Valuation process finished.")
            # if 'driver' in locals():
            #     driver.quit()
        

    except (TimeoutException, ValueError, Exception) as e:
        print(f"[KBB] ERROR: A step in the process failed. Details: {e}")
        return None
    finally:
        if driver:
            driver.quit()
   

# --- Main Processing Logic ---
def parse_listing_title(title):
    match = re.search(r"(\b\d{4}\b)\s+([a-zA-Z\s\-'.]+)", title)
    if match:
        year = match.group(1).strip()
        remaining_title = title[match.end():].strip()
        return {'year': year, 'full_title': remaining_title}
    return None

def process_scraped_data(driver, opts, service):
    print("--- Starting Unified Valuation Processor ---")
    # official_makes = get_all_makes()
    # if not official_makes: return
    try:
        listings = []
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            for line in f: listings.append(json.loads(line))
        print(f"Loaded {len(listings)} listings from '{DATABASE_FILE}'.")
    except FileNotFoundError:
        print(f"ERROR: Database file '{DATABASE_FILE}' not found. Run a scraper first.")
        return

    for i, listing in enumerate(listings):
        
        # print("driver: " + str(driver) )
        # if driver is None:
        #     print("driver is none")
            # service = Service()
            # opts = webdriver.ChromeOptions()
        print(f"\n--- Processing Listing {i+1}/{len(listings)}: {listing['title']} ---")
        parsed_info = parse_listing_title(listing['title'])
        if listing['priceChecked']:
            continue


        if not parsed_info: continue
        if listing['title'] == 'N/A':
            continue
        if i > 0:
            driver = webdriver.Chrome(service=service, options=opts)
        # best_make_match = process.extractOne(parsed_info['full_title'], official_makes)
        # if not best_make_match or best_make_match[1] < MATCH_SCORE_THRESHOLD: continue
        # validated_make = best_make_match[0]
        
        # model_guess = parsed_info['full_title'].replace(validated_make, "", 1).strip()
        # official_models = get_models_for_make(validated_make)
        # if not official_models: continue
        
        # best_model_match = process.extractOne(model_guess, official_models)
        # if not best_model_match or best_model_match[1] < MATCH_SCORE_THRESHOLD: continue
            
        # print(f"[NHTSA] Vehicle validated.")
        
        # City/State parsing from listing['location']
        location_parts = listing.get('location', '').split(',')
        city = location_parts[0].strip() if len(location_parts) > 0 else "El Paso"
        state = location_parts[1].strip() if len(location_parts) > 1 else "TX"

        newData = get_kbb_valuation_via_search(driver= driver,
            opts= opts,
            service= service,
            listing_title=listing['title'],
            mileage=listing.get('mileage', '0'),
            city=city,
            state=state
        )
        # updatedData = {'title'=listing['title'],
        #     mileage=listing.get('mileage', '0'),
        #     city=city,
        #     state=state}
        
        if newData:
            print(f"KBB VALUATION FOUND: {newData}")
            update_listing(listings, listing.get('link', ' ',), newData)
        else:
            print("KBB VALUATION FAILED for this vehicle.")

# if __name__ == "__main__":
#     process_scraped_data()

































































# MATCH_SCORE_THRESHOLD = 85
# NHTSA_MAKES_CACHE_FILE = "nhtsa_makes.json"
# NHTSA_MODELS_CACHE_DIR = "nhtsa_models_cache"
# NHTSA_BASE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles"

# # --- NHTSA Manager Functions ---
# def get_all_makes():
#     if os.path.exists(NHTSA_MAKES_CACHE_FILE):
#         with open(NHTSA_MAKES_CACHE_FILE, 'r') as f: return json.load(f)
#     try:
#         url = f"{NHTSA_BASE_URL}/GetAllMakes?format=json"
#         response = requests.get(url, timeout=30)
#         response.raise_for_status()
#         makes_list = sorted([m['Make_Name'].strip() for m in response.json()['Results']])
#         with open(NHTSA_MAKES_CACHE_FILE, 'w') as f: json.dump(makes_list, f, indent=4)
#         return makes_list
#     except requests.exceptions.RequestException as e: return []

# def get_models_for_make(make_name):
#     if not os.path.exists(NHTSA_MODELS_CACHE_DIR): os.makedirs(NHTSA_MODELS_CACHE_DIR)
#     safe_make_name = "".join(c for c in make_name if c.isalnum())
#     cache_file = os.path.join(NHTSA_MODELS_CACHE_DIR, f"{safe_make_name}.json")
#     if os.path.exists(cache_file):
#         with open(cache_file, 'r') as f: return json.load(f)
#     try:
#         url = f"{NHTSA_BASE_URL}/GetModelsForMake/{make_name.replace(' ', '%20')}?format=json"
#         response = requests.get(url, timeout=30)
#         response.raise_for_status()
#         models_list = sorted([m['Model_Name'].strip() for m in response.json()['Results']])
#         with open(cache_file, 'w') as f: json.dump(models_list, f, indent=4)
#         return models_list
#     except requests.exceptions.RequestException as e: return []


    # Target the <object> tag directly by its unique ID for maximum reliability.
            # final_page_soup = BeautifulSoup(driver.page_source, 'html.parser')
            # finallyPrice = finallyPrice.get_attribute("data")
            # svg_object = final_page_soup.find('object', id='priceAdvisor')
            # driver.get(finallyPrice)
            # if not svg_object or not svg_object.has_attr('data'):
            #     raise ValueError("Found the page but could not find the SVG object with id='priceAdvisor' or its data attribute.")

            # svg_url = svg_object['data']
            # full_svg_url = urljoin(driver.current_url, svg_url)

            # print(f"[EXTRACT] Navigating to SVG URL: {full_svg_url}")
            # driver.get(full_svg_url)

            # textYuh = finallyPrice.get_attribute("text")
            # svg_soup = BeautifulSoup(driver.page_source, 'xml')
            # print("pruec??: " + str(textYuh))
            # price_text_nodes = svg_soup.select("g text")
            # if not price_text_nodes:
            #     raise ValueError("Could not find any price text nodes within the SVG.")
            
            # values = [node.text for node in price_text_nodes if '$' in node.text]
            # private_party_value = values[0] if values else "Price Not Found"
# driver.get(initial_url)
            # --- Multi-Step Navigation Loop ---
        # for step in range(MAX_NAVIGATION_STEPS):
        #     print(f"[KBB Nav Step {step+1}] Navigating to: {current_url}")
        #     driver.get(current_url)
        #     page_source = driver.page_source
        #     soup = BeautifulSoup(page_source, 'html.parser')

        #     # CHECK 1: Are we on the final valuation page? (Success condition)
        #     svg_object = soup.find('object', {'type': 'image/svg+xml'})
        #     if svg_object:
        #         print("[KBB] Valuation page reached. Proceeding to price extraction.")
        #         # The rest of the logic will run after this loop breaks
        #         break
            
        #     # CHECK 2: Are we on a CATEGORY selection page? (e.g., Sedan, SUV)
        #     # Selector targets the clickable div you provided. We find its parent link.
        #     category_link = soup.select_one('a:has(div[data-lean-auto^="category-"])')
        #     if category_link and category_link.get('href'):
        #         print("[KBB] Category selection page detected. Selecting first category.")
        #         path = category_link['href']
        #         current_url = f"https://www.kbb.com{path}"
        #         continue # Go to the next step in the loop with the new URL
            
        #     # CHECK 3: Are we on a STYLE/TRIM selection page?
        #     style_link = soup.select_one("a[data-testid^='style-card-content-']")
        #     if style_link and style_link.get('href'):
        #         print("[KBB] Style/Trim selection page detected. Selecting first style.")
        #         path = style_link['href']
                
        #         # We MUST rebuild the URL with our parameters
        #         base_url = f"https://www.kbb.com{path}"
        #         parsed_url = urlparse(base_url)
        #         query_params = parse_qs(parsed_url.query)
        #         query_params.update(params)
                
        #         new_query = urlencode(query_params, doseq=True)
        #         current_url = urlunparse(parsed_url._replace(query=new_query))
        #         continue # Go to the next step in the loop

        #     # If none of the above, we are on an unknown page
        #     raise ValueError(f"Unknown page structure at {driver.current_url}. Aborting.")
        # else:
        #     # This 'else' belongs to the 'for' loop. It runs if the loop completes without 'break'.
        #     raise TimeoutError(f"Failed to reach valuation page within {MAX_NAVIGATION_STEPS} steps.")

        # # --- Price Extraction (runs after loop breaks successfully) ---
        # svg_url = svg_object['data']
        # print(f"[KBB] Navigating to SVG content: {svg_url}")
        # driver.get(svg_url)
        
        # svg_source = driver.page_source
        # svg_soup = BeautifulSoup(svg_source, 'xml')
        # price_text_nodes = svg_soup.select("g text")
        
        # if len(price_text_nodes) > 1:
        #     private_party_value = price_text_nodes[1].text
        #     print(f"[KBB] SUCCESS: Found Private Party Value: {private_party_value}")
        #     return {"private_party_value": private_party_value}
        # else:
        #     raise ValueError("Could not find price text within SVG source.")



     #     headers = {

    #         'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    #     }
        
    #     session = requests.Session()
    #     session.headers.update(headers)
    #     # session = requests.Session()
    #     # session.headers.update({
    #     #     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    #     # })
    #     # `allow_redirects=True` is the default, requests handles it automatically
    #     response = session.get("https://www.kbb.com/bmw/4-series/2018/styles/?intent=buy-used&mileage=180000", timeout=20, proxies=proxies)
    #     response.raise_for_status()

    #     final_html = ""
        
    #     # Step 2: Analyze the response (redirect or style selection)
    #     if response.history: # A redirect occurred
    #         print("[KBB Direct] Redirect detected. No style selection needed.")
    #         final_url = response.url
    #         # Replicate `transformURLFirstCase` logic to ensure pricetype is set
    #         parsed_url = urlparse(final_url)
    #         query_params = parse_qs(parsed_url.query)
    #         query_params['pricetype'] = ['private-party']
            
    #         # Rebuild the URL
    #         new_query = urlencode(query_params, doseq=True)
    #         url_to_fetch = urlunparse(parsed_url._asdict()._replace(query=new_query))
            
    #         print(f"[KBB Direct] Fetching final redirected URL: {url_to_fetch}")
    #         final_response = session.get(url_to_fetch, timeout=20)
    #         final_response.raise_for_status()
    #         final_html = final_response.text
    #     else: # No redirect, style selection is required
    #         print("[KBB Direct] Style selection required. Parsing styles...")
    #         soup = BeautifulSoup(response.text, 'html.parser')
    #         # Find all style links and pragmatically choose the first one
    #         style_links = soup.select("a[data-testid^='style-card-content-']")
    #         if not style_links:
    #             raise ValueError("Could not find any style/trim options on the page.")
            
    #         first_style_path = style_links[0]['href']
    #         style_url = f"https://www.kbb.com{first_style_path}"
            
    #         # Replicate `fetchHtmlDataFromKbbBodyStyleSelected`
    #         parsed_style_url = urlparse(style_url)
    #         query_params = parse_qs(parsed_style_url.query)
    #         query_params.update(params) # Add original params like mileage
    #         query_params['pricetype'] = ['private-party']
            
    #         url_to_fetch = urlunparse(parsed_style_url._asdict()._replace(query=new_query))
            
    #         print(f"[KBB Direct] Fetching selected style URL: {url_to_fetch}")
    #         final_response = session.get(url_to_fetch, timeout=20)
    #         final_response.raise_for_status()
    #         final_html = final_response.text

    #     # Step 3: Extract the SVG URL from the final HTML
    #     print("[KBB Direct] Parsing final HTML to find SVG URL...")
    #     final_soup = BeautifulSoup(final_html, 'html.parser')
    #     # The SVG is often inside an <object> tag
    #     svg_object = final_soup.find('object', {'type': 'image/svg+xml'})
    #     if not svg_object or not svg_object.get('data'):
    #         raise ValueError("Could not find the SVG object tag in the final HTML.")
            
    #     svg_url = svg_object['data']
        
    #     # Step 4: Fetch the SVG content
    #     print(f"[KBB Direct] Fetching SVG content from: {svg_url}")
    #     svg_response = session.get(svg_url, timeout=20)
    #     svg_response.raise_for_status()
        
    #     # Step 5: Parse the SVG XML to get the price
    #     print("[KBB Direct] Parsing SVG to extract price text...")
    #     svg_soup = BeautifulSoup(svg_response.text, 'xml')
    #     price_text_nodes = svg_soup.select("g text")
        
    #     if len(price_text_nodes) > 1:
    #         private_party_value = price_text_nodes[1].text
    #         print(f"[KBB Direct] SUCCESS: Found Private Party Value: {private_party_value}")
    #         # The extension logic can be expanded here to get Trade-In etc.
    #         return {"private_party_value": private_party_value}
    #     else:
    #         raise ValueError("Could not find price text nodes within the SVG.")

    # except requests.exceptions.RequestException as e:
    #     print(f"[KBB Direct] ERROR: An HTTP request failed. {e}")
    #     return None
    # except (ValueError, IndexError, AttributeError) as e:
    #     print(f"[KBB Direct] ERROR: Failed to parse page content or SVG. Site structure may have changed. {e}")
    #     return None
    #     # --- KBB Interaction Sequence using Absolute XPaths ---
    #     print("[KBB] Executing interaction sequence...")
        
    #     # User Step 1
    #     wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div/div[1]/div[2]/div[1]/div[2]/div/div/div[2]/div/div[2]/div/div[2]/div[1]/div[2]/div/div/div[1]/a"))).click()
        
    #     # User Step 2
    #     wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/main/div[2]/div/div/div/div/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div/div[1]/label/div/div/div/div/div[2]/span"))).click()
        
    #     # User Step 3: Input Mileage
    #     mileage_input = wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[2]/div/main/div[2]/div/div/div/div/div/div/div[1]/div[2]/div/div[2]/div/div[1]/div/div[1]/label/input")))
    #     mileage_input.send_keys(re.sub(r'\D', '', str(mileage)))
        
    #     # User Step 4: Input Zip Code
    #     zip_input = wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[2]/div/main/div[2]/div/div/div/div/div/div/div[1]/div[2]/div/div[2]/div/div[1]/div/div[2]/label/input")))
    #     zip_input.send_keys(Keys.CONTROL + "a"); zip_input.send_keys(Keys.DELETE)
    #     zip_input.send_keys(zip_code)

    #     # User Step 5
    #     wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/main/div[2]/div/div/div/div/div/div/div[1]/div[2]/div/div[2]/div/div[2]/div/div/button"))).click()

    #     # User Steps 6-9: Condition Questions
    #     wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/main/div[2]/div/div/div/div/div/div/div[1]/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div[2]/label/div/div"))).click()
    #     wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/main/div[2]/div/div/div/div/div/div/div[1]/div[2]/div/div[2]/div/div/div/div[2]/div/div/div[2]/div/div[1]/label/div"))).click()
    #     wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/main/div[2]/div/div/div/div/div/div/div[1]/div[2]/div/div[2]/div/div/div/div[3]/div[2]/label[1]/div/div/div"))).click()
    #     wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/main/div[2]/div/div/div/div/div/div/div[1]/div[2]/div/div[3]/div/div/button"))).click()
        
    #     # User Steps 10-12 are likely transient pages/popups, we proceed to value extraction.
        
    #     # --- Value Extraction ---
    #     object_element_xpath = "/html/body/div[2]/div/main/div[2]/div/div/div/div/div/div/div/div[1]/div/div[3]/div/div/div/div[3]/div[1]/div/div[2]/div[1]/div[2]/div/div/div/object"
    #     svg_text_xpath_inside_frame = "/svg/g[1]/g/text[2]"

    #     # Extract Trade-In Value
    #     print("[KBB] Extracting Trade-In Value...")
    #     wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, object_element_xpath)))
    #     trade_in_text_element = wait.until(EC.visibility_of_element_located((By.XPATH, svg_text_xpath_inside_frame)))
    #     valuation_results["trade_in_value"] = trade_in_text_element.text
    #     driver.switch_to.default_content()

    #     # User Step: Click Private Party Button
    #     private_party_button_xpath = "/html/body/div[2]/div/main/div[2]/div/div/div/div/div/div/div/div[1]/div/div[3]/div/div/div/div[2]/div/div[2]/div/button[1]/div"
    #     wait.until(EC.element_to_be_clickable((By.XPATH, private_party_button_xpath))).click()
        
    #     # Extract Private Party Value
    #     print("[KBB] Extracting Private Party Value...")
    #     wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, object_element_xpath)))
    #     private_party_text_element = wait.until(EC.visibility_of_element_located((By.XPATH, svg_text_xpath_inside_frame)))
    #     valuation_results["private_party_value"] = private_party_text_element.text
    #     driver.switch_to.default_content()
        
    #     return valuation_results

    # except (TimeoutException, NoSuchElementException) as e:
    #     print(f"[KBB] ERROR: A step in the sequence failed. An XPath may be broken. Details: {e}")
    #     return None
    # finally:
    #     driver.quit()