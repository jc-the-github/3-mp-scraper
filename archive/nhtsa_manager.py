import requests
import json
import os

# --- Constants ---
BASE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles"
MAKES_CACHE_FILE = "nhtsa_makes.json"
MODELS_CACHE_DIR = "nhtsa_models_cache"

# --- Main Functions ---
def get_all_makes(force_refresh=False):
    """
    Fetches a list of all vehicle makes from the NHTSA API.
    Caches the results locally in a JSON file to minimize API calls.
    """
    if not force_refresh and os.path.exists(MAKES_CACHE_FILE):
        print("[NHTSA Manager] Loading makes from local cache.")
        with open(MAKES_CACHE_FILE, 'r') as f:
            return json.load(f)

    print("[NHTSA Manager] Fetching all makes from NHTSA API...")
    try:
        url = f"{BASE_URL}/GetAllMakes?format=json"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # We only need the 'Make_Name' from the results
        makes_list = sorted([make['Make_Name'].strip() for make in data['Results']])
        
        with open(MAKES_CACHE_FILE, 'w') as f:
            json.dump(makes_list, f, indent=4)
        print(f"[NHTSA Manager] Saved {len(makes_list)} makes to '{MAKES_CACHE_FILE}'.")
        return makes_list
        
    except requests.exceptions.RequestException as e:
        print(f"[NHTSA Manager] ERROR: Could not fetch makes from API. {e}")
        return []

def get_models_for_make(make_name, force_refresh=False):
    """
    Fetches all models for a specific make.
    Caches results in individual files to prevent re-fetching.
    """
    if not os.path.exists(MODELS_CACHE_DIR):
        os.makedirs(MODELS_CACHE_DIR)
        
    safe_make_name = "".join(c for c in make_name if c.isalnum())
    cache_file_path = os.path.join(MODELS_CACHE_DIR, f"{safe_make_name}.json")
    
    if not force_refresh and os.path.exists(cache_file_path):
        with open(cache_file_path, 'r') as f:
            return json.load(f)
            
    print(f"[NHTSA Manager] Fetching models for '{make_name}' from NHTSA API...")
    try:
        url = f"{BASE_URL}/GetModelsForMake/{make_name.replace(' ', '%20')}?format=json"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        models_list = sorted([model['Model_Name'].strip() for model in data['Results']])
        
        with open(cache_file_path, 'w') as f:
            json.dump(models_list, f, indent=4)
        return models_list
        
    except requests.exceptions.RequestException as e:
        print(f"[NHTSA Manager] ERROR: Could not fetch models for '{make_name}'. {e}")
        return []

if __name__ == '__main__':
    import time

    # --- Comprehensive Local Database Builder ---
    # This script will fetch and cache all models for every make from the NHTSA.
    # It is designed to be run once to build your local database.
    # It is resumable; if it's interrupted, it will skip makes it has already downloaded.
    
    print("--- Starting NHTSA Local Database Population ---")
    
    # 1. Fetch the master list of all makes.
    # This will use the cache if available, or fetch from the API if not.
    all_makes = get_all_makes()
    
    if all_makes:
        total_makes = len(all_makes)
        print(f"Successfully loaded {total_makes} makes. Now fetching models for each.")
        
        # 2. Iterate through each make and fetch its models.
        for i, make_name in enumerate(all_makes):
            # Provide progress feedback.
            print(f"--> Processing make {i + 1}/{total_makes}: '{make_name}'")
            
            # The function will automatically use the cache if the model file for this
            # make already exists, so it's safe to re-run this script.
            get_models_for_make(make_name)
            
            # 3. Add a respectful delay between API calls.
            # This prevents overwhelming the NHTSA API and getting your IP blocked.
            # A 0.2 to 0.5 second delay is standard practice.
            time.sleep(0.25)
            
        print("\n--- NHTSA Local Database Population Complete ---")
        print(f"Model data for all {total_makes} makes is now cached locally.")
    else:
        print("Could not retrieve the list of makes. Aborting model fetch.")