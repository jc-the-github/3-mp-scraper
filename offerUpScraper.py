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


def performAction(action, searchType, name, keys):
    global driver
    element = ''

    # if searchType == 'CSS_SELECTOR':

    # elif searchType == 'XPATH':
    #     element = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
    #         (By.XPATH, name)))

    if action == 'click':
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, name))).click()
    elif action == 'send_keys':
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, name))).send_keys(keys)
    elif action == 'get_attribute':
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, name))).get_attribute(keys)


def waitFuncDefault():
    try:
        time_over = inputimeout(
            prompt='End code? (Input y)', timeout=1)
        if str(time_over) == "y":
            print("Ending code...")
            exitTime = True
            sys.exit()

    except TimeoutOccurred:
        print("cont")


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


def fromElectronicsCategory():
    global driver
    driver.get("https://search.cashamerica.com/#/categories")
    try:

        time_over = inputimeout(prompt='End code? (Input y)', timeout=3)
        if str(time_over) == "y":
            print("Ending code...")
            exitTime = True
            sys.exit()
    except TimeoutOccurred:
        print("cont")


def fromCategoriesPage():

    # global driver
    driver.get("https://search.cashamerica.com/#/")

    # waitFuncSpecified(10000)

    WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, "body > div.ng-scope > div > div > div.main-search > a"))).click()

    # # click address field
    # WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
    #     (By.ID, "address"))).click()
    # agent = driver.execute_script("return navigator.userAgent")
    # print('user agent ' + str(agent))

    # # type in address
    # WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
    #     (By.ID, "address"))).send_keys('79930')

    # # click apply
    # WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
    #     (By.CSS_SELECTOR, "body > div.modal.fade.ng-isolate-scope.in > div > div > form > div.modal-footer > button.btn.btn-primary"))).click()

    # # click music instruments
    # WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
    #     (By.XPATH, "/html/body/div[1]/div/div[2]/div/div/div[4]/div/a"))).click()

    # WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
    #     (By.XPATH, "/html/body/div[1]/div/div[3]/div/div/div[9]/a"))).click()


def changeCategory():
    global categoryIndex

    # general musical instruments
    if categoryIndex == 0:
        element = 'body > div.ng-scope > div > div.container-fluid.ng-scope > div > div > div:nth-child(10) > div > a > img'
        performAction('click', 'CSS_SELECTOR', element, '')

        waitFuncSpecified(5)
        element = '/html/body/div[1]/div/div[1]/search-form/form/div/span/button'
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, element))).click()

        scrollPages()
        driver.back()
        driver.back()
        # waitFuncSpecified(50000)
    # video games
    elif categoryIndex == 1:
        element = '/html/body/div[1]/div/div[2]/div/div/div[4]/div/a/img'
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, element))).click()

        element = 'body > div.ng-scope > div > div.container-fluid.ng-scope > div > div > div:nth-child(9) > a > div > h3'
        performAction('click', 'CSS_SELECTOR', element, '')
        print("wgy")

        scrollPages()
        driver.back()
        driver.back()
    # # general clothes and shoes
    # elif categoryIndex == 2:
    #     element = '/html/body/div[1]/div/div[2]/div/div/div[3]/div/a/img'
    #     WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
    #         (By.XPATH, element))).click()

    #     waitFuncSpecified(5)
    #     element = '/html/body/div[1]/div/div[1]/search-form/form/div/span/button'
    #     WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
    #         (By.XPATH, element))).click()

    #     scrollPages()
    #     driver.back()
    #     driver.back()

    # computer equipment
    elif categoryIndex == 3:
        element = '/html/body/div[1]/div/div[2]/div/div/div[4]/div/a/img'
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, element))).click()

        element = '/html/body/div[1]/div/div[3]/div/div/div[2]/a/div/h3'
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, element))).click()

        waitFuncSpecified(10)


        scrollPages()
        driver.back()
        driver.back()

    elif categoryIndex == 4:
        # click electronics
        element = '/html/body/div[1]/div/div[2]/div/div/div[4]/div/a/img'
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, element))).click()

        # click search bar
        waitFuncSpecified(5)
        # element = '/html/body/div[1]/div/div[3]/div/div/div[2]'
        element = '/html/body/div[1]/div/div[1]/search-form/form/div/span/button'
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, element))).click()

        scrollPages()
        driver.back()
        driver.back()
    elif categoryIndex == 5:
        element = '/html/body/div[1]/div/div[2]/div/div/div[2]/div/a/img'
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, element))).click()

        element = 'body > div.ng-scope > div > div.search-bar.ng-scope > search-form > form > div > span > button'
        performAction('click', 'CSS_SELECTOR', element, '')
        print("wgy")

        scrollPages()
        driver.back()
        driver.back()
