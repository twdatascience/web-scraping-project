from utils.helpers import save_data, load_data
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import datetime
import os


import pdb
# Fetch dynamic content
# sopris = 'https://soprisselfstorage.com/rent-storage/'
# sopris_soup = fetch_sopris_self_storage(sopris)

url = 'https://www.storquest.com/self-storage/co/carbondale/9160/unit-sizes-prices#/'

def fetch_storquest_self_storage(url, html_path=None):
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path = f"./web_data/{today_str}_storquestselfstorage.html"
    # Ensure the directory exists
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    # Set up Selenium (Chrome)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)

    # Navigate to the dynamic website
    driver.get(url)

    delay = 20
    try:
        view_all_units = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[span[text()='View All Units']]"))
    )
        view_all_units.click()
        
    except TimeoutException:
        print("Timed out waiting for page to load")

    # Get the page source after the content is loaded
    page_source = driver.page_source

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(page_source)

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(page_source, "html.parser")

    # Close the browser
    driver.quit()

    return soup

stor = fetch_storquest_self_storage(url)

units_tables = {}
for idx, div in enumerate(stor.find_all("div", class_="DesktopUnitTableCondensed_unit_3f_Tu Unit_unit_2YeZT")):
    units_tables[f'unitsTable_{idx}'] = div.decode_contents()

results = {}
for idx, (key, table_html) in enumerate(units_tables.items()):

    table_soup = BeautifulSoup(table_html, "html.parser")
    # Extract unit name from <span class="candee_translate unitName">
    unit_name_span = table_soup.find("span", class_="UnitSize_name_21eud")
    unit_name = unit_name_span.get_text(strip=True) if unit_name_span else None

    # Extract currentUnit-price (assuming in an element with class 'currentUnit-price')
    price = table_soup.find(class_="UnitPrices_price_21Ss8")
    price_text = price.get_text(strip=True) if price else None

    results[idx] = (unit_name, price_text)

pdb.set_trace()