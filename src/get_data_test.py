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

# storage_mart = 'https://www.storage-mart.com/basalt#unitstable'
# all_hours = "https://www.aspenbasaltstorage.com/pages/rent"
carbondale = "https://carbondaleministorage.ccstorage.com/find_units"

def fetch_carbondale(url, html_path=None):
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
            EC.presence_of_element_located((By.XPATH, "//div[@class='grid grid-cols-1 lg:grid-cols-2 gap-6']"))
            )
        
    # Get the page source after the content is loaded
    page_source = driver.page_source

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(page_source, "html.parser")

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(page_source)

    

    # Close the browser
    driver.quit()

    return soup

stor = fetch_carbondale(url)

units_tables = {}
for idx, div in enumerate(stor.find_all("div", class_="bg-white rounded-xl shadow-xl border flex flex-col")):
    units_tables[f'unitsTable_{idx}'] = div.decode_contents()


results = {}
for idx, (key, table_html) in enumerate(units_tables.items()):

    table_soup = BeautifulSoup(table_html, "html.parser")
    unit_name = table_soup.find("p", class_="text-xl font-bold")
    unit_name_text = unit_name.get_text(strip=True) if unit_name else None
    price = table_soup.find("dd", class_="text-xl font-bold")
    price_text = price.get_text(strip=True) if price else None

    results[idx] = (unit_name_text, price_text)

print(results)