def scrollPages():

    global categoryIndex
    global pageScrollAmount
    currentPageScrollAmount = pageScrollAmount
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.XPATH, '//*[@id="radiusRadios-499"]'))).click()

    if categoryIndex == 4:
        for i in range(currentPageScrollAmount):
            # copy listing info
            # body > div.ng-scope > div > div > div.container-fluid > div
            # /html/body/div[1]/div/div/div[2]/div/div[2]/div[1]
            
            saveHTML()
            print("should b e scrolling")
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "body > div.ng-scope > div > div > div.container-fluid > div > div.col-xs-12.col-sm-9.no-float > div:nth-child(2) > ul > li.next > a"))).click()

    else:
        for i in range(currentPageScrollAmount):
            saveHTML()
            print("should b e scrolling")
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "body > div.ng-scope > div > div > div.container-fluid > div > div.col-xs-12.col-sm-9.no-float > div:nth-child(2) > ul > li.next > a"))).click()




def saveHTML():
    global categories
    fileName = categories[categoryIndex]
    fileName = 'unsorted HTML Data/' + \
        str(categories[categoryIndex]) + 'PawnHTML.txt'

    waitFuncSpecified(1)
    newPawnListingsHTML = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.XPATH, "/html/body/div[1]/div/div/div[2]/div/div[2]/div[1]"))).get_attribute('outerHTML')

    # save to file
    # first read contents
    pawnListingsHTMLFile = open(
        fileName, 'r', encoding="utf8")
    pawnListingsHTML = pawnListingsHTMLFile.read()
    pawnListingsHTMLFile.close()

    # add to contents
    pawnListingsHTML += "\n"
    pawnListingsHTML += str(newPawnListingsHTML)
    print("huh " + pawnListingsHTML)

    # write to contents
    pawnListingsHTMLFile = open(fileName, 'w', encoding="utf8")
    pawnListingsHTMLFile.write(str(pawnListingsHTML))
    pawnListingsHTMLFile.close()


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

# # with webdriver.Chrome() as driver:
# # ---- Start -----
# fromCategoriesPage()
# categoryIndex = 5
# # pageScrollAmount = 171
# # pageScrollAmount = 80
# pageScrollAmount = 150
# categories = ['GeneralMusicInstruments', 'VideoGames',
#               'GeneralClothesandShoes', 'ComputerEquipment','GeneralElectronics', 'GeneralCamerasAndProjectors']
# # CURRENTLY HAVE FIRST TO 80 PAGES AND THEN ANOTHER 160 OR SOMETHING LIKE THAT, 
# # MUST CHANGE
# for i in range(1):
#     changeCategory()
#     print("aa")
#     # scrollPages()
#     # categoryIndex -= 4
#     categoryIndex += 4
#     # pageScrollAmount = 80
#     pageScrollAmount = 165

