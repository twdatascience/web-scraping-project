from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from bs4 import BeautifulSoup
import datetime
import os
import time
import pdb

def fetch_storage_mart(url, html_path=None):
    """
    Fetch StorageMart page and return BeautifulSoup object.
    """
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path = f"./web_data/{today_str}_storage_mart.html"
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Large')]"))
    )
    time.sleep(5)
    
    # parking = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]")
    h3_large = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Large')]")
    ActionChains(driver).scroll_to_element(h3_large).perform()
    ActionChains(driver).scroll_by_amount(0, 200).perform()
    time.sleep(2)
    try:
        h3_medium = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Medium')]")
        h3_medium.click()
    except Exception as e:
        print(f"could not find medium div\n{e}")
    # parking = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]")
    # ActionChains(driver).scroll_to_element(parking).perform()
    h3_large = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Large')]")
    ActionChains(driver).scroll_to_element(h3_large).perform()
    ActionChains(driver).scroll_by_amount(0, 200).perform()
    time.sleep(2)
    try:
        h3_large = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Large')]")
        h3_large.click()
    except:
        print("could not find large div")
    # parking = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]")
    # ActionChains(driver).scroll_to_element(parking).perform()
    h3_large = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Large')]")
    ActionChains(driver).scroll_to_element(h3_large).perform()
    ActionChains(driver).scroll_by_amount(0, 200).perform()
    time.sleep(2)
    # try:
    #     h3_parking = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]")
    #     h3_parking.click()
    # except:
    #     print("could not find parking div")
    load_more_units_btns = driver.find_elements(By.XPATH, "//button[@class='rnl-Button themed-button themed-tertiary-button'][contains(., 'Load More Units')]")
    while len(load_more_units_btns) > 0:
        try:
            ActionChains(driver).scroll_to_element(load_more_units_btns[0]).scroll_by_amount(0, 100).perform()
            time.sleep(2)
            load_more_units_btns[0].click()
        except Exception as e:
            print(f"could not click load more units button\n{e}")
            break
        load_more_units_btns = driver.find_elements(By.XPATH, "//button[@class='rnl-Button themed-button themed-tertiary-button'][contains(., 'Load More Units')]")
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(page_source)
    driver.quit()
    return soup

def extract_storage_mart(storage_mart_soup):
    """
    Extracts unit name and price from StorageMart HTML.
    Adds climate_controlled field based on unit_type.
    """
    units_tables = {}
    for idx, tr in enumerate(storage_mart_soup.find_all("tr", class_="znHaZ2O_cNrdovZfcxrWe")):
        units_tables[f'unitsTable_{idx}'] = tr.decode_contents()
    results = {}
    for idx, (key, table_html) in enumerate(units_tables.items()):
        table_soup = BeautifulSoup(table_html, "html.parser")
        unit_name_div = table_soup.find("div", class_="qJmPGq06cwU2AuJemRUX-")
        span_texts = [span.get_text(strip=True) for span in unit_name_div.find_all("span")]
        unit_size = "".join(span_texts).replace("'", "")
        features = []
        feature_divs = table_soup.find_all("div", class_="_19pkLSfs8NgCWRnd7MtUO1 _1jTh_C-Ii0lUVWiCfhE0s3")
        for div in feature_divs:
            text = div.get_text(strip=True)
            if text:
                features.append(text)
        unit_type = " ".join(features) if features else ""
        # Add climate_controlled field
        climate_controlled = True if "A/C & Heat" in unit_type else False
        tier = "tier 0"  # Default tier
        price = None
        price_div = table_soup.find("div", class_="_1n0aDKzz825gOOrRZCKcmI text-dark-gray")
        if price_div:
            price_span = price_div.find("span")
            if price_span:
                price = price_span.get_text(strip=True).replace("$", "")
        else:
            price = "Sold Out"
        results[idx] = (unit_size, unit_type, price, climate_controlled, tier)
    return results


storage_mart_url = 'https://www.storage-mart.com/basalt#unitstable'

storage_mart_soup = fetch_storage_mart(storage_mart_url)
storage_mart_results = extract_storage_mart(storage_mart_soup)
pdb.set_trace()