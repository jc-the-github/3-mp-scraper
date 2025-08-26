import os
import requests
from bs4 import BeautifulSoup
import json # Python's built-in library for handling JSON
import pandas as pd


# def scrape_craigslist_v2(scrapedLinks, city, query):
def scrape_craigslist_v2(driver, scrapedLinks, link):

    """
    Scrapes Craigslist using the superior JSON-LD data method.
    """
    print(f" Starting Craigslist Scrape V2 for '{link}...")
    
    # url = f"https://{city}.craigslist.org/d/cars-trucks/search/cta?query={query}"
    # url = "https://elpaso.craigslist.org/search/cta?query=car"
    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    # }
    # https_proxy = "http://45.90.219.12:4444"
    # proxies = {
    #     "http": https_proxy
    # }
    try:
        # response = requests.get(url, headers=headers, proxies=proxies)
        # response.raise_for_status()
        driver.get(link)
    except Exception as e:
    # except requests.exceptions.RequestException as e:
        print(f" Error fetching Craigslist page: {e}")
        return []
    
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # --- OUR NEW STRATEGY ---
    # 1. Find the specific script tag with the data
    data_script = soup.find('script', id='ld_searchpage_results')
    
    # If the script tag isn't found, we can't proceed
    if not data_script:
        print(" Could not find the JSON-LD data script on the page. The site structure may have changed.")
        return []
        
    # 2. Extract the JSON content from the script tag
    json_data = json.loads(data_script.string)
    
    # --- The Hybrid Approach to get Links ---
    # The JSON data is missing the URL for each post, so we still need to grab those from the page.
    # We find all the listing containers and extract the `href` from the `<a>` tag inside each.
    # Note: The class 'cl-static-search-result' is what I see now, this might need updating again in the future.
    listing_elements = soup.find_all('li', class_='cl-static-search-result')
    links = [el.find('a')['href'] for el in listing_elements if el.find('a')]

    results = []
    # 3. Loop through the clean data
    # We use enumerate to get an index 'i' which we can use to retrieve the corresponding link.
    for i, item in enumerate(json_data['itemListElement']):
        item_details = item.get('item', {})
        
        title = item_details.get('name', 'N/A')
        
        # Price is nested inside 'offers'
        offers = item_details.get('offers', {})
        price = offers.get('price', '0.00')
        
        # Location is also nested
        location_info = offers.get('availableAtOrFrom', {}).get('address', {})
        location = location_info.get('addressLocality', 'N/A')
        
        # Add the link we scraped separately
        link = links[i] if i < len(links) else "N/A"
        
        if link in scrapedLinks:
            continue
        # Data Cleaning: Let's ignore listings with no price or a placeholder price
        try:
            if float(price) > 100: # Filter out $1 placeholders, etc.
                results.append({
                    'title': title,
                    'price': f"${price}", # Format the price nicely
                    'location': location,
                    'link': link,
                    'source': 'Craigslist'
                })
        except (ValueError, TypeError):
            # This handles cases where price isn't a valid number
            continue
            
    print(f" Found {len(results)} valid results from Craigslist.")
    return results

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