def offerUpScraper():
    
    # Vars
    service = Service()

    opts = webdriver.ChromeOptions()
    PROXY = '45.90.219.12:4444'
    user_agent = 'Mozilla/5.0 CK={} (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'

    webdriver.DesiredCapabilities.CHROME['proxy'] = {
        "httpProxy": PROXY,
        "ftpProxy": PROXY,
        "sslProxy": PROXY,
        "proxyType": "MANUAL",

    }

    webdriver.DesiredCapabilities.CHROME['acceptSslCerts'] = True
    opts.add_argument("user-agent="+user_agent)
    print(webdriver.DesiredCapabilities.CHROME)
    driver = webdriver.Chrome(service=service, options=opts)
    zip_code = 66045
    try:
            # Step 1: Go to the initial page
            print("1. Navigating to OfferUp homepage...")
            driver.get("https://offerup.com/explore/k/5/1?DISTANCE=5000&SORT=-posted")
            # driver.get("https://offerup.com/search?q=car&DISTANCE=5000&SORT=-posted")

            # Wait for the main location/search button to be clickable
        #     # This is a more stable way than using a long XPath
        #     WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        # (By.XPATH, '/html/body/div[1]/div[5]/div[2]/main/div[1]/button'))).click()
        #     # Step 2: Click the location button on the main page
        #     print("2. Clicking the main location button...")
        #     # waitFuncSpecified(20)
        #     WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        # (By.XPATH, '/html/body/div[5]/div[3]/div/div[3]/div/div/div[3]/div[2]/button'))).click()
        #     WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        # (By.XPATH, '/html/body/div[5]/div[3]/div/form/div[4]/div/div/div[4]/div[1]/div/div/input'))).send_keys(Keys.CONTROL + "a").send_keys(zip_code)
        #     WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        # (By.XPATH, '/html/body/div[5]/div[3]/div/form/div[5]/button'))).click()
        #     WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        # (By.XPATH, '/html/body/div[5]/div[3]/div/div[4]/button'))).click()

        #     data = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        # (By.XPATH, '/html/body/div/div[5]/div[2]/div[4]/main/div[3]/div/div[1]/ul'))).get_attribute('outerHTML')
            # print("data: " + str(data))

            # location_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, location_button_selector)))
            # location_button.click()
            
            # # Step 3: Click the "Select location" button in the popup
            # print("3. Clicking 'Select location' in the modal...")
            # select_location_button_selector = 'button[aria-label="Select location"]'
            # select_location_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, select_location_button_selector)))
            # select_location_button.click()

            # # Step 4: Find the zip code input, clear it, and enter the new zip code
            # print(f"4. Entering zip code: {zip_code}...")
            # zip_input_selector = 'input[aria-label="Zip code"]'
            # zip_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, zip_input_selector)))
            
            # # Clear any existing text in the input
            # zip_input.send_keys(Keys.CONTROL + "a")
            # zip_input.send_keys(Keys.DELETE)
            
            # zip_input.send_keys(zip_code)

            # # Step 5: Click the "Apply" button to confirm the new location
            # print("5. Applying new location...")
            # apply_button_selector = 'button[type="submit"]' # Simple and effective
            # apply_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, apply_button_selector)))
            # apply_button.click()
            
            # # Step 6 (Optional but good practice): Wait for the confirmation to close
            # time.sleep(3) # Give it a moment for the page to refresh with the new location

            # # --- Now we perform the search for the desired item ---
            # print(f"6. Searching for '{search_query}'...")
            # search_bar_selector = 'input[aria-label="Search an item"]'
            # search_bar = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, search_bar_selector)))
            # search_bar.send_keys(search_query)
            # search_bar.send_keys(Keys.ENTER)
            
            # # --- Scrape the results ---
            # print("7. Scraping results...")
            # time.sleep(5) # Wait for search results to load

            # # Now we grab the HTML of the results list, just like you identified
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # # You correctly identified the <ul> as the container. Let's find all the list items.
            # # The class name "jss369" from your example might change, but the list item tag <li> is stable.
            # # We will target the link `<a>` inside each list item as it contains all the data we need.
            listings = soup.find_all('a', class_='jss254') # Using a class from your example that seems specific to listings
            
            results = []
            for listing in listings:
                title = listing.get('title', 'N/A')
                link = "https://offerup.com" + listing.get('href', 'N/A')
                
                # Extracting price and location is trickier due to complex classes
                # We find all text elements and piece it together
                text_spans = listing.find_all('span')
                
                price = "N/A"
                location = "N/A"
                
                # This logic assumes a consistent structure within the listing card
                if len(text_spans) >= 4:
                    price = text_spans[2].text.strip()
                    location = text_spans[3].text.strip()

                results.append({
                    'title': title,
                    'price': price,
                    'location': location,
                    'link': link,
                    'source': 'OfferUp'
                })
                
            print(f" Found {len(results)} results from OfferUp.")
            return results
    except Exception as e:
        print("e: " + str(e))
        traceback.print_exc()
    finally:
        driver.quit() # Always close the browser`

