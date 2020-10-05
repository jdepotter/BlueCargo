import requests

def download_page_content(url):
    page = requests.get(url)

    if page.status_code == 200:
        return page.text

    raise Exception(page.status_code, f'Fail to download page for: {url}')