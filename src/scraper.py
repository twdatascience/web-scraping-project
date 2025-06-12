import os
from bs4 import BeautifulSoup
import pickle
from selenium import webdriver

def fetch_page(url):
    # Use Selenium with headless browser to fetch JavaScript-rendered content
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    browser = webdriver.Chrome(options=options)
    try:
        browser.get(url)
        html = browser.page_source
    finally:
        browser.quit()
    return html

def parse_html(html):
    soup = BeautifulSoup(html, 'lxml')  # Use lxml for better performance
    return soup

def extract_information(soup):
    # Example: Extracting all the headings from the page
    headings = soup.find_all('h1')
    return [heading.get_text() for heading in headings]

def main(url, save=False, use_cache=False, html_path='page.html', soup_path='soup.pkl'):
    if use_cache and os.path.exists(html_path) and os.path.exists(soup_path):
        html, soup = load_data(html_path, soup_path)
    else:
        html = fetch_page(url)
        soup = parse_html(html)
        if save:
            save_data(html, soup, html_path, soup_path)
    information = extract_information(soup)
    return information

if __name__ == "__main__":
    url = 'https://soprisselfstorage.com/rent-storage/'  # Replace with the target website
    data = main(url, save=True, use_cache=True)
    print(data)