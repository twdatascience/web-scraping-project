def clean_text(text):
    """Cleans the input text by stripping whitespace and removing unwanted characters."""
    return text.strip()

def format_data(data):
    """Formats the extracted data into a desired structure, such as a dictionary."""
    return {key: clean_text(value) for key, value in data.items()}

def extract_links(html_content):
    """Extracts all hyperlinks from the given HTML content."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, 'html.parser')
    return [a['href'] for a in soup.find_all('a', href=True)]