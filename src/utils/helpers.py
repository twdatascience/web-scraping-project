# =========================
# Imports
# =========================
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
import glob

# =========================
# Excel Helpers
# =========================

def write_multiple_results_to_excel(
    sopris_results, storquest_results, storage_mart_results,
    all_hours_results, carbondale_results, basalt_results,
    excel_path="storage_results.xlsx"
):
    """
    Write results for each facility to separate sheets in a single Excel file.
    """
    today_str = datetime.date.today().isoformat()
    with pd.ExcelWriter(excel_path) as writer:
        # Sopris sheet
        df_sopris = pd.DataFrame.from_dict(sopris_results, orient='index', columns=['unit_size', 'unit_type', 'price'])
        df_sopris.to_excel(writer, index=False, sheet_name=f"{today_str} Sopris Self Storage")
        # StorQuest sheet
        df_storquest = pd.DataFrame.from_dict(storquest_results, orient='index', columns=['unit_size', 'unit_type', 'price'])
        df_storquest.to_excel(writer, index=False, sheet_name=f"{today_str} StorQuest Self Storage")
        # Storage Mart sheet
        df_storage_mart = pd.DataFrame.from_dict(storage_mart_results, orient='index', columns=['unit_size', 'unit_type', 'price'])
        df_storage_mart.to_excel(writer, index=False, sheet_name=f"{today_str} StorageMart")
        # All Hours sheet
        df_all_hours = pd.DataFrame.from_dict(all_hours_results, orient='index', columns=['unit_size', 'unit_type', 'price'])
        df_all_hours.to_excel(writer, index=False, sheet_name=f"{today_str} All Hours Storage")
        # Carbondale sheet
        df_carbondale = pd.DataFrame.from_dict(carbondale_results, orient='index', columns=['unit_size', 'unit_type', 'price'])
        df_carbondale.to_excel(writer, index=False, sheet_name=f"{today_str} Carbondale Mini Storage")
        # Basalt Mini sheet
        df_basalt = pd.DataFrame.from_dict(basalt_results, orient='index', columns=['unit_size', 'unit_type', 'price'])
        df_basalt.to_excel(writer, index=False, sheet_name=f"{today_str} Basalt Mini Storage")

# =========================
# Sopris Self Storage
# =========================

def fetch_sopris_self_storage(url, html_path=None):
    """
    Fetch Sopris Self Storage page and return BeautifulSoup object.
    """
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path = f"./web_data/{today_str}_soprisselfstorage.html"
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    delay = 20
    try:
        WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'currentUnit-price'))
        )
    except TimeoutException:
        print("Timed out waiting for page to load")
    page_source = driver.page_source
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(page_source)
    soup = BeautifulSoup(page_source, "html.parser")
    driver.quit()
    return soup

def extract_sopris(sopris_soup):
    """
    Extracts unit name and price from Sopris Self Storage HTML.
    """
    units_tables = {}
    for idx, div in enumerate(sopris_soup.find_all("div", class_="unitsTable")):
        units_tables[f'unitsTable_{idx}'] = div.decode_contents()
    results = {}
    for idx, (key, table_html) in enumerate(units_tables.items()):
        table_soup = BeautifulSoup(table_html, "html.parser")
        unit_name_span = table_soup.find("span", class_="candee_translate unitName")
        unit_name = unit_name_span.get_text(strip=True) if unit_name_span else None
        parts = unit_name.split(" ", 1)
        if len(parts) == 2:
            unit_size, unit_type = parts
        else:
            unit_size = unit_name
            unit_type = ""
        price = table_soup.find(class_="currentUnit-price")
        price_text = price.get_text(strip=True) if price else None
        results[idx] = (unit_size, unit_type, price_text)
    return results

# =========================
# StorQuest Self Storage
# =========================

def fetch_storquest_self_storage(url, html_path=None):
    """
    Fetch StorQuest Self Storage page and return BeautifulSoup object.
    """
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path = f"./web_data/{today_str}_storquestselfstorage.html"
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    delay = 20
    try:
        view_all_units = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[span[text()='View All Units']]"))
        )
        view_all_units.click()
    except TimeoutException:
        print("Timed out waiting for page to load")
    page_source = driver.page_source
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(page_source)
    soup = BeautifulSoup(page_source, "html.parser")
    driver.quit()
    return soup

