from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from bs4 import BeautifulSoup
import datetime
import pandas as pd
import os
import time
import sqlite3
import re

def write_multiple_results_to_excel(sopris_results, storquest_results, storage_mart_results, all_hours_results, carbondale_results, excel_path="storage_results.xlsx"):
    """
    Write Sopris and StorQuest results to different sheets in a single Excel file.
    """
    today_str = datetime.date.today().isoformat()
    with pd.ExcelWriter(excel_path) as writer:
        # Sopris sheet
        df_sopris = pd.DataFrame.from_dict(sopris_results, orient='index', columns=['unit_size', 'unit_type', 'price'])
        df_sopris.to_excel(writer, index=False, sheet_name=f"{today_str}_sopris_results")
        # StorQuest sheet
        df_storquest = pd.DataFrame.from_dict(storquest_results, orient='index', columns=['unit_size', 'unit_type', 'price'])
        df_storquest.to_excel(writer, index=False, sheet_name=f"{today_str}_storquest_results")
        # Storage Mart sheet
        df_storage_mart = pd.DataFrame.from_dict(storage_mart_results, orient='index', columns=['unit_size', 'unit_type', 'price'])
        df_storage_mart.to_excel(writer, index=False, sheet_name=f"{today_str}_storage_mart_results")
        # All Hours sheet
        df_all_hours = pd.DataFrame.from_dict(all_hours_results, orient='index', columns=['unit_size', 'unit_type', 'price'])
        df_all_hours.to_excel(writer, index=False, sheet_name=f"{today_str}_all_hours_results")
        # Carbondale sheet
        df_carbondale = pd.DataFrame.from_dict(carbondale_results, orient='index', columns=['unit_size', 'unit_type', 'price'])
        df_carbondale.to_excel(writer, index=False, sheet_name=f"{today_str}_carbondale_results")

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
        parts = unit_name.split(" ", 1)
        if len(parts) == 2:
            unit_size, unit_type = parts
        else:
            unit_size = unit_name
            unit_type = ""

        # Extract currentUnit-price (assuming in an element with class 'currentUnit-price')
        price = table_soup.find(class_="currentUnit-price")
        price_text = price.get_text(strip=True) if price else None

        results[idx] = (unit_size, unit_type, price_text)

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
        price_text = price.get_text(strip=True).replace("$", "") + ".00" if price else None
        unit_size = unit_name.replace(" ", "")
        unit_type = table_soup.find(class_="DesktopUnitTableCondensed_amenities-list-container_2vbvz").get_text(strip=True) if table_soup.find(class_="DesktopUnitTableCondensed_amenities-list-container_2vbvz") else ""

        
        # Only add unique (unit_size, unit_type, price_text)
        if (unit_size, unit_type, price_text) not in seen:
            results[idx] = (unit_size, unit_type, price_text)
            seen.add((unit_size, unit_type, price_text))

    return results

def fetch_storage_mart(url, html_path=None):
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path = f"./web_data/{today_str}_storage_mart.html"
    # Ensure the directory exists
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    # Set up Selenium (Chrome)
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
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
        # print(len(load_more_units_btns))
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

def extract_storage_mart(storage_mart_soup):
    """
    Extracts unit name and price from storquest_soup and removes duplicate (unit_name, price) pairs.
    """
    units_tables = {}
    for idx, tr in enumerate(storage_mart_soup.find_all("tr", class_="znHaZ2O_cNrdovZfcxrWe")):
        units_tables[f'unitsTable_{idx}'] = tr.decode_contents()

    results = {}
    for idx, (key, table_html) in enumerate(units_tables.items()):

        table_soup = BeautifulSoup(table_html, "html.parser")
        # Extract unit name from <span class="candee_translate unitName">
        unit_name = ""
        unit_name_div = table_soup.find("div", class_="qJmPGq06cwU2AuJemRUX-")
        # Extract all text from <span> tags inside this div and join with spaces
        span_texts = [span.get_text(strip=True) for span in unit_name_div.find_all("span")]
        unit_size = "".join(span_texts).replace("'", "")

        features = []
        feature_divs = table_soup.find_all("div", class_="_19pkLSfs8NgCWRnd7MtUO1 _1jTh_C-Ii0lUVWiCfhE0s3")
        for div in feature_divs:
            # Get the text after the SVG (strip to remove whitespace)
            text = div.get_text(strip=True)
            if text:
                features.append(text)
    
        if len(features) > 0:
            unit_type = " ".join(features)


        price = None
        price_div = table_soup.find("div", class_="_1n0aDKzz825gOOrRZCKcmI text-dark-gray")
        # Defensive check: make sure price_div is not None before calling .find
        if price_div:
            price_span = price_div.find("span")
            if price_span:
                price = price_span.get_text(strip=True).replace("$", "")
        else:
            price = "Sold Out"

        results[idx] = (unit_size, unit_type, price)

    return results

def fetch_all_hours(url, html_path=None):
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path = f"./web_data/{today_str}_all_hours.html"
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
            EC.presence_of_element_located((By.XPATH, "//div[@class='unit-type-container-large']"))
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

