from bs4 import BeautifulSoup
import pandas as pd

def extract_units_tables(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    units_tables = {}
    for idx, div in enumerate(soup.find_all("div", class_="unitsTable")):
        units_tables[f'unitsTable_{idx}'] = div.decode_contents()
    return units_tables

# Example usage:
if __name__ == "__main__":
    html_file = "./page.html"
    tables_dict = extract_units_tables(html_file)


    # Loop through all tables and extract unitName and currentUnit-price
    results = {}
    for idx, (key, table_html) in enumerate(tables_dict.items()):
        table_soup = BeautifulSoup(table_html, "html.parser")
        # Extract unit name from <span class="candee_translate unitName">
        unit_name_span = table_soup.find("span", class_="candee_translate unitName")
        unit_name = unit_name_span.get_text(strip=True) if unit_name_span else None

        # Extract currentUnit-price (assuming in an element with class 'currentUnit-price')
        price = table_soup.find(class_="currentUnit-price")
        price_text = price.get_text(strip=True) if price else None

        results[idx] = (unit_name, price_text)

    # Write results to Excel file without index column and with sheet name "name1"
    df = pd.DataFrame.from_dict(results, orient='index', columns=['unit_name', 'price'])
    df.to_excel("units_results.xlsx", index=False, sheet_name="name1")