def extract_storquest(storquest_soup):
    """
    Extracts unit name and price from StorQuest Self Storage HTML.
    Removes duplicate (unit_name, price) pairs.
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
        if (unit_size, unit_type, price_text) not in seen:
            results[idx] = (unit_size, unit_type, price_text)
            seen.add((unit_size, unit_type, price_text))
    return results

# =========================
# StorageMart
# =========================

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
        EC.presence_of_element_located((By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]"))
    )
    time.sleep(5)
    parking = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]")
    ActionChains(driver).scroll_to_element(parking).perform()
    time.sleep(2)
    try:
        h3_medium = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Medium')]")
        h3_medium.click()
    except Exception as e:
        print(f"could not find medium div\n{e}")
    parking = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]")
    ActionChains(driver).scroll_to_element(parking).perform()
    time.sleep(2)
    try:
        h3_large = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Large')]")
        h3_large.click()
    except:
        print("could not find large div")
    parking = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]")
    ActionChains(driver).scroll_to_element(parking).perform()
    ActionChains(driver).scroll_by_amount(0, 200).perform()
    time.sleep(2)
    try:
        h3_parking = driver.find_element(By.XPATH, "//h3[@class='e39HRxPzw1eCSAWspRQoK']/div[@role='button'][contains(., 'Parking')]")
        h3_parking.click()
    except:
        print("could not find parking div")
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
        price = None
        price_div = table_soup.find("div", class_="_1n0aDKzz825gOOrRZCKcmI text-dark-gray")
        if price_div:
            price_span = price_div.find("span")
            if price_span:
                price = price_span.get_text(strip=True).replace("$", "")
        else:
            price = "Sold Out"
        results[idx] = (unit_size, unit_type, price)
    return results

# =========================
# All Hours Storage
# =========================

def fetch_all_hours(url, html_path=None):
    """
    Fetch All Hours Storage page and return BeautifulSoup object.
    """
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path = f"./web_data/{today_str}_all_hours.html"
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='unit-type-container-large']"))
    )
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(page_source)
    driver.quit()
    return soup

def extract_all_hours(all_hours_soup):
    """
    Extracts unit name and price from All Hours Storage HTML.
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

# =========================
# Carbondale Mini Storage
# =========================

def fetch_carbondale(url, html_path=None):
    """
    Fetch Carbondale Mini Storage page and return BeautifulSoup object.
    """
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path = f"./web_data/{today_str}_carbondale.html"
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='grid grid-cols-1 lg:grid-cols-2 gap-6']"))
    )
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(page_source)
    driver.quit()
    return soup

def extract_carbondale(carbondale_soup):
    """
    Extracts unit name and price from Carbondale Mini Storage HTML.
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

# =========================
# Basalt Mini Storage (CC and Regular)
# =========================

def fetch_basalt_mini(basalt_cc, basalt_reg, html_path=None):
    """
    Fetch Basalt Mini Storage (CC and Regular) pages and return two BeautifulSoup objects.
    """
    if html_path is None:
        today_str = datetime.date.today().isoformat()
        html_path_reg = f"./web_data/{today_str}_basaltmini_reg.html"
        html_path_cc = f"./web_data/{today_str}_basaltmini_cc.html"
    os.makedirs(os.path.dirname(html_path_reg), exist_ok=True)
    os.makedirs(os.path.dirname(html_path_cc), exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.get(basalt_reg)
    delay = 20
    try:
        WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.XPATH, '//li[@class="list-group-item btn-primary ng-binding"]'))
        )
    except TimeoutException:
        print("Timed out waiting for page to load")
    page_source = driver.page_source
    with open(html_path_reg, 'w', encoding='utf-8') as f:
        f.write(page_source)
    soup1 = BeautifulSoup(page_source, "html.parser")
    driver.quit()
    driver = webdriver.Chrome(options=options)
    driver.get(basalt_cc)
    try:
        WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.XPATH, '//li[@class="list-group-item btn-primary ng-binding"]'))
        )
    except TimeoutException:
        print("Timed out waiting for page to load")
    page_source2 = driver.page_source
    with open(html_path_cc, 'w', encoding='utf-8') as f:
        f.write(page_source2)
    soup2 = BeautifulSoup(page_source2, "html.parser")
    driver.quit()
    return soup1, soup2

def extract_basalt(basalt_soup1, basalt_soup2):
    """
    Extracts unit name and price from Basalt Mini Storage HTML (CC and Regular).
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

