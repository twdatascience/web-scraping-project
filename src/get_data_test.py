from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

import pdb

url = 'https://soprisselfstorage.com/rent-storage/'

# Set up Selenium (Chrome)
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=options)

# Navigate to the dynamic website
driver.get(url)

delay = 20

try:
    myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'currentUnit-price')))
except TimeoutException:
    print("Timed out waiting for page to load")

# Get the page source after the content is loaded
page_source = driver.page_source

with open("page.html", 'w', encoding='utf-8') as f:
        f.write(page_source)

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(page_source, "html.parser")



# Extract the dynamic content (e.g., specific elements)
dynamic_content = soup.find("div", {"class": "unitsTable"})

# Print the dynamic content
print(dynamic_content)

# Close the browser
driver.quit()