if __name__ == "__main__":
    # You can change these values to whatever you need
    target_zip = "78741" 
    target_query = "car"
    
    offerup_deals = offerUpScraper()
        # offerup_deals = offerUpScraper(zip_code=target_zip, search_query=target_query)

    if offerup_deals:
        df = pd.DataFrame(offerup_deals)
        print(df)

# webdriver.DesiredCapabilities.CHROME['proxy'] = {
#     "httpProxy": PROXY,
#     "ftpProxy": PROXY,
#     "sslProxy": PROXY,
#     "proxyType": "manual",
# }

# options.add_argument('--proxy-server=%s' % PROXY)

# # Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36
# options.add_argument('--ignore-certificate-errors')
# options.add_argument('--ignore-ssl-errors')
# options.add_argument(
#     "user-agent=Mozilla/5.0 (Windows 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
# driver = webdriver.Chrome(service=service, options=options)


# main = Main()
# pawnListingsHTMLFile = open(
#     'unsorted HTML Data/unsortedPawnHTML.txt', 'r', encoding="utf8")
# pawnListingsHTML = pawnListingsHTMLFile.read()
# pawnListingsHTMLFile.close()
# pawnListingsParser = pawnListingsParser(pawnListingsHTML)

# main.matchPriceGuidesAndListings(main.parsedPawnListings, "OfferUp")
# revealed.send_keys('78741')


# btn btn-primary
# button = driver.find_element(By.CLASS_NAME, u"form-control ng-pristine ng-valid ng-touched")
# driver.implicitly_wait(10)
# ActionChains(driver).move_to_element(button).click(button).perform()


# driver.find_element(By.NAME, "btnI").click()

# wait = WebDriverWait(driver, timeout=5000)


# wait.until(lambda d : revealed.is_displayed())

# revealed.send_keys("Displayed")
# assert revealed.get_property("value") == "Displayed"

# clickable = driver.find_element(By.CSS_SELECTOR, "#gbqfbb")
# clickable.click()
# clickable = driver.find_element(By.CSS_SELECTOR, "#gbqfbb")
# ActionChains(driver)\
#     .click(clickable)\
#     .perform()


# clickable = driver.find_element(by=id, value='gbqfbb')
# ActionChains(driver)\
#     .click(clickable)\
#     .perform()

# print(driver.title)


# revealed = driver.find_element(By.CSS_SELECTOR, "#gbqfbb")
# driver.find_element(By.ID, "gbqfbb").click()

# driver.find_element(By.ID, "gbqfbb").click()

    # waitFuncDefault()

    # click apply button
    # revealed = driver.find_element(
    #     By.CSS_SELECTOR, "body > div.modal.fade.ng-isolate-scope.in > div > div > form > div.modal-footer > button.btn.btn-primary")
    # driver.find_element(
    #     By.CSS_SELECTOR, "body > div.modal.fade.ng-isolate-scope.in > div > div > form > div.modal-footer > button.btn.btn-primary").click()
    # errors = [NoSuchElementException, ElementNotInteractableException]
    # wait = WebDriverWait(
    #     driver, timeout=2, poll_frequency=.2, ignored_exceptions=errors)
    # wait.until(lambda d: revealed.send_keys("") or True)
