# Web Scraping Project

## Overview
This project scrapes storage unit pricing and availability from multiple self-storage facility websites, stores the data in a local SQLite database, and provides an interactive dashboard for analysis.

## Features
- Automated scraping of several storage facility websites using Selenium and BeautifulSoup
- Data extraction and normalization for unit size, type, and price
- Daily HTML archiving for reproducibility and backup
- Data storage in a SQLite database with deduplication
- Export of results to Excel (one sheet per facility)
- Interactive dashboard (Dash/Plotly) for price comparison and history

## Installation

1. **Clone the repository:**
   ```
   git clone <repository-url>
   ```
2. **Navigate to the project directory:**
   ```
   cd web-scraping-project
   ```
3. **Install the required packages:**
   ```
   pip install -r requirements.txt
   ```

## Usage

### 1. Scrape and Store Data
To run the web scraping script and update the database and Excel file:
```
python src/scraper.py
```
- If today's data already exists in `web_data/`, it will only sync to the database.
- Otherwise, it will fetch new data, extract, store, and export.

### 2. Launch the Dashboard
To view and analyze the collected data in your browser:
```
python src/dashboard.py
```
- The dashboard will open automatically and allow you to filter, compare, and visualize storage unit prices by size, facility, and date.

## Project Structure

```
web-scraping-project/
│
├── src/
│   ├── scraper.py        # Main scraping and data pipeline script
│   ├── dashboard.py      # Interactive dashboard for data analysis
│   └── utils/
│       └── helpers.py    # All scraping, extraction, and database helper functions
│
├── web_data/             # Archived HTML files from each scrape (auto-created)
├── storage_data.db       # SQLite database (auto-created)
├── storage_results.xlsx  # Excel export (auto-created)
├── requirements.txt      # Python dependencies
└── README.md
```

## Contributing
If you would like to contribute to this project, please fork the repository and submit a pull request with your changes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.