
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

# storage_mart = 'https://www.storage-mart.com/basalt#unitstable'
# all_hours = "https://www.aspenbasaltstorage.com/pages/rent"
# carbondale = "https://carbondaleministorage.ccstorage.com/find_units"
# storquest = 'https://www.storquest.com/self-storage/co/carbondale/9160/unit-sizes-prices#/'
url1 = 'https://www.spacecontroletrans.com/scStarOnlinePayment/index.html?CompanyId=327-SF&ConnectionType=Connection#/displaySizes'
url2 = 'https://www.spacecontroletrans.com/scStarOnlinePayment/index.html?CompanyId=327-BS&ConnectionType=Connection#/displaySizes'


def fetch_basalt_mini(url1, url2, html_path=None):
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path1 = f"./web_data/{today_str}_basaltmini_reg.html"
        html_path2 = f"./web_data/{today_str}_basaltmini_cc.html"
    # Ensure the directory exists
    os.makedirs(os.path.dirname(html_path1), exist_ok=True)
    os.makedirs(os.path.dirname(html_path2), exist_ok=True)
    # Set up Selenium (Chrome)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)

    # Navigate to the dynamic website
    driver.get(url1)

    delay = 20
    try:
        WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.XPATH, '//li[@class="list-group-item btn-primary ng-binding"]'))
        )
    except TimeoutException:
        print("Timed out waiting for page to load")
    
    # Get the page source after the content is loaded
    page_source = driver.page_source

    with open(html_path1, 'w', encoding='utf-8') as f:
        f.write(page_source)

    # Parse the HTML with BeautifulSoup
    soup1 = BeautifulSoup(page_source, "html.parser")

    # Close the browser
    driver.quit()

    driver = webdriver.Chrome(options=options)
    driver.get(url2)

    delay = 20
    try:
        WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.XPATH, '//li[@class="list-group-item btn-primary ng-binding"]'))
        )
    except TimeoutException:
        print("Timed out waiting for page to load")

    # Get the page source after the content is loaded
    page_source2 = driver.page_source

    with open(html_path2, 'w', encoding='utf-8') as f:
        f.write(page_source2)

    # Parse the HTML with BeautifulSoup
    soup2 = BeautifulSoup(page_source2, "html.parser")
    # Close the browser
    driver.quit()

    return soup1, soup2

def extract_storquest(basalt_soup1, basalt_soup2):
    """
    Extracts unit name and price from storquest_soup and removes duplicate (unit_name, price) pairs.
    """
    units_tables1 = {}
    for idx, div in enumerate(basalt_soup1.find_all("div", class_="bs-component")):
        units_tables1[f'unitsTable_{idx}'] = div.decode_contents()

    units_tables2 = {}
    for idx, div in enumerate(basalt_soup2.find_all("div", class_="bs-component")):
        units_tables2[f'unitsTable_{idx}'] = div.decode_contents()

    results1 = {}
    results2 = {}

    for idx, (key, table_html) in enumerate(units_tables1.items()):
        table_soup = BeautifulSoup(table_html, "html.parser")
        unit_name_span = table_soup.find("li", class_="list-group-item btn-primary ng-binding")
        unit_name = unit_name_span.get_text(strip=True) if unit_name_span else None
        price = table_soup.find("span", class_="ng-binding")
        price_text = price.get_text(strip=True).replace("$", "") if price else None
        unit_size = unit_name.split(" ")[0] if unit_name else None
        unit_type = " ".join(unit_name.split(" ")[1:]) if unit_name.split(" ")[1:] else ""

        results1[idx] = (unit_size, unit_type, price_text)
          
    for idx, (key, table_html) in enumerate(units_tables2.items()):
        table_soup = BeautifulSoup(table_html, "html.parser")
        unit_name_span = table_soup.find("li", class_="list-group-item btn-primary ng-binding")
        unit_name = unit_name_span.get_text(strip=True) if unit_name_span else None
        price = table_soup.find("span", class_="ng-binding")
        price_text = price.get_text(strip=True).replace("$", "") if price else None
        unit_size = unit_name.split(" ")[0] if unit_name else None
        unit_type = " ".join(unit_name.split(" ")[1:]) if unit_name.split(" ")[1:] else ""

        results2[idx] = (unit_size, unit_type, price_text)

    combined_results = {**results1, **{idx + len(results1): v for idx, v in results2.items()}}

    return combined_results

basalt_soup1, basalt_soup2 = fetch_basalt_mini(url1, url2)

basalt_results = extract_storquest(basalt_soup1, basalt_soup2)
