import json
import kbb_valuator # Import the new KBB manager

DATABASE_FILE = "scraped_listings.jsonl"

def process_scraped_data():
    print("--- Starting Valuation Processor (Google-Powered) ---")
    
    # 1. Load links of listings we have already valuated to avoid redundant work.
    processed_links = kbb_valuator.load_processed_links()
    print(f"Loaded {len(processed_links)} previously processed listings.")
    
    # 2. Load the raw scraped listings
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            listings_to_process = [json.loads(line) for line in f]
        print(f"Loaded {len(listings_to_process)} listings from '{DATABASE_FILE}'.")
    except FileNotFoundError:
        print(f"ERROR: Database file '{DATABASE_FILE}' not found. Run main_scraper.py first.")
        return
        
    # 3. Filter out listings that have already been processed
    new_listings = [listing for listing in listings_to_process if listing['link'] not in processed_links]
    print(f"Found {len(new_listings)} new listings to process.")

    # 4. Process each new listing
    for i, listing in enumerate(new_listings):
        print(f"\n--- Processing New Listing {i+1}/{len(new_listings)} ---")
        print(f"Title: {listing['title']}")
        print(f"Link: {listing['link']}")
        
        # Use the new Google-based valuation function
        valuation = kbb_valuator.get_valuation_via_google(listing)
        
        if valuation:
            print(f"SUCCESS: Valuation found and logged for '{listing['title']}'")
            print(json.dumps(valuation, indent=2))
        else:
            print(f"FAIL: Valuation could not be completed for '{listing['title']}'")
            
if __name__ == "__main__":
    process_scraped_data()
    # https://www.kbb.com/hyundai/santa-fe/2007/gls-sport-utility-4d/condition/?extcolor=beige&intent=trade-in-sell&mileage=150000&modalview=false&offeroptions=true&options=6332682%7Ctrue&pricetype=trade-in&subintent=trade&vehicleid=83881
    # https://www.kbb.com/hyundai/santa-fe/2007/gls-sport-utility-4d/offeroption/?vehicleid=83881&mileage=150000&modalview=false&intent=trade-in-sell&pricetype=trade-in&options=6332682%7ctrue&extcolor=beige&subintent=trade
    # https://www.kbb.com/hyundai/santa-fe/2007/gls-sport-utility-4d/?vehicleid=83881&mileage=150000&offeroptions=true&modalview=false&intent=trade-in-sell&pricetype=trade-in&condition=verygood&options=6332682%7Ctrue&extcolor=beige&subintent=trade&entry=defymmt