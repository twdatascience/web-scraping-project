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