def extract_all_hours(all_hours_soup):
    """
    Extracts unit name and price from storquest_soup and removes duplicate (unit_name, price) pairs.
    """
    units_tables = {}
    for idx, div in enumerate(all_hours_soup.find_all("div", class_="unit-type")):
        units_tables[f'unitsTable_{idx}'] = div.decode_contents()

    results = {}
    for idx, (key, table_html) in enumerate(units_tables.items()):

        table_soup = BeautifulSoup(table_html, "html.parser")
        unit_name_span = table_soup.find("h4", class_="primary-color")
        unit_name = unit_name_span.get_text(strip=True) if unit_name_span else None
        price_span = table_soup.find("div", class_="unit-menu")
        price_text = price_span.get_text(strip=True) if price_span else None
        price_text = price_text.split('\n')[0].replace("$", "") + ".00"
        unit_size = re.search(r"\((.*?)\)", unit_name)
        unit_size = unit_size.group(1).replace(" ", "") if unit_size else None
        unit_type = unit_name.split(" (")[0] if unit_name else None

        results[idx] = (unit_size, unit_type, price_text)

    return results

def fetch_carbondale(url, html_path=None):
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path = f"./web_data/{today_str}_carbondale.html"
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

def extract_carbondale(carbondale_soup):
    """
    Extracts unit name and price from storquest_soup and removes duplicate (unit_name, price) pairs.
    """
    units_tables = {}
    for idx, div in enumerate(carbondale_soup.find_all("div", class_="bg-white rounded-xl shadow-xl border flex flex-col")):
        units_tables[f'unitsTable_{idx}'] = div.decode_contents()


    results = {}
    for idx, (key, table_html) in enumerate(units_tables.items()):

        table_soup = BeautifulSoup(table_html, "html.parser")
        unit_name = table_soup.find("p", class_="text-xl font-bold")
        unit_name_text = unit_name.get_text(strip=True) if unit_name else None
        price = table_soup.find("dd", class_="text-xl font-bold")
        price_text = price.get_text(strip=True).replace("$", "") if price else None
        if len(unit_name_text.split(" ")) < 2:
            unit_type = table_soup.find("p", class_="text-sm").get_text(strip=True) if table_soup.find("p", class_="text-sm") else ""
            unit_size = unit_name_text.split(" ")[0]
        else:
            unit_size = unit_name_text.split(" ")[0]
            unit_type = table_soup.find("p", class_="text-sm").get_text(strip=True) if table_soup.find("p", class_="text-sm") else ""
            unit_type = unit_type.join(unit_name_text.split(" ")[1:])


        results[idx] = (unit_size, unit_type, price_text)

    return results


def combine_all_results(sopris_results, storquest_results, storage_mart_results, all_hours_results, carbondale_results):
    """
    Combines all results from extract functions into a single list of dictionaries.
    Each dictionary contains: facility_name, date_acquired, unit_type, price
    """
    today_str = datetime.date.today().isoformat()
    combined = []

    for idx, (unit_size, unit_type, price) in sopris_results.items():
        combined.append({
            "facility_name": "Sopris Self Storage",
            "date_acquired": today_str,
            "unit_size": unit_size,
            "unit_type": unit_type,
            "price": price
        })
    for idx, (unit_size, unit_type, price) in storquest_results.items():
        combined.append({
            "facility_name": "StorQuest Self Storage",
            "date_acquired": today_str,
            "unit_size": unit_size,
            "unit_type": unit_type,
            "price": price
        })
    for idx, (unit_size, unit_type, price) in storage_mart_results.items():
        combined.append({
            "facility_name": "StorageMart",
            "date_acquired": today_str,
            "unit_size": unit_size,
            "unit_type": unit_type,
            "price": price
        })
    for idx, (unit_size, unit_type, price) in all_hours_results.items():
        combined.append({
            "facility_name": "All Hours Storage",
            "date_acquired": today_str,
            "unit_size": unit_size,
            "unit_type": unit_type,
            "price": price
        })
    for idx, (unit_size, unit_type, price) in carbondale_results.items():
        combined.append({
            "facility_name": "Carbondale Mini Storage",
            "date_acquired": today_str,
            "unit_size": unit_size,
            "unit_type": unit_type,
            "price": price
        })

    return combined

def create_db_and_table(db_path="storage_data.db"):
    """
    Creates a SQLite database and a table for storage results if they do not exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS storage_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_name TEXT,
            date_acquired TEXT,
            unit_size TEXT,
            unit_type TEXT,
            price TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_combined_results(results, db_path="storage_data.db"):
    """
    Inserts a list of combined results (list of dicts) into the storage_results table.
    Checks to make sure all data is added and avoids inserting duplicates.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    success_count = 0
    for entry in results:
        # Check if this entry already exists in the database
        cursor.execute("""
            SELECT 1 FROM storage_results
            WHERE facility_name = ? AND date_acquired = ? AND unit_size = ? AND unit_type = ? AND price = ?
        """, (
            entry.get("facility_name"),
            entry.get("date_acquired"),
            entry.get("unit_size"),
            entry.get("unit_type"),
            entry.get("price")
        ))
        exists = cursor.fetchone()
        if not exists:
            cursor.execute("""
                INSERT INTO storage_results (facility_name, date_acquired, unit_size, unit_type, price)
                VALUES (?, ?, ?, ?, ?)
            """, (
                entry.get("facility_name"),
                entry.get("date_acquired"),
                entry.get("unit_size"),
                entry.get("unit_type"),
                entry.get("price")
            ))
            success_count += 1
    conn.commit()

    print(f"{success_count} new records added to the database (duplicates skipped).")

    conn.close()

def get_all_storage_results(db_path="storage_data.db"):
    """
    Retrieves all records from the storage_results table.
    Returns a list of dictionaries.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT facility_name, date_acquired, unit_size, unit_type, price FROM storage_results")
    rows = cursor.fetchall()
    conn.close()
    # Convert to list of dicts
    results = [
        {
            "facility_name": row[0],
            "date_acquired": row[1],
            "unit_size": row[2],
            "unit_type": row[3],
            "price": row[4]
        }
        for row in rows
    ]

    return results