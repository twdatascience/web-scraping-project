from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import pickle
import datetime
import pandas as pd
import os
import pdb

def save_data(html, soup, html_path='page.html', soup_path='soup.pkl'):
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    with open(soup_path, 'wb') as f:
        pickle.dump(soup, f)

def load_data(html_path='page.html', soup_path='soup.pkl'):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    with open(soup_path, 'rb') as f:
        soup = pickle.load(f)
    return html, soup

import pandas as pd

def write_multiple_results_to_excel(sopris_results, storquest_results, excel_path="storage_results.xlsx"):
    """
    Write Sopris and StorQuest results to different sheets in a single Excel file.
    """
    today_str = datetime.date.today().isoformat()
    with pd.ExcelWriter(excel_path) as writer:
        # Sopris sheet
        df_sopris = pd.DataFrame.from_dict(sopris_results, orient='index', columns=['unit_name', 'price'])
        df_sopris.to_excel(writer, index=False, sheet_name=f"{today_str}_sopris_results")
        # StorQuest sheet
        df_storquest = pd.DataFrame.from_dict(storquest_results, orient='index', columns=['unit_name', 'price'])
        df_storquest.to_excel(writer, index=False, sheet_name=f"{today_str}_storquest_results")

def fetch_sopris_self_storage(url, html_path=None):
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path = f"./web_data/{today_str}_soprisselfstorage.html"
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
        WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'currentUnit-price'))
        )
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

def extract_sopris(sopris_soup):
    """
    Extracts unit name and price from tables_dict and writes to an Excel file.
    """
    units_tables = {}
    for idx, div in enumerate(sopris_soup.find_all("div", class_="unitsTable")):
        units_tables[f'unitsTable_{idx}'] = div.decode_contents()

    results = {}
    for idx, (key, table_html) in enumerate(units_tables.items()):

        table_soup = BeautifulSoup(table_html, "html.parser")
        # Extract unit name from <span class="candee_translate unitName">
        unit_name_span = table_soup.find("span", class_="candee_translate unitName")
        unit_name = unit_name_span.get_text(strip=True) if unit_name_span else None

        # Extract currentUnit-price (assuming in an element with class 'currentUnit-price')
        price = table_soup.find(class_="currentUnit-price")
        price_text = price.get_text(strip=True) if price else None

        results[idx] = (unit_name, price_text)

    # Write results to Excel file without index column and with specified sheet name
    # df = pd.DataFrame.from_dict(results, orient='index', columns=['unit_name', 'price'])
    # df.to_excel(excel_path, index=False, sheet_name=sheet_name)
    return results


# storquest

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

    # delay = 20
    # try:
    #     view_all_units = WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.XPATH, "//a[span[text()='View All Units']]"))
    # )
    #     view_all_units.click()
        
    # except TimeoutException:
    #     print("Timed out waiting for page to load")

    # Get the page source after the content is loaded
    page_source = driver.page_source

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(page_source)

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(page_source, "html.parser")

    # Close the browser
    driver.quit()

    return soup

def extract_storquest(storquest_soup):
    """
    Extracts unit name and price from storquest_soup and removes duplicate (unit_name, price) pairs.
    """
    units_tables = {}
    for idx, div in enumerate(storquest_soup.find_all("div", class_="DesktopUnitTableCondensed_unit_3f_Tu Unit_unit_2YeZT")):
        units_tables[f'unitsTable_{idx}'] = div.decode_contents()

    results = {}
    seen = set()
  
    for idx, (key, table_html) in enumerate(units_tables.items()):
        table_soup = BeautifulSoup(table_html, "html.parser")
        unit_name_span = table_soup.find("span", class_="UnitSize_name_21eud")
        unit_name = unit_name_span.get_text(strip=True) if unit_name_span else None
        price = table_soup.find(class_="UnitPrices_price_21Ss8")
        price_text = price.get_text(strip=True) if price else None

        
        # Only add unique (unit_name, price_text) pairs
        if (unit_name, price_text) not in seen:
            results[idx] = (unit_name, price_text)
            seen.add((unit_name, price_text))

    return results
