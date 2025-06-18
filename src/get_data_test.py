from utils.helpers import save_data, load_data
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from bs4 import BeautifulSoup
import datetime
import os
import time


import pdb
# Fetch dynamic content
# sopris = 'https://soprisselfstorage.com/rent-storage/'
# sopris_soup = fetch_sopris_self_storage(sopris)

storage_mart = 'https://www.storage-mart.com/basalt#unitstable'

def fetch_storage_mart(url, html_path=None):
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path = f"./web_data/{today_str}_storage_mart.html"
    # Ensure the directory exists
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    # Set up Selenium (Chrome)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)

    # Navigate to the dynamic website
    driver.get(url)
    element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]"))
            )
    
    time.sleep(5)
    parking = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]")
    ActionChains(driver)\
        .scroll_to_element(parking)\
        .perform()

    time.sleep(2)
    try:
        h3_medium = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Medium')]")
        h3_medium.click()
    except Exception as e:
        print(f"could not find medium div\n{e}")

    parking = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]")
    ActionChains(driver)\
        .scroll_to_element(parking)\
        .perform()

    time.sleep(2)
    try:
        h3_large = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Large')]")
        h3_large.click()
    except:
        print("could not find large div")
    
    parking = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]")
    ActionChains(driver)\
        .scroll_to_element(parking)\
        .perform()
    
    ActionChains(driver).scroll_by_amount(0, 200).perform()

    time.sleep(2)
    try:
        h3_parking = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]")
        h3_parking.click()
    except:
        print("could not find parking div")

    load_more_units_btns = driver.find_elements(By.XPATH, "//button[@class='rnl-Button themed-button themed-tertiary-button'][contains(., 'Load More Units')]")

    while len(load_more_units_btns) > 0:
        print(len(load_more_units_btns))
        try:
            ActionChains(driver).scroll_to_element(load_more_units_btns[0]).scroll_by_amount(0, 100).perform()
            time.sleep(2)
            load_more_units_btns[0].click()
        except Exception as e:
            print(f"could not click load more units button\n{e}")
            break
        
        load_more_units_btns = driver.find_elements(By.XPATH, "//button[@class='rnl-Button themed-button themed-tertiary-button'][contains(., 'Load More Units')]")                                    
    
    
    # Get the page source after the content is loaded
    page_source = driver.page_source

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(page_source, "html.parser")

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(page_source)

    

    # Close the browser
    driver.quit()

    return soup

# stor = fetch_storage_mart(url)
stor = BeautifulSoup(load_data(r'C:\Users\Admin\Documents\github\scraper\web-scraping-project\web_data\2025-06-18_storage_mart.html'), "html.parser")
units_tables = {}
for idx, tr in enumerate(stor.find_all("tr", class_="znHaZ2O_cNrdovZfcxrWe")):
    units_tables[f'unitsTable_{idx}'] = tr.decode_contents()

results = {}
for idx, (key, table_html) in enumerate(units_tables.items()):

    table_soup = BeautifulSoup(table_html, "html.parser")
    # Extract unit name from <span class="candee_translate unitName">
    unit_name = ""
    unit_name_div = table_soup.find("div", class_="qJmPGq06cwU2AuJemRUX-")
    # Extract all text from <span> tags inside this div and join with spaces
    span_texts = [span.get_text(strip=True) for span in unit_name_div.find_all("span")]
    unit_name = "".join(span_texts)

    features = []
    feature_divs = table_soup.find_all("div", class_="_19pkLSfs8NgCWRnd7MtUO1 _1jTh_C-Ii0lUVWiCfhE0s3")
    for div in feature_divs:
        # Get the text after the SVG (strip to remove whitespace)
        text = div.get_text(strip=True)
        if text:
            features.append(text)
    
    if len(features) > 0:
        unit_name += " (" + ", ".join(features) + ")"


    price = None
    price_div = table_soup.find("div", class_="_1n0aDKzz825gOOrRZCKcmI text-dark-gray")
    # Defensive check: make sure price_div is not None before calling .find
    if price_div:
        price_span = price_div.find("span")
        if price_span:
            price = price_span.get_text(strip=True)
    else:
        price = "Sold Out"

    results[idx] = (unit_name, price)

print(results)