# =========================
# Data Combination
# =========================

def combine_all_results(
    sopris_results, storquest_results, storage_mart_results,
    all_hours_results, carbondale_results, basalt_results
):
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
    for idx, (unit_size, unit_type, price) in basalt_results.items():
        combined.append({
            "facility_name": "Basalt Mini Storage",
            "date_acquired": today_str,
            "unit_size": unit_size,
            "unit_type": unit_type,
            "price": price
        })
    return combined

# =========================
# Database Helpers
# =========================

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

# =========================
# Sync Web Data to Database
# =========================

def sync_web_data_to_db(db_path="storage_data.db", web_data_dir="./web_data"):
    """
    Checks if the database has the info from web_data. If not, loads HTML files,
    processes them, and adds them to the database.
    """
    html_files = glob.glob(os.path.join(web_data_dir, "*.html"))
    existing = get_all_storage_results(db_path=db_path)
    existing_set = set(
        (r["facility_name"], r["date_acquired"], r["unit_size"], r["unit_type"], r["price"])
        for r in existing
    )
    extract_map = [
        ("soprisselfstorage", extract_sopris, "Sopris Self Storage"),
        ("storquestselfstorage", extract_storquest, "StorQuest Self Storage"),
        ("storage_mart", extract_storage_mart, "StorageMart"),
        ("all_hours", extract_all_hours, "All Hours Storage"),
        ("carbondale", extract_carbondale, "Carbondale Mini Storage"),
        ("basaltmini_cc", lambda soup: extract_basalt(soup, BeautifulSoup("", "html.parser")), "Basalt Mini Storage"),
        ("basaltmini_reg", lambda soup: extract_basalt(BeautifulSoup("", "html.parser"), soup), "Basalt Mini Storage"),
    ]
    new_results = []
    for html_file in html_files:
        basename = os.path.basename(html_file)
        for pattern, extract_func, facility_name in extract_map:
            if pattern in basename:
                date_str = basename.split("_")[0]
                # Special handling for Basalt Mini Storage (needs both cc and reg files)
                if pattern == "basaltmini_cc":
                    cc_file = os.path.join(web_data_dir, f"{date_str}_basaltmini_cc.html")
                    reg_file = os.path.join(web_data_dir, f"{date_str}_basaltmini_reg.html")
                    if os.path.exists(cc_file) and os.path.exists(reg_file):
                        with open(cc_file, encoding="utf-8") as f1, open(reg_file, encoding="utf-8") as f2:
                            soup1 = BeautifulSoup(f1.read(), "html.parser")
                            soup2 = BeautifulSoup(f2.read(), "html.parser")
                        results = extract_basalt(soup1, soup2)
                        for idx, (unit_size, unit_type, price) in results.items():
                            key = (facility_name, date_str, unit_size, unit_type, price)
                            if key not in existing_set:
                                new_results.append({
                                    "facility_name": facility_name,
                                    "date_acquired": date_str,
                                    "unit_size": unit_size,
                                    "unit_type": unit_type,
                                    "price": price
                                })
                    break  # Don't process cc file again as reg
                elif pattern == "basaltmini_reg":
                    # Only process in cc block above
                    break
                else:
                    with open(html_file, encoding="utf-8") as f:
                        soup = BeautifulSoup(f.read(), "html.parser")
                    results = extract_func(soup)
                    for idx, (unit_size, unit_type, price) in results.items():
                        key = (facility_name, date_str, unit_size, unit_type, price)
                        if key not in existing_set:
                            new_results.append({
                                "facility_name": facility_name,
                                "date_acquired": date_str,
                                "unit_size": unit_size,
                                "unit_type": unit_type,
                                "price": price
                            })
                    break
    if new_results:
        print(f"Adding {len(new_results)} new records from web_data to the database.")
        insert_combined_results(new_results, db_path=db_path)
    else:
        print("No new records to add from web_data.")

# =========================
# END OF FILE
# =========================